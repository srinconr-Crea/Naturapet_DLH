import json
import re
from typing import Dict, List

from pyspark.sql import DataFrame


MONTH_PATTERN = re.compile(r"^(0[1-9]|1[0-2])$")


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
                }
            )

    return sorted(
        source_files,
        key=lambda item: (
            item["source_month"] or "00",
            item["source_file_name"],
        ),
    )


def read_csv_with_schema(
    spark,
    path: str,
    schema=None,
    header: bool = True,
) -> DataFrame:
    reader = spark.read.option("header", str(header).lower())
    if schema is not None:
        reader = reader.schema(schema)
    else:
        reader = reader.option("inferSchema", "true")
    return reader.csv(path)


def ensure_directory(dbutils, path: str) -> None:
    dbutils.fs.mkdirs(path)


def move_file_to_historic(dbutils, source_path: str, target_path: str) -> None:
    ensure_directory(dbutils, target_path.rsplit("/", 1)[0])
    dbutils.fs.mv(source_path, target_path)


def dumps_task_value(payload: Dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False)
