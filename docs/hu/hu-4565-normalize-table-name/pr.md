# Borrador de PR — hu-4565-normalize-table-name

## 1. Identidad y enlace

- Rama origen: feature/hu-4565.
- Rama destino: develop.
- Remoto: origin, https://github.com/srinconr-Crea/Naturapet_DLH.git.
- Proveedor: GitHub, formulario manual; no crear PR por API.
- Formulario previsto: https://github.com/srinconr-Crea/Naturapet_DLH/compare/develop...feature/hu-4565?expand=1
- Estado: archivo y commit/push autorizados por respuesta humana «adelante» del 2026-10-20. Archivo completado; commit/push pendientes al guardar este borrador. El recibo y SHA se entregan en la respuesta final. El enlace no acredita un PR creado.

## 2. Título para copiar

fix: normalizar extensiones y sufijo mensual de nombres de tabla (HU-4565)

## 3. Descripción para copiar

HU-4565 corrige normalize_table_name para retirar una extensión final CSV, JSON o Parquet sin distinguir mayúsculas y después un único sufijo mensual exacto. Por ejemplo, fact_ventas_01.JSON con mes 01 devuelve fact_ventas. Conserva la caja del nombre, puntos internos y extensiones desconocidas.

Incluye 32 casos de prueba y actualiza el contrato bronze-ingestion. El reviewer independiente verificó los 10 escenarios y sincronizó el requisito completo conservando las reglas del detector y lector. Pruebas locales: 32 específicas y 46 totales aprobadas; validación estricta del cambio aprobada; validación de specs: 10 passed, 0 failed, con avisos de longitud documentados. Sin cambios Spark ni pruebas de runtime requeridas.

Cambio OpenSpec archivado con autorización humana en openspec/changes/archive/2026-10-20-hu-4565-normalize-table-name/. La rama incluye además el commit separado de preparación Crea 22e33e9336c8053b5277b31da8168d22debb9c73, todavía ausente de origin/develop c5efcf154c7e56101e6dd6c3ea830f6512e6b184, referencia confirmada tras fetch. La aprobación humana de publicación incluye expresamente este commit previo.

## 4. Candidato y alcance de aprobación

Candidato funcional identificado por SHA256 en handoff-reviewer.md:

- src/common/schema.py: 23D072F906EACDBBA8F6919DE11B9AEAE4A280F15D29B3540A4DD66D68228F27.
- tests/test_normalize_table_name.py: 1BC8EC858B5F5907E73D4A12A30D0F60E310EC8B05A7506A8BC63F4A7753B69A.
- openspec/specs/bronze-ingestion/spec.md: 08A7B3335631CAFE03F37272A53D518337D22FB6C458D927A10A9BD3C805F7A7.

Archivos previstos para versionar:

- src/common/schema.py
- tests/test_normalize_table_name.py
- openspec/specs/bronze-ingestion/spec.md
- openspec/changes/hu-4565-normalize-table-name/.openspec.yaml
- openspec/changes/hu-4565-normalize-table-name/proposal.md
- openspec/changes/hu-4565-normalize-table-name/design.md
- openspec/changes/hu-4565-normalize-table-name/tasks.md
- openspec/changes/hu-4565-normalize-table-name/specs/bronze-ingestion/spec.md
- docs/hu/hu-4565-normalize-table-name/evidencia.md
- docs/hu/hu-4565-normalize-table-name/handoff-planner.md
- docs/hu/hu-4565-normalize-table-name/handoff-developer.md
- docs/hu/hu-4565-normalize-table-name/handoff-reviewer.md
- docs/hu/hu-4565-normalize-table-name/pr.md

Los cinco archivos del cambio activo ya se movieron a openspec/changes/archive/2026-10-20-hu-4565-normalize-table-name/ mediante archive autorizado; las rutas activas de la lista anterior se versionarán en esa ubicación de archivo. Sus hashes y los del candidato funcional permanecen idénticos al aprobarse. Se incluyen el recibo de aprobación y metadatos de archivo/publicación previstos.

Se excluye la modificación ajena sin commit en .codex/config.toml. No merge, deploy ni borrado de ramas. Commit previsto: fix: normalize table names for HU-4565. Publicación solicitada: commit del alcance indicado y push ordinario a origin/feature/hu-4565; destino del formulario manual develop. Antes de publicar se comprobarán remoto y commits nuevamente.
