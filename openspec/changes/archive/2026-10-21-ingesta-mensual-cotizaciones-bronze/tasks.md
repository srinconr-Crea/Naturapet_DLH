# Tasks

La implementación fue autorizada posteriormente; las casillas reflejan su estado verificable y no solo existencia de código. Checks y casos en design.md §8; revisión operativa de aislamiento autorizada en §9. No marcar runtime passed por pruebas locales.

## 1. Contrato y clasificación

- [x] 1.1 Crear `src/common/cotizaciones_contract.py` con 20 campos, tipos/nulos, códigos y parsing; verificar CA04/06/07/08 con `tests/test_cotizaciones_contract.py` y casos sintéticos en `tests/fixtures/cotizaciones/cases.json`, incluyendo límites INT/DECIMAL y original recuperable.
- [x] 1.2 Añadir clasificación y alertas CA09/10, fórmulas HALF_UP/tolerancia/nulos y duplicados normalizados CA05; verificar tests de negativos/cero, 0.01/0.02, A/A consolidado y A/A/B rechazado, documentando decisiones técnicas en evidencia.

## 2. Lectura y evidencia

- [x] 2.1 Crear adaptador `src/common/cotizaciones_ingestion.py` para CSV UTF-8/quotes/multiline, checksum y registro determinista; verificar CA01/02/03 con fixtures Unicode, comillas, columnas desplazadas, nombre/periodo incorrectos y referencia cruda estable, sin collect de datos al driver.
- [x] 2.2 Implementar preservación inmutable y evidencia de todos los originales/conversiones, incluidos consolidados; verificar identidad estable en reparticionamiento/reintento y recuperación de payload previo después de actualizar PK; registrar resultado en evidencia.

## 3. Persistencia e idempotencia

- [x] 3.1 Añadir rutas específicas en config y Delta principal estable entre años; verificar CA12 por merge cotizacion_id y pruebas de enero/febrero/año siguiente, conservar ausentes y detener destino incompatible sin migración automática.
- [x] 3.2 Implementar cuarentena, file_audit, failed_files y record_evidence por rutas Delta `_control/cotizaciones`, sin registro de negocio UC; verificar CA11/13 por una incidencia por registro, lista completa de errores y salida todo rechazado, con pruebas en `tests/test_cotizaciones_ingestion.py`.
- [x] 3.3 Implementar etapas, reserva/secuencia de recepción, recuperación previa a nuevos contenidos y SUCCESS tras conciliación; verificar leídos=aceptados únicos+rechazados+consolidados, fallos tras cada escritura, fallo doble de log y no archivo; documentar etapas y resultados.
- [x] 3.4 Implementar replay completado sin reescritura de principal/cuarentena y corrección por contenido nuevo; verificar A->B->replay A, renombrado mismo hash, mismo nombre distinto hash e intento parcial antiguo sin reversión; conservar trazabilidad de cada recepción.

## 4. Integración y archivo

- [x] 4.1 Modificar runner y notebooks comerciales Bronze según manifiesto, con dispatch antes de diccionario genérico y parámetro opcional cotizaciones_month; verificar CA01/14 y regresión local de otra entidad comercial/shared, sin alterar normalizador genérico ni incorporar la HU anterior.
- [x] 4.2 Integrar archivo especializado por hash y conciliación, preservando archivo genérico; verificar CA13 con fuente cambiada, histórico igual/distinto, colisión de nombre y fallo entre movimiento/actualización de estado; actualizar evidencia con resultados.
- [x] 4.3 Ejecutar `.\.venv\Scripts\python.exe -m pytest tests/test_cotizaciones_contract.py tests/test_cotizaciones_ingestion.py -q` y `.\.venv\Scripts\python.exe -m pytest tests -q`; registrar comandos, resultados y candidato en handoff-developer, distinguiendo dobles de runtime.

## 5. Integración Spark y revisión independiente

- [x] 5.1 Adaptar guardas y metadatos del notebook `notebooks/comercial/bronze/tests/validate_cotizaciones.ipynb` al catálogo exacto crea_cotizaciones_test_20261020_01a15a7c y raíz aprobada de design §9, separando managed/data y prohibiendo naturapet*; verificar JSON/celdas y pruebas negativas locales de catálogo/ruta antes de ejecutar. Reabierta por nueva restricción de aislamiento, sin invalidar la suite funcional ya construida.
- [x] 5.2 Ejecutar notebook completo con aislamiento y compute temporal expresamente autorizados en design §9; registrar versiones/IDs y exigir aserciones de datos/esquemas, replay, fallos y regresión passed. Crear/actualizar inventario-recursos.md incluso ante fallos; terminar clúster al final y verificar su estado, conservar warehouse/catálogo/fixtures/workspace para inspección. Si falta recurso/permiso efectivo, registrar not_run/blocked sin sync/archive.
- [x] 5.3 Con autorización de acceso pertinente y skills Databricks cargadas, ejecutar `databricks bundle validate --strict --target dev --profile CREA_DEV` por notebooks añadidos/modificados y registrar resultado; no usarlo como prueba Spark ni desplegar/ejecutar jobs.
- [x] 5.4 Reviewer independiente revisa candidato/manifiesto, repite checks pertinentes y ejecuta openspec-verify-change; entregar handoff-reviewer con evidencia y resolver hallazgos antes de declarar resultado favorable.
- [x] 5.5 Ejecutar `openspec.cmd validate ingesta-mensual-cotizaciones-bronze --strict` y `git diff --check`; revisar también archivos nuevos y registrar matriz CA01–14, resultados reales y pendientes. Kit no aplica salvo expansión autorizada del alcance.

## Workflow follow-up

- Tras todos los checks requeridos passed y revisión favorable, reviewer ejecuta openspec-sync-specs solo para bronze-ingestion/data-contracts y presenta diff; no sincronizar con runtime failed/blocked/not_run.
- Principal prepara candidato, manifiesto final y borrador `docs/hu/ingesta-mensual-cotizaciones-bronze/pr.md`, muestra rama/remoto/base y solicita aprobación humana específica de archive y, por separado en alcance explícito, commit/push. Esta propuesta no concede esa autorización.
- Solo tras autorización humana explícita para este candidato, reviewer ejecuta openspec-archive-change; verificar movimiento de este cambio y specs previstas, sin archivar otros cambios.
- Solo principal hace commit/push autorizado en feature/hu-cotizaciones-bronze hacia origin, base develop. La persona solicitó explícitamente crear el PR GitHub al terminar: crear/verificar PR tras checks/revisión y alcance de publicación vigente, sin inferir aprobación de archive del candidato final. Sin merge, deploy, force-push o borrado de rama.
