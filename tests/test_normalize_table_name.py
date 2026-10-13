import pytest

from src.common.schema import normalize_table_name


@pytest.mark.parametrize(
    "file_name,month,expected",
    [
        ("fact_ventas_01.csv", "01", "fact_ventas"),
        ("fact_ventas_01.json", "01", "fact_ventas"),
        ("fact_ventas_01.parquet", "01", "fact_ventas"),
        ("Fact_Ventas_01.CSV", "01", "Fact_Ventas"),
        ("fact_ventas_01.JsOn", "01", "fact_ventas"),
        ("fact_ventas.PARQUET", "", "fact_ventas"),
        ("fact_ventas_02.csv", "01", "fact_ventas_02"),
        ("fact_ventas_01.csv", "", "fact_ventas_01"),
        ("fact.ventas_01.json", "01", "fact.ventas"),
        ("fact_ventas_01.xlsx", "01", "fact_ventas_01.xlsx"),
        ("fact_ventas_01", "01", "fact_ventas"),
    ],
)
def test_normalize_table_name_acceptance(file_name, month, expected):
    assert normalize_table_name(file_name, month) == expected
