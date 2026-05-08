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

gold_schema = "shared_gold"
storage_uri = f"abfss://{storage_container}@{storage_account}.dfs.core.windows.net"
gold_root = f"{storage_uri}/external/{environment}/shared/gold/{data_year}"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{gold_schema}`")


def full_name(schema, name):
    return f"`{catalog}`.`{schema}`.`{name}`"


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


ventas = spark.table(full_name("comercial_gold", "mart_ventas_mensual"))
ventas_producto = spark.table(full_name("comercial_gold", "mart_ventas_producto_mensual"))
devoluciones = spark.table(full_name("comercial_gold", "mart_devoluciones_mensual"))
inventario = spark.table(full_name("operaciones_gold", "mart_inventario_mensual"))
logistica = spark.table(full_name("operaciones_gold", "mart_logistica_mensual"))
marketing = spark.table(full_name("comercial_gold", "mart_marketing_mensual"))
finanzas = spark.table(full_name("finanzas_gold", "mart_finanzas_mensual"))
objetivos = spark.table(full_name("finanzas_gold", "mart_objetivos_mensual"))

ventas_mes = ventas.groupBy("mes_carga").agg(
    F.sum("ventas_totales").alias("ventas_totales"),
    F.sum("ventas_sin_iva").alias("ventas_sin_iva"),
    F.sum("margen_bruto").alias("margen_bruto"),
    F.sum("numero_ventas").alias("numero_ventas"),
)

unidades_mes = ventas_producto.groupBy("mes_carga").agg(F.sum("unidades_vendidas").alias("unidades_vendidas"))
devoluciones_mes = devoluciones.groupBy("mes_carga").agg(F.sum("devoluciones").alias("devoluciones"), F.sum("valor_reintegrado").alias("valor_reintegrado"))
inventario_mes = inventario.groupBy("mes_carga").agg(
    F.avg("cobertura_dias_promedio").alias("cobertura_dias_promedio"),
    F.sum("productos_bajo_reorden").alias("productos_bajo_reorden"),
)
logistica_mes = logistica.groupBy("mes_carga").agg(
    F.sum("entregas").alias("entregas"),
    F.sum("entregas_a_tiempo").alias("entregas_a_tiempo"),
    F.sum("costo_envio_total").alias("costo_envio_total"),
)
marketing_mes = marketing.groupBy("mes_carga").agg(F.sum("gasto_marketing").alias("gasto_marketing"), F.sum("ventas_atribuidas_valor").alias("ventas_atribuidas_valor"))
finanzas_mes = finanzas.groupBy("mes_carga").agg(
    F.sum("presupuesto").alias("presupuesto"),
    F.sum("ejecutado").alias("ejecutado"),
    F.sum("costos_reales").alias("costos_reales"),
)
objetivos_mes = objetivos.groupBy("mes_carga").agg(F.sum("meta_ventas").alias("meta_ventas"), F.sum("ventas_totales").alias("ventas_objetivo_totales"))

kpis = (
    ventas_mes.join(unidades_mes, "mes_carga", "left")
    .join(devoluciones_mes, "mes_carga", "left")
    .join(inventario_mes, "mes_carga", "left")
    .join(logistica_mes, "mes_carga", "left")
    .join(marketing_mes, "mes_carga", "left")
    .join(finanzas_mes, "mes_carga", "left")
    .join(objetivos_mes, "mes_carga", "left")
    .withColumn("ventas_netas", F.col("ventas_totales") - F.coalesce(F.col("valor_reintegrado"), F.lit(0)))
    .withColumn("margen_bruto_pct", safe_divide(F.col("margen_bruto"), F.col("ventas_sin_iva")))
    .withColumn("ticket_promedio", safe_divide(F.col("ventas_totales"), F.col("numero_ventas")))
    .withColumn("tasa_devolucion", safe_divide(F.col("devoluciones"), F.col("numero_ventas")))
    .withColumn("valor_reintegrado_pct", safe_divide(F.col("valor_reintegrado"), F.col("ventas_totales")))
    .withColumn("entregas_a_tiempo_pct", safe_divide(F.col("entregas_a_tiempo"), F.col("entregas")))
    .withColumn("costo_logistico_sobre_venta_pct", safe_divide(F.col("costo_envio_total"), F.col("ventas_totales")))
    .withColumn("marketing_roas", safe_divide(F.col("ventas_atribuidas_valor"), F.col("gasto_marketing")))
    .withColumn("ejecucion_presupuesto_pct", safe_divide(F.col("ejecutado"), F.col("presupuesto")))
    .withColumn("costos_sobre_ventas_pct", safe_divide(F.col("costos_reales"), F.col("ventas_totales")))
    .withColumn("cumplimiento_ventas_pct", safe_divide(F.col("ventas_objetivo_totales"), F.col("meta_ventas")))
)

summary = [write_gold(kpis, "mart_kpis_ejecutivos_mensual")]
display(spark.createDataFrame(summary))
