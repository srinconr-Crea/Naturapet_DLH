import pytest

from src.common.schema import normalize_table_name


@pytest.mark.parametrize(
    "extension",
    ["csv", "CSV", "CsV", "json", "JSON", "JsOn", "parquet", "PARQUET", "PaRqUeT"],
)
def test_recognized_extension_preserves_name_case(extension):
    assert normalize_table_name(f"Ventas_01.{extension}", "01") == "Ventas"


@pytest.mark.parametrize("month", ["", None])
def test_unset_month_preserves_month_suffix(month):
    assert normalize_table_name("Ventas_01.JSON", month) == "Ventas_01"


def test_omitted_month_preserves_month_suffix():
    assert normalize_table_name("Ventas_01.JSON") == "Ventas_01"


@pytest.mark.parametrize(
    "file_name,month,expected",
    [
        ("fact_ventas_01.json", "01", "fact_ventas"),
        ("Ventas_01.parquet", "1", "Ventas_01"),
        ("Ventas_01.parquet", "02", "Ventas_01"),
        ("Ventas_010.csv", "01", "Ventas_010"),
        ("Ventas_01_extra.csv", "01", "Ventas_01_extra"),
        ("Ventas_01.xlsx", "01", "Ventas_01.xlsx"),
        ("Ventas_01.csv.gz", "01", "Ventas_01.csv.gz"),
        ("Ventas_01.csv.backup", "01", "Ventas_01.csv.backup"),
        ("Ventas.v2_01.JsOn", "01", "Ventas.v2"),
        ("Ventas.csv.json", "01", "Ventas.csv"),
        ("Ventas_01", "01", "Ventas"),
        ("Ventas_01_01", "01", "Ventas_01"),
        ("Ventas_01_01.CSV", "01", "Ventas_01"),
        ("Ventas.csv_01", "01", "Ventas.csv"),
        ("Ventas.xlsx_01", "01", "Ventas.xlsx"),
        ("Ventas", "01", "Ventas"),
        ("", "", ""),
        ("", "01", ""),
        ("Ventas_ENERO.JSON", "enero", "Ventas_ENERO"),
        ("Ventas_ENERO.JSON", "ENERO", "Ventas"),
    ],
)
def test_extension_then_exact_month_once(file_name, month, expected):
    assert normalize_table_name(file_name, month) == expected
