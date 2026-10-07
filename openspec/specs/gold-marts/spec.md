# Marts y métricas Gold

## Purpose

Definir los productos analíticos publicados, sus granularidades mínimas y fórmulas críticas para planificar cambios sin reinterpretar los KPIs.

Contrato del comportamiento implementado, documentado mediante lectura estática de `develop@eb35b87b79eb541c4832fccc8f8825412755f498`. Los escenarios describen resultados esperados del código actual; no constituyen evidencia de ejecución de Spark ni de despliegue en Databricks.

## Sources

- [notebooks/comercial/gold/01_comercial_marts.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/comercial/gold/01_comercial_marts.ipynb)
- [notebooks/operaciones/gold/02_operaciones_marts.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/operaciones/gold/02_operaciones_marts.ipynb)
- [notebooks/finanzas/gold/03_finanzas_objetivos.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/finanzas/gold/03_finanzas_objetivos.ipynb)
- [notebooks/shared/gold/04_kpis_ejecutivos.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/shared/gold/04_kpis_ejecutivos.ipynb)

## Products

| Esquema | Productos |
| --- | --- |
| comercial_gold | mart_ventas_mensual, mart_ventas_producto_mensual, mart_devoluciones_mensual, mart_marketing_mensual |
| operaciones_gold | mart_inventario_mensual, mart_compras_proveedores_mensual, mart_logistica_mensual |
| finanzas_gold | mart_finanzas_mensual, mart_objetivos_mensual |
| shared_gold | mart_kpis_ejecutivos_mensual |

## Contratos de productos

En esta tabla, mes corresponde a mes_carga y las divisiones usan safe_divide. Las granularidades indican las agrupaciones previas al enriquecimiento; los joins no comprueban unicidad de las dimensiones ni imponen PK en las tablas publicadas.

| Producto | Fuentes y agrupación | Medidas y derivaciones |
| --- | --- | --- |
| mart_ventas_mensual | fact_ventas_cabecera comercial; mes, tienda_id, ciudad_id, canal_id. | Sumas de valor_bruto→ventas_brutas, descuento_total→descuentos, iva_total→iva, base_neta_sin_iva→ventas_sin_iva, valor_total→ventas_totales, costo_total, margen_bruto y numero_lineas; countDistinct venta_id→numero_ventas y venta_id con campana_id no nulo→ventas_con_campana. Ratios: margen_bruto/ventas_sin_iva, ventas_totales/numero_ventas, ventas_sin_iva/numero_ventas, numero_lineas/numero_ventas, descuentos/ventas_brutas y ventas_con_campana/numero_ventas. |
| mart_ventas_producto_mensual | fact_ventas_detalle comercial; mes, tienda_id, ciudad_id, canal_id, categoria_id, producto_id. | countDistinct venta_id→numero_ventas y detalle_venta_id→lineas_vendidas; sumas cantidad→unidades_vendidas, base_sin_iva→ventas_linea_sin_iva, valor_total_linea→ventas_linea_con_iva, costo_total_linea y margen_bruto_linea. Precios promedio=ventas_linea_sin_iva o ventas_linea_con_iva/unidades_vendidas; margen_linea_pct=margen_bruto_linea/ventas_linea_sin_iva. |
| mart_devoluciones_mensual | fact_devoluciones comercial; mes, tienda_id, ciudad_id, categoria_id, producto_id, motivo_devolucion_id. Bases auxiliares de cabecera por mes/tienda/ciudad y detalle por mes/tienda/ciudad/categoría/producto. | countDistinct devolucion_id→devoluciones, venta_id→ventas_con_devolucion y detalle_venta_id→lineas_con_devolucion; sumas cantidad_devuelta→unidades_devueltas, valor_reintegrado y filas requiere_revision_calidad=true→devoluciones_revision_calidad; avg dias_hasta_devolucion. Tasas: ventas_con_devolucion/numero_ventas, lineas_con_devolucion/total_lineas_vendidas, valor_reintegrado/ventas_totales, devoluciones_revision_calidad/devoluciones; ventas_netas=ventas_totales-valor_reintegrado. |
| mart_marketing_mensual | fact_marketing y dim_campana_marketing comercial; mes, campana_id, campana_nombre, tipo_campana, categorias_objetivo, canales_objetivo, ciudad_id, canal_id, medio_principal. | Sumas gasto_marketing, impresiones, clics, leads, conversiones_atribuidas, ventas_atribuidas_valor; ctr=clics/impresiones; cvr_lead=conversiones_atribuidas/leads; cpc=gasto_marketing/clics; cpl=gasto_marketing/leads; cpa=gasto_marketing/conversiones_atribuidas; roas=ventas_atribuidas_valor/gasto_marketing. |
| mart_inventario_mensual | fact_inventario_mensual operaciones; mes, tienda_id, producto_id, categoria_id. | Sumas stock_inicial, entradas_compras, salidas_ventas, ajuste_unidades, merma_unidades, stock_final y valor_inventario_costo; avg cobertura_dias→cobertura_dias_promedio y stock_promedio; conteos por condición alerta_reorden, alerta_stock_seguridad y stock_final<=0; rotacion_inventario=salidas_ventas/stock_promedio; merma_pct=merma_unidades/stock_inicial. |
| mart_compras_proveedores_mensual | fact_compras con bridge_producto_proveedor y dim_proveedor de operaciones; mes, tienda_id, proveedor_id, proveedor_nombre, tipo_proveedor, especialidad, estado_proveedor, producto_id, categoria_id, motivo_compra. | countDistinct orden_compra_id; sumas cantidad_comprada, subtotal_sin_iva→subtotal_compras, iva_valor→iva_compras, valor_total_compra→compras_totales; conteos por estado Recibida o Pendiente/Parcial; avg costo_negociado, coalesce(lead_time_dias,lead_time_promedio_dias) y calificacion_servicio. Costos promedio=compras_totales o subtotal_compras/cantidad_comprada; ordenes_recibidas_pct=ordenes_recibidas/ordenes_compra; variacion_vs_costo_negociado=costo_sin_iva_promedio-costo_negociado_promedio y su ratio sobre costo_negociado_promedio. |
| mart_logistica_mensual | fact_logistica_entregas operaciones; mes, tienda_id, ciudad_origen_id, ciudad_destino_id, canal_id, transportista_id; ventas comercial agregadas por mes/tienda/canal. | countDistinct entrega_id; conteos de flags a tiempo, tardía, fallida, cancelada, pendiente; avg dias_prometidos, dias_reales_entrega y dias_retraso; sumas peso_estimado_kg y costo_envio. Ratios entregas_a_tiempo/entregas, entregas_pendientes/entregas, costo_envio_total/entregas, costo_envio_total/peso_total_kg y costo_envio_total/ventas_totales_asociadas. |
| mart_finanzas_mensual | fact_presupuesto_mensual y fact_costos_mensual finanzas agrupados por mes/tienda mediante full join, seguidos de ventas comercial mediante left join. | Sumas monto_presupuesto→presupuesto, monto_ejecutado→ejecutado, monto_presupuestado→costos_presupuestados, monto_real→costos_reales, más ventas_totales, ventas_sin_iva, margen_bruto y numero_ventas. variacion_presupuesto=ejecutado-presupuesto; variacion_costos=costos_reales-costos_presupuestados; margen_despues_costos=margen_bruto-costos_reales; ratios sobre presupuesto, costos_presupuestados, ventas_totales o ventas_sin_iva según columna. |
| mart_objetivos_mensual | fact_objetivos_mensuales finanzas por mes/tienda como base; ventas y devoluciones comercial y logística operaciones por mes/tienda mediante left joins. | Sumas meta_ventas, meta_tickets, meta_margen_bruto, meta_entregas; avg meta_tasa_devolucion. Cumplimiento ventas, tickets y margen=real/meta; brechas=real-meta; cumple_meta correspondiente cuando ratio>=1; tasa_devolucion_ticket=devoluciones/numero_ventas; tasa_devolucion_vs_meta=tasa_devolucion_ticket/meta_tasa_devolucion; entregas_vs_meta=entregas/meta_entregas. |
| mart_kpis_ejecutivos_mensual | Marts comercial, operaciones y finanzas agregados por mes; ventas como base y los demás con left join. | Sumas ventas_totales, ventas_sin_iva, margen_bruto, numero_ventas, unidades_vendidas, devoluciones, valor_reintegrado, productos_bajo_reorden, entregas, entregas_a_tiempo, costo_envio_total, gasto_marketing, ventas_atribuidas_valor, presupuesto, ejecutado, costos_reales, meta_ventas y ventas de objetivos→ventas_objetivo_totales; avg cobertura_dias_promedio. ventas_netas=ventas_totales-coalesce(valor_reintegrado,0). Ratios ejecutivos definidos en el requisito siguiente. |

## Requirements

### Requirement: Productos por dominio

Gold SHALL generar los marts de la sección Products, utilizando fuentes Silver y dimensiones compartidas según cada notebook. Las columnas descriptivas SHALL proceder de los joins existentes; no SHALL asumirse que cada join es uno a uno sin validar claves de las fuentes.

#### Scenario: Marts comerciales
- **WHEN** se ejecuta el notebook comercial con fuentes disponibles
- **THEN** se preparan los cuatro productos comerciales de la tabla

### Requirement: Granularidades mensuales

El mart de ventas SHALL agrupar por mes, tienda, ciudad y canal; ventas por producto SHALL añadir categoría y producto. Inventario SHALL agrupar por mes, tienda, producto y categoría. Finanzas y objetivos SHALL agrupar sus bases por mes y tienda; los KPIs ejecutivos SHALL agrupar por mes. mes_expr SHALL priorizar mes_carga y usar año/mes técnico como fallback.

#### Scenario: Ventas en dos canales
- **WHEN** una tienda tiene ventas del mismo mes en dos canales
- **THEN** el mart de ventas conserva grupos separados por canal

### Requirement: Fórmulas y ratios agregados

Los ratios SHALL calcularse a partir de los agregados indicados y usar safe_divide, que devuelve NULL ante denominador NULL o cero. Ticket promedio SHALL ser ventas_totales/numero_ventas; margen bruto porcentual SHALL ser margen_bruto/ventas_sin_iva; ROAS SHALL ser ventas_atribuidas_valor/gasto_marketing. Los campos _pct SHALL conservar el cociente sin multiplicarlo automáticamente por 100.

#### Scenario: Ticket promedio
- **WHEN** ventas_totales es 1000 y numero_ventas es 4
- **THEN** ticket_promedio es 250

#### Scenario: Margen porcentual
- **WHEN** margen_bruto es 20 y ventas_sin_iva es 100
- **THEN** margen_bruto_pct es 0.2

### Requirement: Finanzas, objetivos y KPIs

Finanzas SHALL calcular variacion_presupuesto=ejecutado-presupuesto y margen_despues_costos=margen_bruto-costos_reales. Objetivos SHALL calcular cumplimiento_ventas_pct=ventas_totales/meta_ventas y cumple_meta_ventas cuando el cociente es al menos 1. Los KPIs ejecutivos SHALL calcular ventas_netas=ventas_totales-coalesce(valor_reintegrado,0), partiendo de meses de ventas y añadiendo los demás agregados con joins left.

#### Scenario: Meta cumplida
- **WHEN** ventas_totales es 120 y meta_ventas es 100
- **THEN** cumplimiento_ventas_pct es 1.2 y cumple_meta_ventas es true

#### Scenario: Reintegro ausente en KPI ejecutivo
- **WHEN** ventas_totales es 100 y valor_reintegrado es NULL
- **THEN** ventas_netas es 100

### Requirement: Staging antes de publicación

write_gold SHALL escribir <mart>__staging bajo _staging/<mart>, añadir metadatos Gold y contar filas antes de publicar. SHALL rechazar staging vacío; con filas SHALL sobrescribir la tabla final externa con overwriteSchema=true. Este procedimiento no SHALL presentarse como una transacción atómica de todos los marts.

#### Scenario: Staging vacío
- **WHEN** el staging de un mart tiene cero filas
- **THEN** se genera ValueError antes de sobrescribir su tabla final

### Requirement: Fuentes completas y ausencia de filtros de estado

Gold SHALL leer las tablas completas indicadas en Contratos de productos, sin filtro general por año, mes o estado de venta, devolución, compra o entrega. data_year SHALL parametrizar la ruta física, sin seleccionar el año de las filas. Las lecturas SHALL fallar si una tabla requerida no existe, sin sustituirla por una tabla vacía. mes_expr SHALL usar coalesce(mes_carga,concat_ws('-',_np_source_year,_np_source_month)) y no SHALL crear por sí solo un calendario completo.

#### Scenario: Ventas en dos años
- **WHEN** la tabla Silver contiene dos años y Gold recibe data_year=2026
- **THEN** la agregación incluye las filas disponibles de ambos años y publica bajo la raíz física 2026

#### Scenario: Devolución en revisión
- **WHEN** una devolución En revision está presente en Silver
- **THEN** Gold no la excluye mediante un filtro de estado

### Requirement: Enriquecimiento y cardinalidad de joins

Los marts SHALL añadir descripciones mediante left joins con dimensiones: tiendas y ciudades compartidas; canales para ventas, marketing y logística; productos y categorías para ventas por producto, devoluciones, inventario y compras; motivos compartidos para devoluciones; campañas comerciales para marketing; proveedores, bridge y transportistas de operaciones para compras/logística. Las ciudades de tienda SHALL conservar atributos tienda_ciudad_nombre, tienda_departamento y tienda_region; los atributos de ciudad directa u origen/destino SHALL ser columnas diferenciadas. Los joins no SHALL deduplicar las dimensiones ni validar relaciones uno a uno antes de ejecutarse.

#### Scenario: Dimensión no coincidente
- **WHEN** un grupo agregado tiene producto_id sin correspondencia
- **THEN** el left join conserva el grupo con descripciones de producto NULL

#### Scenario: Campaña duplicada
- **WHEN** dim_campana_marketing contiene varias filas coincidentes para una campaña
- **THEN** el join previo a la agregación puede multiplicar filas y medidas; no hay deduplicación automática de esa dimensión

### Requirement: Agregados y unidades de métricas

Cada producto SHALL implementar las agrupaciones, sumas, conteos distintos, promedios y ratios de Contratos de productos. Los precios, costos y tasas agregadas SHALL dividir sus agregados, sin promediar ratios de fila salvo los promedios explícitos. La cobertura ejecutiva SHALL usar avg de cobertura_dias_promedio de los grupos de inventario, sin ponderación. El código no SHALL atribuirse conversión de moneda ni multiplicación por 100 para porcentajes.

#### Scenario: Precio unitario agregado
- **WHEN** dos filas tienen cantidades 1 y 3 y valores sin IVA 10 y 90 en el mismo grupo
- **THEN** el precio promedio unitario sin IVA es 100/4=25

#### Scenario: Cobertura ejecutiva
- **WHEN** dos grupos de inventario tienen cobertura_dias_promedio 10 y 30
- **THEN** la cobertura mensual ejecutiva es 20 mediante promedio simple

### Requirement: Denominadores reutilizados entre grupos de devoluciones y logística

El mart de devoluciones SHALL unir ventas_base por mes/tienda/ciudad y lineas_base por mes/tienda/ciudad/categoría/producto. El mart de logística SHALL unir ventas_logistica por mes/tienda/canal. Estos denominadores SHALL repetirse cuando existen varios grupos de detalle dentro de la misma clave de unión; no SHALL describirse como ventas distribuidas proporcionalmente entre motivos, productos, rutas o transportistas.

#### Scenario: Dos motivos de devolución
- **WHEN** dos grupos comparten mes, tienda y ciudad pero tienen motivos distintos
- **THEN** ambos reciben el mismo agregado de ventas_base para calcular sus ratios

#### Scenario: Dos transportistas
- **WHEN** dos grupos logísticos comparten mes, tienda y canal
- **THEN** ambos reciben ventas_totales_asociadas de esa misma clave

### Requirement: Finanzas y objetivos sin relleno general de faltantes

Finanzas SHALL usar full join entre presupuesto y costos y después left join a ventas. Objetivos SHALL partir de objetivos_base y añadir ventas, devoluciones y entregas mediante left joins. Las brechas, ratios y flags SHALL conservar NULL cuando sus operandos o denominadores no permiten cálculo; no SHALL sustituirse todos los reales faltantes por cero.

#### Scenario: Costo sin presupuesto
- **WHEN** hay un mes/tienda en costos_base sin correspondencia en presupuesto_base
- **THEN** el full join conserva la clave con presupuesto y ejecutado NULL

#### Scenario: Meta sin ventas
- **WHEN** hay una meta de ventas sin fila comercial correspondiente
- **THEN** el grupo de objetivos permanece con ventas_totales y cumplimiento_ventas_pct NULL

### Requirement: Ratios ejecutivos completos y meses base

Los KPIs SHALL calcular margen_bruto_pct=margen_bruto/ventas_sin_iva; ticket_promedio=ventas_totales/numero_ventas; tasa_devolucion=devoluciones/numero_ventas; valor_reintegrado_pct=valor_reintegrado/ventas_totales; entregas_a_tiempo_pct=entregas_a_tiempo/entregas; costo_logistico_sobre_venta_pct=costo_envio_total/ventas_totales; marketing_roas=ventas_atribuidas_valor/gasto_marketing; ejecucion_presupuesto_pct=ejecutado/presupuesto; costos_sobre_ventas_pct=costos_reales/ventas_totales; cumplimiento_ventas_pct=ventas_objetivo_totales/meta_ventas. Solo ventas_netas SHALL rellenar el reintegro ausente con cero. Los meses presentes solo en marts auxiliares no SHALL añadirse a la base de ventas mediante los left joins.

#### Scenario: Mes solo financiero
- **WHEN** un mes existe en finanzas pero no en ventas_mes
- **THEN** ese mes no aparece en el KPI ejecutivo

#### Scenario: Devoluciones ausentes
- **WHEN** un mes de ventas no tiene fila de devoluciones
- **THEN** ventas_netas conserva ventas_totales, mientras tasa_devolucion y valor_reintegrado_pct quedan NULL

### Requirement: Publicación secuencial y retención de staging

Cada notebook SHALL publicar sus marts en el orden de sus llamadas write_gold: ventas, ventas por producto, devoluciones y marketing; inventario, compras y logística; finanzas y objetivos; después el Job ejecuta KPIs y calidad. Cada mart SHALL conservar staging y salida final externa con _np_gold_layer y _np_gold_processed_ts. No SHALL borrar el staging al terminar, ni restaurar automáticamente los marts ya publicados cuando falla una llamada posterior.

#### Scenario: Segundo mart fallido
- **WHEN** el primer mart se publica y el segundo genera una excepción
- **THEN** el primero permanece publicado y las llamadas siguientes del notebook no se ejecutan

#### Scenario: Publicación satisfactoria
- **WHEN** write_gold termina con filas en staging
- **THEN** quedan registradas la tabla staging y la final; el código no ejecuta limpieza de staging
