from typing import Dict, List, Optional

from pyspark.sql import DataFrame, functions as F


ALLOW_SCHEMA_INFERENCE_TABLES = {"manifest"}


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


def validate_non_empty_dataframe(dataframe: DataFrame, table_name: str) -> None:
    if dataframe.limit(1).count() == 0:
        raise ValueError(f"El archivo origen para {table_name} no contiene registros.")


def validate_mes_carga_alignment(
    dataframe: DataFrame,
    table_name: str,
    source_year: str,
    source_month: Optional[str],
) -> None:
    if not source_month or "mes_carga" not in dataframe.columns:
        return

    expected_value = f"{source_year}-{source_month}"
    mismatched = (
        dataframe.filter(F.col("mes_carga").cast("string") != F.lit(expected_value))
        .limit(1)
        .count()
    )

    if mismatched:
        raise ValueError(
            f"La tabla {table_name} contiene valores de mes_carga que no coinciden "
            f"con el folder {source_year}/{source_month}. Valor esperado: {expected_value}."
        )
