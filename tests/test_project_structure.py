from src.utilities.file_ingestion import (
    IngestionConfig,
    AUDIT_TABLE_NAME,
    build_audit_table_path,
    build_historic_file_path,
    build_table_path,
    normalize_table_name,
)


def test_build_table_path():
    config = IngestionConfig(
        catalog="naturapet_dev",
        schema="comercial_bronze",
        table_name="fact_ventas_cabecera",
        external_base_path="abfss://democodex@demodldb.dfs.core.windows.net/external/dev/comercial/bronze",
        data_year="2026",
    )

    assert (
        build_table_path(config)
        == "abfss://democodex@demodldb.dfs.core.windows.net/external/dev/comercial/bronze/2026/fact_ventas_cabecera"
    )


def test_normalize_monthly_table_name():
    assert (
        normalize_table_name("fact_ventas_cabecera_01.csv", "01")
        == "fact_ventas_cabecera"
    )


def test_build_historic_monthly_file_path():
    assert (
        build_historic_file_path(
            "abfss://democodex@demodldb.dfs.core.windows.net/historic/comercial",
            "2026",
            "fact_ventas_cabecera_01.csv",
            "01",
        )
        == "abfss://democodex@demodldb.dfs.core.windows.net/historic/comercial/2026/01/fact_ventas_cabecera_01.csv"
    )


def test_build_audit_table_path():
    assert (
        build_audit_table_path(
            "abfss://democodex@demodldb.dfs.core.windows.net/external/dev/comercial/bronze",
            "2026",
        )
        == f"abfss://democodex@demodldb.dfs.core.windows.net/external/dev/comercial/bronze/2026/_control/{AUDIT_TABLE_NAME}"
    )
