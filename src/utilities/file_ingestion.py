from dataclasses import dataclass
from typing import Optional


AUDIT_TABLE_NAME = "bronze_file_load_audit"


@dataclass
class IngestionConfig:
    catalog: str
    schema: str
    table_name: str
    external_base_path: str
    data_year: str = "2026"


def normalize_table_name(file_name: str, month: Optional[str] = None) -> str:
    table_name = file_name.removesuffix(".csv")
    if month and table_name.endswith(f"_{month}"):
        return table_name[: -(len(month) + 1)]
    return table_name


def build_table_path(config: IngestionConfig) -> str:
    return f"{config.external_base_path}/{config.data_year}/{config.table_name}"


def build_historic_file_path(
    historic_base_path: str,
    data_year: str,
    source_file_name: str,
    month: Optional[str] = None,
) -> str:
    if month:
        return f"{historic_base_path}/{data_year}/{month}/{source_file_name}"
    return f"{historic_base_path}/{data_year}/{source_file_name}"


def build_audit_table_path(external_base_path: str, data_year: str) -> str:
    return f"{external_base_path}/{data_year}/_control/{AUDIT_TABLE_NAME}"
