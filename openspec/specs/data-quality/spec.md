# Calidad de datos Silver y Gold

## Purpose

Precisar los controles realmente definidos, sus tolerancias y el alcance del resultado de calidad frente al estado de ejecución del job.

Contrato del comportamiento implementado, documentado mediante lectura estática de `develop@eb35b87b79eb541c4832fccc8f8825412755f498`. Los escenarios describen resultados esperados del código actual; no constituyen evidencia de ejecución de Spark ni de despliegue en Databricks.

## Sources

- [notebooks/shared/silver/05_quality_checks.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/shared/silver/05_quality_checks.ipynb)
- [notebooks/gobierno/gold/05_quality_checks.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/gobierno/gold/05_quality_checks.ipynb)

## Relaciones FK declaradas

| Origen | Columna | Referencia | Columna |
| --- | --- | --- | --- |
| dim_tienda | ciudad_id | dim_ciudad | ciudad_id |
| dim_cliente | ciudad_id | dim_ciudad | ciudad_id |
| dim_empleado | tienda_id | dim_tienda | tienda_id |
| dim_empleado | area_id | dim_area_negocio | area_id |
| dim_producto | categoria_id | dim_categoria_producto | categoria_id |
| dim_proveedor | ciudad_id | dim_ciudad | ciudad_id |
| bridge_producto_proveedor | producto_id | dim_producto | producto_id |
| bridge_producto_proveedor | proveedor_id | dim_proveedor | proveedor_id |
| fact_ventas_cabecera | fecha_id | dim_fecha | fecha_id |
| fact_ventas_cabecera | tienda_id | dim_tienda | tienda_id |
| fact_ventas_cabecera | cliente_id | dim_cliente | cliente_id |
| fact_ventas_cabecera | canal_id | dim_canal_venta | canal_id |
| fact_ventas_detalle | venta_id | fact_ventas_cabecera | venta_id |
| fact_ventas_detalle | producto_id | dim_producto | producto_id |
| fact_devoluciones | detalle_venta_id | fact_ventas_detalle | detalle_venta_id |
| fact_logistica_entregas | venta_id | fact_ventas_cabecera | venta_id |
| fact_compras | producto_id | dim_producto | producto_id |
| fact_compras | proveedor_id | dim_proveedor | proveedor_id |
| fact_inventario_mensual | producto_id | dim_producto | producto_id |

## Ecuaciones aritméticas

| Tabla | Comparación |
| --- | --- |
| fact_ventas_cabecera | abs(double(valor_bruto-descuento_total+iva_total-valor_total))>0.02; abs(double(valor_bruto-descuento_total-costo_total-margen_bruto))>0.02. |
| fact_ventas_detalle | abs(double(base_sin_iva+iva_valor-valor_total_linea))>0.02; abs(double(base_sin_iva-costo_total_linea-margen_bruto_linea))>0.02. |
| fact_compras | abs(double(subtotal_sin_iva+iva_valor-valor_total_compra))>0.02. |
| fact_inventario_mensual | stock_inicial+entradas_compras-salidas_ventas+ajuste_unidades-merma_unidades<>stock_final, sin tolerancia monetaria. |

## Requirements

### Requirement: Controles Silver por tabla y relación

Los controles Silver SHALL evaluar PK duplicadas y nulas para claves configuradas disponibles, tablas vacías y las FK declaradas cuando ambas tablas/columnas existan. SHALL resolver primero la tabla del dominio y después shared_silver. Las FK SHALL contar valores distintos no nulos sin correspondencia; no SHALL contar nulos como errores FK. SHALL excluir silver_quality_checks y silver_processing_audit del inventario de tablas de negocio.

#### Scenario: FK huérfana
- **WHEN** un valor FK no nulo y distinto no tiene correspondencia en la referencia disponible
- **THEN** aumenta failing_count del control de esa relación

#### Scenario: Referencia ausente
- **WHEN** falta una tabla o columna necesaria para una FK declarada
- **THEN** ese control se omite; su omisión no demuestra integridad referencial

### Requirement: Consistencia aritmética Silver

Los controles SHALL registrar fallos cuando la desviación absoluta monetaria es mayor que 0.02 para las ecuaciones de ventas, detalle y compras definidas en el notebook. Para inventario SHALL contrastar stock_inicial+entradas_compras-salidas_ventas+ajuste_unidades-merma_unidades con stock_final. No SHALL interpretarse una comparación con NULL como validación explícita de completitud.

#### Scenario: Total de compra inconsistente
- **WHEN** subtotal_sin_iva+iva_valor difiere de valor_total_compra en 0.03
- **THEN** la fila aumenta el conteo del control aritmético

#### Scenario: Sin tablas Silver
- **WHEN** no hay tablas de negocio en el dominio
- **THEN** se genera el control informativo no_silver_tables con failing_count=0

### Requirement: Persistencia de resultados Silver

El resultado SHALL persistir en silver_quality_checks con environment, dominio, tabla, control, severidad, conteo, estado e instante de revisión. SHALL usar PASS para conteo cero y FAIL para conteo mayor que cero. Un resultado FAIL no SHALL describirse como excepción automática: el notebook actual escribe y muestra resultados sin lanzar error por ese estado.

#### Scenario: Control fallido registrado
- **WHEN** un control de PK registra duplicados
- **THEN** se publica FAIL en el reporte; ese estado por sí solo no hace fallar la tarea

### Requirement: Conciliación Gold con Silver

Gold SHALL comparar KPIs mensuales con ventas y devoluciones Silver: conteos por igualdad y ventas_totales, margen_bruto y valor_reintegrado con tolerancia absoluta de 0.05. SHALL exponer los valores del resumen_mensual_validacion de gobierno como columnas de control; esos valores no SHALL presentarse como condiciones adicionales del PASS actual.

#### Scenario: Conciliación satisfactoria
- **WHEN** todos los conteos coinciden y todas las diferencias monetarias son como máximo 0.05
- **THEN** gold_quality_status es PASS

#### Scenario: Comparación fallida o ausente
- **WHEN** alguna comparación es falsa o no permite confirmar la conjunción por valores NULL
- **THEN** gold_quality_status es FAIL y se prepara su reporte gold_quality_checks sin excepción automática por ese estado


### Requirement: Conteos de PK y tablas vacías

primary_key_unique SHALL contar grupos de claves con count>1, no el número total de filas duplicadas ni el exceso de filas por grupo. primary_key_not_null SHALL contar filas con algún componente disponible de PK NULL. table_not_empty SHALL producir failing_count=1 para tabla vacía y 0 para no vacía. Los tres controles SHALL usar severidad ERROR. El mapa PK de calidad SHALL conservar el inventario de negocio descrito en data-contracts y usar únicamente componentes presentes.

#### Scenario: Tres filas con una misma PK
- **WHEN** un único grupo de PK contiene tres filas
- **THEN** primary_key_unique registra failing_count=1

#### Scenario: Tabla vacía
- **WHEN** una tabla enumerada no contiene filas
- **THEN** table_not_empty registra FAIL con failing_count=1

### Requirement: Cobertura FK y omisiones

Las FK SHALL limitarse a las relaciones de la tabla Relaciones FK declaradas. Tanto origen como referencia SHALL resolverse primero en el schema del dominio y después en shared_silver. Se SHALL contar valores FK distintos no nulos mediante left_anti contra claves destino distintas. Una relación sin tabla o columna SHALL omitirse sin generar un control SKIPPED; la presencia de PASS en otros controles no SHALL interpretarse como cobertura de esa relación.

#### Scenario: FK repetida sin referencia
- **WHEN** diez filas tienen el mismo valor FK huérfano
- **THEN** el control FK registra failing_count=1

#### Scenario: Origen disponible solo en shared
- **WHEN** la tabla origen no existe en el dominio pero sí en shared_silver
- **THEN** resolve_table usa la tabla shared para ese control

### Requirement: Identificación y límites aritméticos

Los controles de Ecuaciones aritméticas SHALL usar check_name=arithmetic_consistency y severidad ERROR. Las dos ecuaciones de cabecera y las dos de detalle SHALL compartir el mismo nombre, diferenciadas por description. Los controles SHALL ejecutarse si existe la tabla local, sin comprobación previa de todas sus columnas. Un predicado NULL no SHALL contar como fallo y una columna faltante puede causar error Spark en lugar de un reporte de control.

#### Scenario: Tolerancia exacta
- **WHEN** una desviación monetaria absoluta es exactamente 0.02
- **THEN** el predicado >0.02 no cuenta esa fila como fallo

#### Scenario: Operando nulo
- **WHEN** la comparación aritmética devuelve NULL
- **THEN** el filtro no incluye esa fila en failing_count

#### Scenario: Columna aritmética ausente
- **WHEN** fact_compras existe pero no contiene iva_valor
- **THEN** la expresión puede fallar durante su evaluación; no se convierte en un registro SKIPPED

### Requirement: Reporte de calidad completo y reemplazo

Silver SHALL escribir el reporte completo del dominio mediante overwrite y overwriteSchema=true en <silver_root>/_control/silver_quality_checks, con environment, domain_name, table_name, check_name, severity, failing_count, status, description y checked_at. No SHALL conservar allí un histórico append de cada revisión. Los flags de domain_normalization no SHALL producir por sí solos controles en este reporte; el notebook actual no los consulta.

#### Scenario: Segunda revisión
- **WHEN** quality_checks se ejecuta otra vez
- **THEN** reemplaza el reporte publicado con los controles de la ejecución actual

#### Scenario: Flag de dominio falso
- **WHEN** estado_stock_codigo_valido es false
- **THEN** ese flag no añade un control específico a silver_quality_checks en el código actual

### Requirement: Conciliación Gold y ausencia de datos

Gold SHALL agregar Silver por mes, partir de los meses de los KPIs Gold y unir ventas, devoluciones y controles mediante left joins. SHALL exigir las tablas leídas, incluida gobierno_silver.resumen_mensual_validacion, sin fallback por ausencia. PASS SHALL requerir las cinco comparaciones Gold/Silver: ventas y margen con tolerancia <=0.05, tickets y devoluciones por igualdad, reintegro con tolerancia <=0.05. Los valores de control externos SHALL ser columnas informativas y no intervenir en esa conjunción.

#### Scenario: Diferencia en resumen externo
- **WHEN** las cinco comparaciones Gold/Silver son true pero control_ventas_totales difiere
- **THEN** gold_quality_status es PASS

#### Scenario: Mes sin devoluciones
- **WHEN** faltan los agregados de devoluciones para un mes Gold
- **THEN** los operandos NULL no satisfacen la conjunción y gold_quality_status es FAIL

#### Scenario: Tabla de control ausente
- **WHEN** no existe gobierno_silver.resumen_mensual_validacion
- **THEN** la lectura falla; no se omite automáticamente esa fuente

### Requirement: Publicación del reporte Gold y significado operacional

Gold SHALL publicar gold_quality_checks en gobierno_gold mediante el mismo staging no vacío y overwrite usado para marts. El reporte SHALL conservar comparaciones y valores conciliados. Los notebooks de calidad no SHALL lanzar una excepción solo por una fila FAIL ni configurar alertas o notificaciones a partir de ese resultado. Un error Spark o un staging vacío sí SHALL interrumpir la ejecución por su excepción.

#### Scenario: Reporte no vacío con fallos
- **WHEN** checks contiene filas con gold_quality_status=FAIL
- **THEN** write_gold puede publicar el reporte y terminar normalmente

#### Scenario: Reporte vacío
- **WHEN** la base de KPIs produce cero filas de checks
- **THEN** la comprobación del staging genera ValueError antes de publicar la tabla final
