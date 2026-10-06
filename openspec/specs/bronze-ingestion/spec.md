# Ingesta y archivo Bronze

## Purpose

Establecer el contrato actual de descubrimiento, validación, carga Delta, auditoría y traslado a histórico de archivos por dominio.

Base documental sugerida, derivada por lectura de código en `develop@9c48831022a329902f765058de37e6d0a1528eb7`. Requiere revisión humana antes de adoptarse; no acredita ejecución de Spark ni despliegue Databricks.

## Sources

- [src/common/io.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/src/common/io.py)
- [src/common/schema.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/src/common/schema.py)
- [src/common/validation.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/src/common/validation.py)
- [src/common/delta_load.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/src/common/delta_load.py)
- [src/common/notebook_runner.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/src/common/notebook_runner.py)
- [tests/test_project_structure.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/tests/test_project_structure.py)

## Requirements

### Requirement: Descubrimiento y formatos admitidos

El descubrimiento SHALL considerar archivos directos del directorio anual como load_mode full, y archivos directamente dentro de carpetas 01 a 12 como incremental. SHALL admitir CSV, JSON y Parquet y rechazar Excel y extensiones no soportadas. SHALL ordenar por mes y nombre; no SHALL tratar full como una instrucción de borrado de la tabla.

La normalización del nombre de tabla a partir del nombre de archivo SHALL eliminar primero la extensión final .csv, .json o .parquet, sin distinguir mayúsculas y minúsculas en la extensión. Después SHALL eliminar el sufijo _<month> únicamente si month está informado y coincide exactamente al final del nombre ya sin extensión. SHALL preservar las mayúsculas y minúsculas del nombre de tabla, conservar las extensiones no reconocidas y conservar los puntos internos del nombre. La normalización mantiene la firma vigente, con month opcional y vacío por defecto, y no SHALL alterar la detección de formatos ni la lectura de datos.

#### Scenario: Archivo mensual
- **WHEN** se descubre fact_ventas_cabecera_01.csv dentro de 01
- **THEN** se registra mes 01 y modo incremental, y normalize_table_name devuelve fact_ventas_cabecera

#### Scenario: Excel no admitido
- **WHEN** se intenta detectar el formato de una fuente .xlsx
- **THEN** se genera ValueError y no se considera una fuente soportada

#### Scenario: Extensión CSV con sufijo de mes
- **WHEN** se normaliza fact_ventas_01.csv con month 01
- **THEN** el nombre de tabla resultante es fact_ventas

#### Scenario: Extensión JSON con sufijo de mes
- **WHEN** se normaliza fact_ventas_01.json con month 01
- **THEN** el nombre de tabla resultante es fact_ventas

#### Scenario: Extensión Parquet con sufijo de mes
- **WHEN** se normaliza fact_ventas_01.parquet con month 01
- **THEN** el nombre de tabla resultante es fact_ventas

#### Scenario: Extensión en mayúsculas con nombre en mayúsculas mixtas
- **WHEN** se normaliza Fact_Ventas_01.CSV con month 01
- **THEN** el nombre de tabla resultante es Fact_Ventas y se preservan las mayúsculas del nombre

#### Scenario: Extensión con mayúsculas y minúsculas mezcladas
- **WHEN** se normaliza fact_ventas_01.JsOn con month 01
- **THEN** el nombre de tabla resultante es fact_ventas

#### Scenario: Archivo anual sin month
- **WHEN** se normaliza fact_ventas.PARQUET con month vacío
- **THEN** el nombre de tabla resultante es fact_ventas

#### Scenario: Sufijo distinto del mes informado
- **WHEN** se normaliza fact_ventas_02.csv con month 01
- **THEN** se elimina la extensión, no se elimina _02 y el nombre de tabla resultante es fact_ventas_02

#### Scenario: Month vacío no elimina sufijo numérico
- **WHEN** se normaliza fact_ventas_01.csv con month vacío
- **THEN** se elimina solo la extensión y el nombre de tabla resultante es fact_ventas_01

#### Scenario: Punto interno en el nombre
- **WHEN** se normaliza fact.ventas_01.json con month 01
- **THEN** el nombre de tabla resultante es fact.ventas y se conserva el punto interno

#### Scenario: Extensión no reconocida
- **WHEN** se normaliza fact_ventas_01.xlsx con month 01
- **THEN** el nombre de tabla resultante es fact_ventas_01.xlsx, sin eliminar la extensión ni el sufijo de mes

#### Scenario: Nombre sin extensión
- **WHEN** se normaliza fact_ventas_01 con month 01
- **THEN** se elimina el sufijo de mes y el nombre de tabla resultante es fact_ventas

### Requirement: Validación previa a la carga

El runner SHALL rechazar archivos vacíos, tablas ausentes del diccionario salvo manifest, data_dictionary y resumen_mensual_validacion, y columnas requeridas faltantes. Para tablas del diccionario SHALL seleccionar y convertir sus columnas. Con carpeta mensual y columna mes_carga, SHALL rechazar valores no nulos que no correspondan a año-mes.

#### Scenario: Mes compatible
- **WHEN** la carpeta es 2026/01 y mes_carga es 2026-01, 2026-01-01 o 2026-01 00:00:00
- **THEN** la validación de correspondencia mensual acepta el valor

#### Scenario: Mes distinto o prefijo ambiguo
- **WHEN** la carpeta es 2026/01 y mes_carga es 2026-02, 202601 o 2026-0101
- **THEN** la validación rechaza el valor

#### Scenario: Mes nulo
- **WHEN** mes_carga es NULL
- **THEN** la comprobación de correspondencia mensual no lo rechaza por sí sola

### Requirement: Identidad y carga Delta

La carga SHALL añadir metadatos _np_ de dominio, año, mes, fuente, modo e instante de ingesta. La tabla nueva SHALL crearse como Delta externa particionada por _np_source_year y _np_source_month; la existente SHALL hacer MERGE con igualdad null-safe, actualizando coincidencias e insertando claves nuevas.

#### Scenario: Tabla nueva
- **WHEN** la tabla destino todavía no existe
- **THEN** se escribe en target_path con mergeSchema=true y las particiones técnicas de año y mes

#### Scenario: Tabla existente
- **WHEN** existe la tabla y la entrada contiene claves existentes y nuevas
- **THEN** el MERGE actualiza las coincidencias e inserta las nuevas sin configurar autoMerge global de la sesión

### Requirement: Claves y deduplicación de entrada

La carga SHALL usar las PK disponibles declaradas por el diccionario o, en su ausencia, _np_record_hash SHA-256 excluyendo _np_ingestion_ts. SHALL seleccionar una fila por clave con prioridad por instante y ruta/nombre de fuente cuando existan; no SHALL prometer desempate entre filas idénticas en todos esos criterios.

#### Scenario: Sin PK declarada
- **WHEN** no hay claves de diccionario disponibles en la entrada
- **THEN** se crea _np_record_hash, se deduplica por ese hash y se usa como clave del MERGE

### Requirement: Auditoría y ausencia de archivos

El runner SHALL registrar SUCCESS o FAILED por archivo procesado y emitir un resumen. Sin archivos SHALL registrar NO_DATA con __NO_FILES__. Si existen fallos procesados, SHALL generar RuntimeError después del resumen. La serialización de taskValues SHALL conservar payloads pequeños y compactar los grandes con conteos y muestras.

#### Scenario: Sin archivos nuevos
- **WHEN** el descubrimiento no devuelve fuentes
- **THEN** se registra NO_DATA, no se carga el diccionario y el resumen general es OK con no_data_message

#### Scenario: Resumen grande
- **WHEN** un resumen supera 48 KiB UTF-8
- **THEN** dumps_task_value usa una representación compacta con task_value_truncated y conteos; el caso cubierto por la prueba queda dentro del límite

### Requirement: Histórico solo de cargas exitosas pendientes

El archivo SHALL seleccionar auditorías con status SUCCESS y archived_at nulo. SHALL mover la fuente al histórico y actualizar su estado; si la fuente ya no existe pero sí el destino, SHALL registrar éxito. Si ambos faltan, SHALL registrar FAILED de archivo y generar error en el resumen.

#### Scenario: Reanudación de un archivo ya movido
- **WHEN** una auditoría exitosa sigue pendiente, la fuente falta y el histórico existe
- **THEN** se marca el archivo como exitoso sin exigir repetir el movimiento

#### Scenario: Carga fallida
- **WHEN** la auditoría de carga tiene status FAILED
- **THEN** no entra en list_pending_archives
