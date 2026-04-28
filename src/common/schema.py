from typing import Dict, List, Tuple

from pyspark.sql import DataFrame, functions as F
from pyspark.sql import types as T


CSV_TO_SPARK_TYPE = {
    "object": T.StringType(),
    "int64": T.LongType(),
    "float64": T.DoubleType(),
}


def normalize_table_name(file_name: str, month: str = "") -> str:
    table_name = file_name.removesuffix(".csv")
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


def build_spark_schema(entries: List[Dict[str, str]]) -> T.StructType:
    return T.StructType(
        [
            T.StructField(
                entry["campo"],
                CSV_TO_SPARK_TYPE.get(entry["tipo_dato_csv"], T.StringType()),
                True,
            )
            for entry in entries
        ]
    )


def validate_expected_columns(
    dataframe: DataFrame,
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
    dataframe: DataFrame,
    table_name: str,
    dictionary_map: Dict[str, List[Dict[str, str]]],
) -> DataFrame:
    if table_name not in dictionary_map:
        return dataframe

    entries = dictionary_map[table_name]
    select_expressions = []
    for entry in entries:
        column_name = entry["campo"]
        spark_type = CSV_TO_SPARK_TYPE.get(entry["tipo_dato_csv"], T.StringType())
        select_expressions.append(F.col(column_name).cast(spark_type).alias(column_name))

    return dataframe.select(*select_expressions)


def with_hash_key_if_needed(
    dataframe: DataFrame,
    table_name: str,
    primary_key_map: Dict[str, List[str]],
) -> Tuple[DataFrame, List[str]]:
    merge_keys = [
        key for key in primary_key_map.get(table_name, []) if key in dataframe.columns
    ]
    if merge_keys:
        return dataframe.dropDuplicates(merge_keys), merge_keys

    hash_columns = [
        F.coalesce(F.col(column_name).cast("string"), F.lit("<null>"))
        for column_name in dataframe.columns
    ]
    dataframe = dataframe.withColumn(
        "_np_record_hash",
        F.sha2(F.concat_ws("||", *hash_columns), 256),
    )
    return dataframe.dropDuplicates(["_np_record_hash"]), ["_np_record_hash"]
