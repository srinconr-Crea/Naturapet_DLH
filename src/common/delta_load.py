from datetime import datetime
from typing import Dict, List, Optional

from delta.tables import DeltaTable
from pyspark.sql import DataFrame, functions as F, types as T


AUDIT_TABLE_SCHEMA = T.StructType(
    [
        T.StructField("load_id", T.StringType(), False),
        T.StructField("area", T.StringType(), False),
        T.StructField("table_name", T.StringType(), False),
        T.StructField("load_mode", T.StringType(), False),
        T.StructField("source_year", T.StringType(), False),
        T.StructField("source_month", T.StringType(), True),
        T.StructField("source_path", T.StringType(), False),
        T.StructField("source_file_name", T.StringType(), False),
        T.StructField("source_format", T.StringType(), False),
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


def ensure_catalog_schema(spark, catalog: str, schema: str) -> None:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema}`")


def table_exists(spark, target_table: str) -> bool:
    return spark.catalog.tableExists(target_table)


def add_ingestion_metadata(
    dataframe: DataFrame,
    area: str,
    source_year: str,
    source_month: Optional[str],
    source_path: str,
    source_file_name: str,
    load_mode: str,
) -> DataFrame:
    return (
        dataframe.withColumn("_np_area", F.lit(area))
        .withColumn("_np_source_year", F.lit(source_year))
        .withColumn("_np_source_month", F.lit(source_month).cast("string"))
        .withColumn("_np_source_path", F.lit(source_path))
        .withColumn("_np_source_file_name", F.lit(source_file_name))
        .withColumn("_np_load_mode", F.lit(load_mode))
        .withColumn("_np_ingestion_ts", F.current_timestamp())
    )


def create_or_merge_delta(
    spark,
    dataframe: DataFrame,
    target_table: str,
    target_path: str,
    merge_keys: List[str],
) -> None:
    spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")

    if not table_exists(spark, target_table):
        (
            dataframe.write.format("delta")
            .mode("overwrite")
            .option("path", target_path)
            .partitionBy("_np_source_year", "_np_source_month")
            .saveAsTable(target_table)
        )
        return

    merge_condition = " AND ".join(
        [f"target.`{key}` <=> source.`{key}`" for key in merge_keys]
    )

    (
        DeltaTable.forPath(spark, target_path)
        .alias("target")
        .merge(dataframe.alias("source"), merge_condition)
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )


def build_audit_record(
    *,
    load_id: str,
    area: str,
    table_name: str,
    load_mode: str,
    source_year: str,
    source_month: Optional[str],
    source_path: str,
    source_file_name: str,
    source_format: str,
    target_table: str,
    target_path: str,
    record_count: Optional[int],
    status: str,
    error_message: Optional[str],
    historic_path: str,
) -> Dict[str, object]:
    now = datetime.utcnow()
    return {
        "load_id": load_id,
        "area": area,
        "table_name": table_name,
        "load_mode": load_mode,
        "source_year": source_year,
        "source_month": source_month,
        "source_path": source_path,
        "source_file_name": source_file_name,
        "source_format": source_format,
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


def append_audit_records(
    spark,
    audit_records: List[Dict[str, object]],
    audit_table: str,
    audit_table_path: str,
) -> None:
    if not audit_records:
        return

    dataframe = spark.createDataFrame(audit_records, schema=AUDIT_TABLE_SCHEMA)
    writer = dataframe.write.format("delta").option("path", audit_table_path)

    if table_exists(spark, audit_table):
        writer.mode("append").saveAsTable(audit_table)
    else:
        writer.mode("overwrite").saveAsTable(audit_table)


def list_pending_archives(spark, audit_table: str) -> List[Dict[str, object]]:
    if not table_exists(spark, audit_table):
        return []

    return [
        row.asDict()
        for row in spark.table(audit_table)
        .filter((F.col("status") == "SUCCESS") & F.col("archived_at").isNull())
        .orderBy("source_year", "source_month", "table_name")
        .collect()
    ]


def update_archive_status(spark, audit_table: str, updates: List[Dict[str, object]]) -> None:
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
    updates_df = spark.createDataFrame(updates, schema=update_schema)

    (
        DeltaTable.forName(spark, audit_table)
        .alias("target")
        .merge(updates_df.alias("source"), "target.load_id = source.load_id")
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
