import pytest

from src.common.schema import normalize_table_name


@pytest.mark.parametrize(
    "file_name, month, expected",
    [
        pytest.param("fact_ventas_01.csv", "01", "fact_ventas", id="csv"),
        pytest.param("fact_ventas_01.json", "01", "fact_ventas", id="json"),
        pytest.param("fact_ventas_01.parquet", "01", "fact_ventas", id="parquet"),
        pytest.param(
            "Fact_Ventas_01.CSV", "01", "Fact_Ventas", id="extension-mayuscula-nombre-preservado"
        ),
        pytest.param("fact_ventas_01.JsOn", "01", "fact_ventas", id="extension-mixta"),
        pytest.param("fact_ventas.PARQUET", "", "fact_ventas", id="parquet-mayuscula-sin-mes"),
        pytest.param("fact_ventas_02.csv", "01", "fact_ventas_02", id="sufijo-distinto-al-mes"),
        pytest.param("fact_ventas_01.csv", "", "fact_ventas_01", id="mes-vacio"),
        pytest.param("fact.ventas_01.json", "01", "fact.ventas", id="punto-interno"),
        pytest.param(
            "fact_ventas_01.xlsx", "01", "fact_ventas_01.xlsx", id="extension-no-reconocida"
        ),
        pytest.param("fact_ventas_01", "01", "fact_ventas", id="sin-extension"),
        pytest.param(
            "fact_ventas_01.csv.json", "01", "fact_ventas_01.csv", id="solo-una-extension"
        ),
        pytest.param(
            "fact_ventas_01.xlsx", "01", "fact_ventas_01.xlsx", id="xlsx-conserva-sufijo-mes"
        ),
    ],
)
def test_normalize_table_name(file_name, month, expected):
    assert normalize_table_name(file_name, month) == expected


def test_normalize_table_name_month_default_is_empty():
    assert normalize_table_name("fact_ventas_01.csv") == "fact_ventas_01"
