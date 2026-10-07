# Operación, auditoría y recuperación del lakehouse

## Purpose

Describir estados observables, persistencia parcial y mecanismos actuales de reanudación. El contrato registra las capacidades existentes, sin introducir procedimientos de reparación, SLA o automatizaciones ausentes del código.

Contrato del comportamiento implementado, documentado mediante lectura estática de `develop@eb35b87b79eb541c4832fccc8f8825412755f498`. Los escenarios describen resultados esperados del código actual; no constituyen evidencia de ejecución de Spark ni de despliegue en Databricks.

## Sources

- [src/common/notebook_runner.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/src/common/notebook_runner.py)
- [src/common/delta_load.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/src/common/delta_load.py)
- [src/common/io.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/src/common/io.py)
- [src/common/silver_incremental.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/src/common/silver_incremental.py)
- [notebooks/shared/silver/01_schema_standardization.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/shared/silver/01_schema_standardization.ipynb)
- [notebooks/shared/silver/02_null_corrections.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/shared/silver/02_null_corrections.ipynb)
- [notebooks/shared/silver/03_domain_normalization.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/shared/silver/03_domain_normalization.ipynb)
- [notebooks/shared/silver/04_business_derivations.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/shared/silver/04_business_derivations.ipynb)
- [notebooks/comercial/gold/01_comercial_marts.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/comercial/gold/01_comercial_marts.ipynb)
- [notebooks/shared/silver/05_quality_checks.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/shared/silver/05_quality_checks.ipynb)
- [notebooks/gobierno/gold/05_quality_checks.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/gobierno/gold/05_quality_checks.ipynb)
- [resources/jobs/monthly_data_mesh_refresh.job.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/resources/jobs/monthly_data_mesh_refresh.job.yml)

## Estados y persistencia

| Componente | Estados o resultado | Persistencia actual |
| --- | --- | --- |
| Carga Bronze | SUCCESS, FAILED, NO_DATA; resumen OK/ERROR. | Append en bronze_file_load_audit; load_id UUID por intento de archivo; resumen taskValues. |
| Archivo Bronze | archive_status SUCCESS/FAILED; archived_at solo para éxito; resumen OK/ERROR. | Actualización por load_id en la auditoría de carga; resumen taskValues. |
| Transformación Silver | SUCCESS o NO_DATA en los caminos explícitos; excepciones sin registro FAILED garantizado. | Append en silver_processing_audit por tabla y paso. |
| Calidad Silver | PASS/FAIL por control; INFO para ausencia de tablas. | Overwrite de silver_quality_checks, con checked_at. |
| Marts Gold | Resumen de tabla, ruta y filas; excepción por staging vacío o error de plataforma. | Staging y overwrite final por mart, con timestamp Gold. |
| Calidad Gold | PASS/FAIL por mes; no excepción por FAIL por sí solo. | Staging y overwrite de gobierno_gold.gold_quality_checks. |

## Requirements

### Requirement: Resultado de carga y ausencia de fuentes

Bronze SHALL registrar cada archivo procesado exitosamente o fallido en su auditoría y generar un resumen antes de lanzar RuntimeError cuando failed_files no está vacío. Sin fuentes SHALL registrar NO_DATA para __NO_FILES__, sin cargar diccionario y con resumen OK. La ausencia de fuentes no SHALL interpretarse como prueba de frescura o completitud mensual. Los fallos iniciales y errores de path_exists SHALL conservar los límites descritos en bronze-ingestion.

#### Scenario: Carga parcial
- **WHEN** un archivo se carga y otro falla dentro del try por archivo
- **THEN** se conservan auditorías de ambos y el resumen ERROR precede a RuntimeError, sin revertir el primero

#### Scenario: Sin entregas nuevas
- **WHEN** no se descubren archivos
- **THEN** el resumen es OK con no_data_message y auditoría NO_DATA

### Requirement: Auditoría Bronze y estados de archivo

bronze_file_load_audit SHALL conservar load_id, área, tabla, modo, año, mes, ruta/nombre/formato fuente, tabla/ruta destino, record_count, status, error_message, historic_path y timestamps UTC created_at/updated_at. Los estados de archivo SHALL mantenerse en archived_at, archive_status y archive_error_message, inicialmente NULL. La selección pendiente SHALL exigir status=SUCCESS y archived_at NULL, sin excluir por archive_status=FAILED.

#### Scenario: Archivo con fallo previo de movimiento
- **WHEN** una carga SUCCESS conserva archived_at NULL y archive_status FAILED
- **THEN** list_pending_archives la vuelve a seleccionar

#### Scenario: Carga fallida
- **WHEN** status es FAILED
- **THEN** no es elegible para archivado

### Requirement: Reanudación del movimiento histórico

El archivador SHALL mover una fuente existente al destino; si la fuente falta y el destino existe SHALL registrar éxito sin verificar contenido. Si ambos faltan SHALL registrar FAILED de archivo. SHALL acumular actualizaciones por load_id, persistirlas después del bucle y lanzar RuntimeError si hubo fallos de archivo. No SHALL restaurar movimientos ya hechos cuando otro archivo falla.

#### Scenario: Interrupción tras mover
- **WHEN** un movimiento terminó pero archived_at no se persistió
- **THEN** la siguiente ejecución puede marcar éxito si encuentra solo el destino

#### Scenario: Ambos ausentes
- **WHEN** faltan fuente e histórico de una carga SUCCESS pendiente
- **THEN** el archivador registra error y su resumen termina ERROR

### Requirement: Auditoría y reanudación Silver

silver_processing_audit SHALL conservar environment, domain_name, step_name, table_name, source_table, target_table, input_rows, output_rows, status, message, watermark_column, previous_watermark, new_watermark, target_path y timestamps UTC. La estandarización SHALL recuperar el máximo new_watermark SUCCESS por paso/tabla; los pasos siguientes SHALL seleccionar marcas previas. Una excepción entre MERGE y auditoría SHALL dejar posible escritura sin SUCCESS y no SHALL causar rollback automático.

#### Scenario: Escritura sin auditoría posterior
- **WHEN** el MERGE termina y falla append_silver_audit
- **THEN** la tabla puede conservar sus cambios y el próximo watermark deriva únicamente de auditorías SUCCESS persistidas

#### Scenario: Paso intermedio pendiente
- **WHEN** null_corrections terminó y domain_normalization falló antes de escribir esa fila
- **THEN** la marca null_corrections permite que domain_normalization la seleccione en otra ejecución

### Requirement: Reejecución y backfill actuales

No SHALL atribuirse al repositorio un comando dedicado de backfill, reset de watermark, reconstrucción histórica o reparación de auditorías. Reejecutar Bronze SHALL volver a descubrir archivos de raw; Silver SHALL aplicar sus watermarks y marcas; Gold SHALL reconstruir agregados desde tablas disponibles. Cambiar data_year SHALL cambiar las rutas físicas pero no SHALL filtrar automáticamente las tablas existentes ni resetear auditorías. El código no SHALL ofrecer una transacción de recuperación de todo el mesh.

#### Scenario: Cambio de año Silver
- **WHEN** se cambia data_year conservando el catálogo y schema con auditorías existentes
- **THEN** latest_success_watermark sigue consultando la tabla de auditoría por paso/tabla, sin filtro por año

#### Scenario: Reejecución Gold
- **WHEN** se vuelve a ejecutar el notebook con fuentes disponibles
- **THEN** escribe nuevamente staging y reemplaza cada mart final en su orden

### Requirement: Observabilidad disponible y límites de alertas

Los runners Bronze SHALL publicar taskValues con claves <área>_bronze_load_summary y <área>_bronze_archive_summary, compactando payloads grandes según bronze-ingestion. Silver SHALL mostrar su resumen de paso; Gold SHALL mostrar un resumen de tablas publicadas; calidad SHALL mostrar reportes. Los Jobs no SHALL atribuirse notificaciones, thresholds de salud o alertas configuradas en sus YAML. El repositorio no SHALL definir un SLA/SLO, RPO/RTO, frescura máxima ni escalamiento de incidentes.

#### Scenario: Reporte de calidad fallido
- **WHEN** se publica un FAIL Silver o Gold
- **THEN** el código persiste/muestra el resultado sin enviar una notificación ni generar una excepción solo por ese estado

### Requirement: Retención y limpieza existentes

Las auditorías Bronze/Silver SHALL acumular registros mediante append y el archivo SHALL conservar archivos en historic. Los reportes de calidad SHALL reemplazarse mediante overwrite. Las tablas staging Gold SHALL permanecer tras la publicación. El repositorio no SHALL atribuirse limpieza programada de staging/historic/auditorías, VACUUM, backup o política de retención automatizada.

#### Scenario: Dos revisiones de calidad
- **WHEN** se ejecutan dos controles Silver consecutivos
- **THEN** la tabla publicada conserva la revisión reemplazada por el segundo overwrite, sin un append histórico de controles

#### Scenario: Fin de publicación Gold
- **WHEN** el mart se publica correctamente
- **THEN** el staging continúa registrado y no se ejecuta un paso de borrado

### Requirement: Concurrencia y éxito del mesh

La operación SHALL usar los límites por Job y dependencias de orchestration-delivery. El orquestador SHALL encadenar Bronze, Silver y Gold mediante tareas dependientes, sin lock global por tabla o archivo implementado en el código común. El éxito técnico del mesh no SHALL interpretarse como ausencia de FAIL en los reportes de calidad ni como validación de todas las FK o frescura; la evaluación de calidad SHALL seguir data-quality.

#### Scenario: Pipeline con controles fallidos
- **WHEN** todos los notebooks terminan normalmente y un reporte registra FAIL
- **THEN** las dependencias técnicas pueden completar el mesh sin que eso convierta el reporte en PASS
