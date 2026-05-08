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

silver_schema = "operaciones_silver"
gold_schema = "operaciones_gold"
storage_uri = f"abfss://{storage_container}@{storage_account}.dfs.core.windows.net"
gold_root = f"{storage_uri}/external/{environment}/operaciones/gold/{data_year}"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{gold_schema}`")


def table(name):
    return f"`{catalog}`.`{silver_schema}`.`{name}`"


def sales_table(name):
    return f"`{catalog}`.`comercial_silver`.`{name}`"


def gold_table(name):
    return f"`{catalog}`.`{gold_schema}`.`{name}`"


def mes_expr(alias):
    return F.coalesce(
        F.col(f"{alias}.mes_carga"),
        F.concat_ws("-", F.col(f"{alias}._np_source_year"), F.col(f"{alias}._np_source_month")),
    )


def safe_divide(numerator, denominator):
    return F.when(denominator.isNull() | (denominator == 0), F.lit(None)).otherwise(numerator / denominator)


def write_gold(df, name):
    target_table = gold_table(name)
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


inventario = spark.table(table("fact_inventario_mensual")).alias("i")
compras = spark.table(table("fact_compras")).alias("c")
proveedores = spark.table(table("dim_proveedor")).select("proveedor_id", "lead_time_promedio_dias", "calificacion_servicio").alias("p")
bridge = spark.table(table("bridge_producto_proveedor")).select("producto_id", "proveedor_id", "costo_negociado", "lead_time_dias").alias("b")
logistica = spark.table(table("fact_logistica_entregas")).alias("l")
ventas = spark.table(sales_table("fact_ventas_cabecera")).alias("v")

ventas_logistica = (
    ventas.withColumn("mes_carga", mes_expr("v"))
    .groupBy("mes_carga", "tienda_id", "canal_id")
    .agg(F.sum("valor_total").alias("ventas_totales_asociadas"))
)

inventario_mensual = (
    inventario.withColumn("mes_carga", mes_expr("i"))
    .groupBy("mes_carga", "tienda_id", "producto_id", "categoria_id")
    .agg(
        F.sum("stock_inicial").alias("stock_inicial"),
        F.sum("entradas_compras").alias("entradas_compras"),
        F.sum("salidas_ventas").alias("salidas_ventas"),
        F.sum("ajuste_unidades").alias("ajuste_unidades"),
        F.sum("merma_unidades").alias("merma_unidades"),
        F.sum("stock_final").alias("stock_final"),
        F.sum("valor_inventario_costo").alias("valor_inventario_costo"),
        F.avg("cobertura_dias").alias("cobertura_dias_promedio"),
        F.sum(F.when(F.col("alerta_reorden") == True, F.lit(1)).otherwise(F.lit(0))).alias("productos_bajo_reorden"),
        F.sum(F.when(F.col("alerta_stock_seguridad") == True, F.lit(1)).otherwise(F.lit(0))).alias("productos_bajo_stock_seguridad"),
        F.sum(F.when(F.col("stock_final") <= 0, F.lit(1)).otherwise(F.lit(0))).alias("stockout_count"),
        F.avg("stock_promedio").alias("stock_promedio"),
    )
    .withColumn("rotacion_inventario", safe_divide(F.col("salidas_ventas"), F.col("stock_promedio")))
    .withColumn("merma_pct", safe_divide(F.col("merma_unidades"), F.col("stock_inicial")))
)

compras_proveedores_mensual = (
    compras.withColumn("mes_carga", mes_expr("c"))
    .join(bridge, ["producto_id", "proveedor_id"], "left")
    .join(proveedores, "proveedor_id", "left")
    .groupBy("mes_carga", "tienda_id", "proveedor_id", "producto_id", "categoria_id", "motivo_compra")
    .agg(
        F.countDistinct("orden_compra_id").alias("ordenes_compra"),
        F.sum("cantidad_comprada").alias("cantidad_comprada"),
        F.sum("subtotal_sin_iva").alias("subtotal_compras"),
        F.sum("iva_valor").alias("iva_compras"),
        F.sum("valor_total_compra").alias("compras_totales"),
        F.sum(F.when(F.col("estado_orden") == "Recibida", F.lit(1)).otherwise(F.lit(0))).alias("ordenes_recibidas"),
        F.sum(F.when(F.col("estado_orden").isin("Pendiente", "Parcial"), F.lit(1)).otherwise(F.lit(0))).alias("ordenes_abiertas"),
        F.avg("costo_negociado").alias("costo_negociado_promedio"),
        F.avg(F.coalesce(F.col("lead_time_dias"), F.col("lead_time_promedio_dias"))).alias("lead_time_promedio_proveedor"),
        F.avg("calificacion_servicio").alias("calificacion_servicio_promedio"),
    )
    .withColumn("costo_unitario_promedio_con_iva", safe_divide(F.col("compras_totales"), F.col("cantidad_comprada")))
    .withColumn("costo_sin_iva_promedio", safe_divide(F.col("subtotal_compras"), F.col("cantidad_comprada")))
    .withColumn("ordenes_recibidas_pct", safe_divide(F.col("ordenes_recibidas"), F.col("ordenes_compra")))
    .withColumn("variacion_vs_costo_negociado", F.col("costo_sin_iva_promedio") - F.col("costo_negociado_promedio"))
    .withColumn("variacion_vs_costo_negociado_pct", safe_divide(F.col("variacion_vs_costo_negociado"), F.col("costo_negociado_promedio")))
)

logistica_mensual = (
    logistica.withColumn("mes_carga", mes_expr("l"))
    .groupBy("mes_carga", "tienda_id", "ciudad_origen_id", "ciudad_destino_id", "canal_id", "transportista_id")
    .agg(
        F.countDistinct("entrega_id").alias("entregas"),
        F.sum(F.when(F.col("entrega_a_tiempo") == True, F.lit(1)).otherwise(F.lit(0))).alias("entregas_a_tiempo"),
        F.sum(F.when(F.col("entrega_tardia") == True, F.lit(1)).otherwise(F.lit(0))).alias("entregas_tardias"),
        F.sum(F.when(F.col("entrega_fallida") == True, F.lit(1)).otherwise(F.lit(0))).alias("entregas_fallidas"),
        F.sum(F.when(F.col("entrega_cancelada") == True, F.lit(1)).otherwise(F.lit(0))).alias("entregas_canceladas"),
        F.sum(F.when(F.col("entrega_pendiente") == True, F.lit(1)).otherwise(F.lit(0))).alias("entregas_pendientes"),
        F.avg("dias_prometidos").alias("dias_prometidos_promedio"),
        F.avg("dias_reales_entrega").alias("dias_reales_promedio"),
        F.avg("dias_retraso").alias("dias_retraso_promedio"),
        F.sum("peso_estimado_kg").alias("peso_total_kg"),
        F.sum("costo_envio").alias("costo_envio_total"),
    )
    .join(ventas_logistica, ["mes_carga", "tienda_id", "canal_id"], "left")
    .withColumn("entregas_a_tiempo_pct", safe_divide(F.col("entregas_a_tiempo"), F.col("entregas")))
    .withColumn("entregas_pendientes_pct", safe_divide(F.col("entregas_pendientes"), F.col("entregas")))
    .withColumn("costo_envio_promedio", safe_divide(F.col("costo_envio_total"), F.col("entregas")))
    .withColumn("costo_por_kg", safe_divide(F.col("costo_envio_total"), F.col("peso_total_kg")))
    .withColumn("costo_logistico_sobre_venta_pct", safe_divide(F.col("costo_envio_total"), F.col("ventas_totales_asociadas")))
)

summary = [
    write_gold(inventario_mensual, "mart_inventario_mensual"),
    write_gold(compras_proveedores_mensual, "mart_compras_proveedores_mensual"),
    write_gold(logistica_mensual, "mart_logistica_mensual"),
]

display(spark.createDataFrame(summary))
