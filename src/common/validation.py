import re
from typing import Dict, List, Optional


ALLOW_SCHEMA_INFERENCE_TABLES = {
    "manifest",
    "data_dictionary",
    "resumen_mensual_validacion",
}


def validate_table_known_or_allowed(
    table_name: str,
    dictionary_map: Dict[str, List[Dict[str, str]]],
) -> None:
    if table_name in dictionary_map:
        return
    if table_name in ALLOW_SCHEMA_INFERENCE_TABLES:
        return

    raise ValueError(
        f"La tabla {table_name} no existe en data_dictionary.csv y tampoco esta "
        f"autorizada para inferencia libre de esquema."
    )


def validate_non_empty_dataframe(dataframe, table_name: str) -> None:
    if dataframe.limit(1).count() == 0:
        raise ValueError(f"El archivo origen para {table_name} no contiene registros.")


def build_mes_carga_regex(expected_value: str) -> str:
    return rf"^{re.escape(expected_value)}($|[^0-9])"


def matches_expected_mes_carga_text(
    value: Optional[str],
    expected_value: str,
) -> bool:
    if value is None:
        return True
    return bool(re.match(build_mes_carga_regex(expected_value), value.strip()))


def validate_mes_carga_alignment(
    dataframe,
    table_name: str,
    source_year: str,
    source_month: Optional[str],
) -> None:
    if not source_month or "mes_carga" not in dataframe.columns:
        return

    from pyspark.sql import functions as F

    expected_value = f"{source_year}-{source_month}"
    mes_carga_as_text = F.trim(F.col("mes_carga").cast("string"))
    valid_mes_carga = mes_carga_as_text.rlike(build_mes_carga_regex(expected_value))
    mismatched_rows = dataframe.filter(
        F.col("mes_carga").isNotNull() & (~valid_mes_carga)
    )
    mismatched = (
        mismatched_rows
        .limit(1)
        .count()
    )

    if mismatched:
        actual_values = [
            row["mes_carga"]
            for row in mismatched_rows.select(mes_carga_as_text.alias("mes_carga"))
            .distinct()
            .limit(5)
            .collect()
        ]
        raise ValueError(
            f"La tabla {table_name} contiene valores de mes_carga que no coinciden "
            f"con el folder {source_year}/{source_month}. Valor esperado: {expected_value}. "
            f"Valores encontrados: {actual_values}."
        )
