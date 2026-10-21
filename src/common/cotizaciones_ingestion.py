"""Isolated cotizaciones path: strict CSV, durable stages and Delta adapters.

Only small file/audit metadata reaches the driver. File bytes and business rows
are parsed on executors, with a measured, explicit per-file resource limit.
"""
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import re
import uuid

from src.common.cotizaciones_contract import (
    CONTRACT_VERSION, FIELDS, FIELD_TYPES, json_value, normalize_record,
)

MAX_FILE_BYTES = 64 * 1024 * 1024
NAME_PATTERN = re.compile(r"fact_cotizaciones_(0[1-9]|1[0-2])\.csv")
STAGES = ("ORIGINAL", "EVIDENCE", "MAIN", "QUARANTINE", "AUDIT", "SUCCESS")


def is_cotizaciones(area, source):
    return area == "comercial" and source["source_file_name"].lower().startswith("fact_cotizaciones")


def split_sources(area, sources, month=""):
    if month and not re.fullmatch(r"0[1-9]|1[0-2]", month):
        raise ValueError("INVALID_COTIZACIONES_MONTH")
    specialized, generic = [], []
    for source in sources:
        if is_cotizaciones(area, source):
            if not month or source.get("source_month") == month:
                specialized.append(source)
        else:
            generic.append(source)
    return specialized, generic


def _valid_quotes(raw):
    state = "start"
    for character in raw:
        if state == "quoted":
            if character == '"':
                state = "end"
        elif state == "end" and character == '"':
            state = "quoted"
        elif character in ",\r\n":
            state = "start"
        elif state == "start":
            state = "quoted" if character == '"' else "unquoted"
        elif character == '"' or state == "end":
            return False
    return state != "quoted"


def resolve_period(source, year):
    match = NAME_PATTERN.fullmatch(source["source_file_name"])
    if not match or not re.fullmatch(r"[0-9]{4}", year):
        raise ValueError("INVALID_FILE_NAME_OR_YEAR")
    month = match.group(1)
    parts = source["source_path"].rstrip("/").split("/")
    if source.get("source_month") != month or parts[-3:-1] != [year, month]:
        raise ValueError("FILE_FOLDER_PARAMETER_PERIOD_MISMATCH")
    return f"{year}-{month}"


def logical_file_id(period, checksum):
    return hashlib.sha256(f"fact_cotizaciones|{period}|{checksum}".encode()).hexdigest()


def parse_csv_bytes(content, period, max_bytes=MAX_FILE_BYTES):
    """Yield records with logical ordinal + physical line bounds in exact bytes.

    A framing error is a file failure; a delimited width error is one rejected
    record. The immutable file allows reconstruction even for invalid UTF-8.
    """
    if not content or len(content) > max_bytes:
        raise ValueError("EMPTY_FILE" if not content else "FILE_SIZE_LIMIT")
    try:
        text = bytes(content).decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError("INVALID_UTF8") from error
    # str.splitlines also splits valid U+0085/U+2028/U+2029 inside CSV fields.
    # StringIO universal newlines uses precisely the CSV physical line endings.
    lines = io.StringIO(text, newline="").readlines()
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=",", quotechar='"',
                        doublequote=True, strict=True)
    try:
        header = next(reader)
        if len(set(header)) != len(header) or not set(FIELDS).issubset(header):
            raise ValueError("INVALID_HEADER")
        extra = set(header) - set(FIELDS)
        end, count = reader.line_num, 0
        for ordinal, tokens in enumerate(reader, 1):
            start, previous = end + 1, end
            end, count = reader.line_num, ordinal
            original = dict(zip(header, tokens))
            row = normalize_record(original, period)
            if len(tokens) != len(header) or not _valid_quotes("".join(lines[previous:end])):
                row["errors"].append({"field": "__record__", "code": "CSV_MALFORMED"})
            row["alerts"].extend({"field": field, "code": "EXTRA_COLUMN"} for field in sorted(extra))
            row.update(ordinal=ordinal, line_start=start, line_end=end,
                       raw_record="".join(lines[previous:end]), original_tokens=tokens)
            yield row
        if not count:
            raise ValueError("EMPTY_DATA")
    except (csv.Error, StopIteration) as error:
        raise ValueError("CSV_FRAMING_ERROR") from error


class CotizacionesEngine:
    """State machine shared by the real Delta adapter and local failure tests."""

    def __init__(self, store, config):
        self.store, self.config = store, config

    def _failure(self, audit, stage, error):
        audit.update(status="FAILED", failed_stage=stage, error_type=type(error).__name__)
        failures = []
        try:
            self.store.save_audit(audit)
        except Exception as log_error:
            failures.append(type(log_error).__name__)
        try:
            self.store.log_failure(audit, stage, error)
        except Exception as log_error:
            failures.append(str(log_error))
        if failures:
            raise RuntimeError(f"FAILED_LOG_UNAVAILABLE stage={stage} hash={audit.get('checksum')} {' '.join(failures)}") from error

    def _complete(self, audit):
        stage = "ORIGINAL"
        try:
            if not self.store.exists(audit["original_path"]):
                if self.store.checksum(audit["source_path"]) != audit["checksum"]:
                    raise ValueError("SOURCE_CHECKSUM_CHANGED")
                self.store.copy(audit["source_path"], audit["original_path"])
            if self.store.checksum(audit["original_path"]) != audit["checksum"]:
                raise ValueError("ORIGINAL_CHECKSUM_MISMATCH")
            self.store.checkpoint(stage)
            audit.update(status="PROCESSING")
            rows = self.store.prepare(audit)
            audit["metrics"] = self.store.metrics(rows)
            metrics = audit["metrics"]
            if metrics["read"] != sum(metrics[k] for k in ("accepted", "rejected", "consolidated")):
                raise ValueError("UNBALANCED_CLASSIFICATION")
            for stage, operation in [("EVIDENCE", self.store.write_evidence),
                                      ("MAIN", self.store.write_main),
                                      ("QUARANTINE", self.store.write_quarantine)]:
                # Re-execution is idempotent; persisted stages are still verified
                # during reconciliation. Never trust a stage label alone.
                if stage not in audit["completed"]:
                    operation(audit, rows)
                    self.store.checkpoint(stage)
                    audit["completed"].append(stage)
                    self.store.save_audit(audit)
            stage = "AUDIT"
            self.store.save_audit(audit)
            self.store.checkpoint(stage)
            self.store.reconcile(audit)
            audit["status"] = "SUCCESS"
            stage = "SUCCESS"
            self.store.save_audit(audit)
            self.store.checkpoint(stage)
            return audit
        except Exception as error:
            self._failure(audit, stage, error)
            raise
        finally:
            if "rows" in locals() and hasattr(rows, "unpersist"):
                rows.unpersist()

    def ingest(self, source):
        owner = str(uuid.uuid4())
        self.store.reserve(owner)
        try:
            # Complete older partial contents before assigning a new version.
            for pending in self.store.pending():
                pending["attempt_id"] = owner
                self._complete(pending)
            audit = {"attempt_id": owner, "file_id": "invalid-" + owner,
                     "source_path": source["source_path"], "source_file_name": source["source_file_name"],
                     "period": None, "checksum": None, "sequence": 0, "completed": [], "receipts": []}
            try:
                period = resolve_period(source, self.config["data_year"])
                checksum = self.store.checksum(source["source_path"])
                file_id = logical_file_id(period, checksum)
                audit.update(file_id=file_id, period=period, checksum=checksum)
            except Exception as error:
                # Invalid files are logged, but do not enter recoverable data stages.
                self.store.log_failure(audit, "IDENTIFY", error)
                raise
            existing = self.store.audit(file_id)
            if existing:
                audit = existing
                audit["attempt_id"] = owner
            else:
                audit.update(sequence=self.store.next_sequence(), status="PROCESSING",
                    contract_version=CONTRACT_VERSION,
                    initial_attempt_id=owner,
                    original_path=f"{self.config['originals']}/{checksum}/{source['source_file_name']}",
                    created_at=datetime.now(timezone.utc).isoformat())
            receipt = {"attempt_id": owner, "source_path": source["source_path"],
                       "source_file_name": source["source_file_name"], "archived": False,
                       "received_at": datetime.now(timezone.utc).isoformat(),
                       "historic_path": f"{self.config['historic_area_root']}/{period[:4]}/{period[5:]}/cotizaciones/{checksum}/{source['source_file_name']}"}
            audit["receipts"].append(receipt)
            try:
                self.store.save_audit(audit)
            except Exception as error:
                self._failure(audit, "RESERVE_FILE", error)
                raise
            if audit["status"] == "SUCCESS":
                try:
                    self.store.reconcile(audit, current=False)
                except Exception as error:
                    # Preserve completion marker: a replay must never reapply
                    # old values after a subsequent correction.
                    self.store.log_failure(audit, "REPLAY_RECONCILE", error)
                    raise
                return audit
            return self._complete(audit)
        finally:
            self.store.release(owner)


def archive_receipt(store, audit, receipt):
    """Only a reconciled reception may move, including recovery after a move."""
    if audit["status"] != "SUCCESS":
        raise ValueError("ARCHIVE_REQUIRES_SUCCESS")
    store.reconcile(audit, current=False)
    source, target, checksum = receipt["source_path"], receipt["historic_path"], audit["checksum"]
    source_exists, target_exists = store.exists(source), store.exists(target)
    if source_exists and store.checksum(source) != checksum:
        raise ValueError("SOURCE_CHECKSUM_CHANGED")
    if target_exists and store.checksum(target) != checksum:
        raise ValueError("HISTORIC_CHECKSUM_MISMATCH")
    if not source_exists and not target_exists:
        raise FileNotFoundError("SOURCE_AND_HISTORIC_MISSING")
    if source_exists:
        if not target_exists:
            store.move(source, target)
        else:
            # A previous reception already archived these exact bytes.
            store.remove(source)
    if store.checksum(target) != checksum:
        raise ValueError("HISTORIC_CHECKSUM_MISMATCH")
    store.checkpoint("MOVE")
    receipt.update(archived=True, archived_at=datetime.now(timezone.utc).isoformat())
    store.save_audit(audit)


def _spark_types():
    from pyspark.sql import types as T
    issue = T.ArrayType(T.StructType([
        T.StructField("field", T.StringType(), False),
        T.StructField("code", T.StringType(), False),
    ]), False)
    def datatype(kind):
        if kind.startswith("decimal"):
            return T.DecimalType(*map(int, re.findall(r"\d+", kind)))
        return {"string": T.StringType(), "int": T.IntegerType(), "date": T.DateType()}[kind]
    business = [T.StructField(name, datatype(kind), True) for name, kind in FIELD_TYPES.items()]
    metadata = [
        T.StructField("_np_file_id", T.StringType(), False),
        T.StructField("_np_load_id", T.StringType(), False),
        T.StructField("_np_attempt_id", T.StringType(), False),
        T.StructField("_np_record_id", T.StringType(), False),
        T.StructField("_np_sequence", T.LongType(), False),
        T.StructField("_np_source_year", T.StringType(), False),
        T.StructField("_np_source_month", T.StringType(), False),
        T.StructField("_np_source_path", T.StringType(), False),
        T.StructField("_np_source_file_name", T.StringType(), False),
        T.StructField("_np_original_path", T.StringType(), False),
        T.StructField("_np_ingestion_ts", T.TimestampType(), False),
        T.StructField("_np_quality_alerts", issue, False),
    ]
    evidence = [
        T.StructField("ordinal", T.LongType(), False),
        T.StructField("line_start", T.LongType(), False),
        T.StructField("line_end", T.LongType(), False),
        T.StructField("raw_record", T.StringType(), False),
        T.StructField("payload", T.StringType(), False),
        T.StructField("normalized", T.StringType(), False),
        T.StructField("conversions", T.StringType(), False),
        T.StructField("errors", issue, False),
        T.StructField("fingerprint", T.StringType(), False),
    ]
    return T, issue, business, metadata, evidence


def _parse_partition(files, audit):
    """Executor-only parser. No SparkSession or driver objects in closure."""
    processed_at = datetime.fromisoformat(audit["created_at"]).replace(tzinfo=None)
    for file in files:
        for record in parse_csv_bytes(file.content, audit["period"]):
            ordinal = record["ordinal"]
            yield {
                **record["values"], "ordinal": ordinal,
                "line_start": record["line_start"], "line_end": record["line_end"],
                "raw_record": record["raw_record"],
                "payload": json_value({"fields": record["original"], "tokens": record["original_tokens"]}),
                "normalized": json_value(record["values"]), "conversions": json_value(record["conversions"]),
                "errors": record["errors"], "fingerprint": record["fingerprint"],
                "_np_file_id": audit["file_id"],
                "_np_load_id": audit["file_id"], "_np_attempt_id": audit["initial_attempt_id"],
                "_np_record_id": hashlib.sha256(f"{audit['file_id']}|{ordinal}".encode()).hexdigest(),
                "_np_sequence": audit["sequence"],
                "_np_source_year": audit["period"][:4], "_np_source_month": audit["period"][5:],
                "_np_source_path": audit["source_path"], "_np_source_file_name": audit["source_file_name"],
                "_np_original_path": audit["original_path"], "_np_ingestion_ts": processed_at,
                "_np_quality_alerts": record["alerts"],
            }


class SparkDeltaStore:
    """Real Spark/Delta backend. Control tables are path-only, outside UC lists.

    Reservation is fail-closed: no clock-based lock stealing while an operation
    could still be running. A killed driver leaves a visible reservation for
    operator reconciliation; ordinary exceptions always release it.
    """
    def __init__(self, spark, dbutils, config):
        from src.common.config import cotizaciones_paths
        from delta.tables import DeltaTable
        from pyspark.sql import functions as F, types as T
        self.spark, self.dbutils, self.config = spark, dbutils, config
        self.paths = cotizaciones_paths(config)
        self.DeltaTable, self.F, self.T = DeltaTable, F, T
        self.owner = None
        self.audit_schema = T.StructType([
            T.StructField("file_id", T.StringType(), False),
            T.StructField("payload", T.StringType(), False),
            T.StructField("status", T.StringType(), False),
            T.StructField("sequence", T.LongType(), False),
            T.StructField("owner", T.StringType(), True),
        ])

    def checkpoint(self, stage):
        """Durable boundary; synthetic suites inject failure by overriding it."""
        return None

    def _exists_delta(self, path):
        return self.DeltaTable.isDeltaTable(self.spark, path)

    def _read(self, name):
        return self.spark.read.format("delta").load(self.paths[name])

    def _merge(self, name, dataframe, keys, update=True):
        path = self.paths[name]
        if not self._exists_delta(path):
            dataframe.write.format("delta").mode("errorifexists").save(path)
            return
        condition = " AND ".join(f"t.`{key}` = s.`{key}`" for key in keys)
        merge = self.DeltaTable.forPath(self.spark, path).alias("t").merge(dataframe.alias("s"), condition)
        if update:
            merge = merge.whenMatchedUpdateAll()
        merge.whenNotMatchedInsertAll().execute()

    def _initialize_control(self):
        if self._exists_delta(self.paths["file_audit"]):
            return
        row = {"file_id": "__ENTITY__", "payload": "{}", "status": "RESERVATION", "sequence": 0, "owner": None}
        try:
            self.spark.createDataFrame([row], self.audit_schema).write.format("delta").mode("errorifexists").save(self.paths["file_audit"])
        except Exception:
            # Concurrent initialization is fine only if a valid lock row exists.
            if not self._exists_delta(self.paths["file_audit"]):
                raise

    def _lock(self):
        rows = self._read("file_audit").filter(self.F.col("file_id") == "__ENTITY__").take(2)
        if len(rows) != 1:
            raise RuntimeError("INVALID_ENTITY_RESERVATION")
        return rows[0]

    def _assert_owner(self):
        if self.owner is None or self._lock().owner != self.owner:
            raise RuntimeError("ENTITY_RESERVATION_LOST")

    def reserve(self, owner):
        self._initialize_control()
        F = self.F
        self.DeltaTable.forPath(self.spark, self.paths["file_audit"]).update(
            condition=(F.col("file_id") == "__ENTITY__") & F.col("owner").isNull(),
            set={"owner": F.lit(owner)})
        if self._lock().owner != owner:
            raise RuntimeError("CONCURRENT_OR_UNRECOVERED_ENTITY_RESERVATION")
        self.owner = owner

    def release(self, owner):
        self.DeltaTable.forPath(self.spark, self.paths["file_audit"]).update(
            condition=(self.F.col("file_id") == "__ENTITY__") & (self.F.col("owner") == owner),
            set={"owner": self.F.lit(None).cast("string")})
        self.owner = None

    def next_sequence(self):
        self._assert_owner()
        F = self.F
        self.DeltaTable.forPath(self.spark, self.paths["file_audit"]).update(
            condition=(F.col("file_id") == "__ENTITY__") & (F.col("owner") == self.owner),
            set={"sequence": F.col("sequence") + F.lit(1)})
        return self._lock().sequence

    def audit(self, file_id):
        rows = self._read("file_audit").filter(self.F.col("file_id") == file_id).take(2)
        if len(rows) > 1:
            raise RuntimeError("DUPLICATED_FILE_AUDIT")
        return json.loads(rows[0].payload) if rows else None

    def pending(self):
        # Small control metadata, streamed. Never collects business/file bytes.
        rows = self._read("file_audit").filter(
            (self.F.col("file_id") != "__ENTITY__") & (self.F.col("status") != "SUCCESS"))
        return (json.loads(row.payload) for row in rows.orderBy("sequence").toLocalIterator())

    def save_audit(self, audit):
        self._assert_owner()
        row = {"file_id": audit["file_id"], "payload": json_value(audit),
               "status": audit["status"], "sequence": audit["sequence"], "owner": None}
        self._merge("file_audit", self.spark.createDataFrame([row], self.audit_schema), ["file_id"])

    def log_failure(self, audit, stage, error):
        self._assert_owner()
        T = self.T
        names = ["failure_id", "attempt_id", "file_id", "checksum", "source_path", "period", "stage", "error_type", "error_code", "processed_at"]
        schema = T.StructType([T.StructField(name, T.StringType(), True) for name in names])
        row = {"failure_id": f"{audit['attempt_id']}|{stage}", "attempt_id": audit["attempt_id"],
               "file_id": audit["file_id"], "checksum": audit.get("checksum"),
               "source_path": audit["source_path"], "period": audit.get("period"),
               "stage": stage, "error_type": type(error).__name__,
               "error_code": str(error) if re.fullmatch(r"[A-Z_]+", str(error)) else type(error).__name__,
               "processed_at": datetime.now(timezone.utc).isoformat()}
        self._merge("failed_files", self.spark.createDataFrame([row], schema), ["failure_id"], update=False)

    def _binary(self, path):
        return self.spark.read.format("binaryFile").load(path)

    def checksum(self, path):
        # Projection executes SHA-256 on executor, returns a single hash/length.
        rows = self._binary(path).select(self.F.sha2("content", 256).alias("checksum"), "length").take(2)
        if len(rows) != 1:
            raise ValueError("EXPECTED_ONE_SOURCE_FILE")
        if rows[0].length > MAX_FILE_BYTES:
            raise ValueError("FILE_SIZE_LIMIT")
        return rows[0].checksum

    def exists(self, path):
        try:
            self.dbutils.fs.ls(path)
            return True
        except Exception as error:
            message = str(error)
            if any(code in message for code in ("FileNotFoundException", "PATH_NOT_FOUND", "RESOURCE_DOES_NOT_EXIST", "No such file")):
                return False
            raise

    def copy(self, source, target):
        if self.exists(target):
            raise FileExistsError("IMMUTABLE_ORIGINAL_ALREADY_EXISTS")
        self.dbutils.fs.mkdirs(target.rsplit("/", 1)[0])
        if not self.dbutils.fs.cp(source, target):
            raise OSError("ORIGINAL_COPY_FAILED")

    def move(self, source, target):
        if self.exists(target):
            raise FileExistsError("HISTORIC_ALREADY_EXISTS")
        self.dbutils.fs.mkdirs(target.rsplit("/", 1)[0])
        if not self.dbutils.fs.mv(source, target):
            raise OSError("HISTORIC_MOVE_FAILED")

    def remove(self, path):
        if not self.dbutils.fs.rm(path, False):
            raise OSError("ARCHIVED_SOURCE_REMOVE_FAILED")

    def prepare(self, audit):
        from functools import partial
        T, issue, business, metadata, evidence = _spark_types()
        F = self.F
        parsed = self.spark.createDataFrame(
            self._binary(audit["original_path"]).select("content").rdd.mapPartitions(partial(_parse_partition, audit=audit)),
            T.StructType(business + metadata + evidence))
        groups = parsed.groupBy("cotizacion_id").agg(
            F.countDistinct("fingerprint").alias("_variants"),
            F.max(F.when(F.size("errors") > 0, 1).otherwise(0)).alias("_invalid"),
            F.count("ordinal").alias("_occurrences"), F.min("ordinal").alias("representative_ordinal"))
        joined = parsed.alias("p").join(groups.alias("g"), F.col("p.cotizacion_id").eqNullSafe(F.col("g.cotizacion_id")), "inner").select(
            "p.*", "g._variants", "g._invalid", "g._occurrences", "g.representative_ordinal")
        conflict = F.col("cotizacion_id").isNotNull() & (F.col("_occurrences") > 1) & ((F.col("_variants") > 1) | (F.col("_invalid") > 0))
        duplicate_error = F.array(F.struct(F.lit("cotizacion_id").alias("field"), F.lit("DUPLICATE_PK").alias("code")))
        return joined.withColumn("errors", F.when(conflict, F.concat("errors", duplicate_error)).otherwise(F.col("errors"))).withColumn(
            "category", F.when(F.size("errors") > 0, "REJECTED").when(F.col("ordinal") == F.col("representative_ordinal"), "ACCEPTED").otherwise("CONSOLIDATED")
        ).withColumn("representative_ordinal", F.when(F.col("category") != "REJECTED", F.col("representative_ordinal"))).drop("_variants", "_invalid", "_occurrences").persist()

    def metrics(self, rows):
        F = self.F
        values = rows.agg(F.count("ordinal").alias("read"), *[
            F.sum(F.when(F.col("category") == category, 1).otherwise(0)).alias(name)
            for name, category in [("accepted", "ACCEPTED"), ("rejected", "REJECTED"), ("consolidated", "CONSOLIDATED")]
        ]).first()
        return {key: int(values[key] or 0) for key in ("read", "accepted", "rejected", "consolidated")}

    def write_evidence(self, audit, rows):
        self._assert_owner()
        self._merge("record_evidence", rows, ["_np_file_id", "_np_record_id"], update=False)

    def write_quarantine(self, audit, rows):
        self._assert_owner()
        self._merge("quarantine", rows.filter(self.F.col("category") == "REJECTED"), ["_np_file_id", "_np_record_id"], update=False)

    def _ensure_main(self, dataframe):
        path, table = self.paths["main"], self.paths["target_table"]
        expected = {field.name: field.dataType.simpleString() for field in dataframe.schema}
        if self.spark.catalog.tableExists(table):
            detail = self.spark.sql(f"DESCRIBE DETAIL {table}").first()
            if detail.format != "delta" or detail.location.rstrip("/") != path.rstrip("/") or detail.partitionColumns != ["_np_source_year", "_np_source_month"]:
                raise ValueError("INCOMPATIBLE_COTIZACIONES_LOCATION_OR_FORMAT")
        if self._exists_delta(path):
            existing = self._read("main")
            actual = {field.name: field.dataType.simpleString() for field in existing.schema}
            if expected != actual:
                raise ValueError("INCOMPATIBLE_COTIZACIONES_SCHEMA")
            if existing.schema["cotizacion_id"].nullable:
                raise ValueError("INCOMPATIBLE_COTIZACIONES_PK_CONSTRAINT")
            detail = self.DeltaTable.forPath(self.spark, path).detail().first()
            if detail.partitionColumns != ["_np_source_year", "_np_source_month"]:
                raise ValueError("INCOMPATIBLE_COTIZACIONES_PARTITIONS")
            if existing.filter(self.F.col("cotizacion_id").isNull()).limit(1).count():
                raise ValueError("INCOMPATIBLE_COTIZACIONES_NULL_PK")
            if existing.groupBy("cotizacion_id").count().filter(self.F.col("count") > 1).limit(1).count():
                raise ValueError("INCOMPATIBLE_COTIZACIONES_DUPLICATED_PK")
            if not self.spark.catalog.tableExists(table):
                self.spark.sql(f"CREATE TABLE {table} USING DELTA LOCATION '{_sql_path(path)}'")
        elif self.spark.catalog.tableExists(table):
            raise ValueError("INCOMPATIBLE_COTIZACIONES_NON_DELTA")
        else:
            definitions = []
            for field in dataframe.schema:
                nullable = " NOT NULL" if field.name == "cotizacion_id" else ""
                definitions.append(f"`{field.name}` {field.dataType.simpleString()}{nullable}")
            self.spark.sql(f"CREATE TABLE {table} ({', '.join(definitions)}) USING DELTA PARTITIONED BY (`_np_source_year`, `_np_source_month`) LOCATION '{_sql_path(path)}'")

    def write_main(self, audit, rows):
        self._assert_owner()
        _, _, business, metadata, _ = _spark_types()
        dataframe = rows.filter(self.F.col("category") == "ACCEPTED").select(*[field.name for field in business + metadata])
        self._ensure_main(dataframe)
        self.DeltaTable.forPath(self.spark, self.paths["main"]).alias("t").merge(
            dataframe.alias("s"), "t.cotizacion_id = s.cotizacion_id"
        ).whenMatchedUpdateAll(condition="s._np_sequence >= t._np_sequence").whenNotMatchedInsertAll().execute()

    def reconcile(self, audit, current=True):
        F = self.F
        evidence = self._read("record_evidence").filter(F.col("_np_file_id") == audit["file_id"])
        if self.metrics(evidence) != audit["metrics"]:
            raise ValueError("EVIDENCE_CONCILIATION_FAILED")
        if evidence.select("_np_record_id").distinct().count() != audit["metrics"]["read"]:
            raise ValueError("DUPLICATED_RECORD_EVIDENCE")
        rejected = evidence.filter(F.col("category") == "REJECTED")
        quarantine = self._read("quarantine").filter(F.col("_np_file_id") == audit["file_id"])
        if quarantine.count() != audit["metrics"]["rejected"] or rejected.exceptAll(quarantine).limit(1).count() or quarantine.exceptAll(rejected).limit(1).count():
            raise ValueError("QUARANTINE_CONCILIATION_FAILED")
        persisted = self.audit(audit["file_id"])
        if not persisted or persisted.get("metrics") != audit["metrics"]:
            raise ValueError("AUDIT_CONCILIATION_FAILED")
        # Both initial completion and replay/archive require each accepted PK
        # to remain present. A later reception may legitimately replace it;
        # the same reception must retain its identity and typed values.
        # Keep current for the store protocol, but never weaken reconciliation.
        accepted = evidence.filter(F.col("category") == "ACCEPTED").alias("e")
        main = self._read("main").alias("m")
        missing = accepted.join(main, F.col("e.cotizacion_id") == F.col("m.cotizacion_id"), "left").filter(
            F.col("m.cotizacion_id").isNull() | F.col("m._np_sequence").isNull() |
            (F.col("m._np_sequence") < audit["sequence"]) |
            ((F.col("m._np_sequence") == audit["sequence"]) &
             ~F.col("m._np_record_id").eqNullSafe(F.col("e._np_record_id"))))
        if missing.limit(1).count():
            raise ValueError("MAIN_CONCILIATION_FAILED")
        from functools import reduce
        same_values = reduce(lambda a, b: a & b, [
            F.col(f"e.{field}").eqNullSafe(F.col(f"m.{field}")) for field in FIELDS])
        unequal = accepted.join(main, F.col("e.cotizacion_id") == F.col("m.cotizacion_id"), "inner").filter(
            (F.col("m._np_sequence") == audit["sequence"]) & ~same_values)
        if unequal.limit(1).count():
            raise ValueError("MAIN_VALUE_CONCILIATION_FAILED")

    def completed_audits(self):
        if not self._exists_delta(self.paths["file_audit"]):
            return iter(())
        return (json.loads(row.payload) for row in self._read("file_audit").filter(
            (self.F.col("file_id") != "__ENTITY__") & (self.F.col("status") == "SUCCESS")
        ).orderBy("sequence").toLocalIterator())


def _sql_path(path):
    if "'" in path or "\\" in path:
        raise ValueError("UNSUPPORTED_PATH_CHARACTERS")
    return path


def load_cotizaciones(spark, dbutils, config, sources):
    from src.common.config import cotizaciones_paths
    store = SparkDeltaStore(spark, dbutils, config)
    engine = CotizacionesEngine(store, config | cotizaciones_paths(config))
    results, failures = [], []
    for source in sources:
        try:
            audit = engine.ingest(source)
            results.append({"table_name": "fact_cotizaciones", "source_file_name": source["source_file_name"],
                "source_month": source["source_month"], "record_count": audit["metrics"]["accepted"],
                "file_id": audit["file_id"], "metrics": audit["metrics"], "target_table": store.paths["target_table"], "target_path": store.paths["main"]})
        except Exception as error:
            failures.append({"table_name": "fact_cotizaciones", "source_file_name": source["source_file_name"], "error": str(error)})
            # A pending older file must stop new contents, not merely skip it.
            break
    return results, failures


def archive_cotizaciones(spark, dbutils, config):
    store = SparkDeltaStore(spark, dbutils, config)
    if not store._exists_delta(store.paths["file_audit"]):
        return [], []
    owner = str(uuid.uuid4())
    store.reserve(owner)
    archived, failures = [], []
    try:
        for audit in store.completed_audits():
            for receipt in audit["receipts"]:
                if receipt["archived"]:
                    continue
                try:
                    archive_receipt(store, audit, receipt)
                    archived.append({"table_name": "fact_cotizaciones", "source_file_name": receipt["source_file_name"], "historic_path": receipt["historic_path"]})
                except Exception as error:
                    audit["attempt_id"] = owner
                    try:
                        store.log_failure(audit, "ARCHIVE", error)
                    except Exception as log_error:
                        raise RuntimeError(f"FAILED_LOG_UNAVAILABLE stage=ARCHIVE hash={audit['checksum']}") from log_error
                    failures.append({"table_name": "fact_cotizaciones", "source_file_name": receipt["source_file_name"], "error": str(error)})
    finally:
        store.release(owner)
    return archived, failures
