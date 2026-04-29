import json
import re
from typing import Dict, List


MONTH_PATTERN = re.compile(r"^(0[1-9]|1[0-2])$")
SUPPORTED_SOURCE_FORMATS = {"csv", "json", "parquet"}
TASK_VALUE_MAX_BYTES = 48 * 1024
TASK_VALUE_SAMPLE_LIMIT = 10
TASK_VALUE_ERROR_MAX_CHARS = 500


def path_exists(dbutils, path: str) -> bool:
    try:
        dbutils.fs.ls(path)
        return True
    except Exception:
        return False


def discover_area_files(dbutils, raw_year_path: str) -> List[Dict[str, str]]:
    source_files: List[Dict[str, str]] = []

    for entry in dbutils.fs.ls(raw_year_path):
        entry_name = entry.name.rstrip("/")
        if entry.isDir() and MONTH_PATTERN.match(entry_name):
            for monthly_file in dbutils.fs.ls(entry.path):
                if monthly_file.isDir():
                    continue
                source_files.append(
                    {
                        "source_path": monthly_file.path,
                        "source_file_name": monthly_file.name,
                        "source_month": entry_name,
                        "load_mode": "incremental",
                        "source_format": detect_file_format(monthly_file.name),
                    }
                )
            continue

        if not entry.isDir():
            source_files.append(
                {
                    "source_path": entry.path,
                    "source_file_name": entry.name,
                    "source_month": None,
                    "load_mode": "full",
                    "source_format": detect_file_format(entry.name),
                }
            )

    return sorted(
        source_files,
        key=lambda item: (
            item["source_month"] or "00",
            item["source_file_name"],
        ),
    )


def detect_file_format(file_name: str) -> str:
    if "." not in file_name:
        raise ValueError(
            f"No fue posible detectar el tipo de archivo para {file_name}. "
            f"Se esperaba una extension como .csv, .json o .parquet."
        )

    file_format = file_name.rsplit(".", 1)[1].lower()
    if file_format in {"xlsx", "xls"}:
        raise ValueError(
            f"El archivo {file_name} es Excel y este flujo no lo procesa de forma nativa. "
            f"Con el dataset actual de Naturapet el formato esperado es CSV."
        )
    if file_format not in SUPPORTED_SOURCE_FORMATS:
        raise ValueError(
            f"Formato {file_format} no soportado para {file_name}. "
            f"Use uno de: {sorted(SUPPORTED_SOURCE_FORMATS)}."
        )

    return file_format


def read_csv_with_schema(
    spark,
    path: str,
    schema=None,
    header: bool = True,
):
    reader = spark.read.option("header", str(header).lower())
    if schema is not None:
        reader = reader.schema(schema)
    else:
        reader = reader.option("inferSchema", "true")
    return reader.csv(path)


def read_json_with_schema(spark, path: str, schema=None):
    reader = spark.read
    if schema is not None:
        reader = reader.schema(schema)
    else:
        reader = reader.option("inferSchema", "true")
    return reader.json(path)


def read_parquet_with_schema(spark, path: str, schema=None):
    reader = spark.read
    if schema is not None:
        reader = reader.schema(schema)
    return reader.parquet(path)


def read_source_file(
    spark,
    path: str,
    source_format: str,
    schema=None,
    header: bool = True,
):
    if source_format == "csv":
        return read_csv_with_schema(
            spark=spark,
            path=path,
            schema=schema,
            header=header,
        )
    if source_format == "json":
        return read_json_with_schema(
            spark=spark,
            path=path,
            schema=schema,
        )
    if source_format == "parquet":
        return read_parquet_with_schema(
            spark=spark,
            path=path,
            schema=schema,
        )

    raise ValueError(
        f"Formato {source_format} no soportado para la lectura del archivo {path}."
    )


def ensure_directory(dbutils, path: str) -> None:
    dbutils.fs.mkdirs(path)


def move_file_to_historic(dbutils, source_path: str, target_path: str) -> None:
    ensure_directory(dbutils, target_path.rsplit("/", 1)[0])
    dbutils.fs.mv(source_path, target_path)


def _serialize_task_value(payload: Dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _task_value_size(payload: Dict[str, object]) -> int:
    return len(_serialize_task_value(payload).encode("utf-8"))


def _truncate_text(value: object, max_chars: int = TASK_VALUE_ERROR_MAX_CHARS) -> object:
    if not isinstance(value, str) or len(value) <= max_chars:
        return value
    return f"{value[: max_chars - 15]}...(truncado)"


def _compact_file_items(
    items: List[Dict[str, object]],
    fields: List[str],
    include_truncated_error: bool = False,
) -> List[Dict[str, object]]:
    compact_items: List[Dict[str, object]] = []

    for item in items[:TASK_VALUE_SAMPLE_LIMIT]:
        compact_item = {
            field: item.get(field)
            for field in fields
            if item.get(field) is not None
        }
        if include_truncated_error and "error" in item:
            compact_item["error"] = _truncate_text(item.get("error"))
        compact_items.append(compact_item)

    return compact_items


def _build_compact_task_value(payload: Dict[str, object]) -> Dict[str, object]:
    compact_payload: Dict[str, object] = {
        "status": payload.get("status"),
        "area": payload.get("area"),
        "environment": payload.get("environment"),
        "catalog": payload.get("catalog"),
        "bronze_schema": payload.get("bronze_schema"),
        "task_value_truncated": True,
    }

    processed_files = payload.get("processed_files")
    if isinstance(processed_files, list):
        compact_payload["processed_file_count"] = len(processed_files)
        compact_payload["processed_tables"] = sorted(
            {
                item.get("table_name")
                for item in processed_files
                if isinstance(item, dict) and item.get("table_name")
            }
        )[:TASK_VALUE_SAMPLE_LIMIT]
        compact_payload["processed_files_sample"] = _compact_file_items(
            processed_files,
            fields=[
                "table_name",
                "source_file_name",
                "source_month",
                "load_mode",
                "source_format",
                "record_count",
            ],
        )
        compact_payload["processed_files_omitted"] = max(
            len(processed_files) - TASK_VALUE_SAMPLE_LIMIT,
            0,
        )

    failed_files = payload.get("failed_files")
    if isinstance(failed_files, list):
        compact_payload["failed_file_count"] = len(failed_files)
        compact_payload["failed_files_sample"] = _compact_file_items(
            failed_files,
            fields=["table_name", "source_file_name"],
            include_truncated_error=True,
        )
        compact_payload["failed_files_omitted"] = max(
            len(failed_files) - TASK_VALUE_SAMPLE_LIMIT,
            0,
        )

    archived_files = payload.get("archived_files")
    if isinstance(archived_files, list):
        compact_payload["archived_file_count"] = len(archived_files)
        compact_payload["archived_files_sample"] = _compact_file_items(
            archived_files,
            fields=["table_name", "source_file_name"],
        )
        compact_payload["archived_files_omitted"] = max(
            len(archived_files) - TASK_VALUE_SAMPLE_LIMIT,
            0,
        )

    archive_failures = payload.get("archive_failures")
    if isinstance(archive_failures, list):
        compact_payload["archive_failure_count"] = len(archive_failures)
        compact_payload["archive_failures_sample"] = _compact_file_items(
            archive_failures,
            fields=["table_name", "source_file_name"],
            include_truncated_error=True,
        )
        compact_payload["archive_failures_omitted"] = max(
            len(archive_failures) - TASK_VALUE_SAMPLE_LIMIT,
            0,
        )

    return compact_payload


def dumps_task_value(payload: Dict[str, object]) -> str:
    serialized_payload = _serialize_task_value(payload)
    if len(serialized_payload.encode("utf-8")) <= TASK_VALUE_MAX_BYTES:
        return serialized_payload

    compact_payload = _build_compact_task_value(payload)
    compact_payload["original_payload_bytes"] = len(serialized_payload.encode("utf-8"))

    if _task_value_size(compact_payload) <= TASK_VALUE_MAX_BYTES:
        return _serialize_task_value(compact_payload)

    minimal_payload = {
        "status": payload.get("status"),
        "area": payload.get("area"),
        "environment": payload.get("environment"),
        "catalog": payload.get("catalog"),
        "bronze_schema": payload.get("bronze_schema"),
        "processed_file_count": len(payload.get("processed_files", []) or []),
        "failed_file_count": len(payload.get("failed_files", []) or []),
        "archived_file_count": len(payload.get("archived_files", []) or []),
        "archive_failure_count": len(payload.get("archive_failures", []) or []),
        "task_value_truncated": True,
        "original_payload_bytes": len(serialized_payload.encode("utf-8")),
    }
    return _serialize_task_value(minimal_payload)
