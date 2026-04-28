import os
from typing import Any, Dict, Optional


VALID_ENVS = {"dev", "qa", "prod"}
STORAGE_URI = "abfss://democodex@demodldb.dfs.core.windows.net"
LOCAL_DATASET_ROOT = (
    r"C:\Users\Stiveen Rincon Ruge\Documents\Naturapet-Demo\retail_mascotas_colombia_dataset"
)
CATALOG_BY_ENV = {
    "dev": "naturapet_dev",
    "qa": "naturapet_qa",
    "prod": "naturapet_prod",
}


def _get_env(name: str, default: str) -> str:
    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) else value


def _coalesce(value: Optional[str], default: str) -> str:
    if value is None:
        return default
    cleaned = value.strip()
    return cleaned if cleaned else default


def get_config(spark=None, area: Optional[str] = None) -> Dict[str, Any]:
    env = _get_env("APP_ENV", _get_env("ENV", "dev")).lower()
    if env not in VALID_ENVS:
        raise ValueError(
            f"Ambiente '{env}' no válido. Use uno de: {sorted(VALID_ENVS)}"
        )

    resolved_area = _coalesce(area, _get_env("AREA", "shared")).lower()
    data_year = _get_env("DATA_YEAR", "2026")
    catalog = _get_env("CATALOG", CATALOG_BY_ENV[env])
    bronze_schema = _get_env("BRONZE_SCHEMA", f"{resolved_area}_bronze")

    raw_environment_root = _get_env("RAW_ENV_ROOT", f"{STORAGE_URI}/raw/{env}")
    external_environment_root = _get_env(
        "EXTERNAL_ENV_ROOT",
        f"{STORAGE_URI}/external/{env}",
    )
    historic_root = _get_env("HISTORIC_ROOT", f"{STORAGE_URI}/historic")

    raw_area_root = _get_env("RAW_AREA_ROOT", f"{raw_environment_root}/{resolved_area}")
    raw_year_path = _get_env("RAW_YEAR_PATH", f"{raw_area_root}/{data_year}")

    bronze_area_root = _get_env(
        "BRONZE_AREA_ROOT",
        f"{external_environment_root}/{resolved_area}/bronze",
    )
    bronze_year_root = _get_env("BRONZE_YEAR_ROOT", f"{bronze_area_root}/{data_year}")

    historic_area_root = _get_env(
        "HISTORIC_AREA_ROOT",
        f"{historic_root}/{resolved_area}",
    )
    historic_year_root = _get_env(
        "HISTORIC_YEAR_ROOT",
        f"{historic_area_root}/{data_year}",
    )

    government_dictionary_path = _get_env(
        "DATA_DICTIONARY_PATH",
        f"{raw_environment_root}/gobierno/{data_year}/data_dictionary.csv",
    )

    audit_table_name = _get_env("AUDIT_TABLE_NAME", "bronze_file_load_audit")
    audit_table_path = _get_env(
        "AUDIT_TABLE_PATH",
        f"{bronze_year_root}/_control/{audit_table_name}",
    )

    return {
        "env": env,
        "catalog": catalog,
        "area": resolved_area,
        "data_year": data_year,
        "bronze_schema": bronze_schema,
        "storage_uri": STORAGE_URI,
        "local_dataset_root": LOCAL_DATASET_ROOT,
        "raw_environment_root": raw_environment_root,
        "raw_area_root": raw_area_root,
        "raw_year_path": raw_year_path,
        "bronze_area_root": bronze_area_root,
        "bronze_year_root": bronze_year_root,
        "historic_area_root": historic_area_root,
        "historic_year_root": historic_year_root,
        "data_dictionary_path": government_dictionary_path,
        "audit_table_name": audit_table_name,
        "audit_table_path": audit_table_path,
    }


def build_raw_file_path(config: Dict[str, Any], relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/").lstrip("/")
    return f"{config['raw_environment_root']}/{normalized}"


def build_bronze_table_path(config: Dict[str, Any], table_name: str) -> str:
    return f"{config['bronze_year_root']}/{table_name}"


def build_historic_file_path(
    config: Dict[str, Any],
    source_file_name: str,
    source_month: Optional[str] = None,
) -> str:
    if source_month:
        return f"{config['historic_year_root']}/{source_month}/{source_file_name}"
    return f"{config['historic_year_root']}/{source_file_name}"


def build_audit_table_fqn(config: Dict[str, Any]) -> str:
    return (
        f"`{config['catalog']}`.`{config['bronze_schema']}`.`{config['audit_table_name']}`"
    )
