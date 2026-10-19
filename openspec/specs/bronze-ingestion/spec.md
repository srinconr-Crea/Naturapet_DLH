# Ingesta y archivo Bronze

## Purpose

Establecer el contrato actual de descubrimiento, validación, carga Delta, auditoría y traslado a histórico de archivos por dominio.

Contrato del comportamiento implementado, documentado mediante lectura estática de `develop@eb35b87b79eb541c4832fccc8f8825412755f498`. Los escenarios describen resultados esperados del código actual; no constituyen evidencia de ejecución de Spark ni de despliegue en Databricks.

## Sources

- [src/common/io.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/src/common/io.py)
- [src/common/schema.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/src/common/schema.py)
- [src/common/validation.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/src/common/validation.py)
- [src/common/delta_load.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/src/common/delta_load.py)
- [src/common/notebook_runner.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/src/common/notebook_runner.py)
- [tests/test_project_structure.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/tests/test_project_structure.py)

## Requirements

### Requirement: Descubrimiento y formatos admitidos

El descubrimiento SHALL considerar archivos directos del directorio anual como load_mode full, y archivos directamente dentro de carpetas 01 a 12 como incremental. SHALL admitir CSV, JSON y Parquet y rechazar Excel y extensiones no soportadas. SHALL ordenar por mes y nombre; no SHALL tratar full como una instrucción de borrado de la tabla.

#### Scenario: Archivo mensual
- **WHEN** se descubre fact_ventas_cabecera_01.csv dentro de 01
- **THEN** se registra mes 01 y modo incremental, y normalize_table_name devuelve fact_ventas_cabecera

#### Scenario: Excel no admitido
- **WHEN** se intenta detectar el formato de una fuente .xlsx
- **THEN** se genera ValueError y no se considera una fuente soportada

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

### Requirement: Nombre de tabla y lectura por formato

detect_file_format SHALL comparar la extensión final en minúsculas y admitir csv, json y parquet. normalize_table_name SHALL eliminar únicamente el sufijo literal .csv, sensible a mayúsculas, y después el sufijo _<mes> si queda al final. El soporte del lector no SHALL interpretarse como eliminación de extensiones JSON, Parquet o CSV en mayúsculas al resolver tablas. CSV y JSON SHALL leerse con inferencia cuando no hay schema; CSV SHALL usar header=true y Parquet su esquema almacenado.

#### Scenario: Nombre JSON mensual
- **WHEN** se resuelve fact_ventas_01.json con mes 01
- **THEN** el nombre permanece fact_ventas_01.json; no se convierte automáticamente en fact_ventas

#### Scenario: CSV en mayúsculas
- **WHEN** se detecta y normaliza fact_ventas_01.CSV
- **THEN** el lector detecta csv y el normalizador conserva fact_ventas_01.CSV

### Requirement: Diccionario y evolución de columnas Bronze

load_data_dictionary SHALL leer CSV con header=true y agrupar sus filas por tabla usando tabla, campo, rol y tipo_dato_csv. conform_to_dictionary SHALL seleccionar únicamente las columnas declaradas y mapear object a string, int64 a long y float64 a double; otros tipos SHALL usar string. Las columnas declaradas faltantes SHALL causar ValueError; las columnas adicionales SHALL descartarse en tablas del diccionario. La tabla nueva SHALL usar mergeSchema=true y el MERGE existente no SHALL añadir explícitamente columnas ni activar autoMerge de sesión.

#### Scenario: Columna extra
- **WHEN** un CSV conocido tiene todas las columnas declaradas y una columna adicional
- **THEN** conform_to_dictionary excluye la adicional antes de la carga

#### Scenario: Tipo no reconocido
- **WHEN** tipo_dato_csv contiene un valor fuera de los tres tipos mapeados
- **THEN** la columna se convierte a string

#### Scenario: Evolución de tabla existente
- **WHEN** la entrada declarada incorpora una nueva columna y la tabla Delta ya existe
- **THEN** el código invoca MERGE sin ALTER TABLE ni configuración global de autoMerge; el resultado depende del esquema y runtime Delta

### Requirement: Relectura e identidad de archivos

run_bronze_load SHALL procesar todos los archivos descubiertos aún presentes en raw, sin excluirlos por auditorías SUCCESS anteriores y sin comprobar checksum de archivo. Una nueva lectura SHALL añadir un instante de ingesta nuevo y crear otro load_id. Las PK de diccionario SHALL prevalecer sobre el hash; cuando se usa hash SHALL incluir columnas de negocio y metadatos disponibles excepto _np_ingestion_ts, en el orden de columnas de entrada.

#### Scenario: Archivo exitoso que sigue en raw
- **WHEN** un archivo con auditoría SUCCESS anterior se descubre de nuevo
- **THEN** el runner vuelve a leerlo y realiza la carga por claves; no lo omite basándose en la auditoría

#### Scenario: Misma fila en otra fuente sin PK
- **WHEN** la fila de negocio se presenta con otra ruta y nombre de fuente
- **THEN** los metadatos participan en el hash y no se garantiza la misma identidad que en la fuente anterior

### Requirement: Límites de auditoría y fallos iniciales

El manejo por archivo SHALL abarcar validación de tabla, lectura, validaciones de datos, escritura y auditoría de ese archivo. El descubrimiento y la carga del diccionario SHALL ejecutarse antes del try por archivo; los fallos en esas fases no SHALL describirse como registros FAILED por archivo ni como resumen taskValues garantizado. path_exists SHALL devolver false ante cualquier excepción de ls; run_bronze_load SHALL tratar ese resultado como ausencia de fuentes si no falla una operación posterior.

#### Scenario: Formato no soportado descubierto
- **WHEN** discover_area_files encuentra un .xlsx en raw
- **THEN** detect_file_format lanza ValueError antes del bucle por archivo; no se genera el resumen final por ese camino

#### Scenario: Error al listar raw
- **WHEN** dbutils.fs.ls falla dentro de path_exists
- **THEN** path_exists devuelve false y el runner toma el camino sin fuentes; no distingue aquí permisos insuficientes de ruta ausente

### Requirement: Persistencia parcial y movimiento a histórico

La escritura de tabla, el append de auditoría y el movimiento a histórico SHALL ejecutarse por separado, sin rollback global. El archivador SHALL construir la carpeta destino y llamar dbutils.fs.mv, sin comparación de checksum ni política explícita de resolución de colisiones. El estado de archivo SHALL actualizarse por load_id; archived_at SHALL fijarse solo para éxitos de archivo.

#### Scenario: Fallo después de una escritura
- **WHEN** la escritura Delta termina y una operación posterior falla
- **THEN** el código no restaura la versión previa de la tabla; los datos escritos pueden permanecer

#### Scenario: Fuente y destino presentes
- **WHEN** el archivador encuentra la fuente y ya existe el destino histórico
- **THEN** invoca mv; no resuelve la colisión ni verifica equivalencia de contenido por su cuenta
