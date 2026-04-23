from src.utilities.file_ingestion import IngestionConfig, build_table_path


def test_build_table_path():
    config = IngestionConfig(
        catalog="dev",
        schema="area1_bronze",
        table_name="monthly_client_files",
        external_base_path="abfss://datos@stclienteexample.dfs.core.windows.net/external/dev/clientes",
    )

    assert (
        build_table_path(config)
        == "abfss://datos@stclienteexample.dfs.core.windows.net/external/dev/clientes/area1_bronze/monthly_client_files"
    )

