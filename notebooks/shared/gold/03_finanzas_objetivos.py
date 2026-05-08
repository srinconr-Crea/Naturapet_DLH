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

gold_schema = "finanzas_gold"
storage_uri = f"abfss://{storage_container}@{storage_account}.dfs.core.windows.net"
gold_root = f"{storage_uri}/external/{environment}/finanzas/gold/{data_year}"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{gold_schema}`")


def full_name(schema, name):
    return f"`{catalog}`.`{schema}`.`{name}`"


def mes_expr(alias):
    return F.coalesce(
        F.col(f"{alias}.mes_carga"),
        F.concat_ws("-", F.col(f"{alias}._np_source_year"), F.col(f"{alias}._np_source_month")),
    )


def safe_divide(numerator, denominator):
    return F.when(denominator.isNull() | (denominator == 0), F.lit(None)).otherwise(numerator / denominator)


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


costos = spark.table(full_name("finanzas_silver", "fact_costos_mensual")).alias("c")
presupuesto = spark.table(full_name("finanzas_silver", "fact_presupuesto_mensual")).alias("p")
objetivos = spark.table(full_name("finanzas_silver", "fact_objetivos_mensuales")).alias("o")
ventas = spark.table(full_name("comercial_silver", "fact_ventas_cabecera")).alias("v")
devoluciones = spark.table(full_name("comercial_silver", "fact_devoluciones")).alias("r")
logistica = spark.table(full_name("operaciones_silver", "fact_logistica_entregas")).alias("l")

ventas_base = (
    ventas.withColumn("mes_carga", mes_expr("v"))
    .groupBy("mes_carga", "tienda_id")
    .agg(
        F.sum("valor_total").alias("ventas_totales"),
        F.sum("base_neta_sin_iva").alias("ventas_sin_iva"),
        F.sum("margen_bruto").alias("margen_bruto"),
        F.countDistinct("venta_id").alias("numero_ventas"),
    )
)

devoluciones_base = (
    devoluciones.withColumn("mes_carga", mes_expr("r"))
    .groupBy("mes_carga", "tienda_id")
    .agg(F.countDistinct("devolucion_id").alias("devoluciones"))
)

logistica_base = (
    logistica.withColumn("mes_carga", mes_expr("l"))
    .groupBy("mes_carga", "tienda_id")
    .agg(F.countDistinct("entrega_id").alias("entregas"))
)

costos_base = (
    costos.withColumn("mes_carga", mes_expr("c"))
    .groupBy("mes_carga", "tienda_id")
    .agg(
        F.sum("monto_presupuestado").alias("costos_presupuestados"),
        F.sum("monto_real").alias("costos_reales"),
    )
)

presupuesto_base = (
    presupuesto.withColumn("mes_carga", mes_expr("p"))
    .groupBy("mes_carga", "tienda_id")
    .agg(
        F.sum("monto_presupuesto").alias("presupuesto"),
        F.sum("monto_ejecutado").alias("ejecutado"),
    )
)

finanzas_mensual = (
    presupuesto_base.join(costos_base, ["mes_carga", "tienda_id"], "full")
    .join(ventas_base, ["mes_carga", "tienda_id"], "left")
    .withColumn("variacion_presupuesto", F.col("ejecutado") - F.col("presupuesto"))
    .withColumn("variacion_presupuesto_pct", safe_divide(F.col("variacion_presupuesto"), F.col("presupuesto")))
    .withColumn("ejecucion_presupuesto_pct", safe_divide(F.col("ejecutado"), F.col("presupuesto")))
    .withColumn("variacion_costos", F.col("costos_reales") - F.col("costos_presupuestados"))
    .withColumn("variacion_costos_pct", safe_divide(F.col("variacion_costos"), F.col("costos_presupuestados")))
    .withColumn("costos_sobre_ventas_pct", safe_divide(F.col("costos_reales"), F.col("ventas_totales")))
    .withColumn("margen_despues_costos", F.col("margen_bruto") - F.col("costos_reales"))
    .withColumn("margen_despues_costos_pct", safe_divide(F.col("margen_despues_costos"), F.col("ventas_sin_iva")))
)

objetivos_base = (
    objetivos.withColumn("mes_carga", mes_expr("o"))
    .groupBy("mes_carga", "tienda_id")
    .agg(
        F.sum("meta_ventas").alias("meta_ventas"),
        F.sum("meta_tickets").alias("meta_tickets"),
        F.sum("meta_margen_bruto").alias("meta_margen_bruto"),
        F.avg("meta_tasa_devolucion").alias("meta_tasa_devolucion"),
        F.sum("meta_entregas").alias("meta_entregas"),
    )
)

objetivos_mensual = (
    objetivos_base.join(ventas_base, ["mes_carga", "tienda_id"], "left")
    .join(devoluciones_base, ["mes_carga", "tienda_id"], "left")
    .join(logistica_base, ["mes_carga", "tienda_id"], "left")
    .withColumn("cumplimiento_ventas_pct", safe_divide(F.col("ventas_totales"), F.col("meta_ventas")))
    .withColumn("cumplimiento_tickets_pct", safe_divide(F.col("numero_ventas"), F.col("meta_tickets")))
    .withColumn("cumplimiento_margen_pct", safe_divide(F.col("margen_bruto"), F.col("meta_margen_bruto")))
    .withColumn("brecha_ventas", F.col("ventas_totales") - F.col("meta_ventas"))
    .withColumn("brecha_tickets", F.col("numero_ventas") - F.col("meta_tickets"))
    .withColumn("brecha_margen", F.col("margen_bruto") - F.col("meta_margen_bruto"))
    .withColumn("cumple_meta_ventas", F.col("cumplimiento_ventas_pct") >= 1)
    .withColumn("cumple_meta_tickets", F.col("cumplimiento_tickets_pct") >= 1)
    .withColumn("cumple_meta_margen", F.col("cumplimiento_margen_pct") >= 1)
    .withColumn("tasa_devolucion_ticket", safe_divide(F.col("devoluciones"), F.col("numero_ventas")))
    .withColumn("tasa_devolucion_vs_meta", safe_divide(F.col("tasa_devolucion_ticket"), F.col("meta_tasa_devolucion")))
    .withColumn("entregas_vs_meta", safe_divide(F.col("entregas"), F.col("meta_entregas")))
)

summary = [
    write_gold(finanzas_mensual, "mart_finanzas_mensual"),
    write_gold(objetivos_mensual, "mart_objetivos_mensual"),
]

display(spark.createDataFrame(summary))
