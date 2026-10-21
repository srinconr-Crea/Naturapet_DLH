"""Contract tests use synthetic values, never source datasets."""
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src.common.cotizaciones_contract import FIELDS, classify_duplicates, normalize_record


def valid(**changes):
    row = dict(zip(FIELDS, ["Q001", "20260203", "2026-02-03", "2026-02", " T001 ",
        "001", "C1", "P1", "G1", "2", "100.00", "0", "0", "200",
        "0.19", "38", "238", "COP", "Aceptada", "30"]))
    return row | changes


def test_schema_original_and_safe_normalization():
    original = valid(tienda_id=" 001 ", ciudad_id="   ")
    result = normalize_record(original, "2026-02")
    assert len(FIELDS) == 20
    assert result["values"]["tienda_id"] == "001"
    assert result["values"]["ciudad_id"] is None
    assert result["values"]["fecha_cotizacion"] == date(2026, 2, 3)
    assert result["values"]["precio_unitario"] == Decimal("100.00")
    assert result["original"] == original
    assert not result["errors"] and not result["alerts"]
    assert any(c["field"] == "tienda_id" and c["original"] == " 001 " for c in result["conversions"])


@pytest.mark.parametrize("field,value,code", [tuple(case) for case in json.loads(
    (Path(__file__).parent / "fixtures/cotizaciones/cases.json").read_text())])
def test_invalid_tokens(field, value, code):
    result = normalize_record(valid(**{field: value}), "2026-02")
    assert {"field": field, "code": code} in result["errors"]
    assert result["original"][field] == value


@pytest.mark.parametrize("token", ["2026-02-03", "03/02/2026", "2026/02/03"])
def test_date_formats(token):
    result = normalize_record(valid(fecha_cotizacion=token), "2026-02")
    assert not result["errors"]
    assert any(c["field"] == "fecha_cotizacion" for c in result["conversions"])


def test_integer_and_decimal_exact_limits():
    result = normalize_record(valid(cantidad="2147483647", precio_unitario="9999999999999999.99",
        descuento_pct="999999.9999", descuento_valor="1.2300"), "2026-02")
    assert not result["errors"]
    assert result["values"]["descuento_valor"] == Decimal("1.23")


def test_alerts_do_not_reject_and_nulls_are_not_zero():
    result = normalize_record(valid(cantidad="0", vigencia_dias="-1", descuento_pct="1.1",
        moneda="USD", estado_cotizacion="Pendiente", precio_unitario=""), "2026-02")
    assert not result["errors"]
    assert result["values"]["precio_unitario"] is None
    assert {a["field"] for a in result["alerts"]} >= {
        "cantidad", "vigencia_dias", "descuento_pct", "moneda", "estado_cotizacion", "base_sin_iva"}


@pytest.mark.parametrize("total,alert", [("238.01", False), ("238.02", True)])
def test_money_tolerance(total, alert):
    result = normalize_record(valid(valor_total_cotizacion=total), "2026-02")
    assert any(a["field"] == "valor_total_cotizacion" for a in result["alerts"]) == alert
    assert result["values"]["valor_total_cotizacion"] == Decimal(total)


def test_half_up_equation():
    result = normalize_record(valid(cantidad="1", precio_unitario="0.05", base_sin_iva="0.05",
        iva_tasa="0.1", iva_valor="0.01", valor_total_cotizacion="0.06"), "2026-02")
    assert not result["alerts"]


def test_post_normalization_duplicates_and_conflicts_preserve_all():
    rows = [normalize_record(valid(), "2026-02"),
            normalize_record(valid(cotizacion_id=" Q001 ", fecha_cotizacion="03/02/2026"), "2026-02")]
    assert [r["category"] for r in classify_duplicates(rows)] == ["ACCEPTED", "CONSOLIDATED"]
    rows.append(normalize_record(valid(cantidad="3"), "2026-02"))
    classified = classify_duplicates(rows)
    assert all(r["category"] == "REJECTED" for r in classified)
    assert all({"field": "cotizacion_id", "code": "DUPLICATE_PK"} in r["errors"] for r in classified)


def test_invalid_group_cannot_pick_a_valid_representative():
    result = classify_duplicates([normalize_record(valid(), "2026-02"),
        normalize_record(valid(cantidad="cinco"), "2026-02")])
    assert all(r["category"] == "REJECTED" for r in result)
