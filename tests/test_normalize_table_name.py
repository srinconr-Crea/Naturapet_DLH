import pytest

from src.common.schema import normalize_table_name


@pytest.mark.parametrize(
    "file_name, month, expected",
    [
        pytest.param("fact_ventas_01.csv", "01", "fact_ventas", id="csv-mensual"),
        pytest.param("fact_ventas_01.json", "01", "fact_ventas", id="json-mensual"),
        pytest.param("fact_ventas_01.parquet", "01", "fact_ventas", id="parquet-mensual"),
        pytest.param("Fact_Ventas_01.CSV", "01", "Fact_Ventas", id="csv-mayusculas"),
        pytest.param("fact_ventas_01.JsOn", "01", "fact_ventas", id="json-mixto"),
        pytest.param("fact_ventas.PARQUET", "", "fact_ventas", id="parquet-anual-sin-mes"),
        pytest.param("fact_ventas_02.csv", "01", "fact_ventas_02", id="sufijo-distinto-del-mes"),
        pytest.param("fact_ventas_01.csv", "", "fact_ventas_01", id="mes-vacio-conserva-sufijo"),
        pytest.param("fact.ventas_01.json", "01", "fact.ventas", id="punto-interno"),
        pytest.param("fact_ventas_01.xlsx", "01", "fact_ventas_01.xlsx", id="extension-no-reconocida"),
        pytest.param("fact_ventas_01", "01", "fact_ventas", id="sin-extension"),
    ],
)
def test_normalize_table_name(file_name, month, expected):
    assert normalize_table_name(file_name, month) == expected
