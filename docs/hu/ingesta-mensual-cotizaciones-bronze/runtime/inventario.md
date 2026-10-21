# Recursos de validación de cotizaciones

Autorización humana 2026-10-20: crear recursos aislados fuera de NaturaPet; warehouse existente y clúster clásico temporal confirmados. Actualización de plan y continuación confirmadas. Perfil CREA_DEV, identidad srinconr@creasistemas.com, workspace adb-7405606739630987.7.azuredatabricks.net.

## Registro incremental

| Recurso | Identificador o ruta | Origen | Estado y persistencia |
| --- | --- | --- | --- |
| SQL warehouse | naturapet_serverless_wh / dd74907a9f5cb481 | Preexistente | STOPPED al inicio, auto-stop 10 min. Se conserva sin cambiar configuración. |
| Clúster dedicado de un nodo | crea-cotizaciones-test-20261020-01a15a7c / 1020-210854-9y22c5h7 | Creado en esta ejecución | **TERMINATED verificado** en cluster-status.json. DBR 16.4 LTS, Standard_D4ads_v6, auto-terminación 10 min. Definición conservada; no se pidió permanent-delete. |
| Catálogo de prueba | crea_cotizaciones_test_20261020_01a15a7c | Creado en esta ejecución | **Conservado**. 41 schemas de prueba, más default/information_schema; 32 tablas EXTERNAL. Separado de todos los catálogos naturapet*. |
| Raíz autorizada | abfss://demo@demodldb.dfs.core.windows.net/_tests/cotizaciones/20261020_01a15a7c | Creada en esta ejecución | **Conservada**. managed y data en subrutas separadas. Archivos, originales, evidencia, cuarentena, auditoría, logs y directorios Delta sin registro UC permanecen. |

No se han modificado catálogos NaturaPet, ubicaciones externas, credenciales, grants, jobs ni schedules existentes. Se registrarán aquí los resultados, nuevas rutas y estado final antes de la entrega.

## Resultado y estado final verificados

- Integración completa: **SUCCESS**, run 853804030647399 / task 169503786443292. CA01–CA14 **passed**; `validated-result.json` conserva la matriz estructurada. Ejecución 1017 s, setup 1 s, DBR 16.4 / Spark 3.5.2 / Python 3.12.3 / Delta integrada; shuffle partitions=4 exclusivamente en la sesión sintética.
- Inspección final: **SUCCESS**, run 775572081212517 / task 93265957589326. `resource-summary-attempt03.json` enumera los 43 schemas totales, las 32 tablas externas de ambos intentos que crearon datos, y las rutas por caso. No se creó namespace del intento2, que falló antes del preflight.
- Clúster: solicitado terminar y consultado nuevamente con API get; **TERMINATED**, definición aún visible, `cluster-status.json`. Las máquinas no permanecen como compute activo según Databricks; no se afirma haber inspeccionado recursos Azure directamente.
- Warehouse: preexistente `naturapet_serverless_wh` / dd74907a9f5cb481, **STOPPED** verificado, auto-stop 10 min y tamaño 2X-Small originales; `warehouse-final-state.json`. No creado, eliminado ni reconfigurado.
- Workspace: **se conservan** 11 módulos `.py` como Workspace Files, notebook `checkout/notebooks/comercial/bronze/tests/validate_cotizaciones` y notebook auxiliar `inspect-runtime`, bajo `/Users/srinconr@creasistemas.com/crea_tests/20261020_01a15a7c/`. Hashes en `uploaded-modules.json` y `candidate-identity.json`.
- Ejecuciones únicas e historial: intentos 1, 2, 3 e inspecciones 1/3 conservan sus recibos. No se creó un job guardado, schedule, pipeline o automatización; `jobs submit` genera ejecuciones únicas con su historial administrado por Databricks.
- Los 613 eventos del intento1 y 659 del intento3 registran creaciones, fallos esperados, movimientos y eliminaciones puntuales de archivos sintéticos de colisión. **No hubo limpieza general** de catálogo, schemas, tablas o raíz. Por ello permanecen también los fixtures del intento1 fallido.

## Rutas e inventarios para inspección posterior

- Raíz de almacenamiento: `abfss://demo@demodldb.dfs.core.windows.net/_tests/cotizaciones/20261020_01a15a7c`.
- Managed catalog root: `<raíz>/managed` (sin tablas managed de negocio creadas por la suite).
- Intentos con datos: `<raíz>/data/runtime_attempt01` y `<raíz>/data/runtime_attempt03`; cada caso usa directorios propios de raw, Bronze, controles e histórico.
- Inventario incremental por intento: `_inventory.json`; el auxiliar dejó copias visibles `inventory.json` y `resource-summary.json` en cada intento inspeccionado para consulta SQL posterior. `read_files` omite por defecto archivos con prefijo `_`; por eso la consulta inicial de runtime-metadata-result.json devolvió cero filas y no se usa como prueba de versiones.
- Fuentes canónicas locales del resultado final: `validated-result.json`, `resource-summary-attempt03.json`, `cluster-status.json`, `warehouse-final-state.json`. `catalog-check-result.json`, `table-inventory-result.json` y otros snapshots anteriores son evidencia intermedia, no el recuento final.

## Uso futuro y limpieza

Conservar estos recursos permite inspeccionar fallos, logs y reintentos sin leer datos NaturaPet. Para otra ejecución elegir un `test_run_id` y token de idempotencia nuevos; nunca sobrescribir los namespaces previos. El notebook actual exige catálogo, raíz y compute aprobados explícitamente. Para nuevos entornos debe revisarse ese contrato, en lugar de sustituirlo por destinos operativos.

El SQL warehouse sirve para DDL y verificaciones SQL; la implementación actual requiere cómputo clásico dedicado compatible con Python/RDD. `Standard_DS3_v2` falló por SkuNotAvailable en eastus2; `Standard_D4ads_v6` pudo arrancar en esta ejecución. Esto es evidencia de disponibilidad observada, no garantía futura de capacidad.

Limpieza futura (no ejecutada): comprobar inventario y ausencia de ejecuciones activas; eliminar únicamente el catálogo aislado y objetos de prueba aprobados, después la raíz exacta de almacenamiento y la carpeta exacta de workspace. **DROP CATALOG no elimina los archivos de las tablas externas ni sus directorios auxiliares**; requieren limpieza separada. No borrar la ubicación externa existente, su credencial ni el warehouse. La definición del clúster temporal podría eliminarse permanentemente si se autoriza después.

Los documentos de inventario y recibos están preparados en el checkout para la entrega Git; no se afirma commit/push de estos archivos antes de que el principal publique el candidato autorizado.

Primer aprovisionamiento: TERMINATED / CLOUD_PROVIDER_RESOURCE_STOCKOUT, Azure SkuNotAvailable para Standard_DS3_v2 en eastus2. Se editó únicamente este clúster temporal a Standard_D4ads_v6 (4 cores, 16 GiB), habilitado según node_info, y se reintentó arranque; mismo cluster_id. No se alteraron otros recursos.

CREATE CATALOG confirmado SUCCEEDED vía warehouse dd74907a9f5cb481; statement_id 01f1ccca-8605-1c35-844a-dddaa79b80cf. Ubicación efectiva managed/__unitystorage/catalogs/a691cd24-3bee-4b70-87c7-8315abfd6777. Se conservan catálogo y datos sintéticos para inspección; sin limpieza automática. Copiados 11 módulos Python como Workspace Files y un notebook en /Users/srinconr@creasistemas.com/crea_tests/20261020_01a15a7c/checkout. Ver uploaded-modules.json para hashes. Ejecución única enviada: run_id 213340312329490, token cotizaciones-20261020-01a15a7c-attempt01, test_run_id runtime_attempt01; sin crear job persistente ni schedule.

Revisión de guardas independiente: favorable. El inventario local canónico es runtime/inventario.md (este archivo). Al finalizar se consultarán todas las tablas del catálogo aislado para incluir las tablas de regresión genéricas fact_ventas_cabecera, dim_tienda y auditorías, además de las rutas Delta especializadas. No se asumirá que planned_tables contiene todas las tablas.

Intento de integración 1: FAILED en regresión genérica con PATH_OUTSIDE_APPROVED_TEST_DATA_ROOT, al validar FileInfo.path de un directorio retornado por dbutils.fs.ls. Guardas impidieron continuar; no escrituras fuera de raíz. Ejecución real 1545 segundos, setup 382 segundos. Bloques de contrato/calidad/replay/fallos/errores de archivo/integridad terminaron antes de CA14; no se declara suite completa passed. Salida preservada en attempt01-output.json. Se prepara corrección del notebook y repetición completa, sin modificar lógica de negocio.

Intento 2: run_id 582119187788237 / task 149461545064842 terminó FAILED (16 s) ANTES de la petición de cancelación, no por la cancelación. Causa real: INVALID_PARAMETER_VALUE.LOCATION_OVERLAP al llamar mkdirs sobre /data, padre de tablas externas de intento1. Salida completa attempt02-output.json. No llegó a crear la carpeta ni schemas del intento2. Corrección del preflight: comprobar/crear solo carpeta hoja propia, sin acceder al padre; conservar recursos de intento1. El reviewer pidió comprobar también la referencia nativa notebook.exit del proxy antes de nuevo envío. No se presenta este intento como cancelado ni passed.

Preflight independiente del tercer intento: favorable, 11 tests del notebook pasaron; suite local developer 102 passed. Se conserva notebook.exit nativo, acceso inicial solo hoja propia, sin leer/escribir padre /data y sin relajar aislamiento. Tercer payload submit-run03.json, test_run_id runtime_attempt03, token cotizaciones-20261020-01a15a7c-attempt03; mismo clúster y catálogo, sin nuevos recursos de infraestructura. Shuffle partitions=4 solo en sesión de pruebas, registrado en metadata.
