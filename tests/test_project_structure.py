import os

from src.common.config import (
    build_audit_table_fqn,
    build_bronze_table_path,
    build_historic_file_path,
    build_raw_file_path,
    get_config,
)
from src.common.io import detect_file_format
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
