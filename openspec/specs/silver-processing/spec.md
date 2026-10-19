# Procesamiento incremental Silver

## Purpose

Definir selección incremental, secuencia de transformación, política observable de nulos, derivaciones y persistencia Silver.

Contrato del comportamiento implementado, documentado mediante lectura estática de `develop@eb35b87b79eb541c4832fccc8f8825412755f498`. Los escenarios describen resultados esperados del código actual; no constituyen evidencia de ejecución de Spark ni de despliegue en Databricks.

## Sources

- [src/common/silver_incremental.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/src/common/silver_incremental.py)
- [notebooks/shared/silver/01_schema_standardization.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/shared/silver/01_schema_standardization.ipynb)
- [notebooks/shared/silver/02_null_corrections.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/shared/silver/02_null_corrections.ipynb)
- [notebooks/shared/silver/03_domain_normalization.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/shared/silver/03_domain_normalization.ipynb)
- [notebooks/operaciones/silver/04_business_derivations.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/operaciones/silver/04_business_derivations.ipynb)
- [resources/jobs/monthly_silver_refresh.job.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/resources/jobs/monthly_silver_refresh.job.yml)

- [notebooks/shared/silver/04_business_derivations.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/shared/silver/04_business_derivations.ipynb)

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


### Requirement: Inventario de entrada y marcas de paso

La estandarización SHALL enumerar tablas no temporales del schema Bronze excluyendo bronze_file_load_audit. Los pasos posteriores SHALL enumerar tablas Silver no temporales excluyendo silver_processing_audit y silver_quality_checks. Cada escritura de transformación SHALL actualizar _np_silver_step al paso actual y _np_silver_processed_ts al instante de ejecución. quality_checks SHALL leer las tablas completas, sin filtrar por watermark o marca de paso.

#### Scenario: Fila ya derivada
- **WHEN** una fila tiene _np_silver_step=business_derivations y se vuelve a ejecutar null_corrections
- **THEN** la fila no es pendiente de schema_standardization y queda fuera de ese paso

#### Scenario: Control de calidad posterior
- **WHEN** se ejecuta quality_checks con filas de distintos momentos de carga
- **THEN** valida el inventario completo disponible, sin limitarse al delta recién procesado

### Requirement: Conversión y mes de carga

cast_columns SHALL aplicar los grupos de tipos y claves documentados en data-contracts. Los booleanos SHALL reconocer true,t,1,yes,y,si,s,sí como true y false,f,0,no,n como false tras trim y lower; otras representaciones SHALL convertirse a NULL. mes_carga SHALL extraer únicamente un prefijo de cuatro dígitos, guion y dos dígitos, sin validar aquí el rango del mes ni el resto del texto. Las conversiones numéricas y de fecha SHALL usar casts/to_date de Spark, sin capturar por fila errores de conversión ni establecer ANSI mode.

#### Scenario: Booleano desconocido
- **WHEN** consentimiento_marketing contiene quizá
- **THEN** parse_boolean devuelve NULL

#### Scenario: Mes con sufijo
- **WHEN** mes_carga contiene 2026-01-15
- **THEN** cast_columns conserva 2026-01

#### Scenario: Prefijo de mes fuera de rango
- **WHEN** mes_carga contiene 2026-99
- **THEN** la extracción de texto conserva 2026-99; este paso no valida el calendario

### Requirement: Políticas de nulos por entidad

null_corrections SHALL recortar cadenas y convertir vacíos a NULL. En dim_fecha SHALL conservar festivo_nombre únicamente cuando es_festivo_colombia=true. En dim_empleado SHALL mantener tienda_id y añadir sus indicadores corporativos. En fact_logistica_entregas SHALL añadir razones transportista_tercero o sin_repartidor_informado para repartidor ausente, y cancelado_en_ruta o pendiente_o_no_entregado para fecha_entrega ausente. En fact_ventas_cabecera SHALL marcar campana_null_reason=venta_sin_campana cuando campana_id sea NULL. No SHALL rellenar globalmente cantidades, importes o fechas con cero/defaults.

#### Scenario: Festivo falso
- **WHEN** dim_fecha tiene es_festivo_colombia=false y festivo_nombre informado
- **THEN** festivo_nombre queda NULL

#### Scenario: Entrega cancelada sin fecha
- **WHEN** estado_entrega es Cancelado en ruta y fecha_entrega es NULL
- **THEN** fecha_entrega_null_reason es cancelado_en_ruta y la fecha sigue NULL

#### Scenario: Venta sin campaña
- **WHEN** campana_id es NULL
- **THEN** campana_null_reason es venta_sin_campana sin inventar una campaña

### Requirement: Normalización textual y flags de dominio

domain_normalization SHALL crear los códigos configurados aplicando trim, sustitución de secuencias fuera de A-Za-z0-9 por _, eliminación del _ inicial/final y lower. SHALL conservar los valores originales y añadir flags solo para los cinco catálogos ALLOWED_VALUES documentados en data-contracts. Los flags SHALL comparar la cadena original recortada con valores sensibles a mayúsculas y considerar NULL válido; no SHALL filtrar filas por un flag false.

#### Scenario: Código y flag distintos
- **WHEN** estado_venta contiene emitida en minúsculas
- **THEN** estado_venta_codigo es emitida y su flag es false porque el valor permitido es Emitida

#### Scenario: Carácter acentuado
- **WHEN** una columna configurada contiene En revisión
- **THEN** el código no translitera acentos: sustituye caracteres fuera del patrón y conserva la columna original

#### Scenario: Valor nulo
- **WHEN** estado_stock es NULL
- **THEN** estado_stock_codigo_valido es true por la condición explícita de nulo

### Requirement: Derivaciones vigentes por entidad

business_derivations SHALL aplicar las fórmulas y flags del inventario data-contracts, sin agregación mensual ni rechazo general de negativos. Para devoluciones SHALL añadir dias_hasta_devolucion mediante left join con ventas del mismo schema Silver solo si esa tabla existe; no SHALL buscar una referencia shared ni comprobar unicidad antes del join. Las columnas de derivación SHALL reemplazarse mediante withColumn cuando ya existen.

#### Scenario: Devolución sin tabla de ventas
- **WHEN** fact_ventas_cabecera no existe en el schema del paso de devoluciones
- **THEN** derive conserva los flags de devolución y omite el join y cálculo adicional de días

#### Scenario: Cantidad negativa de compra
- **WHEN** cantidad_comprada es -4 y subtotal_sin_iva es 100
- **THEN** el costo promedio se calcula como -25 y el paso no rechaza la fila

### Requirement: Claves compuestas y esquema incremental

resolve_merge_keys SHALL usar el subconjunto presente de una PK configurada, incluso si falta otro componente; después SHALL recurrir a _np_record_hash y a metadatos de fuente presentes. La deduplicación de estandarización SHALL usar el subconjunto presente de su mapa PK y no SHALL prometer orden total si los criterios de prioridad empatan. align_to_target_schema SHALL rellenar columnas destino ausentes en la entrada con NULL tipado; el MERGE SHALL actualizar todas las columnas e insertar claves nuevas, sin eliminar filas destino ausentes de la entrada.

#### Scenario: PK compuesta incompleta
- **WHEN** fact_inventario_mensual contiene mes_carga y tienda_id pero no producto_id
- **THEN** resolve_merge_keys devuelve las dos claves presentes, sin error por el componente ausente

#### Scenario: Columna destino ausente
- **WHEN** la tabla destino tiene una columna no incluida en la entrada
- **THEN** se añade NULL tipado antes del MERGE y una coincidencia puede actualizar esa columna a NULL

### Requirement: Reprocesamiento y fallos Silver

La estandarización SHALL usar el máximo watermark SUCCESS por paso/tabla y un filtro estrictamente mayor. Los pasos posteriores SHALL basarse en la marca del paso anterior. Una corrección de dimensiones sin nuevas filas de hechos no SHALL causar automáticamente rederivación o reenriquecimiento de esos hechos. Los notebooks de transformación SHALL escribir auditorías SUCCESS o NO_DATA en los caminos explícitos, sin try por tabla ni registro FAILED garantizado para excepciones Spark. El año SHALL determinar rutas físicas, sin filtrar por año las tablas leídas.

#### Scenario: Timestamp igual al límite
- **WHEN** una fila Bronze tiene _np_ingestion_ts igual al último watermark exitoso
- **THEN** la estandarización la excluye

#### Scenario: Error al escribir Silver
- **WHEN** merge_silver_table lanza una excepción
- **THEN** el notebook se interrumpe antes del registro SUCCESS de esa tabla y no crea un FAILED en un manejador inexistente

#### Scenario: Dimensión modificada sin delta de hechos
- **WHEN** se actualiza una dimensión pero los hechos mantienen marca business_derivations
- **THEN** el flujo no vuelve a ejecutar por sí solo las derivaciones de esos hechos
