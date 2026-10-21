# Handoff — ingesta-mensual-cotizaciones-bronze / planner

## Actualización vigente — aislamiento runtime autorizado

Estado **ready** para developer delta de guardas, autorizado mediante «Sí, actualizar el plan y continuar». Revisados proposal.md, design.md §9 y tasks.md; sin cambios de specs ni lógica comercial. Catálogo exacto crea_cotizaciones_test_20261020_01a15a7c, storage aprobado abfss://demo@demodldb.dfs.core.windows.net/_tests/cotizaciones/20261020_01a15a7c con managed/data separados. Prohibición naturapet*. Warehouse existente y clásico temporal autorizados; cluster se termina al final, catálogo/fixtures/workspace y warehouse se conservan con inventario/persistencia/limpieza documentados.

Planner modificó solo tres artefactos existentes y estos dos documentos de evidencia/handoff, sin operaciones remotas ni código. Tarea 5.1 reabierta; 5.2 pendiente. No deltas nuevos. Principal transmite autorización de crear PR al terminar; archive necesita aprobación específica del candidato final. Siguiente paso: developer adapta notebook y verifica guardas; no repetir gate de apply ya satisfecho para esa adaptación. Las secciones siguientes conservan el handoff original de planificación y su contexto histórico.

## 1. Identidad y estado

- HU/cambio: ingesta-mensual-cotizaciones-bronze.
- Agente real: /root/validar_hu_cotizaciones, planner, gpt-6.1-sol / medium (TOML low; discrepancia explícita).
- Estado: ready para revisión de planificación, sin implementación.
- Candidato: HEAD inicial 6029d05c3d47ccc0139cee4aef3c3df3fb50155c + archivos nuevos listados abajo; rama feature/hu-cotizaciones-bronze. No commit/push de planner.

## 2. Entrada y alcance

HU mensual CA01–14, contrato humano de 20 campos, decisiones de PK/update, nulos/alertas, duplicados después de normalización y log Delta fallido. Contexto y código leídos según evidencia.md. Escritura autorizada solo en openspec/changes/ingesta-mensual-cotizaciones-bronze/** y docs/hu/ingesta-mensual-cotizaciones-bronze/**. Sin datos externos, código, tests, configuración, specs principales ni operaciones remotas.

## 3. Resultado

Archivos creados:

- openspec/changes/ingesta-mensual-cotizaciones-bronze/.openspec.yaml (scaffold CLI).
- openspec/changes/ingesta-mensual-cotizaciones-bronze/proposal.md.
- openspec/changes/ingesta-mensual-cotizaciones-bronze/specs/bronze-ingestion/spec.md.
- openspec/changes/ingesta-mensual-cotizaciones-bronze/specs/data-contracts/spec.md.
- openspec/changes/ingesta-mensual-cotizaciones-bronze/design.md.
- openspec/changes/ingesta-mensual-cotizaciones-bronze/tasks.md.
- docs/hu/ingesta-mensual-cotizaciones-bronze/evidencia.md.
- docs/hu/ingesta-mensual-cotizaciones-bronze/handoff-planner.md.

CA01–14 cubiertos en escenarios y matriz de evidencia. Design distingue decisiones humanas y propuestas técnicas, manifiesto concreto, rutas derivadas de configuración, contrato de reintento/replay, auxiliar failed_files y suite sintética local/runtime. Tareas de implementación sin marcar; sync/archive/publicación son follow-up condicionado, sin simular ejecución.

## 4. Validación

2026-10-20, local: root/context/list/show/new/instructions/status exitosos; `openspec.cmd validate ingesta-mensual-cotizaciones-bronze --strict` passed, `git diff --check` passed. Detalle y límites en evidencia.md. Pytest/bundle/runtime not_run (no implementación ni entorno/permiso remoto). Kit not_applicable porque no hay cambios de kit. CLI planning complete no acredita implementación.

## 5. Hallazgos y siguiente paso

Código genérico conserva inferencia/casts/deduplicación actual (`src/common/io.py:83`, `schema.py:81`, `schema.py:108`); la propuesta añade excepción temprana específica. No incorporar cambio funcional de HU anterior. Auxiliares Delta por ruta evitan cambios Silver y contaminación de inventario de negocio. Revisar las decisiones técnicas propuestas en design, especialmente rutas estables/histórico, replay/recuperación, CSV y redondeo; no afirmarlas aprobadas antes de revisar plan.

Principal presenta artefactos y espera NUEVA solicitud humana de apply. No pasar automáticamente al developer. Runtime exige autorización futura; sin checks required passed, reviewer no sincroniza ni archiva.

## 6. Configuración y extensiones usadas

OpenSpec spec-driven, openspec-propose (antes explore), crea-orquestador. CLI local y herramientas de archivos únicamente. Perfil de referencia CREA_DEV / target dev, sin conexión ni ejecución. Sin MCP/hooks/extensiones ni subdelegación. No modelos/herramientas inventados; discrepancia de esfuerzo del rol registrada.
