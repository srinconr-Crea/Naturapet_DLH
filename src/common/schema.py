from typing import Dict, List, Tuple

_RECOGNIZED_EXTENSIONS = (".csv", ".json", ".parquet")


def _require_pyspark():
    from pyspark.sql import functions as F
    from pyspark.sql import types as T

    csv_to_spark_type = {
        "object": T.StringType(),
        "int64": T.LongType(),
        "float64": T.DoubleType(),
    }
    return F, T, csv_to_spark_type


def normalize_table_name(file_name: str, month: str = "") -> str:
    """Resuelve el nombre de tabla a partir del nombre de archivo.

    Orden de normalización:
    1. Elimina una sola extensión final reconocida (.csv, .json o .parquet),
       sin distinguir mayúsculas de minúsculas.
    2. Elimina el sufijo ``_<month>`` solo si ``month`` está informado y
       coincide exactamente al final del nombre ya sin extensión.

    Preserva las mayúsculas del nombre de tabla, las extensiones no
    reconocidas (por ejemplo .xlsx) y los puntos internos del nombre.
    """
    table_name = file_name
    lowered_name = file_name.lower()
    for extension in _RECOGNIZED_EXTENSIONS:
        if lowered_name.endswith(extension):
            table_name = file_name[: -len(extension)]
            break
    if month and table_name.endswith(f"_{month}"):
        return table_name[: -(len(month) + 1)]
    return table_name


def load_data_dictionary(spark, data_dictionary_path: str) -> Dict[str, List[Dict[str, str]]]:
    dictionary_df = spark.read.option("header", "true").csv(data_dictionary_path)
    grouped_rows = {}

    for row in dictionary_df.collect():
        grouped_rows.setdefault(row["tabla"], []).append(row.asDict())

    return grouped_rows


def build_primary_key_map(
    dictionary_map: Dict[str, List[Dict[str, str]]]
) -> Dict[str, List[str]]:
    primary_keys = {}
    for table_name, entries in dictionary_map.items():
        keys = [entry["campo"] for entry in entries if entry["rol"] == "PK"]
        if keys:
            primary_keys[table_name] = keys
    return primary_keys


def build_spark_schema(entries: List[Dict[str, str]]):
    _, T, csv_to_spark_type = _require_pyspark()
    return T.StructType(
        [
            T.StructField(
                entry["campo"],
                csv_to_spark_type.get(entry["tipo_dato_csv"], T.StringType()),
                True,
            )
            for entry in entries
        ]
    )


def validate_expected_columns(
    dataframe,
    table_name: str,
    dictionary_map: Dict[str, List[Dict[str, str]]],
) -> None:
    if table_name not in dictionary_map:
        return

    expected_columns = [entry["campo"] for entry in dictionary_map[table_name]]
    missing_columns = [column for column in expected_columns if column not in dataframe.columns]

    if missing_columns:
        raise ValueError(
            f"La tabla {table_name} no contiene todas las columnas esperadas según "
            f"data_dictionary.csv. Faltan: {missing_columns}. "
            f"Columnas encontradas: {dataframe.columns}"
        )


def conform_to_dictionary(
    dataframe,
    table_name: str,
    dictionary_map: Dict[str, List[Dict[str, str]]],
):
    if table_name not in dictionary_map:
        return dataframe

    F, T, csv_to_spark_type = _require_pyspark()
    entries = dictionary_map[table_name]
    select_expressions = []
    for entry in entries:
        column_name = entry["campo"]
        spark_type = csv_to_spark_type.get(entry["tipo_dato_csv"], T.StringType())
        select_expressions.append(F.col(column_name).cast(spark_type).alias(column_name))

    return dataframe.select(*select_expressions)


def with_hash_key_if_needed(
    dataframe,
    table_name: str,
    primary_key_map: Dict[str, List[str]],
) -> Tuple[object, List[str]]:
    F, _, _ = _require_pyspark()
    from pyspark.sql import Window

    def latest_by_keys(input_dataframe, keys: List[str]):
        order_columns = []
        if "_np_ingestion_ts" in input_dataframe.columns:
            order_columns.append(F.col("_np_ingestion_ts").desc_nulls_last())
        for column_name in ["_np_source_path", "_np_source_file_name"]:
            if column_name in input_dataframe.columns:
                order_columns.append(F.col(column_name).desc_nulls_last())
        if not order_columns:
            order_columns = [F.lit(1)]
        window_spec = Window.partitionBy(*[F.col(key) for key in keys]).orderBy(
            *order_columns
        )
        return (
            input_dataframe.withColumn("_np_row_priority", F.row_number().over(window_spec))
            .filter(F.col("_np_row_priority") == 1)
            .drop("_np_row_priority")
        )

    merge_keys = [
        key for key in primary_key_map.get(table_name, []) if key in dataframe.columns
    ]
    if merge_keys:
        return latest_by_keys(dataframe, merge_keys), merge_keys

    volatile_columns = {"_np_ingestion_ts"}
    hash_columns = [
        F.coalesce(F.col(column_name).cast("string"), F.lit("<null>"))
        for column_name in dataframe.columns
        if column_name not in volatile_columns
    ]
    dataframe = dataframe.withColumn(
        "_np_record_hash",
        F.sha2(F.concat_ws("||", *hash_columns), 256),
    )
    return latest_by_keys(dataframe, ["_np_record_hash"]), ["_np_record_hash"]
