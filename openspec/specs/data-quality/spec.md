# Calidad de datos Silver y Gold

## Purpose

Precisar los controles realmente definidos, sus tolerancias y el alcance del resultado de calidad frente al estado de ejecución del job.

Base documental sugerida, derivada por lectura de código en `develop@9c48831022a329902f765058de37e6d0a1528eb7`. Requiere revisión humana antes de adoptarse; no acredita ejecución de Spark ni despliegue Databricks.

## Sources

- [notebooks/shared/silver/05_quality_checks.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/notebooks/shared/silver/05_quality_checks.ipynb)
- [notebooks/gobierno/gold/05_quality_checks.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/notebooks/gobierno/gold/05_quality_checks.ipynb)

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

