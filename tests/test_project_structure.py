import os
import json

from src.common.config import (
    build_audit_table_fqn,
    build_bronze_table_path,
    build_historic_file_path,
    build_raw_file_path,
    get_config,
)
from src.common.io import TASK_VALUE_MAX_BYTES, detect_file_format, dumps_task_value
from src.common.schema import normalize_table_name


def test_get_config_defaults():
    original_env = os.environ.copy()
    try:
        os.environ["APP_ENV"] = "dev"
        os.environ["AREA"] = "comercial"
        config = get_config()

        assert config["catalog"] == "naturapet_dev"
        assert config["bronze_schema"] == "comercial_bronze"
        assert (
            config["raw_year_path"]
            == "abfss://democodex@demodldb.dfs.core.windows.net/raw/dev/comercial/2026"
        )
        assert (
            config["bronze_year_root"]
            == "abfss://democodex@demodldb.dfs.core.windows.net/external/dev/comercial/bronze/2026"
        )
    finally:
        os.environ.clear()
        os.environ.update(original_env)


def test_build_raw_file_path():
    original_env = os.environ.copy()
    try:
        os.environ["APP_ENV"] = "dev"
        os.environ["AREA"] = "comercial"
        config = get_config()

        assert (
            build_raw_file_path(config, r"comercial\2026\01\fact_ventas_cabecera_01.csv")
            == "abfss://democodex@demodldb.dfs.core.windows.net/raw/dev/comercial/2026/01/fact_ventas_cabecera_01.csv"
        )
    finally:
        os.environ.clear()
        os.environ.update(original_env)


def test_build_bronze_table_path():
    original_env = os.environ.copy()
    try:
        os.environ["APP_ENV"] = "dev"
        os.environ["AREA"] = "comercial"
        config = get_config()

        assert (
            build_bronze_table_path(config, "fact_ventas_cabecera")
            == "abfss://democodex@demodldb.dfs.core.windows.net/external/dev/comercial/bronze/2026/fact_ventas_cabecera"
        )
    finally:
        os.environ.clear()
        os.environ.update(original_env)


def test_build_historic_monthly_file_path():
    original_env = os.environ.copy()
    try:
        os.environ["APP_ENV"] = "dev"
        os.environ["AREA"] = "comercial"
        config = get_config()

        assert (
            build_historic_file_path(config, "fact_ventas_cabecera_01.csv", "01")
            == "abfss://democodex@demodldb.dfs.core.windows.net/historic/comercial/2026/01/fact_ventas_cabecera_01.csv"
        )
    finally:
        os.environ.clear()
        os.environ.update(original_env)


def test_build_audit_table_fqn():
    original_env = os.environ.copy()
    try:
        os.environ["APP_ENV"] = "dev"
        os.environ["AREA"] = "comercial"
        config = get_config()

        assert build_audit_table_fqn(config) == (
            "`naturapet_dev`.`comercial_bronze`.`bronze_file_load_audit`"
        )
    finally:
        os.environ.clear()
        os.environ.update(original_env)


def test_normalize_monthly_table_name():
    assert (
        normalize_table_name("fact_ventas_cabecera_01.csv", "01")
        == "fact_ventas_cabecera"
    )


def test_detect_file_format():
    assert detect_file_format("fact_ventas_cabecera_01.csv") == "csv"
    assert detect_file_format("fact_ventas.json") == "json"
    assert detect_file_format("fact_ventas.parquet") == "parquet"


def test_dumps_task_value_keeps_small_payload():
    payload = {
        "status": "OK",
        "area": "shared",
        "processed_files": [{"table_name": "dim_producto"}],
        "failed_files": [],
    }

    serialized = dumps_task_value(payload)

    assert json.loads(serialized) == payload


def test_dumps_task_value_compacts_large_payload():
    large_error = "X" * (TASK_VALUE_MAX_BYTES + 500)
    payload = {
        "status": "ERROR",
        "area": "shared",
        "environment": "dev",
        "catalog": "naturapet_dev",
        "bronze_schema": "shared_bronze",
        "processed_files": [
            {
                "table_name": f"dim_tabla_{index:02d}",
                "source_file_name": f"dim_tabla_{index:02d}.csv",
                "source_month": None,
                "load_mode": "full",
                "source_format": "csv",
                "record_count": index,
                "target_table": "target",
                "target_path": "path",
            }
            for index in range(12)
        ],
        "failed_files": [
            {
                "table_name": "dim_producto",
                "source_file_name": "dim_producto.csv",
                "error": large_error,
            }
        ],
    }

    serialized = dumps_task_value(payload)
    result = json.loads(serialized)

    assert len(serialized.encode("utf-8")) <= TASK_VALUE_MAX_BYTES
    assert result["task_value_truncated"] is True
    assert result["processed_file_count"] == 12
    assert result["failed_file_count"] == 1
    assert len(result["processed_files_sample"]) == 10
    assert result["processed_files_omitted"] == 2
    assert result["failed_files_sample"][0]["error"].endswith("...(truncado)")
