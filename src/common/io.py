import json
import re
from typing import Dict, List


MONTH_PATTERN = re.compile(r"^(0[1-9]|1[0-2])$")
SUPPORTED_SOURCE_FORMATS = {"csv", "json", "parquet"}


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


def dumps_task_value(payload: Dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False)
