# Databricks notebook source
import json
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql import types as T


AUDIT_TABLE_NAME = "bronze_file_load_audit"
MONTH_PATTERN = re.compile(r"^(0[1-9]|1[0-2])$")


AUDIT_SCHEMA = T.StructType(
    [
        T.StructField("load_id", T.StringType(), False),
        T.StructField("domain", T.StringType(), False),
        T.StructField("table_name", T.StringType(), False),
        T.StructField("load_mode", T.StringType(), False),
        T.StructField("source_year", T.StringType(), False),
        T.StructField("source_month", T.StringType(), True),
        T.StructField("source_path", T.StringType(), False),
        T.StructField("source_file_name", T.StringType(), False),
        T.StructField("target_table", T.StringType(), False),
        T.StructField("target_path", T.StringType(), False),
        T.StructField("record_count", T.LongType(), True),
        T.StructField("status", T.StringType(), False),
        T.StructField("error_message", T.StringType(), True),
        T.StructField("historic_path", T.StringType(), True),
        T.StructField("archived_at", T.TimestampType(), True),
        T.StructField("archive_status", T.StringType(), True),
        T.StructField("archive_error_message", T.StringType(), True),
        T.StructField("created_at", T.TimestampType(), False),
        T.StructField("updated_at", T.TimestampType(), False),
    ]
)


def ensure_text_widget(name: str, default_value: str) -> str:
    try:
        return dbutils.widgets.get(name)
    except Exception:
        dbutils.widgets.text(name, default_value)
        return default_value


def normalize_table_name(file_name: str, month: Optional[str] = None) -> str:
    table_name = file_name.removesuffix(".csv")
    if month and table_name.endswith(f"_{month}"):
        return table_name[: -(len(month) + 1)]
    return table_name


def build_raw_year_path(raw_domain_root: str, year: str) -> str:
    return f"{raw_domain_root}/{year}"


def build_external_table_path(external_domain_root: str, year: str, table_name: str) -> str:
    return f"{external_domain_root}/{year}/{table_name}"


def build_historic_file_path(
    historic_domain_root: str,
    year: str,
    source_file_name: str,
    month: Optional[str] = None,
) -> str:
    if month:
        return f"{historic_domain_root}/{year}/{month}/{source_file_name}"
    return f"{historic_domain_root}/{year}/{source_file_name}"


def build_audit_table_path(external_domain_root: str, year: str) -> str:
    return f"{external_domain_root}/{year}/_control/{AUDIT_TABLE_NAME}"


def fully_qualified_name(catalog_name: str, schema_name: str, table_name: str) -> str:
    return f"`{catalog_name}`.`{schema_name}`.`{table_name}`"


def table_exists(target_table: str) -> bool:
    return spark.catalog.tableExists(target_table)


def path_exists(path: str) -> bool:
    try:
        dbutils.fs.ls(path)
        return True
    except Exception:
        return False


def parent_directory(path: str) -> str:
    return path.rsplit("/", 1)[0]


def ensure_catalog_schema(catalog_name: str, schema_name: str) -> None:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog_name}`.`{schema_name}`")


def read_source_csv(source_path: str):
    return (
        spark.read.option("header", "true")
        .option("inferSchema", "true")
        .csv(source_path)
    )


def load_primary_key_map(raw_environment_root: str, year: str) -> Dict[str, List[str]]:
    data_dictionary_path = f"{raw_environment_root}/gobierno/{year}/data_dictionary.csv"
    if not path_exists(data_dictionary_path):
        return {}

    primary_key_df = (
        spark.read.option("header", "true").csv(data_dictionary_path).filter(F.col("rol") == "PK")
    )

    return {
        row["tabla"]: [column_name for column_name in row["pk_columns"].split(",") if column_name]
        for row in primary_key_df.groupBy("tabla")
        .agg(F.concat_ws(",", F.collect_list("campo")).alias("pk_columns"))
        .collect()
    }


def source_priority(table_name: str) -> int:
    if table_name.startswith("dim_"):
        return 0
    if table_name.startswith("bridge_"):
        return 1
    if table_name.startswith("fact_"):
        return 2
    return 3


def discover_source_files(raw_domain_root: str, year: str):
    year_path = build_raw_year_path(raw_domain_root, year)
    root_level_files = []
    monthly_files = []

    for entry in dbutils.fs.ls(year_path):
        entry_name = entry.name.rstrip("/")
        if entry.isDir() and MONTH_PATTERN.match(entry_name):
            for monthly_file in dbutils.fs.ls(entry.path):
                if monthly_file.isDir():
                    continue
                monthly_files.append(
                    {
                        "source_path": monthly_file.path,
                        "source_file_name": monthly_file.name,
                        "source_month": entry_name,
                        "load_mode": "incremental",
                        "table_name": normalize_table_name(monthly_file.name, entry_name),
                    }
                )
            continue

        if not entry.isDir():
            root_level_files.append(
                {
                    "source_path": entry.path,
                    "source_file_name": entry.name,
                    "source_month": None,
                    "load_mode": "full",
                    "table_name": normalize_table_name(entry.name),
                }
            )

    root_level_files = sorted(
        root_level_files,
        key=lambda item: (source_priority(item["table_name"]), item["table_name"]),
    )
    monthly_files = sorted(
        monthly_files,
        key=lambda item: (
            item["source_month"],
            source_priority(item["table_name"]),
            item["table_name"],
        ),
    )
    return root_level_files + monthly_files


def add_ingestion_metadata(
    dataframe,
    domain: str,
    source_year: str,
    source_month: Optional[str],
    source_path: str,
    source_file_name: str,
    load_mode: str,
):
    return (
        dataframe.withColumn("_np_domain", F.lit(domain))
        .withColumn("_np_source_year", F.lit(source_year))
        .withColumn("_np_source_month", F.lit(source_month).cast("string"))
        .withColumn("_np_source_path", F.lit(source_path))
        .withColumn("_np_source_file_name", F.lit(source_file_name))
        .withColumn("_np_load_mode", F.lit(load_mode))
        .withColumn("_np_loaded_at", F.current_timestamp())
    )


def add_row_hash_if_needed(dataframe, key_columns: List[str]):
    resolved_key_columns = [column_name for column_name in key_columns if column_name in dataframe.columns]
    if resolved_key_columns:
        return dataframe.dropDuplicates(resolved_key_columns), resolved_key_columns

    business_columns = list(dataframe.columns)
    hash_columns = [
        F.coalesce(F.col(column_name).cast("string"), F.lit("<null>"))
        for column_name in business_columns
    ]

    dataframe = dataframe.withColumn("_np_record_hash", F.sha2(F.concat_ws("||", *hash_columns), 256))
    return dataframe.dropDuplicates(["_np_record_hash"]), ["_np_record_hash"]


def write_initial_table(dataframe, target_table: str, target_path: str) -> None:
    (
        dataframe.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .option("path", target_path)
        .partitionBy("_np_source_year", "_np_source_month")
        .saveAsTable(target_table)
    )


def merge_to_delta(dataframe, target_table: str, target_path: str, merge_keys: List[str]) -> None:
    spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")

    if not table_exists(target_table):
        write_initial_table(dataframe, target_table, target_path)
        return

    merge_condition = " AND ".join(
        [f"target.`{column_name}` <=> source.`{column_name}`" for column_name in merge_keys]
    )

    (
        DeltaTable.forPath(spark, target_path)
        .alias("target")
        .merge(dataframe.alias("source"), merge_condition)
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )


def audit_record(
    *,
    load_id: str,
    domain: str,
    table_name: str,
    load_mode: str,
    source_year: str,
    source_month: Optional[str],
    source_path: str,
    source_file_name: str,
    target_table: str,
    target_path: str,
    record_count: Optional[int],
    status: str,
    error_message: Optional[str],
    historic_path: str,
):
    now = datetime.utcnow()
    return {
        "load_id": load_id,
        "domain": domain,
        "table_name": table_name,
        "load_mode": load_mode,
        "source_year": source_year,
        "source_month": source_month,
        "source_path": source_path,
        "source_file_name": source_file_name,
        "target_table": target_table,
        "target_path": target_path,
        "record_count": record_count,
        "status": status,
        "error_message": error_message,
        "historic_path": historic_path,
        "archived_at": None,
        "archive_status": None,
        "archive_error_message": None,
        "created_at": now,
        "updated_at": now,
    }


def append_audit_records(audit_records, audit_table: str, audit_path: str) -> None:
    if not audit_records:
        return

    audit_dataframe = spark.createDataFrame(audit_records, schema=AUDIT_SCHEMA)
    writer = audit_dataframe.write.format("delta").option("path", audit_path)

    if table_exists(audit_table):
        writer.mode("append").saveAsTable(audit_table)
    else:
        writer.mode("overwrite").saveAsTable(audit_table)


def pending_archive_records(audit_table: str):
    if not table_exists(audit_table):
        return []

    return [
        row.asDict()
        for row in spark.table(audit_table)
        .filter((F.col("status") == "SUCCESS") & F.col("archived_at").isNull())
        .orderBy("source_year", "source_month", "table_name")
        .collect()
    ]


def update_archive_status(audit_table: str, updates: List[dict]) -> None:
    if not updates:
        return

    update_schema = T.StructType(
        [
            T.StructField("load_id", T.StringType(), False),
            T.StructField("archived_at", T.TimestampType(), True),
            T.StructField("archive_status", T.StringType(), True),
            T.StructField("archive_error_message", T.StringType(), True),
            T.StructField("updated_at", T.TimestampType(), False),
        ]
    )
    updates_dataframe = spark.createDataFrame(updates, schema=update_schema)

    (
        DeltaTable.forName(spark, audit_table)
        .alias("target")
        .merge(updates_dataframe.alias("source"), "target.load_id = source.load_id")
        .whenMatchedUpdate(
            set={
                "archived_at": "source.archived_at",
                "archive_status": "source.archive_status",
                "archive_error_message": "source.archive_error_message",
                "updated_at": "source.updated_at",
            }
        )
        .execute()
    )


def summarize_results(summary: dict) -> None:
    print(json.dumps(summary, indent=2, ensure_ascii=False))
