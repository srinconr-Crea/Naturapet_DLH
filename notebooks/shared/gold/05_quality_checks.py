# Databricks notebook source
from pyspark.sql import functions as F

dbutils.widgets.text("environment", "dev")
dbutils.widgets.text("catalog_name", "naturapet_dev")
dbutils.widgets.text("storage_account", "demodldb")
dbutils.widgets.text("storage_container", "democodex")
dbutils.widgets.text("data_year", "2026")

environment = dbutils.widgets.get("environment").strip().lower()
catalog = dbutils.widgets.get("catalog_name").strip()
storage_account = dbutils.widgets.get("storage_account").strip()
storage_container = dbutils.widgets.get("storage_container").strip()
data_year = dbutils.widgets.get("data_year").strip()

gold_schema = "gobierno_gold"
storage_uri = f"abfss://{storage_container}@{storage_account}.dfs.core.windows.net"
gold_root = f"{storage_uri}/external/{environment}/gobierno/gold/{data_year}"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{gold_schema}`")


def full_name(schema, name):
    return f"`{catalog}`.`{schema}`.`{name}`"


def mes_expr(alias):
    return F.coalesce(
        F.col(f"{alias}.mes_carga"),
        F.concat_ws("-", F.col(f"{alias}._np_source_year"), F.col(f"{alias}._np_source_month")),
    )


def write_gold(df, name):
    target_table = full_name(gold_schema, name)
    target_path = f"{gold_root}/{name}"
    (
        df.withColumn("_np_gold_layer", F.lit("gold"))
        .withColumn("_np_gold_processed_ts", F.current_timestamp())
        .write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .option("path", target_path)
        .saveAsTable(target_table)
    )
    return {"table_name": name, "target_table": target_table, "target_path": target_path, "rows": spark.table(target_table).count()}


silver_ventas = (
    spark.table(full_name("comercial_silver", "fact_ventas_cabecera"))
    .alias("v")
    .withColumn("mes_carga", mes_expr("v"))
    .groupBy("mes_carga")
    .agg(
        F.countDistinct("venta_id").alias("silver_numero_ventas"),
        F.sum("valor_total").alias("silver_ventas_totales"),
        F.sum("margen_bruto").alias("silver_margen_bruto"),
    )
)

silver_devoluciones = (
    spark.table(full_name("comercial_silver", "fact_devoluciones"))
    .alias("r")
    .withColumn("mes_carga", mes_expr("r"))
    .groupBy("mes_carga")
    .agg(
        F.countDistinct("devolucion_id").alias("silver_devoluciones"),
        F.sum("valor_reintegrado").alias("silver_valor_reintegrado"),
    )
)

gold_kpis = spark.table(full_name("shared_gold", "mart_kpis_ejecutivos_mensual")).select(
    "mes_carga",
    F.col("numero_ventas").alias("gold_numero_ventas"),
    F.col("ventas_totales").alias("gold_ventas_totales"),
    F.col("margen_bruto").alias("gold_margen_bruto"),
    F.col("devoluciones").alias("gold_devoluciones"),
    F.col("valor_reintegrado").alias("gold_valor_reintegrado"),
)

controls = spark.table(full_name("gobierno_silver", "resumen_mensual_validacion")).alias("c").withColumn("mes_carga_control", mes_expr("c"))

checks = (
    gold_kpis.join(silver_ventas, "mes_carga", "left")
    .join(silver_devoluciones, "mes_carga", "left")
    .join(controls, gold_kpis.mes_carga == F.col("mes_carga_control"), "left")
    .select(
        gold_kpis.mes_carga,
        "gold_numero_ventas",
        "silver_numero_ventas",
        F.col("ventas").alias("control_numero_ventas"),
        "gold_ventas_totales",
        "silver_ventas_totales",
        F.col("valor_total").alias("control_ventas_totales"),
        "gold_margen_bruto",
        "silver_margen_bruto",
        F.col("margen_bruto").alias("control_margen_bruto"),
        "gold_devoluciones",
        "silver_devoluciones",
        F.col("devoluciones").alias("control_devoluciones"),
        "gold_valor_reintegrado",
        "silver_valor_reintegrado",
        F.col("valor_reintegrado").alias("control_valor_reintegrado"),
    )
    .withColumn("ventas_match_silver", F.abs(F.col("gold_ventas_totales") - F.col("silver_ventas_totales")) <= F.lit(0.05))
    .withColumn("margen_match_silver", F.abs(F.col("gold_margen_bruto") - F.col("silver_margen_bruto")) <= F.lit(0.05))
    .withColumn("tickets_match_silver", F.col("gold_numero_ventas") == F.col("silver_numero_ventas"))
    .withColumn("devoluciones_match_silver", F.col("gold_devoluciones") == F.col("silver_devoluciones"))
    .withColumn("valor_reintegrado_match_silver", F.abs(F.col("gold_valor_reintegrado") - F.col("silver_valor_reintegrado")) <= F.lit(0.05))
    .withColumn(
        "gold_quality_status",
        F.when(
            F.col("ventas_match_silver")
            & F.col("margen_match_silver")
            & F.col("tickets_match_silver")
            & F.col("devoluciones_match_silver")
            & F.col("valor_reintegrado_match_silver"),
            F.lit("PASS"),
        ).otherwise(F.lit("FAIL")),
    )
)

summary = [write_gold(checks, "gold_quality_checks")]
display(spark.createDataFrame(summary))
