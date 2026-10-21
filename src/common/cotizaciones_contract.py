"""Versioned Bronze contract. Pure Python; imports never contact Databricks."""
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, DecimalException, ROUND_HALF_UP, localcontext
import json
import re

CONTRACT_VERSION = "cotizaciones-v1"
FIELD_TYPES = {
    "cotizacion_id": "string", "fecha_id": "string", "fecha_cotizacion": "date",
    "mes_carga": "string", "tienda_id": "string", "ciudad_id": "string",
    "canal_id": "string", "producto_id": "string", "categoria_id": "string",
    "cantidad": "int", "precio_unitario": "decimal(18,2)",
    "descuento_pct": "decimal(10,4)", "descuento_valor": "decimal(18,2)",
    "base_sin_iva": "decimal(18,2)", "iva_tasa": "decimal(10,4)",
    "iva_valor": "decimal(18,2)", "valor_total_cotizacion": "decimal(18,2)",
    "moneda": "string", "estado_cotizacion": "string", "vigencia_dias": "int",
}
FIELDS = tuple(FIELD_TYPES)
ID_FIELDS = {f for f in FIELDS if f.endswith("_id")}


def json_value(value):
    """Canonical representation is unambiguous for field positions and NULL."""
    return json.dumps(value, default=str, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def normalize_record(original, period):
    values, errors, alerts, conversions = {}, [], [], []

    def issue(target, field, code):
        target.append({"field": field, "code": code})

    for field, kind in FIELD_TYPES.items():
        raw = original.get(field)
        token = raw.strip() if isinstance(raw, str) else raw
        token = None if token == "" else token
        value, rule = token, "TRIM_NULL"
        if field not in ID_FIELDS and kind == "string":
            # Business enums and period are exact; whitespace is not a correction.
            value = None if token is None else raw
        if kind == "int" and token is not None:
            if not re.fullmatch(r"[+-]?[0-9]+", token):
                issue(errors, field, "INVALID_INTEGER")
                value = None
            else:
                digits = token.lstrip("+-").lstrip("0")
                value = int(token) if len(digits) <= 10 and len(token) < 1000 else None
                if value is None or not -(2**31) <= value < 2**31:
                    issue(errors, field, "INTEGER_OVERFLOW")
                    value = None
            rule = "INT_EXACT"
        elif kind.startswith("decimal") and token is not None:
            precision, scale = map(int, re.findall(r"\d+", kind))
            rule = "DECIMAL_EXACT"
            if not re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)", token):
                issue(errors, field, "INVALID_DECIMAL")
                value = None
            else:
                value = Decimal(token)
                with localcontext() as context:
                    context.prec = max(64, len(token) + 10)
                    quantum = Decimal(1).scaleb(-scale)
                    if abs(value) >= Decimal(10) ** (precision - scale):
                        issue(errors, field, "DECIMAL_OVERFLOW")
                        value = None
                    elif value != value.quantize(quantum):
                        issue(errors, field, "DECIMAL_SCALE")
                        value = None
                    else:
                        value = value.quantize(quantum)
        elif kind == "date":
            rule, value = "DATE_ISO", None
            if token is None:
                issue(errors, field, "MISSING_DATE")
            else:
                formats = [(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", "%Y-%m-%d"),
                           (r"[0-9]{2}/[0-9]{2}/[0-9]{4}", "%d/%m/%Y"),
                           (r"[0-9]{4}/[0-9]{2}/[0-9]{2}", "%Y/%m/%d")]
                for pattern, fmt in formats:
                    if re.fullmatch(pattern, token):
                        try:
                            value = datetime.strptime(token, fmt).date()
                        except ValueError:
                            pass
                        break
                if value is None:
                    issue(errors, field, "INVALID_DATE")
                elif value.strftime("%Y-%m") != period:
                    issue(errors, field, "DATE_OUTSIDE_PERIOD")
        values[field] = value
        if value != raw or kind == "date":
            conversions.append({"field": field, "original": raw, "normalized": str(value) if value is not None else None, "rule": rule})

    if values["cotizacion_id"] is None:
        issue(errors, "cotizacion_id", "MISSING_PK")
    fecha_id = values["fecha_id"]
    if fecha_id is None or not re.fullmatch(r"[0-9]{8}", fecha_id):
        issue(errors, "fecha_id", "INVALID_DATE_ID")
    elif values["fecha_cotizacion"] and fecha_id != values["fecha_cotizacion"].strftime("%Y%m%d"):
        issue(errors, "fecha_id", "DATE_ID_MISMATCH")
    month = values["mes_carga"]
    if month is None or not re.fullmatch(r"[0-9]{4}-(?:0[1-9]|1[0-2])", month):
        issue(errors, "mes_carga", "INVALID_PERIOD")
    elif month != period:
        issue(errors, "mes_carga", "PERIOD_MISMATCH")

    checks = {
        "cantidad": lambda x: x > 0, "vigencia_dias": lambda x: x > 0,
        "descuento_pct": lambda x: 0 <= x <= 1, "moneda": lambda x: x == "COP",
        "estado_cotizacion": lambda x: x in {"Aceptada", "Rechazada", "Vencida"},
    }
    for field, predicate in checks.items():
        if values[field] is None:
            issue(alerts, field, "INCOMPLETE_RULE")
        elif not predicate(values[field]):
            issue(alerts, field, "BUSINESS_RULE")
    equations = [
        ("base_sin_iva", ("cantidad", "precio_unitario", "descuento_valor"), lambda a, b, c: a * b - c),
        ("iva_valor", ("base_sin_iva", "iva_tasa"), lambda a, b: a * b),
        ("valor_total_cotizacion", ("base_sin_iva", "iva_valor"), lambda a, b: a + b),
    ]
    for field, operands, equation in equations:
        if any(values[f] is None for f in (*operands, field)):
            issue(alerts, field, "INCOMPLETE_AMOUNT")
            continue
        try:
            with localcontext() as context:
                context.prec = 64
                expected = equation(*(values[f] for f in operands)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if abs(values[field] - expected) > Decimal("0.01"):
                    issue(alerts, field, "AMOUNT_MISMATCH")
        except DecimalException:
            issue(alerts, field, "AMOUNT_NOT_EVALUABLE")
    return {"original": dict(original), "values": values, "errors": errors,
            "alerts": alerts, "conversions": conversions, "fingerprint": json_value(values)}


def classify_duplicates(records):
    """Local contract oracle; Spark adapter uses distributed group aggregation."""
    rows = [dict(r, errors=list(r["errors"])) for r in records]
    groups = defaultdict(list)
    for index, row in enumerate(rows):
        groups[row["values"]["cotizacion_id"]].append(index)
    for key, indexes in groups.items():
        conflict = key is not None and (len({rows[i]["fingerprint"] for i in indexes}) > 1
                    or any(rows[i]["errors"] for i in indexes)) and len(indexes) > 1
        for position, index in enumerate(indexes):
            row = rows[index]
            if conflict:
                row["errors"].append({"field": "cotizacion_id", "code": "DUPLICATE_PK"})
            row["category"] = "REJECTED" if row["errors"] else "ACCEPTED" if position == 0 else "CONSOLIDATED"
            row["representative_ordinal"] = indexes[0] + 1 if row["category"] != "REJECTED" else None
    return rows
