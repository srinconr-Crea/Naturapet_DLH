import os
from typing import Dict


def _get_widget_value(dbutils, name: str, default: str) -> str:
    try:
        value = dbutils.widgets.get(name)
        return value if value else default
    except Exception:
        dbutils.widgets.text(name, default)
        return default


def bootstrap_runtime(dbutils, area: str) -> Dict[str, str]:
    environment = _get_widget_value(dbutils, "environment", "dev").lower()
    catalog_name = _get_widget_value(dbutils, "catalog_name", "")
    data_year = _get_widget_value(dbutils, "data_year", "2026")

    os.environ["APP_ENV"] = environment
    os.environ["AREA"] = area
    os.environ["DATA_YEAR"] = data_year

    if catalog_name:
        os.environ["CATALOG"] = catalog_name

    return {
        "environment": environment,
        "catalog_name": catalog_name,
        "data_year": data_year,
        "area": area,
    }
