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

silver_schema = "comercial_silver"
gold_schema = "comercial_gold"
storage_uri = f"abfss://{storage_container}@{storage_account}.dfs.core.windows.net"
gold_root = f"{storage_uri}/external/{environment}/comercial/gold/{data_year}"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{gold_schema}`")


def table(name):
    return f"`{catalog}`.`{silver_schema}`.`{name}`"


def shared_table(name):
    return f"`{catalog}`.`shared_silver`.`{name}`"


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


ventas = spark.table(table("fact_ventas_cabecera")).alias("v")
detalle = spark.table(table("fact_ventas_detalle")).alias("d")
devoluciones = spark.table(table("fact_devoluciones")).alias("r")
marketing = spark.table(table("fact_marketing")).alias("m")
campanas = spark.table(table("dim_campana_marketing")).select("campana_id", "tipo_campana", "activa").alias("c")

ventas_mensual = (
    ventas.withColumn("mes_gold", mes_expr("v"))
    .groupBy("mes_gold", "tienda_id", "ciudad_id", "canal_id")
    .agg(
        F.sum("valor_bruto").alias("ventas_brutas"),
        F.sum("descuento_total").alias("descuentos"),
        F.sum("iva_total").alias("iva"),
        F.sum("base_neta_sin_iva").alias("ventas_sin_iva"),
        F.sum("valor_total").alias("ventas_totales"),
        F.sum("costo_total").alias("costo_total"),
        F.sum("margen_bruto").alias("margen_bruto"),
        F.countDistinct("venta_id").alias("numero_ventas"),
        F.sum("numero_lineas").alias("numero_lineas"),
        F.countDistinct(F.when(F.col("campana_id").isNotNull(), F.col("venta_id"))).alias("ventas_con_campana"),
    )
    .withColumnRenamed("mes_gold", "mes_carga")
    .withColumn("margen_bruto_pct", safe_divide(F.col("margen_bruto"), F.col("ventas_sin_iva")))
    .withColumn("ticket_promedio", safe_divide(F.col("ventas_totales"), F.col("numero_ventas")))
    .withColumn("ticket_promedio_sin_iva", safe_divide(F.col("ventas_sin_iva"), F.col("numero_ventas")))
    .withColumn("lineas_promedio_por_ticket", safe_divide(F.col("numero_lineas"), F.col("numero_ventas")))
    .withColumn("descuento_pct", safe_divide(F.col("descuentos"), F.col("ventas_brutas")))
    .withColumn("participacion_campana_pct", safe_divide(F.col("ventas_con_campana"), F.col("numero_ventas")))
)

ventas_producto_mensual = (
    detalle.withColumn("mes_gold", mes_expr("d"))
    .groupBy("mes_gold", "tienda_id", "ciudad_id", "canal_id", "categoria_id", "producto_id")
    .agg(
        F.countDistinct("venta_id").alias("numero_ventas"),
        F.countDistinct("detalle_venta_id").alias("lineas_vendidas"),
        F.sum("cantidad").alias("unidades_vendidas"),
        F.sum("base_sin_iva").alias("ventas_linea_sin_iva"),
        F.sum("valor_total_linea").alias("ventas_linea_con_iva"),
        F.sum("costo_total_linea").alias("costo_total_linea"),
        F.sum("margen_bruto_linea").alias("margen_bruto_linea"),
    )
    .withColumnRenamed("mes_gold", "mes_carga")
    .withColumn("precio_promedio_unitario_sin_iva", safe_divide(F.col("ventas_linea_sin_iva"), F.col("unidades_vendidas")))
    .withColumn("precio_promedio_unitario_con_iva", safe_divide(F.col("ventas_linea_con_iva"), F.col("unidades_vendidas")))
    .withColumn("margen_linea_pct", safe_divide(F.col("margen_bruto_linea"), F.col("ventas_linea_sin_iva")))
)

ventas_base = (
    ventas.withColumn("mes_carga", mes_expr("v"))
    .groupBy("mes_carga", "tienda_id", "ciudad_id")
    .agg(F.countDistinct("venta_id").alias("numero_ventas"), F.sum("valor_total").alias("ventas_totales"), F.sum("margen_bruto").alias("margen_bruto"))
)

lineas_base = (
    detalle.withColumn("mes_carga", mes_expr("d"))
    .groupBy("mes_carga", "tienda_id", "ciudad_id", "categoria_id", "producto_id")
    .agg(F.countDistinct("detalle_venta_id").alias("total_lineas_vendidas"))
)

devoluciones_mensual = (
    devoluciones.withColumn("mes_carga", mes_expr("r"))
    .groupBy("mes_carga", "tienda_id", "ciudad_id", "categoria_id", "producto_id", "motivo_devolucion_id")
    .agg(
        F.countDistinct("devolucion_id").alias("devoluciones"),
        F.sum("cantidad_devuelta").alias("unidades_devueltas"),
        F.sum("valor_reintegrado").alias("valor_reintegrado"),
        F.countDistinct("venta_id").alias("ventas_con_devolucion"),
        F.countDistinct("detalle_venta_id").alias("lineas_con_devolucion"),
        F.sum(F.when(F.col("requiere_revision_calidad") == True, F.lit(1)).otherwise(F.lit(0))).alias("devoluciones_revision_calidad"),
        F.avg("dias_hasta_devolucion").alias("dias_promedio_hasta_devolucion"),
    )
    .join(ventas_base, ["mes_carga", "tienda_id", "ciudad_id"], "left")
    .join(lineas_base, ["mes_carga", "tienda_id", "ciudad_id", "categoria_id", "producto_id"], "left")
    .withColumn("tasa_devolucion_ticket", safe_divide(F.col("ventas_con_devolucion"), F.col("numero_ventas")))
    .withColumn("tasa_devolucion_linea", safe_divide(F.col("lineas_con_devolucion"), F.col("total_lineas_vendidas")))
    .withColumn("valor_devuelto_pct", safe_divide(F.col("valor_reintegrado"), F.col("ventas_totales")))
    .withColumn("revision_calidad_pct", safe_divide(F.col("devoluciones_revision_calidad"), F.col("devoluciones")))
    .withColumn("ventas_netas", F.col("ventas_totales") - F.col("valor_reintegrado"))
)

marketing_mensual = (
    marketing.withColumn("mes_carga", mes_expr("m"))
    .join(campanas, "campana_id", "left")
    .groupBy("mes_carga", "campana_id", "ciudad_id", "canal_id", "medio_principal", "tipo_campana")
    .agg(
        F.sum("gasto_marketing").alias("gasto_marketing"),
        F.sum("impresiones").alias("impresiones"),
        F.sum("clics").alias("clics"),
        F.sum("leads").alias("leads"),
        F.sum("conversiones_atribuidas").alias("conversiones_atribuidas"),
        F.sum("ventas_atribuidas_valor").alias("ventas_atribuidas_valor"),
    )
    .withColumn("ctr", safe_divide(F.col("clics"), F.col("impresiones")))
    .withColumn("cvr_lead", safe_divide(F.col("conversiones_atribuidas"), F.col("leads")))
    .withColumn("cpc", safe_divide(F.col("gasto_marketing"), F.col("clics")))
    .withColumn("cpl", safe_divide(F.col("gasto_marketing"), F.col("leads")))
    .withColumn("cpa", safe_divide(F.col("gasto_marketing"), F.col("conversiones_atribuidas")))
    .withColumn("roas", safe_divide(F.col("ventas_atribuidas_valor"), F.col("gasto_marketing")))
)

summary = [
    write_gold(ventas_mensual, "mart_ventas_mensual"),
    write_gold(ventas_producto_mensual, "mart_ventas_producto_mensual"),
    write_gold(devoluciones_mensual, "mart_devoluciones_mensual"),
    write_gold(marketing_mensual, "mart_marketing_mensual"),
]

display(spark.createDataFrame(summary))
