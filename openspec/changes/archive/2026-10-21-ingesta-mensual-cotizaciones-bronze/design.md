# Design

## Context

Ver motivación en proposal.md. Estado inspeccionado: `io.py:83` infiere CSV; `schema.py:81` castea y `schema.py:108` escoge una fila por PK. `notebook_runner.py:104` crea UUID por lectura y `:145` cuenta después de deduplicar. `delta_load.py:155` selecciona SUCCESS pendientes; archivo verifica existencia, no contenido. `config.py:55` construye rutas anuales. No hay contrato cotizaciones versionado; se recibió de la persona. En esta rama `normalize_table_name` solo retira `.csv` literal: no incorporar la mejora de extensiones de otra HU.

La complejidad de persistencia parcial, identidad y varias salidas hace necesario este diseño. Schema spec-driven; planificación únicamente. Rama `feature/hu-cotizaciones-bronze`, base remota informada `origin/develop@c5efcf154c7e56101e6dd6c3ea830f6512e6b184`, HEAD inicial comprobado `6029d05c3d47ccc0139cee4aef3c3df3fb50155c`.

## Goals / Non-Goals

**Goals:** camino específico temprano para cotizaciones, evidencia cruda independiente de casts, clasificación exhaustiva, replay seguro y conciliación verificable con fallos parciales. Funciones de contrato testeables localmente, adaptación Spark y Delta separada.

**Non-Goals:** normalizador genérico, cambios a Silver/Gold, otros contratos, CI, nuevos schedules/jobs, configuración global o permisos. No cargar el diccionario ADLS durante planificación. No declarar atomicidad multi-tabla. Sin deploy ni ejecución de jobs como parte implícita de apply.

## Decisions

### 1. Contrato y dispatch acotado

Decisiones humanas: las 20 columnas constan en delta data-contracts. PK `cotizacion_id`, update/insert y conservar ausentes; sin snapshot mensual. Las tres columnas temporales nulas se rechazan; resto nullable con alerta cuando impida controles. Cantidad y vigencia <=0 permanecen con alerta. Comparar duplicados después de normalizar: iguales consolidan una fila; distintos rechazan todas las ocurrencias.

Propuesta técnica revisable mediante aprobación del plan: `cotizaciones_contract.py` contiene esquema, parsing escalar y códigos; `cotizaciones_ingestion.py` adapta Spark y persistencia. Detectar comercial + patrón de cotizaciones antes de diccionario/casts/selección genéricos. La excepción tiene contrato propio y no requiere editar el diccionario externo. Si existe una tabla previa incompatible, fallar con diagnóstico; no migrarla silenciosamente. Otras tablas siguen los módulos actuales sin cambiar su lógica.

### 2. Ventana y nombre

Año viene del parámetro y carpeta anual; MM del sufijo coincide exactamente con carpeta 01–12. Agregar parámetro opcional `cotizaciones_month` al notebook comercial; vacío significa todos los meses pendientes del año seleccionado, compatible con job existente que solo pasa año. Valor MM filtra cotizaciones exclusivamente y se coteja con carpeta; no filtra otras entidades. No inferir año del nombre. Orden determinista por periodo/ruta; contenido nuevo encontrado después se trata como corrección por orden de recepción, sin inferir una fecha de versión de negocio.

Rechazar nombre/periodo incorrectos mediante log de archivo; no derivar tabla alternativa. Archivos vacíos o sin encabezado/esquema utilizable: FAILED de archivo. Las 20 columnas deben existir una sola vez; columnas adicionales se preservan en original y producen aviso de esquema, sin publicarlas como nuevas columnas de negocio. No habilitar evolución global de esquema.

### 3. Lectura cruda e identificación estable

Propuesta técnica: CSV UTF-8 estricto, delimitador coma, quote doble y escape mediante doble comilla, encabezado explícito; admitir CRLF/LF, BOM inicial y registros entrecomillados con saltos de línea. Parser conserva ordinal lógico y límites verificables del registro; no usar `monotonically_increasing_id` ni orden de particiones para identidad. Detectar exceso/falta de campos antes de proyectar esquema. Si el framing no permite identificar registros, fallar archivo preservando bytes; si el registro es delimitable, cuarentenarlo con CSV_MALFORMED.

Calcular SHA-256 sobre bytes, no nombre. Copiar a evidencia inmutable por hash antes de transformaciones y comprobar hash; verificar que la fuente no cambió antes de archivo. Identidad de carga lógica: entidad + periodo + hash; UUID por intento separado. Identidad de registro: identidad lógica + ordinal del registro original, conservada para duplicados idénticos. Payload almacena campos originales, ordinal y referencia verificable al original completo. Los originales de todas las recepciones se conservan aunque principal se actualice.

Usar operaciones distribuidas/lectura por partición; no recopilar filas ni archivos completos al driver. Medir tamaño en runtime y validar estrategia del parser; error explícito ante límites de recursos, sin truncamiento. Alternativa descartada: inferencia Spark seguida de casts, porque pierde tokens inválidos y original.

### 4. Conversión y clasificación

IDs trim externo y vacío a NULL, conservando ceros. Fechas por tres formatos exactos y validación calendario/periodo, sin completar. fecha_id ocho dígitos, mes_carga exacto. Registrar transformaciones como lista campo/original/normalizado/regla.

Decisión técnica propuesta: INT de 32 bits con léxico entero con signo opcional; decimales con signo opcional y punto, sin miles, porcentaje, NaN, infinito ni notación exponencial. Trim externo numérico explícito y trazado. Vacío/espacios a NULL en campos nullable; cadena literal NULL no se interpreta como nulo. Rechazar overflow y fracciones no representables en escala; ceros fraccionarios excedentes son representables exactamente y pueden normalizarse sin pérdida. No redondear entradas para hacerlas caber. Evaluaciones monetarias con intermedios decimales amplios y redondeo HALF_UP a 2 decimales por ecuación; diferencia absoluta >0.01 alerta. Overflow aritmético de control se registra como alerta no evaluable, sin sustituir el importe original.

Agrupar por PK normalizada con fingerprint de las 20 columnas tipadas usando serialización sin ambigüedad de NULL/campos; metadatos originales no participan. Errores técnicos se conservan antes de agrupar; una fila técnicamente inválida nunca se convierte en aceptada por equivalencia. Si una PK no vacía tiene valores normalizados diferentes, todas las ocurrencias incluyen DUPLICATE_PK, además de sus errores propios. Solo grupos totalmente válidos e idénticos consolidan; si un grupo contiene inválidos, sus ocurrencias quedan rechazadas para no elegir representante de un grupo incierto. Cada registro ocupa una categoría de conciliación; originales consolidados quedan enlazados al representante de menor ordinal, sin perder evidencia.

Alertas tipadas y evaluaciones incompletas acompañan principal en `_np_quality_alerts`; errores en cuarentena. Estados y moneda se comparan con valores exactos confirmados, sin convertirlos a mayúsculas ni traducirlos. No imponer FK válidas en Bronze. Descuento cero y tasas cero explícitos se conservan; no imputar nulos.

### 5. Delta, rutas y auxiliares

Propuestas de ubicación relativas a configuración vigente, sin cambiar storage/catalog/schema: principal `${bronze_area_root}/fact_cotizaciones`, FQN `${catalog}.${bronze_schema}.fact_cotizaciones`. Ubicación estable entre años para una única tabla; particiones técnicas de año/mes conservadas. Es entidad nueva: no reubicar tablas existentes; si ya existe ubicación distinta, detener y revisar migración antes de escribir.

Auxiliares Delta **por ruta, sin registro como tablas de negocio UC** bajo `${bronze_area_root}/_control/cotizaciones/`: `quarantine`, `file_audit`, `failed_files`, `record_evidence`. Esto evita que los notebooks Silver que enumeran `SHOW TABLES` ingieran cuarentena/logs, sin tocar Silver. Son tablas Delta consultables por ruta con los permisos existentes; no crean nuevo catálogo ni schema.

Originales inmutables: `${bronze_area_root}/_control/cotizaciones/originals/<sha256>/<nombre-original>`. Archivo histórico propuesto: `${historic_area_root}/<anio>/<MM>/cotizaciones/<sha256>/<nombre-original>`. Se conserva nombre físico y versiones de contenido distintas; no sobrescribir archivos ya existentes. Original idéntico bajo otro nombre puede compartir contenido, manteniendo las referencias de llegada en auditoría.

`record_evidence`: file_id, record_id, ordinal, payload original/referencia, valores normalizados, conversiones, categoría y errores/alertas. Merge por file_id+record_id. `quarantine`: mismos identificadores, carga lógica/intento, periodo, fuente, timestamp y lista de errores, merge por file_id+record_id; múltiples errores no generan filas extra. `file_audit`: identidad lógica y estado, checksum, esquema/versión de contrato, métricas, etapa, secuencia de recepción estable, rutas originales/históricas, intentos y timestamps; merge por file_id. `failed_files`: append idempotente por intento+etapa con error técnico y referencias, sin payload sensible en mensajes de ejecución. No usar auditoría genérica SUCCESS para cotizaciones.

### 6. Reintento y publicación lógica

Secuencia propuesta: verificar ventana y checksum -> preparar estado PROCESSING y copia cruda -> materializar evidencia/clasificación -> merge principal -> merge cuarentena -> persistir auditoría con conteos/etapas -> releer y conciliar -> marcar SUCCESS -> permitir archivo separado. Incluso con cero aceptados asegurar que tablas salidas existen con esquema y conteos correctos. Leídos son registros de datos, excluyendo encabezado; `leídos = aceptados únicos + rechazados por registro + consolidados`, contando grupo conflictivo íntegramente como rechazado.

No hay transacción multi-tabla. Antes de aceptar contenido nuevo, recuperar cualquier intento parcial anterior de la entidad; la ingesta falla con pendiente explícito si no puede recuperarlo. Asignar secuencia persistida estable al primer intento, reutilizarla al reintentar y proteger actualizaciones por versión de recepción para impedir regresión frente a escrituras posteriores. Camino comercial serializado: mantener max_concurrent_runs=1 existente y rechazar intentos solapados mediante control de estado/reserva optimista Delta de entidad; no depender solo del schedule. Una recuperación de auditoría no reejecuta merge si su etapa está persistida y verificada.

Contenido ya SUCCESS se reconoce por file_id y no reescribe principal/quarentena; verifica evidencia/conciliación almacenada y atiende solo archivo pendiente. Así A SUCCESS -> B corrección -> replay A no revierte B. El conteo por archivo refleja lo aceptado de esa recepción, no el delta del total global ni los valores actuales después de B. Misma PK en nuevos archivos de contenido distinto actualiza según orden de recepción; no se promete resolver correcciones nunca vistas por fecha de negocio.

Cualquier fallo de escritura deja el intento FAILED en audit cuando sea posible, agrega failed_files y propaga error; si falla también el log, propagar fallo visible con etapa/hash y sin archivo. Al reiniciar, PROCESSING pendiente se considera recuperación, no SUCCESS. Auditoría SUCCESS antigua no mueve otro contenido de igual nombre: volver a verificar checksum. Histórico igual permite reconciliar movimiento ya hecho; histórico distinto en ruta esperada es error, no éxito por existencia. Si se mueve y falla actualizar estado, reintento verifica hash y completa estado sin duplicar datos.

### 7. Manifiesto de implementación propuesto

Este manifiesto autoriza operaciones solo tras una NUEVA solicitud humana de apply; no es escritura realizada.

| Ruta concreta | Operación prevista | Límite |
| --- | --- | --- |
| src/common/cotizaciones_contract.py | Crear | Contrato, parsing/normalización, códigos y clasificación pura |
| src/common/cotizaciones_ingestion.py | Crear | Adaptador Spark/Delta, evidencia, estado, cuarentena y archivo especializado |
| src/common/notebook_runner.py | Modificar | Dispatch comercial antes de inferencia/diccionario; mantener rama genérica; incluir resumen especializado |
| src/common/config.py | Modificar | Resolver rutas estables específicas, sin cambiar rutas genéricas |
| notebooks/comercial/bronze/load_to_delta.ipynb | Modificar | Widget opcional cotizaciones_month y paso explícito al runner; sin salidas |
| notebooks/comercial/bronze/archive_to_historic.ipynb | Modificar | Integración de archivo especializado sin cambiar archivo genérico |
| tests/test_cotizaciones_contract.py | Crear | Pruebas puras de reglas/errores/límites |
| tests/test_cotizaciones_ingestion.py | Crear | Orquestación, fallos inyectados, replay/conciliación y dispatch con dobles |
| tests/fixtures/cotizaciones/cases.json | Crear | Escenarios sintéticos; generador de CSV usa biblioteca estándar y tmp_path |
| notebooks/comercial/bronze/tests/validate_cotizaciones.ipynb | Crear | Integración sintética Spark/Delta fuera de jobs, con guardas de entorno/rutas |
| docs/hu/ingesta-mensual-cotizaciones-bronze/evidencia.md | Actualizar | Resultados reales, sin secretos ni datos reales |
| docs/hu/ingesta-mensual-cotizaciones-bronze/handoff-developer.md | Crear | Candidato y resultados del developer |
| docs/hu/ingesta-mensual-cotizaciones-bronze/handoff-reviewer.md | Crear | Revisión independiente y diff sync |
| docs/hu/ingesta-mensual-cotizaciones-bronze/pr.md | Crear por principal | Borrador de entrega, sin publicación implícita |

Sin cambios a schema.py/io.py/validation.py/delta_load.py genéricos, src/utilities/, Silver/Gold, resources/, databricks.yml, conf/, .github/, skills o perfiles. Si implementación necesita ampliar manifiesto, revisar plan antes de hacerlo. Sync posterior afecta solo `openspec/specs/bronze-ingestion/spec.md` y `openspec/specs/data-contracts/spec.md` tras reviewer favorable; archive mueve solo este cambio tras autorización específica.

### 8. Plan de validación ejecutable

Ahora, planificación: `openspec.cmd validate ingesta-mensual-cotizaciones-bronze --strict` y `git diff --check`; revisar además archivos nuevos porque git diff no los incluye. Kit no aplica: no modifica kit/contexto/perfiles. Pytest no aplica a la redacción; durante apply es obligatorio ` .\.venv\Scripts\python.exe -m pytest tests -q` y focalizado ` .\.venv\Scripts\python.exe -m pytest tests/test_cotizaciones_contract.py tests/test_cotizaciones_ingestion.py -q`.

Fixtures: Unicode/quotes/multiline, columnas extra/faltantes, PK blanca/ID con ceros, fechas en tres formatos/leap/imposible/fuera de mes, fecha_id y mes nulos/discrepantes, enteros fraccionales/overflow, tres tokens inválidos CA08, decimales límite/exceso de escala, reglas negativas/cero/nulos, tolerancias 0.01/0.02 y mitad de centavo. Mezcla exacta de cinco filas (2 únicas aceptadas + 2 rechazadas + 1 consolidada), grupos A/A/B conflictivos, filas con varios errores y archivo todo rechazado.

Regresión local: módulos/lectores genéricos mantienen contratos con otra entidad comercial y shared; no exigir el normalizador de otra HU. Mock comprueba llamadas y estados, nunca semántica Spark. `bundle-dev` aplicará si cambian rutas de notebooks/configuración o se añade notebook: `databricks bundle validate --strict --target dev --profile CREA_DEV`, futuro y con autorización de acceso correspondiente; cargar skills Databricks antes de usar CLI.

Runtime requerido, **not_run**: ejecutar manualmente `notebooks/comercial/bronze/tests/validate_cotizaciones.ipynb` completo en dev con sesión Spark/Delta compatible, perfil CREA_DEV, después de autorización humana explícita de ejecución y escrituras sintéticas. No lanzar job productivo ni desplegar bundle. Registrar host/identidad, DBR/Spark/Delta/Python reales, run_id de prueba, schema/ruta aislados aprobados y parámetros; no fijar DBR/computación inexistentes. El notebook exige `allow_synthetic_writes=true`, catálogo dev confirmado y schema/storage de prueba explícitos aprobados, sin fallback al destino operativo. Importa módulos del candidato y ejecuta `run_all_checks` de su propia suite; salida por assert y reporte por CA. Comando CLI remoto queda not_run/no definido hasta seleccionar mecanismo/compute autorizado, sin inventar job_id.

Suite runtime: comparar esquemas/DataFrames (assertDataFrameEqual/assertSchemaEqual si versión disponible, o igualdad bidireccional y esquema explícitos); verificar metadatos de tabla externa, particiones/ruta única entre enero/febrero y cambio de año. Cargar A, replay A, B corrección, replay antiguo A, mismo nombre contenido nuevo, renombrado mismo hash, duplicados y todo rechazado. Inyectar fallo tras evidencia, principal, cuarentena, auditoría, SUCCESS y movimiento; fallar también failed_files y comprobar error visible/no archivo. Reintentar, conciliar IDs/conteos y verificar no reversión ni duplicados. Probar fuente cambiada antes de archivo, destino igual/distinto y ausencia doble. Ejecutar otra entidad comercial y shared por el camino genérico en aislamiento; comprobar que auxiliares no aparecen como negocio UC. No borrar fixtures/tablas automáticamente fuera del namespace de prueba autorizado; acordar limpieza explícita.

Resultados requeridos antes de sync/archive: tests locales y runtime passed; bundle passed cuando aplique. Un blocked/not_run no se convierte en passed ni se suple con mocks.

### 9. Revisión operativa autorizada — aislamiento de pruebas

Esta sección sustituye la referencia de §8 a catálogo dev y compute/namespace pendientes. Autorización humana: «Sí, actualizar el plan y continuar» y «Sí, warehouse existente y clúster temporal». No cambia lógica comercial ni deltas CA01–14.

- Catálogo nuevo exacto: `crea_cotizaciones_test_20261020_01a15a7c`; schemas independientes por caso. Prohibir creación/escritura/eliminación en cualquier catálogo `naturapet*`, incluidos nombres heredados de get_config. El notebook debe sustituir todos los literales naturapet_dev por el catálogo aprobado y rechazar cualquier otro catálogo antes de efectos remotos.
- Raíz autorizada exacta: `abfss://demo@demodldb.dfs.core.windows.net/_tests/cotizaciones/20261020_01a15a7c`, dentro de external location existente `datalake-az`. Separar managed root `<root>/managed` de fixtures/tablas externas/evidencia `<root>/data`; ninguna tabla externa ni payload ocupará la raíz managed o un descendiente suyo. Guardas por igualdad de raíz aprobada y contención normalizada de cada ruta, no por substring únicamente. No crear external locations, credenciales, grants ni cambiar ownership.
- Warehouse existente confirmado: `naturapet_serverless_wh`, ID `dd74907a9f5cb481`, STOPPED en preflight del principal. Se autoriza usarlo para verificaciones SQL complementarias y conservarlo; no demuestra ejecución Python/RDD. No renombrarlo ni eliminarlo.
- Compute aprobado: clúster clásico temporal single-node dedicado a `srinconr@creasistemas.com`, DBR `16.4.x-scala2.12` / Spark 3.5.2, nodo `Standard_DS3_v2` (4 cores, 14 GiB), auto-termination 10 minutos. Ejecución mediante one-time submit, sin job persistente ni despliegue del bundle. Comprobar versiones efectivas en ejecución y registrar IDs reales. Terminar el clúster al finalizar incluso si falla la suite; no inferir que ya se creó por estar autorizado.
- Checkout/notebook remoto de pruebas: `/Users/srinconr@creasistemas.com/crea_tests/20261020_01a15a7c/checkout`. Cargar únicamente candidato necesario sin secretos, usando perfil CREA_DEV y host verificado; no sobrescribir rutas operativas.
- Manifiesto delta de implementación: modificar solo guardas/configuración/metadatos del notebook `notebooks/comercial/bronze/tests/validate_cotizaciones.ipynb` y sus comprobaciones locales necesarias; no alterar reglas de ingesta. Actualizar evidencia e inventario en `docs/hu/ingesta-mensual-cotizaciones-bronze/`.
- Inventario obligatorio `docs/hu/ingesta-mensual-cotizaciones-bronze/inventario-recursos.md`: por recurso registrar nombre/ID/URL o ruta exacta, creado o preexistente, operación/estado real, persistencia y procedimiento de eliminación. Incluir catálogo, schemas, tablas/Delta por ruta, raw/originales/cuarentena/auditoría/histórico, workspace/notebook, clúster, ejecución y warehouse. Actualizar incrementalmente incluso ante fallo. Conservar catálogo, fixtures y workspace para inspección; informar limpieza propuesta sin ejecutarla automáticamente. Terminar el clúster y registrar recibo real de terminación. Warehouse permanece existente.

El principal recibió autorización expresa de crear PR GitHub al terminar, que reemplaza aquí la restricción de entrega manual. No autoriza merge/deploy ni elimina el gate de archive del candidato final. Revisar candidato, checks y diff de sync antes de solicitar esa aprobación. Runtime continúa not_run hasta evidencia efectiva; recursos autorizados no equivalen a recursos creados.

## Risks / Trade-offs

- [Varias tablas sin atomicidad] -> estados durables, idempotencia, secuencia/reserva y recuperación antes de nuevas cargas; consumidores deben considerar frontera SUCCESS para consistencia del archivo.
- [Parser crudo y tamaño de archivos] -> procesamiento fuera del driver, prueba de framing y tamaños sintéticos, medición runtime; no truncar evidencia.
- [Retención de originales y metadatos] -> mayor storage a cambio de evidencia; no programar limpieza ni inventar plazo de retención.
- [Rutas históricas específicas nuevas] -> cambio solo para cotizaciones, nombre físico preservado, checksum evita colisiones; existentes intactas.
- [Una PK sin versiones mensuales] -> correcciones reemplazan estado principal incluso si cambian mes; originales quedan en evidencia, como decidió la persona.
- [Runtime no seleccionado] -> no declarar verificación distribuida hasta permiso/entorno real; impedir sync/archive con pendiente.

## Migration Plan

Implementar en rama feature tras nueva solicitud de apply; comprobar que no existe destino incompatible en entorno autorizado antes de primera carga. Validar primero con sintéticos aislados y reviewer. Publicación/archivo requieren autorización posterior del candidato concreto; no desplegar desde esta HU. Recuperación lógica permite reintento; rollback de código no deshace escrituras. Ante regresión detener solo nuevas cargas cotizaciones, preservar raw/evidencia y reconciliar etapas antes de restaurar una versión Delta específica con autorización humana. No borrar tablas ni revertir otros dominios automáticamente.

## Open Questions

Compute/runtime y namespace se resolvieron mediante autorización de §9. Quedan solo identificadores/estados reales de recursos y ejecución, que se registrarán durante operación sin inventarlos. La revisión de aislamiento no cambia CA01–14 ni convierte pruebas pendientes en passed.
