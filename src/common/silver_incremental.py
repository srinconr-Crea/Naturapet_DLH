from datetime import datetime
from typing import Dict, List, Optional

from delta.tables import DeltaTable
from pyspark.sql import DataFrame, functions as F, types as T


SILVER_AUDIT_TABLE_NAME = "silver_processing_audit"
NO_TABLES_SENTINEL = "__NO_TABLES__"

PRIMARY_KEYS = {
    "dim_fecha": ["fecha_id"],
    "dim_ciudad": ["ciudad_id"],
    "dim_tienda": ["tienda_id"],
    "dim_area_negocio": ["area_id"],
    "dim_centro_costo": ["centro_costo_id"],
    "dim_categoria_producto": ["categoria_id"],
    "dim_producto": ["producto_id"],
    "dim_proveedor": ["proveedor_id"],
    "bridge_producto_proveedor": ["producto_id", "proveedor_id"],
    "dim_cliente": ["cliente_id"],
    "dim_empleado": ["empleado_id"],
    "dim_canal_venta": ["canal_id"],
    "dim_metodo_pago": ["metodo_pago_id"],
    "dim_campana_marketing": ["campana_id"],
    "dim_transportista": ["transportista_id"],
    "dim_motivo_devolucion": ["motivo_devolucion_id"],
    "fact_ventas_cabecera": ["venta_id"],
    "fact_ventas_detalle": ["detalle_venta_id"],
    "fact_devoluciones": ["devolucion_id"],
    "fact_marketing": ["marketing_id"],
    "fact_inventario_mensual": ["mes_carga", "tienda_id", "producto_id"],
    "fact_ajustes_inventario": ["ajuste_id"],
    "fact_compras": ["orden_compra_id"],
    "fact_logistica_entregas": ["entrega_id"],
    "fact_costos_mensual": ["costo_id"],
    "fact_presupuesto_mensual": ["presupuesto_id"],
    "fact_objetivos_mensuales": ["objetivo_id"],
    "fact_calidad_datos_carga": ["control_id"],
    "resumen_mensual_validacion": ["mes_carga"],
    "manifest": ["archivo"],
    "data_dictionary": ["tabla", "campo"],
    "schema_relationships": [
        "tabla_origen",
        "campo_origen",
        "tabla_destino",
        "campo_destino",
    ],
}

SILVER_AUDIT_SCHEMA = T.StructType(
    [
        T.StructField("environment", T.StringType(), False),
        T.StructField("domain_name", T.StringType(), False),
        T.StructField("step_name", T.StringType(), False),
        T.StructField("table_name", T.StringType(), False),
        T.StructField("source_table", T.StringType(), True),
        T.StructField("target_table", T.StringType(), True),
        T.StructField("input_rows", T.LongType(), False),
        T.StructField("output_rows", T.LongType(), False),
        T.StructField("status", T.StringType(), False),
        T.StructField("message", T.StringType(), True),
        T.StructField("watermark_column", T.StringType(), True),
        T.StructField("previous_watermark", T.TimestampType(), True),
        T.StructField("new_watermark", T.TimestampType(), True),
        T.StructField("target_path", T.StringType(), True),
        T.StructField("created_at", T.TimestampType(), False),
        T.StructField("updated_at", T.TimestampType(), False),
    ]
)

STEP_SUMMARY_SCHEMA = T.StructType(
    [
        T.StructField("step_name", T.StringType(), False),
        T.StructField("table_name", T.StringType(), False),
        T.StructField("status", T.StringType(), False),
        T.StructField("input_rows", T.LongType(), False),
        T.StructField("output_rows", T.LongType(), False),
        T.StructField("previous_watermark", T.TimestampType(), True),
        T.StructField("new_watermark", T.TimestampType(), True),
        T.StructField("target_path", T.StringType(), True),
        T.StructField("message", T.StringType(), True),
    ]
)


def table_exists(spark, target_table: str) -> bool:
    return spark.catalog.tableExists(target_table)


def silver_audit_table(catalog: str, silver_schema: str) -> str:
    return f"`{catalog}`.`{silver_schema}`.`{SILVER_AUDIT_TABLE_NAME}`"


def silver_audit_path(silver_root: str) -> str:
    return f"{silver_root}/_control/{SILVER_AUDIT_TABLE_NAME}"


def ensure_silver_audit_table(spark, audit_table: str, audit_path: str) -> None:
    if table_exists(spark, audit_table):
        return

    empty_df = spark.createDataFrame([], SILVER_AUDIT_SCHEMA)
    (
        empty_df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .option("path", audit_path)
        .saveAsTable(audit_table)
    )


def list_processing_tables(spark, catalog: str, schema_name: str) -> List[str]:
    excluded = {SILVER_AUDIT_TABLE_NAME, "silver_quality_checks"}
    return [
        row.tableName
        for row in spark.sql(f"SHOW TABLES IN `{catalog}`.`{schema_name}`").collect()
        if not row.isTemporary and row.tableName not in excluded
    ]


def latest_success_watermark(
    spark,
    audit_table: str,
    step_name: str,
    table_name: str,
):
    if not table_exists(spark, audit_table):
        return None

    row = (
        spark.table(audit_table)
        .filter(
            (F.col("step_name") == F.lit(step_name))
            & (F.col("table_name") == F.lit(table_name))
            & (F.col("status") == F.lit("SUCCESS"))
        )
        .agg(F.max("new_watermark").alias("watermark"))
        .first()
    )
    return row["watermark"] if row else None


def filter_new_bronze_rows(dataframe: DataFrame, previous_watermark) -> DataFrame:
    if previous_watermark is None or "_np_ingestion_ts" not in dataframe.columns:
        return dataframe
    return dataframe.filter(F.col("_np_ingestion_ts") > F.lit(previous_watermark).cast("timestamp"))


def filter_pending_step_rows(dataframe: DataFrame, previous_step: str) -> DataFrame:
    if "_np_silver_step" not in dataframe.columns:
        return dataframe
    return dataframe.filter(F.col("_np_silver_step") == F.lit(previous_step))


def latest_dataframe_watermark(dataframe: DataFrame):
    if "_np_ingestion_ts" not in dataframe.columns:
        return None
    row = dataframe.agg(F.max("_np_ingestion_ts").alias("watermark")).first()
    return row["watermark"] if row else None


def build_merge_condition(merge_keys: List[str]) -> str:
    return " AND ".join([f"target.`{key}` <=> source.`{key}`" for key in merge_keys])


def _sql_type(data_type) -> str:
    return data_type.simpleString()


def _quote_identifier(name: str) -> str:
    return f"`{name.replace('`', '``')}`"


def align_to_target_schema(spark, dataframe: DataFrame, target_table: str) -> DataFrame:
    target_fields = spark.table(target_table).schema.fields
    for field in target_fields:
        if field.name not in dataframe.columns:
            dataframe = dataframe.withColumn(field.name, F.lit(None).cast(field.dataType))
    return dataframe


def add_missing_target_columns(spark, dataframe: DataFrame, target_table: str) -> None:
    target_columns = {field.name for field in spark.table(target_table).schema.fields}
    missing_fields = [
        field
        for field in dataframe.schema.fields
        if field.name not in target_columns
    ]
    if not missing_fields:
        return

    column_definitions = ", ".join(
        f"{_quote_identifier(field.name)} {_sql_type(field.dataType)}"
        for field in missing_fields
    )
    spark.sql(f"ALTER TABLE {target_table} ADD COLUMNS ({column_definitions})")


def resolve_merge_keys(table_name: str, columns: List[str]) -> List[str]:
    keys = [key for key in PRIMARY_KEYS.get(table_name, []) if key in columns]
    if keys:
        return keys
    if "_np_record_hash" in columns:
        return ["_np_record_hash"]

    fallback_keys = [
        key
        for key in [
            "_np_source_year",
            "_np_source_month",
            "_np_source_path",
            "_np_source_file_name",
        ]
        if key in columns
    ]
    if fallback_keys:
        return fallback_keys

    raise ValueError(f"No hay llaves de MERGE disponibles para {table_name}.")


def merge_silver_table(
    spark,
    dataframe: DataFrame,
    target_table: str,
    target_path: str,
    merge_keys: List[str],
) -> None:
    if not table_exists(spark, target_table):
        (
            dataframe.write.format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .option("path", target_path)
            .saveAsTable(target_table)
        )
        return

    dataframe = align_to_target_schema(spark, dataframe, target_table)
    add_missing_target_columns(spark, dataframe, target_table)
    (
        DeltaTable.forName(spark, target_table)
        .alias("target")
        .merge(dataframe.alias("source"), build_merge_condition(merge_keys))
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )


def append_silver_audit(
    spark,
    audit_table: str,
    audit_path: str,
    record: Dict[str, object],
) -> None:
    dataframe = spark.createDataFrame([record], SILVER_AUDIT_SCHEMA)
    writer = dataframe.write.format("delta").option("path", audit_path)

    if table_exists(spark, audit_table):
        writer.mode("append").saveAsTable(audit_table)
    else:
        writer.mode("overwrite").saveAsTable(audit_table)


def build_audit_record(
    *,
    environment: str,
    domain_name: str,
    step_name: str,
    table_name: str,
    source_table: Optional[str],
    target_table: Optional[str],
    input_rows: int,
    output_rows: int,
    status: str,
    message: Optional[str],
    previous_watermark=None,
    new_watermark=None,
    target_path: Optional[str] = None,
) -> Dict[str, object]:
    now = datetime.utcnow()
    return {
        "environment": environment,
        "domain_name": domain_name,
        "step_name": step_name,
        "table_name": table_name,
        "source_table": source_table,
        "target_table": target_table,
        "input_rows": int(input_rows),
        "output_rows": int(output_rows),
        "status": status,
        "message": message,
        "watermark_column": "_np_ingestion_ts",
        "previous_watermark": previous_watermark,
        "new_watermark": new_watermark,
        "target_path": target_path,
        "created_at": now,
        "updated_at": now,
    }


def summary_from_record(record: Dict[str, object]) -> Dict[str, object]:
    return {
        "step_name": record["step_name"],
        "table_name": record["table_name"],
        "status": record["status"],
        "input_rows": record["input_rows"],
        "output_rows": record["output_rows"],
        "previous_watermark": record["previous_watermark"],
        "new_watermark": record["new_watermark"],
        "target_path": record["target_path"],
        "message": record["message"],
    }


def display_step_summary(spark, records: List[Dict[str, object]]) -> DataFrame:
    return spark.createDataFrame(records, STEP_SUMMARY_SCHEMA)
