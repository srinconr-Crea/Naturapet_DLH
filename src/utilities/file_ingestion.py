from dataclasses import dataclass


@dataclass
class IngestionConfig:
    catalog: str
    schema: str
    table_name: str
    external_base_path: str


def build_table_path(config: IngestionConfig) -> str:
    return f"{config.external_base_path}/{config.schema}/{config.table_name}"

