import json
import importlib
import os
import sys
from types import ModuleType
from unittest.mock import MagicMock

from src.common.config import (
    build_audit_table_fqn,
    build_bronze_table_path,
    build_historic_file_path,
    build_raw_file_path,
    get_config,
)
from src.common.io import TASK_VALUE_MAX_BYTES, detect_file_format, dumps_task_value
from src.common.schema import normalize_table_name
from src.common.validation import (
    build_mes_carga_regex,
    matches_expected_mes_carga_text,
)


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


def test_matches_expected_mes_carga_text_accepts_equivalent_month_formats():
    assert matches_expected_mes_carga_text("2026-01", "2026-01") is True
    assert matches_expected_mes_carga_text("2026-01-01", "2026-01") is True
    assert matches_expected_mes_carga_text("2026-01 00:00:00", "2026-01") is True
    assert matches_expected_mes_carga_text(" 2026-01 ", "2026-01") is True


def test_matches_expected_mes_carga_text_rejects_other_month_values():
    assert matches_expected_mes_carga_text("2026-02", "2026-01") is False
    assert matches_expected_mes_carga_text("202601", "2026-01") is False
    assert matches_expected_mes_carga_text("2026-0101", "2026-01") is False
    assert build_mes_carga_regex("2026-01") == r"^2026\-01($|[^0-9])"


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


def _import_delta_load_with_fake_delta():
    original_delta = sys.modules.get("delta")
    original_delta_tables = sys.modules.get("delta.tables")
    original_pyspark = sys.modules.get("pyspark")
    original_pyspark_sql = sys.modules.get("pyspark.sql")
    original_module = sys.modules.get("src.common.delta_load")

    fake_delta = ModuleType("delta")
    fake_delta_tables = ModuleType("delta.tables")
    fake_delta_tables.DeltaTable = MagicMock()
    fake_delta.tables = fake_delta_tables

    fake_pyspark = ModuleType("pyspark")
    fake_pyspark_sql = ModuleType("pyspark.sql")
    fake_functions = ModuleType("pyspark.sql.functions")
    fake_types = ModuleType("pyspark.sql.types")

    fake_pyspark_sql.DataFrame = object
    fake_pyspark_sql.functions = fake_functions
    fake_pyspark_sql.types = fake_types

    fake_types.StructType = MagicMock(side_effect=lambda fields: ("StructType", fields))
    fake_types.StructField = MagicMock(
        side_effect=lambda name, data_type, nullable: (
            "StructField",
            name,
            data_type,
            nullable,
        )
    )
    fake_types.StringType = MagicMock(return_value="StringType")
    fake_types.LongType = MagicMock(return_value="LongType")
    fake_types.TimestampType = MagicMock(return_value="TimestampType")

    fake_pyspark.sql = fake_pyspark_sql

    sys.modules["delta"] = fake_delta
    sys.modules["delta.tables"] = fake_delta_tables
    sys.modules["pyspark"] = fake_pyspark
    sys.modules["pyspark.sql"] = fake_pyspark_sql
    sys.modules.pop("src.common.delta_load", None)

    try:
        module = importlib.import_module("src.common.delta_load")
    finally:
        sys.modules.pop("src.common.delta_load", None)
        if original_module is not None:
            sys.modules["src.common.delta_load"] = original_module
        if original_delta is not None:
            sys.modules["delta"] = original_delta
        else:
            sys.modules.pop("delta", None)
        if original_delta_tables is not None:
            sys.modules["delta.tables"] = original_delta_tables
        else:
            sys.modules.pop("delta.tables", None)
        if original_pyspark is not None:
            sys.modules["pyspark"] = original_pyspark
        else:
            sys.modules.pop("pyspark", None)
        if original_pyspark_sql is not None:
            sys.modules["pyspark.sql"] = original_pyspark_sql
        else:
            sys.modules.pop("pyspark.sql", None)

    return module, fake_delta_tables.DeltaTable


def test_create_or_merge_delta_new_table_uses_merge_schema_without_session_conf():
    delta_load, _ = _import_delta_load_with_fake_delta()
    writer = MagicMock()
    writer.format.return_value = writer
    writer.mode.return_value = writer
    writer.option.return_value = writer
    writer.partitionBy.return_value = writer

    dataframe = MagicMock()
    dataframe.write = writer

    spark = MagicMock()
    delta_load.table_exists = MagicMock(return_value=False)

    delta_load.create_or_merge_delta(
        spark=spark,
        dataframe=dataframe,
        target_table="catalog.schema.table",
        target_path="/tmp/table",
        merge_keys=["id"],
    )

    spark.conf.set.assert_not_called()
    writer.option.assert_any_call("mergeSchema", "true")
    writer.option.assert_any_call("path", "/tmp/table")
    writer.partitionBy.assert_called_once_with(
        "_np_source_year",
        "_np_source_month",
    )
    writer.saveAsTable.assert_called_once_with("catalog.schema.table")


def test_create_or_merge_delta_existing_table_merges_without_session_conf():
    delta_load, delta_table_class = _import_delta_load_with_fake_delta()
    merge_builder = MagicMock()
    merge_builder.whenMatchedUpdateAll.return_value = merge_builder
    merge_builder.whenNotMatchedInsertAll.return_value = merge_builder

    delta_table_instance = MagicMock()
    delta_table_instance.alias.return_value = delta_table_instance
    delta_table_instance.merge.return_value = merge_builder
    delta_table_class.forPath.return_value = delta_table_instance

    dataframe = MagicMock()
    dataframe.alias.return_value = "source_df"

    spark = MagicMock()
    delta_load.table_exists = MagicMock(return_value=True)

    delta_load.create_or_merge_delta(
        spark=spark,
        dataframe=dataframe,
        target_table="catalog.schema.table",
        target_path="/tmp/table",
        merge_keys=["id"],
    )

    spark.conf.set.assert_not_called()
    delta_table_class.forPath.assert_called_once_with(spark, "/tmp/table")
    delta_table_instance.merge.assert_called_once()
    merge_builder.execute.assert_called_once_with()
