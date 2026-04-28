from src.utilities.file_ingestion import IngestionConfig, build_table_path


def test_build_table_path():
    config = IngestionConfig(
        catalog="naturapet_dev",
        schema="comercial_bronze",
        table_name="monthly_naturapet_files",
        external_base_path="abfss://democodex@demodldb.dfs.core.windows.net/external/dev/comercial/bronze/2026/01",
    )

    assert (
        build_table_path(config)
        == "abfss://democodex@demodldb.dfs.core.windows.net/external/dev/comercial/bronze/2026/01/comercial_bronze/monthly_naturapet_files"
    )
