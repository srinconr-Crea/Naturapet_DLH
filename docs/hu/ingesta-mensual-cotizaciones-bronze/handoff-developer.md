# Handoff — ingesta-mensual-cotizaciones-bronze / developer

## 1. Identidad y estado

- HU/cambio: ingesta-mensual-cotizaciones-bronze.
- Agente real: /root/implementar_cotizaciones, developer, gpt-6.1-sol / medium; sin subdelegación.
- Estado: ready para revisión local independiente; no passed ni ready_for_archive. Runtime not_run y reserva de driver abortado por evaluar (posible needs_changes).
- Candidato: HEAD 6029d05c3d47ccc0139cee4aef3c3df3fb50155c + diff/untracked siguientes, rama feature/hu-cotizaciones-bronze. Sin commit/push.

## 2. Entrada y alcance

Apply humano «bueno aplicalo» posterior a propuesta, manifiesto design §7 y CA01–14. Leídos AGENTS, proyecto/contexto, entrega Git, prácticas general/Python/Spark/Databricks/SQL/gobierno, README, conf, bundle/job Bronze, utilidades y módulos, notebooks, tests y contextFiles completos de apply. OpenSpec list/status/instructions apply reales: root local, spec-driven, state ready. Usuario difirió selección de entorno: ninguna ejecución Spark ni escritura remota.

## 3. Resultado

Archivos exactos creados/modificados por developer:

- src/common/cotizaciones_contract.py (nuevo).
- src/common/cotizaciones_ingestion.py (nuevo).
- src/common/config.py (rutas específicas).
- src/common/notebook_runner.py (dispatch y archivo específicos).
- notebooks/comercial/bronze/load_to_delta.ipynb (widget opcional).
- notebooks/comercial/bronze/archive_to_historic.ipynb (documenta integración).
- tests/test_cotizaciones_contract.py (nuevo).
- tests/test_cotizaciones_ingestion.py (nuevo).
- tests/fixtures/cotizaciones/cases.json (nuevo).
- notebooks/comercial/bronze/tests/validate_cotizaciones.ipynb (nuevo).
- openspec/changes/ingesta-mensual-cotizaciones-bronze/tasks.md (6/16 verificadas localmente).
- docs/hu/ingesta-mensual-cotizaciones-bronze/evidencia.md (append etapa developer).
- docs/hu/ingesta-mensual-cotizaciones-bronze/handoff-developer.md (este archivo).

Los demás untracked son planificación previa del planner; preservados. No tocaron specs principales/deltas, diseño, propuesta, conf, jobs, bundle, skills ni perfiles.

CA01–14 tienen implementación y matriz en evidencia; CA12/13 y adaptador Spark requieren ejecución real. Parsing de bytes distribuido por ejecutor con límite explícito 64 MiB, UTF-8/CSV estricto y ordinal estable; datos originales inmutables por hash; contrato puro y fingerprint post normalización; evidencia por ocurrencia, cuarentena por registro, merge de estado por cotizacion_id y secuencia. Auxiliares path-only fuera UC negocio. Archivo por hash y recuperación de movimiento. No prometer atomicidad multi-tabla.

## 4. Validación

2026-10-20; ver detalle de comandos/resultados y matriz en evidencia.md.

- Local focalizado exacto: 59 passed en ejecución previa a dos regresiones adicionales (un warning de cache).
- Local completo exacto: 73 passed en esa ejecución (un warning de cache).
- Final completo con cacheprovider desactivado: `.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider` → 75 passed, sin warnings (61 nuevos + 14 previos).
- AST Python 6 archivos, JSON/AST/outputs vacíos 3 notebooks: passed.
- `openspec.cmd validate ingesta-mensual-cotizaciones-bronze --strict`: passed.
- `git diff --check`, revisión whitespace nuevos: passed al cierre.
- `databricks bundle validate --strict --target dev --profile CREA_DEV`: primer intento sandbox blocked por cache local Access denied; mismo comando fuera sandbox con aprobación de lectura → Validation OK!, passed. No ACL/ignore alterados.
- Runtime notebook completo: not_run, usuario difirió entorno; ningún mock suple Spark.
- Kit: not_applicable. Sync/archive/publicación/despliegue: not_run, fuera de etapa.

## 5. Hallazgos y siguiente paso

Repetir pytest completo/focalizado y revisar SparkDeltaStore/Delta schemas/joins/concurrencia/archivo y suite notebook. No cerrar ni sincronizar con 5.2 not_run. Entorno futuro debe permitir RDD y registrar compute/DBR/Spark/Delta/Python reales, catálogo dev y schema/storage aislados aprobados.

Limitación explícita: reserva optimista fail-closed sin caducidad. Fallos capturados liberan owner y reintento recupera PROCESSING/FAILED; muerte de driver sin finally conserva owner y rechaza nuevas cargas hasta reconciliación operativa. No se implementó liberación remota ni lease/liveness fuera del plan. 3.3 permanece pendiente; reviewer debe decidir si detención con pendiente explícito cumple design §6 o remitir needs_changes al planner si requiere recuperación automática del driver abortado. No hay prueba ni claim de recuperación automática de ese caso.

No más decisiones funcionales añadidas. Principal recibe candidato para reviewer independiente; requiere autorización humana posterior para runtime, sync/archivo/publicación según flujo.

## 6. Configuración y extensiones usadas

Skills leídas: crea-orquestador, openspec-apply-change, test-driven-development, verification-before-completion, systematic-debugging; databricks-core, databricks-dabs y unity-catalog para adaptador/bundle. Se ignoran ejemplos de deploy de referencia de dabs porque usuario/proyecto prohíben despliegue. CLI perfil CREA_DEV únicamente para lectura de autenticación/validación. Sin MCP, instalaciones, extensiones, hooks o cambios globales.

## 7. Corrección R1 — ronda 1/2

Estado actual: **ready para segunda revisión independiente**, runtime not_run. R1 corregido: reconcile valida principal en current=True/False por PK, secuencia no nula y no anterior, identidad y 20 valores NULL-safe si misma secuencia. Versiones posteriores legítimas se aceptan sin reescribir principal. No driver collect ni cambio de plan.

Nuevas pruebas locales del método real con doble relacional: 16 combinaciones de PK eliminada, secuencia vieja/nula, identidad/valores/NULL alterados y versiones posterior/intacta. RED 7 fallos esperados antes del cambio; después **77 focalizadas y 91 totales passed**, sin warnings con no:cacheprovider. AST/JSON de tres notebooks, outputs vacíos, OpenSpec strict y diff check passed. Notebook sintético añade prueba Delta real de estas condiciones, archivo bloqueado, corrección B y replay A sin nueva escritura: no ejecutado.

Rutas modificadas en ronda: cotizaciones_ingestion.py, test_cotizaciones_ingestion.py, validate_cotizaciones.ipynb y append a evidencia.md/este handoff. Handoff reviewer preservado. No nuevas tareas marcadas; 6/16 verificadas. Bundle previo passed no repetido por mantener rutas/configuración. Skills adicionales: receiving-code-review para validar hallazgo antes de corregir.

Reviewer ya consideró la reserva abortada fail-closed compatible con design §6 y no exige lease/liveness. Repetir focalizado/completo y revisar R1; runtime requiere entorno/autorización posterior. Sin sync/archive/publicación ni declaraciones de aprobación propia.

## 8. Delta autorizado de aislamiento runtime — 2026-10-20

Estado ready para envío/ejecución por principal. Leídos design §9 y tasks revisados tras autorización humana «Sí, actualizar el plan y continuar». Guardas ahora exigen catálogo exacto crea_cotizaciones_test_20261020_01a15a7c, raíz exacta abfss://demo@demodldb.dfs.core.windows.net/_tests/cotizaciones/20261020_01a15a7c/data, compute exacto 1020-210854-9y22c5h7 e identidad autorizada. Rechazan naturapet*, otra raíz/contenedor, managed, traversal normal/encoded, query y prefijos hermanos. Cada config sobreescribe catálogo y rutas heredadas; GuardedFS valida operaciones y registra antes/después/fallo, y finalize_inventory recoge tablas/rutas incluso si falla la suite. Raíz /data se crea antes del ls inicial; run_id nuevo evita sobrescritura entre ejecuciones.

Widgets exactos para principal:

- allow_synthetic_writes = true
- approved_catalog = crea_cotizaciones_test_20261020_01a15a7c
- approved_schema_prefix = hu_cotizaciones_test_run
- approved_storage_root = abfss://demo@demodldb.dfs.core.windows.net/_tests/cotizaciones/20261020_01a15a7c/data
- approved_compute_reference = 1020-210854-9y22c5h7
- candidate_checkout_path = /Workspace/Users/srinconr@creasistemas.com/crea_tests/20261020_01a15a7c/checkout
- test_run_id = valor nuevo de 8–40 caracteres [a-z0-9_], o vacío para UUID automático.

Subir notebook en checkout/notebooks/comercial/bronze/tests/validate_cotizaciones y módulos como Workspace Files .py: src/common/__init__.py (src es namespace package, sin src/__init__.py) y config.py, cotizaciones_contract.py, cotizaciones_ingestion.py, notebook_runner.py, delta_load.py, io.py, schema.py, validation.py. Sin importarlos como notebooks. DBR 16.4 debe distribuir sys.path Workspace a ejecutores; confirmarlo en la ejecución real. Librerías externas utilizadas Spark/Delta del DBR; resto stdlib. No se requiere pytest remoto ni librerías adicionales.

Inventario incremental runtime queda en <approved_storage_root>/<test_run_id>/_inventory.json y stdout JSON; principal incorpora recibos al inventario versionado de recursos, bajo su ownership. Este developer no tocó docs/runtime ni inventario-recursos.md ni creó recursos remotos.

Test negativo extrae/ejecuta solo funciones puras de guardas reales desde AST del notebook, sin Spark: RED antes de adaptar / GREEN después. Suite completa local: 92 passed; AST/JSON notebook y OpenSpec strict/diff check passed. Tarea 5.1 cerrada tras verificación local; runtime 5.2 queda pendiente de ejecución principal, ya autorizado pero no probado. Rutas delta: notebook, tests/test_cotizaciones_ingestion.py, tasks.md y append a evidencia/este handoff; sin cambios de lógica productiva ni planificación.

## 9. Corrección de guarda tras runtime attempt01

Principal informó run 213340312329490 / task 360442301870637 FAILED tras 25m45s: check_generic_regression → discover_area_files → GuardedFS.ls rechazaba FileInfo.path terminado en /. Leído recibo runtime/attempt01-output.json sin modificarlo. Causa reproducida localmente RED: posixpath.normpath retiraba la barra final de directorio y comparación estricta fallaba. Se acepta ahora exactamente una barra final canónica, dentro de raíz exacta. Se mantienen rechazos de doble barra, traversal, encoding, query/fragment incluso vacío, prefijo hermano y otro contenedor; sin ampliar catálogo o raíz.

Notebook fija spark.sql.shuffle.partitions=4 solo en su sesión sintética y registra el valor; conserva aserciones de repartition(2/3) y suite completa. Inventario incremental añade tablas genéricas y auditoría, además de ruta genérica Delta. run_all_checks devuelve metadata/matriz y dbutils.notebook.exit serializa el resultado solo después de todas las aserciones y finally finalize_inventory. Una excepción conserva FAILED y no emite falso resultado exitoso.

Checks: 81 focalizadas y 95 totales passed, AST/JSON/outputs vacíos de tres notebooks passed, OpenSpec strict y diff check passed. Test adicional ejecuta el tail real de notebook con funciones de prueba para demostrar inventario en éxito/fallo y exit solo en éxito. Runtime corregido aún no ejecutado por developer; principal reenviará TODO con test_run_id=runtime_attempt02, restantes widgets de §8 idénticos. Sin subset, lógica productiva ni cambios a runtime/**, recursos o planificación. 5.2 permanece pendiente del rerun real. Estado ready para principal.

## 10. Corrección runtime ronda 2 — leaf exclusivo e interfaz nativa

Estado ready para revisión independiente ANTES de nuevo runtime. Recibo attempt02 leído: fallo real en 16s, AnalysisException INVALID_PARAMETER_VALUE.LOCATION_OVERLAP por raw_fs.mkdirs(storage_root), padre /data de tablas externas registradas en attempt01. No se consultará ni creará ese padre por filesystem. Se valida raíz exacta textualmente y prepare_test_leaf consulta exclusivamente <data>/<run_id>: FileNotFoundError o java.io.FileNotFoundException permiten crear ese leaf; existencia aborta; permisos, LOCATION_OVERLAP y cualquier otro error se propagan. No se borran ni alteran datos/tablas anteriores.

Revisión del proxy local: YA preservaba notebook=dbutils.notebook nativo, junto con jobs/widgets. Se añadió test que ejecuta el assignment real del notebook para comprobar identidad de esas interfaces; el proxy genérico de CA14 es independiente y no se usa para notebook.exit. Se mantienen salida estructurada después de finalize_inventory, shuffle=4 solo sintético, inventario genérico y guarda de slash final.

RED: cinco casos por ausencia del helper leaf; GREEN: preflight nuevo seguro, error Java FileNotFound, leaf existente, permisos y overlap. Prueba AST adicional exige invocación del helper y prohíbe raw_fs.ls/mkdirs(storage_root). Checks finales: 88 focalizadas / 102 totales passed; AST/JSON/sin outputs de tres notebooks passed, OpenSpec strict y diff check passed. Ninguna escritura remota por developer ni modificación de runtime/**/producción/deltas/plan.

Widgets sin cambios salvo test_run_id=runtime_attempt03. Principal sube y reviewer revisa antes de ejecutar run_all_checks completo, sin subconjuntos. Los dos intentos runtime anteriores permanecen FAILED en evidencia; este candidato no acredita runtime. Si requiere otra corrección tras nuevo fallo, informar y solicitar decisión concreta según límite de rondas, sin reintentos indefinidos ni limpieza para evadir UC.

## 11. Cierre developer tras runtime completo SUCCESS

Estado vigente: **ready para revisión independiente definitiva**. No hay cambios de código/tests/notebook desde los 102 tests locales passed. Developer leyó y validó recibos runtime/attempt03-output.json, validated-result.json y candidate-identity.json: parent run 853804030647399, task 169503786443292, result_state SUCCESS, ejecución 1017s + setup1s, run_id runtime_attempt03. Matriz contiene exactamente CA01–CA14 y todos passed. SHA-256 local del notebook coincide con el registrado B59363D997EC510B0AE845133EDE8C0D3D375295ECF04A717B32FE7DF7895CC1; module_hashes_match=true en evidencia principal.

Runtime real: DBR16.4, Spark3.5.2, Python3.12.3, Delta integrada DBR16.4; shuffle.partitions4 solo sesión de prueba; CREA_DEV, identidad srinconr@creasistemas.com, cluster1020-210854-9y22c5h7. Catálogo exclusivo crea_cotizaciones_test_20261020_01a15a7c, datos bajo raíz aprobada /data/runtime_attempt03. No recursos naturapet* modificados. La ejecución y administración de recursos corresponden al principal; developer solo contrastó recibos. Los intentos01/02 fallidos permanecen como historial, ahora superados por suite completa SUCCESS del candidato corregido.

Se completan tareas2.1–4.2 gracias a runtime de parser/evidencia/esquemas/merge/replay/cuarentena/fallos/archivo/regresión, además de locales. Tarea5.4 queda para reviewer final. La ejecución de5.2 pasó; su casilla espera también inventario versionado y recibo de terminación del cluster, incluidos expresamente en la tarea y bajo responsabilidad principal. No se afirma terminación antes de su evidencia. Revisión de proxy nativo y leaf seguro permanece cubierta local/runtime.

Checks de cierre: OpenSpec strict y git diff --check, sin repetir runtime o tests ya válidos de código inalterado. Solo tasks.md y append a evidencia/este handoff en este cierre. Sin sync/archive/commit/push ni escritura en runtime/**.
