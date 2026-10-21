"""Pure parser/state tests; MemoryStore is a persistence double, not Spark."""
from copy import deepcopy
import csv
import hashlib
import io

import pytest

from src.common.config import cotizaciones_paths
from src.common.cotizaciones_contract import FIELDS
from src.common.cotizaciones_ingestion import (
    CotizacionesEngine, archive_receipt, parse_csv_bytes, resolve_period, logical_file_id,
)
from tests.test_cotizaciones_contract import valid


def csv_bytes(rows, extra=()):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=[*FIELDS, *extra])
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def test_csv_unicode_multiline_and_ordinal_reference():
    data = csv_bytes([valid(producto_id='ñ, "gato" 🐾\nsegunda línea'), valid(cotizacion_id="Q2")])
    rows = list(parse_csv_bytes(data, "2026-02"))
    assert rows[0]["values"]["producto_id"] == 'ñ, "gato" 🐾\nsegunda línea'
    assert [r["ordinal"] for r in rows] == [1, 2]
    assert rows[0]["line_end"] > rows[0]["line_start"]
    assert rows[1]["line_start"] == rows[0]["line_end"] + 1
    assert rows[0]["raw_record"].encode("utf-8") in data
    assert list(parse_csv_bytes(data, "2026-02")) == rows


def test_csv_schema_extra_and_malformed_width():
    data = csv_bytes([valid() | {"extra": "recibido"}], extra=("extra",))
    row = list(parse_csv_bytes(data, "2026-02"))[0]
    assert row["original"]["extra"] == "recibido"
    assert {"field": "extra", "code": "EXTRA_COLUMN"} in row["alerts"]
    malformed = data + b"a,b\r\n"
    assert {"field": "__record__", "code": "CSV_MALFORMED"} in list(parse_csv_bytes(malformed, "2026-02"))[1]["errors"]


@pytest.mark.parametrize("data", [b"", b"id\n1\n", b'"unclosed\n', b"\xff", b"a,a\n1,2\n"])
def test_unusable_csv_fails_file(data):
    with pytest.raises(ValueError):
        list(parse_csv_bytes(data, "2026-02"))


def test_bom_and_header_only_and_resource_limit():
    assert len(list(parse_csv_bytes(b"\xef\xbb\xbf" + csv_bytes([valid()]), "2026-02"))) == 1
    with pytest.raises(ValueError, match="EMPTY"):
        list(parse_csv_bytes(csv_bytes([]), "2026-02"))
    with pytest.raises(ValueError, match="SIZE"):
        list(parse_csv_bytes(csv_bytes([valid()]), "2026-02", max_bytes=10))


def test_period_from_filename_requires_folder_and_year():
    source = {"source_file_name": "fact_cotizaciones_02.csv", "source_month": "02", "source_path": "raw/2026/02/fact_cotizaciones_02.csv"}
    assert resolve_period(source, "2026") == "2026-02"
    for changes in [{"source_month": "01"}, {"source_file_name": "fact_cotizaciones_13.csv"},
                    {"source_path": "raw/2025/02/fact_cotizaciones_02.csv"}]:
        with pytest.raises(ValueError):
            resolve_period(source | changes, "2026")


def test_paths_stable_between_years_and_hash_versions():
    config = {"bronze_area_root": "external/dev/comercial/bronze", "historic_area_root": "historic/comercial",
              "catalog": "naturapet_dev", "bronze_schema": "comercial_bronze", "data_year": "2026"}
    assert cotizaciones_paths(config)["main"] == cotizaciones_paths(config | {"data_year": "2027"})["main"]
    assert "/2026" not in cotizaciones_paths(config)["quarantine"]


class MemoryStore:
    def __init__(self):
        self.audits, self.main, self.evidence, self.quarantine, self.failures = {}, {}, {}, {}, {}
        self.files, self.lock, self.sequence = {}, None, 0
        self.fail_after = None
        self.fail_log = False
        self.main_writes = 0

    def reserve(self, owner):
        if self.lock:
            raise RuntimeError("CONCURRENT")
        self.lock = owner

    def release(self, owner):
        assert self.lock == owner
        self.lock = None

    def next_sequence(self):
        self.sequence += 1
        return self.sequence

    def audit(self, file_id):
        return deepcopy(self.audits.get(file_id))

    def pending(self):
        return sorted([deepcopy(a) for a in self.audits.values() if a["status"] != "SUCCESS"], key=lambda a: a["sequence"])

    def save_audit(self, audit):
        self.audits[audit["file_id"]] = deepcopy(audit)

    def checksum(self, path):
        return hashlib.sha256(self.files[path]).hexdigest()

    def exists(self, path):
        return path in self.files

    def copy(self, source, target):
        assert target not in self.files
        self.files[target] = self.files[source]

    def move(self, source, target):
        assert target not in self.files
        self.files[target] = self.files.pop(source)

    def remove(self, path):
        del self.files[path]

    def prepare(self, audit):
        from src.common.cotizaciones_contract import classify_duplicates
        return classify_duplicates(list(parse_csv_bytes(self.files[audit["original_path"]], audit["period"])))

    def write_evidence(self, audit, rows):
        for r in rows:
            self.evidence[(audit["file_id"], r["ordinal"])] = deepcopy(r)

    def write_main(self, audit, rows):
        self.main_writes += 1
        for r in rows:
            if r["category"] == "ACCEPTED":
                key = r["values"]["cotizacion_id"]
                if self.main.get(key, {}).get("sequence", 0) <= audit["sequence"]:
                    self.main[key] = {"sequence": audit["sequence"], "values": r["values"], "file_id": audit["file_id"]}

    def write_quarantine(self, audit, rows):
        for r in rows:
            if r["category"] == "REJECTED":
                self.quarantine[(audit["file_id"], r["ordinal"])] = deepcopy(r)

    def metrics(self, rows):
        return {"read": len(rows), **{name: sum(r["category"] == value for r in rows)
            for name, value in [("accepted", "ACCEPTED"), ("rejected", "REJECTED"), ("consolidated", "CONSOLIDATED")]}}

    def reconcile(self, audit, current=True):
        rows = [r for (file_id, _), r in self.evidence.items() if file_id == audit["file_id"]]
        assert self.metrics(rows) == audit["metrics"]
        assert sum(file_id == audit["file_id"] for file_id, _ in self.quarantine) == audit["metrics"]["rejected"]
        if current:
            for r in rows:
                if r["category"] == "ACCEPTED":
                    assert self.main[r["values"]["cotizacion_id"]]["sequence"] >= audit["sequence"]

    def log_failure(self, audit, stage, error):
        if self.fail_log:
            raise RuntimeError("LOG_FAILED")
        self.failures[(audit["attempt_id"], stage)] = type(error).__name__

    def checkpoint(self, stage):
        if self.fail_after == stage:
            self.fail_after = None
            raise RuntimeError("INJECTED_" + stage)


def setup_engine(rows=None):
    store = MemoryStore()
    source = {"source_file_name": "fact_cotizaciones_02.csv", "source_month": "02",
              "source_path": "raw/2026/02/fact_cotizaciones_02.csv"}
    store.files[source["source_path"]] = csv_bytes(rows if rows is not None else [valid()])
    engine = CotizacionesEngine(store, {"data_year": "2026", "originals": "originals", "historic_area_root": "historic"})
    return store, source, engine


def test_mixed_conciliation_and_all_originals_preserved():
    store, source, engine = setup_engine([valid(), valid(cotizacion_id="Q2"), valid(),
        valid(cotizacion_id=""), valid(cotizacion_id="Q3", cantidad="cinco", fecha_id="")])
    audit = engine.ingest(source)
    assert audit["metrics"] == {"read": 5, "accepted": 2, "rejected": 2, "consolidated": 1}
    assert audit["status"] == "SUCCESS"
    assert len(store.evidence) == 5 and len(store.quarantine) == 2 and len(store.main) == 2
    assert len(next(r for r in store.quarantine.values() if r["values"]["cotizacion_id"] == "Q3")["errors"]) >= 2


def test_replay_old_content_does_not_revert_correction():
    store, source, engine = setup_engine()
    content_a = store.files[source["source_path"]]
    a = engine.ingest(source)
    store.files[source["source_path"]] = csv_bytes([valid(estado_cotizacion="Rechazada")])
    b = engine.ingest(source)
    assert a["file_id"] != b["file_id"]
    store.files[source["source_path"]] = content_a
    engine.ingest(source)
    assert store.main["Q001"]["values"]["estado_cotizacion"] == "Rechazada"
    assert store.main_writes == 2
    assert len(store.audits[a["file_id"]]["receipts"]) == 2


@pytest.mark.parametrize("stage", ["ORIGINAL", "EVIDENCE", "MAIN", "QUARANTINE", "AUDIT", "SUCCESS"])
def test_partial_failure_then_retry_reconciles(stage):
    store, source, engine = setup_engine([valid(), valid(cotizacion_id="")])
    store.fail_after = stage
    with pytest.raises(RuntimeError):
        engine.ingest(source)
    assert store.failures and not any(a["status"] == "SUCCESS" for a in store.audits.values())
    audit = engine.ingest(source)
    assert audit["status"] == "SUCCESS"
    assert len(store.main) == 1 and len(store.quarantine) == 1 and len(store.evidence) == 2


def test_pending_old_attempt_recovered_before_new_content():
    store, source, engine = setup_engine()
    store.fail_after = "MAIN"
    with pytest.raises(RuntimeError):
        engine.ingest(source)
    store.files[source["source_path"]] = csv_bytes([valid(estado_cotizacion="Vencida")])
    engine.ingest(source)
    assert all(a["status"] == "SUCCESS" for a in store.audits.values())
    assert store.main["Q001"]["values"]["estado_cotizacion"] == "Vencida"


def test_double_log_failure_visible_and_lock_released():
    store, source, engine = setup_engine()
    store.fail_after, store.fail_log = "MAIN", True
    with pytest.raises(RuntimeError, match="LOG_FAILED"):
        engine.ingest(source)
    assert store.lock is None
    assert source["source_path"] in store.files


def test_all_rejected_success_and_archive_checksum_safety():
    store, source, engine = setup_engine([valid(cotizacion_id="")])
    audit = engine.ingest(source)
    assert audit["status"] == "SUCCESS" and audit["metrics"]["accepted"] == 0
    receipt = audit["receipts"][0]
    store.files[source["source_path"]] = b"changed"
    with pytest.raises(ValueError, match="CHECKSUM"):
        archive_receipt(store, audit, receipt)
    assert source["source_path"] in store.files


def test_archive_move_then_state_failure_and_equal_existing():
    store, source, engine = setup_engine()
    audit = engine.ingest(source)
    receipt = audit["receipts"][0]
    store.fail_after = "MOVE"
    with pytest.raises(RuntimeError):
        archive_receipt(store, audit, receipt)
    assert not store.exists(receipt["source_path"]) and store.exists(receipt["historic_path"])
    archive_receipt(store, audit, receipt)
    assert receipt["archived"] is True


def test_archive_wrong_historic_and_missing_both():
    store, source, engine = setup_engine()
    audit = engine.ingest(source)
    receipt = audit["receipts"][0]
    store.files[receipt["historic_path"]] = b"collision"
    with pytest.raises(ValueError, match="CHECKSUM"):
        archive_receipt(store, audit, receipt)
    del store.files[receipt["historic_path"]], store.files[source["source_path"]]
    with pytest.raises(FileNotFoundError):
        archive_receipt(store, audit, receipt)


def test_entity_reservation_rejects_overlapping_attempts():
    store, source, engine = setup_engine()
    store.lock = "other-active-attempt"
    with pytest.raises(RuntimeError, match="CONCURRENT"):
        engine.ingest(source)
    assert not store.main and not store.audits


def test_dispatch_happens_before_dictionary(monkeypatch):
    import importlib
    import sys
    from types import ModuleType
    from unittest.mock import MagicMock
    fake = ModuleType("src.common.delta_load")
    for name in ("add_ingestion_metadata", "append_audit_records", "build_audit_record", "create_or_merge_delta",
                 "ensure_catalog_schema", "list_pending_archives", "update_archive_status"):
        setattr(fake, name, MagicMock())
    monkeypatch.setitem(sys.modules, "src.common.delta_load", fake)
    monkeypatch.delitem(sys.modules, "src.common.notebook_runner", raising=False)
    runner = importlib.import_module("src.common.notebook_runner")
    monkeypatch.delitem(sys.modules, "src.common.notebook_runner", raising=False)
    config = {"area": "comercial", "catalog": "test", "bronze_schema": "test_bronze", "env": "dev",
              "data_year": "2026", "raw_year_path": "raw/2026", "audit_table_name": "audit"}
    source = {"source_file_name": "fact_cotizaciones_02.csv", "source_month": "02"}
    monkeypatch.setattr(runner, "get_config", lambda **kw: config)
    monkeypatch.setattr(runner, "path_exists", lambda *args: True)
    monkeypatch.setattr(runner, "discover_area_files", lambda *args: [source])
    def forbidden(*args):
        raise AssertionError("Generic dictionary reached for cotizaciones")
    monkeypatch.setattr(runner, "load_data_dictionary", forbidden)
    monkeypatch.setattr(runner, "load_cotizaciones", lambda *args: ([{"table_name": "fact_cotizaciones"}], []))
    result = runner.run_bronze_load(MagicMock(), MagicMock(), "comercial")
    assert result["processed_files"] == [{"table_name": "fact_cotizaciones"}]


def test_month_selection_is_scoped_to_cotizaciones():
    from src.common.cotizaciones_ingestion import split_sources
    cot = {"source_file_name": "fact_cotizaciones_02.csv", "source_month": "02"}
    other = {"source_file_name": "fact_ventas_01.csv", "source_month": "01"}
    assert split_sources("comercial", [cot, other], "01") == ([], [other])
    assert split_sources("shared", [cot, other], "01") == ([], [cot, other])


def test_csv_unquoted_quote_is_not_silently_accepted():
    content = csv_bytes([valid()]).replace(b"Q001,", b'Q00"1,', 1)
    rows = list(parse_csv_bytes(content, "2026-02"))
    assert {"field": "__record__", "code": "CSV_MALFORMED"} in rows[0]["errors"]


def test_executor_records_are_stable_between_retry_attempts():
    from types import SimpleNamespace
    from src.common.cotizaciones_ingestion import _parse_partition
    store, source, run = setup_engine()
    audit = run.ingest(source)
    records = [SimpleNamespace(content=store.files[audit["original_path"]])]
    first = list(_parse_partition(iter(records), audit))
    retry = list(_parse_partition(iter(records), audit | {"attempt_id": "new-retry"}))
    assert first == retry
    assert first[0]["_np_attempt_id"] == audit["initial_attempt_id"]


def test_unicode_line_separators_are_valid_field_content():
    row = valid(producto_id="ñ\u2028🐾\u0085hola\u2029")
    content = csv_bytes([row])
    parsed = list(parse_csv_bytes(content, "2026-02"))
    assert parsed[0]["values"]["producto_id"] == row["producto_id"].strip()
    assert parsed[0]["raw_record"].encode("utf-8") in content


class _Expression:
    """Small expression double to exercise production reconciliation locally."""
    def __init__(self, evaluate):
        self.evaluate = evaluate

    def _binary(self, other, operation):
        right = other.evaluate if isinstance(other, _Expression) else lambda row: other
        return _Expression(lambda row: operation(self.evaluate(row), right(row)))

    def __eq__(self, other):
        return self._binary(other, lambda a, b: a == b if a is not None and b is not None else False)

    def __ne__(self, other):
        return self._binary(other, lambda a, b: a != b if a is not None and b is not None else False)

    def __lt__(self, other):
        return self._binary(other, lambda a, b: a < b if a is not None and b is not None else False)

    def __and__(self, other):
        return self._binary(other, lambda a, b: a and b)

    def __or__(self, other):
        return self._binary(other, lambda a, b: a or b)

    def __invert__(self):
        return _Expression(lambda row: not self.evaluate(row))

    def isNull(self):
        return _Expression(lambda row: self.evaluate(row) is None)

    def eqNullSafe(self, other):
        return self._binary(other, lambda a, b: a == b)


class _Frame:
    """Relational double only; does not claim Spark compatibility."""
    def __init__(self, rows, columns=None):
        self.rows = rows
        self.columns = columns or list(rows[0] if rows else ())

    def filter(self, condition):
        return _Frame([row for row in self.rows if condition.evaluate(row)], self.columns)

    def select(self, *columns):
        return _Frame([{c: row[c] for c in columns} for row in self.rows], columns)

    def distinct(self):
        result = []
        for row in self.rows:
            if row not in result:
                result.append(row)
        return _Frame(result, self.columns)

    def count(self):
        return len(self.rows)

    def limit(self, size):
        return _Frame(self.rows[:size], self.columns)

    def exceptAll(self, other):
        remainder = list(other.rows)
        result = []
        for row in self.rows:
            if row in remainder:
                remainder.remove(row)
            else:
                result.append(row)
        return _Frame(result, self.columns)

    def alias(self, prefix):
        return _Frame([{prefix + "." + key: value for key, value in row.items()} for row in self.rows],
                      [prefix + "." + key for key in self.columns])

    def join(self, other, condition, how):
        result = []
        for left in self.rows:
            matches = [left | right for right in other.rows if condition.evaluate(left | right)]
            result.extend(matches or ([left | dict.fromkeys(other.columns)] if how == "left" else []))
        return _Frame(result, [*self.columns, *other.columns])


@pytest.mark.parametrize("change,expected_error", [
    ("missing", "MAIN_CONCILIATION_FAILED"),
    ("stale", "MAIN_CONCILIATION_FAILED"),
    ("null_sequence", "MAIN_CONCILIATION_FAILED"),
    ("identity", "MAIN_CONCILIATION_FAILED"),
    ("altered", "MAIN_VALUE_CONCILIATION_FAILED"),
    ("null_altered", "MAIN_VALUE_CONCILIATION_FAILED"),
    ("later", None),
    ("unchanged", None),
])
@pytest.mark.parametrize("current", [False, True])
def test_production_reconciliation_validates_main_on_replay_and_archive(change, expected_error, current):
    from types import SimpleNamespace
    from src.common.cotizaciones_contract import normalize_record
    from src.common.cotizaciones_ingestion import SparkDeltaStore
    accepted = normalize_record(valid(tienda_id=""), "2026-02")["values"] | {
        "_np_file_id": "file-A", "_np_record_id": "record-A", "_np_sequence": 7,
        "category": "ACCEPTED"}
    main = dict(accepted)
    if change == "stale":
        main["_np_sequence"] = 6
    elif change == "null_sequence":
        main["_np_sequence"] = None
    elif change == "identity":
        main["_np_record_id"] = "other"
    elif change == "altered":
        main["estado_cotizacion"] = "Vencida"
    elif change == "null_altered":
        main["tienda_id"] = "T-inventada"
    elif change == "later":
        main.update(_np_sequence=8, _np_record_id="record-B", estado_cotizacion="Rechazada")
    frames = {"record_evidence": _Frame([accepted]), "quarantine": _Frame([]),
              "main": _Frame([] if change == "missing" else [main], list(main))}
    metrics = {"read": 1, "accepted": 1, "rejected": 0, "consolidated": 0}
    audit = {"file_id": "file-A", "sequence": 7, "metrics": metrics}
    store = SparkDeltaStore.__new__(SparkDeltaStore)
    store.F = SimpleNamespace(col=lambda key: _Expression(lambda row: row.get(key)))
    store._read = frames.__getitem__
    store.metrics = lambda frame: metrics
    store.audit = lambda file_id: audit
    if expected_error:
        with pytest.raises(ValueError, match=expected_error):
            store.reconcile(audit, current=current)
    else:
        store.reconcile(audit, current=current)


def _notebook_guard_functions():
    import ast
    import json
    import posixpath
    import re
    from pathlib import Path
    from urllib.parse import urlsplit, unquote
    notebook = json.loads((Path(__file__).parents[1] / "notebooks/comercial/bronze/tests/validate_cotizaciones.ipynb").read_text(encoding="utf-8"))
    tree = ast.parse("\n".join("".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {"validate_test_scope", "assert_test_path"}]
    assert len(nodes) == 2, "Notebook must expose its actual pure guard functions"
    scope = {"re": re, "posixpath": posixpath, "urlsplit": urlsplit, "unquote": unquote}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "notebook-guards", "exec"), scope)
    return scope


def test_notebook_accepts_only_approved_catalog_and_data_root():
    guards = _notebook_guard_functions()
    catalog = "crea_cotizaciones_test_20261020_01a15a7c"
    root = "abfss://demo@demodldb.dfs.core.windows.net/_tests/cotizaciones/20261020_01a15a7c/data"
    assert guards["validate_test_scope"](catalog, root, "hu_cotizaciones_test_run") == (catalog, root)
    assert guards["assert_test_path"](root + "/run/case/main", root) == root + "/run/case/main"
    for bad in ("naturapet_dev", "naturapet_test", "NATURAPET_DEV", "other", catalog + "_extra"):
        with pytest.raises(ValueError):
            guards["validate_test_scope"](bad, root, "hu_cotizaciones_test_run")
    for bad in (root.replace("/data", "/managed"), root + "_sibling", root.replace("demo@", "other@"),
                root + "/../managed", root + "/%2e%2e/managed", root + "?q=x"):
        with pytest.raises(ValueError):
            guards["validate_test_scope"](catalog, bad, "hu_cotizaciones_test_run")
    for bad in (root + "_sibling/a", root + "/../managed/a", root + "/x/../../managed/a",
                root + "/%2e%2e/a", root + "/x?key=secret", root.replace("demo@", "other@") + "/x"):
        with pytest.raises(ValueError):
            guards["assert_test_path"](bad, root)


def test_notebook_guard_accepts_fileinfo_directory_trailing_slash_only():
    from types import SimpleNamespace
    guard = _notebook_guard_functions()["assert_test_path"]
    root = "abfss://demo@demodldb.dfs.core.windows.net/_tests/cotizaciones/20261020_01a15a7c/data"
    directory = SimpleNamespace(path=root + "/runtime_attempt02/generic_comercial/raw/2026/02/")
    assert guard(directory.path, root) == directory.path
    assert guard(root + "/", root) == root + "/"
    for path in (directory.path + "/", root + "/a//b/", root + "/a/../b/", root + "/%2e%2e/",
                 root + "_sibling/", root + "/a?", root + "/a#", root.replace("demo@", "other@") + "/a/"):
        with pytest.raises(ValueError):
            guard(path, root)


@pytest.mark.parametrize("fails", [False, True])
def test_notebook_finalizes_inventory_and_exits_only_after_success(fails):
    import ast
    import json
    from pathlib import Path
    from types import SimpleNamespace
    notebook = json.loads((Path(__file__).parents[1] / "notebooks/comercial/bronze/tests/validate_cotizaciones.ipynb").read_text(encoding="utf-8"))
    tree = ast.parse("".join(notebook["cells"][-1]["source"]))
    # Execute the actual notebook driver tail, without importing or running Spark.
    tail = tree.body[-3:]
    events = []
    result = {"metadata": {"Spark": "synthetic-test"}, "assertions_by_CA": {"CA14": "passed"}}
    def run():
        events.append("run_all_checks")
        if fails:
            raise ValueError("ASSERTION_FAILED")
        return result
    scope = {"json": json, "run_all_checks": run,
             "finalize_inventory": lambda: events.append("finalize_inventory"),
             "dbutils": SimpleNamespace(notebook=SimpleNamespace(exit=lambda payload: events.append(json.loads(payload))))}
    code = compile(ast.Module(body=tail, type_ignores=[]), "notebook-driver-tail", "exec")
    if fails:
        with pytest.raises(ValueError, match="ASSERTION_FAILED"):
            exec(code, scope)
        assert events == ["run_all_checks", "finalize_inventory"]
    else:
        exec(code, scope)
        assert events == ["run_all_checks", "finalize_inventory", result]


def _notebook_first_cell_nodes():
    import ast
    import json
    from pathlib import Path
    notebook = json.loads((Path(__file__).parents[1] / "notebooks/comercial/bronze/tests/validate_cotizaciones.ipynb").read_text(encoding="utf-8"))
    return ast.parse("".join(notebook["cells"][1]["source"])).body


@pytest.mark.parametrize("existing,error", [(False, FileNotFoundError("missing")),
    (False, RuntimeError("java.io.FileNotFoundException: leaf missing")),
    (True, None), (False, PermissionError("PERMISSION_DENIED")),
    (False, RuntimeError("INVALID_PARAMETER_VALUE.LOCATION_OVERLAP"))])
def test_notebook_prepares_only_new_leaf_without_touching_uc_ancestor(existing, error):
    import ast
    import re
    from types import SimpleNamespace
    guards = _notebook_guard_functions()
    nodes = [n for n in _notebook_first_cell_nodes() if isinstance(n, ast.FunctionDef) and n.name == "prepare_test_leaf"]
    assert len(nodes) == 1, "Leaf-only preflight must be explicit and testable"
    scope = {"assert_test_path": guards["assert_test_path"], "re": re}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "notebook-leaf", "exec"), scope)
    root = "abfss://demo@demodldb.dfs.core.windows.net/_tests/cotizaciones/20261020_01a15a7c/data"
    leaf, calls = root + "/runtime_attempt03", []
    def ls(path):
        calls.append(("ls", path))
        if path == root:
            raise AssertionError("UC ancestor must never be touched")
        if error:
            raise error
        return []
    def mkdirs(path):
        calls.append(("mkdirs", path))
        assert path == leaf
        return True
    fs = SimpleNamespace(ls=ls, mkdirs=mkdirs)
    if existing:
        with pytest.raises(FileExistsError):
            scope["prepare_test_leaf"](fs, leaf, root)
        assert calls == [("ls", leaf)]
    elif not isinstance(error, FileNotFoundError) and "FileNotFoundException" not in str(error):
        with pytest.raises(type(error), match=str(error)):
            scope["prepare_test_leaf"](fs, leaf, root)
        assert calls == [("ls", leaf)]
    else:
        scope["prepare_test_leaf"](fs, leaf, root)
        assert calls == [("ls", leaf), ("mkdirs", leaf)]


def test_notebook_proxy_preserves_native_notebook_exit():
    import ast
    from types import SimpleNamespace
    nodes = [n for n in _notebook_first_cell_nodes() if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == "dbutils" for t in n.targets)]
    assert len(nodes) == 1
    native = SimpleNamespace(fs=object(), jobs=object(), widgets=object(), notebook=object())
    guarded = object()
    scope = {"dbutils": native, "SimpleNamespace": SimpleNamespace, "GuardedFS": lambda: guarded}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "notebook-proxy", "exec"), scope)
    assert scope["dbutils"].fs is guarded
    assert scope["dbutils"].notebook is native.notebook
    assert scope["dbutils"].jobs is native.jobs
    assert scope["dbutils"].widgets is native.widgets


def test_notebook_initialization_uses_leaf_preflight_without_ancestor_fs_calls():
    import ast
    nodes = _notebook_first_cell_nodes()
    calls = [n for node in nodes for n in ast.walk(node) if isinstance(n, ast.Call)]
    assert any(isinstance(c.func, ast.Name) and c.func.id == "prepare_test_leaf" for c in calls)
    assert not any(isinstance(c.func, ast.Attribute) and isinstance(c.func.value, ast.Name)
                   and c.func.value.id == "raw_fs" and c.func.attr in {"ls", "mkdirs"}
                   and c.args and isinstance(c.args[0], ast.Name) and c.args[0].id == "storage_root"
                   for c in calls)
