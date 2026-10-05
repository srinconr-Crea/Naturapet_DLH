# Procesamiento incremental Silver

## Purpose

Definir selección incremental, secuencia de transformación, política observable de nulos, derivaciones y persistencia Silver.

Base documental sugerida, derivada por lectura de código en `develop@9c48831022a329902f765058de37e6d0a1528eb7`. Requiere revisión humana antes de adoptarse; no acredita ejecución de Spark ni despliegue Databricks.

## Sources

- [src/common/silver_incremental.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/src/common/silver_incremental.py)
- [notebooks/shared/silver/01_schema_standardization.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/notebooks/shared/silver/01_schema_standardization.ipynb)
- [notebooks/shared/silver/02_null_corrections.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/notebooks/shared/silver/02_null_corrections.ipynb)
- [notebooks/shared/silver/03_domain_normalization.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/notebooks/shared/silver/03_domain_normalization.ipynb)
- [notebooks/operaciones/silver/04_business_derivations.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/notebooks/operaciones/silver/04_business_derivations.ipynb)
- [resources/jobs/monthly_silver_refresh.job.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/resources/jobs/monthly_silver_refresh.job.yml)

## Requirements

### Requirement: Selección incremental y pasos pendientes

La estandarización SHALL recuperar el mayor new_watermark de auditorías SUCCESS para el paso y tabla. Con watermark y _np_ingestion_ts SHALL seleccionar únicamente timestamps estrictamente mayores; sin alguno de ellos SHALL considerar todas las filas. Los pasos posteriores SHALL seleccionar _np_silver_step igual al paso previo cuando exista esa columna.

#### Scenario: Watermark disponible
- **WHEN** el último watermark exitoso es T y Bronze contiene filas en T y después de T
- **THEN** filter_new_bronze_rows solo selecciona las posteriores a T

#### Scenario: Entrada sin columna de control
- **WHEN** la entrada no tiene _np_silver_step
- **THEN** filter_pending_step_rows devuelve la entrada completa

### Requirement: Secuencia y controles de transformación

El flujo SHALL ejecutar schema_standardization, null_corrections, domain_normalization y business_derivations en ese orden antes de quality_checks. La estandarización SHALL recortar cadenas y convertir vacíos a NULL, aplicar tipos definidos por columna y deduplicar por PK disponible. La normalización de dominios SHALL añadir columnas de código y flags de valores admitidos según sus mapas, sin imponer por sí sola rechazo de filas.

#### Scenario: Cadena vacía
- **WHEN** una columna string contiene solo espacios
- **THEN** clean_string_columns la transforma en NULL

#### Scenario: Empleado corporativo
- **WHEN** dim_empleado tiene tienda_id NULL
- **THEN** null_corrections añade es_empleado_corporativo=true y tienda_id_modelo=NO_APLICA conservando la columna original

### Requirement: División segura y costos de compra

safe_divide SHALL devolver NULL para denominador NULL o cero, y el cociente para otros denominadores. Para fact_compras, business_derivations SHALL calcular costo_compra_promedio_sin_iva como subtotal_sin_iva/cantidad_comprada y costo_compra_promedio_con_iva como valor_total_compra/cantidad_comprada mediante esa función. Esta función no SHALL introducir por sí sola rechazo de cantidades negativas.

#### Scenario: Cantidad cero
- **WHEN** cantidad_comprada es 0
- **THEN** los dos costos promedio son NULL

#### Scenario: Cantidad positiva
- **WHEN** subtotal_sin_iva es 100 y cantidad_comprada es 4
- **THEN** costo_compra_promedio_sin_iva es 25

#### Scenario: Denominador negativo
- **WHEN** safe_divide recibe 100 y -4
- **THEN** devuelve -25; rechazar el dato requiere una regla adicional explícita

### Requirement: Escritura y auditoría Silver

Silver SHALL resolver claves con el mapa PRIMARY_KEYS, después _np_record_hash y después metadatos de fuente disponibles; SHALL rechazar la escritura si no hay claves. La tabla nueva SHALL escribirse como Delta externa y la existente SHALL alinearse a su esquema, añadir columnas faltantes y hacer MERGE. Los pasos incrementales SHALL conservar auditoría por tabla con conteos, paso y watermark; sin filas pendientes SHALL registrar NO_DATA.

#### Scenario: Sin claves disponibles
- **WHEN** una tabla no tiene PK configurada, hash ni metadatos de fuente
- **THEN** resolve_merge_keys genera ValueError

#### Scenario: Tabla existente con columna nueva
- **WHEN** la entrada agrega una columna al esquema destino
- **THEN** add_missing_target_columns la incorpora antes del MERGE

