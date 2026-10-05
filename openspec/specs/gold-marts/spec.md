# Marts y métricas Gold

## Purpose

Definir los productos analíticos publicados, sus granularidades mínimas y fórmulas críticas para planificar cambios sin reinterpretar los KPIs.

Base documental sugerida, derivada por lectura de código en `develop@9c48831022a329902f765058de37e6d0a1528eb7`. Requiere revisión humana antes de adoptarse; no acredita ejecución de Spark ni despliegue Databricks.

## Sources

- [notebooks/comercial/gold/01_comercial_marts.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/notebooks/comercial/gold/01_comercial_marts.ipynb)
- [notebooks/operaciones/gold/02_operaciones_marts.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/notebooks/operaciones/gold/02_operaciones_marts.ipynb)
- [notebooks/finanzas/gold/03_finanzas_objetivos.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/notebooks/finanzas/gold/03_finanzas_objetivos.ipynb)
- [notebooks/shared/gold/04_kpis_ejecutivos.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/notebooks/shared/gold/04_kpis_ejecutivos.ipynb)

## Products

| Esquema | Productos |
| --- | --- |
| comercial_gold | mart_ventas_mensual, mart_ventas_producto_mensual, mart_devoluciones_mensual, mart_marketing_mensual |
| operaciones_gold | mart_inventario_mensual, mart_compras_proveedores_mensual, mart_logistica_mensual |
| finanzas_gold | mart_finanzas_mensual, mart_objetivos_mensual |
| shared_gold | mart_kpis_ejecutivos_mensual |

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
