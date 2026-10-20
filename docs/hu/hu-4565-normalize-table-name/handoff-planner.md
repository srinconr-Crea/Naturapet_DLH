# Handoff — hu-4565-normalize-table-name / planner

## 1. Identidad y estado
- HU/cambio: HU-4565 / hu-4565-normalize-table-name.
- Rol e identificador real del agente: planner / /root/planner_hu4565; perfil gpt-6.1-sol, low.
- Estado: ready (planificación, no implementación).
- Candidato: HEAD local 22e33e9336c8053b5277b31da8168d22debb9c73, rama feature/hu-4565; siete archivos nuevos de planificación/evidencia, listados abajo.

## 2. Entrada y alcance

Solicitud humana HU-4565; autorización de rama desde local «si, hasla desde el local», transmitida por principal. Base remota origin/develop c5efcf154c7e56101e6dd6c3ea830f6512e6b184 según preflight principal. Setup en commit separado local, todavía no integrado a develop. No cambiar rama ni publicar.

Leídos: .codex/agents/planner.toml; .agents/skills/openspec-propose/SKILL.md; AGENTS.md; docs/proyecto.json; docs/contexto-proyecto.md; docs/buenas-practicas/general.md y python.md; README.md; docs/entrega-git.md; docs/plantillas/handoff.md y evidencia-hu.md; openspec/config.yaml; openspec/specs/bronze-ingestion/spec.md; src/common/schema.py; src/common/notebook_runner.py (sección de consumo de normalizador); src/utilities/file_ingestion.py (homónimo); tests/test_project_structure.py; conf/environments/dev.yml; conf/jobs/monthly_file_refresh.yml. Inventario y referencias buscadas con rg en conf/resources/jobs/databricks.yml/src/common/src/utilities. tests/test_normalize_table_name.py no existe: lectura inicial reportó ausencia, prevista como alta.

Escrituras limitadas a openspec/changes/hu-4565-normalize-table-name/ y docs/hu/hu-4565-normalize-table-name/. Sin ambigüedad material pendiente; explore/update no ejecutados.

## 3. Resultado

Archivos nuevos exactos:
- openspec/changes/hu-4565-normalize-table-name/.openspec.yaml
- openspec/changes/hu-4565-normalize-table-name/proposal.md
- openspec/changes/hu-4565-normalize-table-name/design.md
- openspec/changes/hu-4565-normalize-table-name/specs/bronze-ingestion/spec.md
- openspec/changes/hu-4565-normalize-table-name/tasks.md
- docs/hu/hu-4565-normalize-table-name/handoff-planner.md
- docs/hu/hu-4565-normalize-table-name/evidencia.md

Criterios cubiertos por plan/delta: tres extensiones finales sin distinguir mayúsculas; firma y caja preservadas; extensión antes de sufijo mensual exacto/informado; desconocidas y puntos internos conservados; fixtures parametrizadas locales; exclusiones respetadas. No se afirma cobertura ejecutada.

Decisiones: una eliminación por fase, sin segundo pase; month None/vacío/omitido conserva sufijo; no validar rango de mes ni aceptar tipos nuevos de file_name; homónimo utilities fuera de alcance. Se conserva contrato completo del lector/detector en requisito modificado.

## 4. Validacion

Fecha 2026-10-19, entorno local, evidencia en evidencia.md:
- passed: openspec list --json (raíz nearest válida y lista inicial vacía).
- passed: openspec context --json (root.path del checkout).
- passed: openspec list --specs; openspec show bronze-ingestion --type spec --json --no-scenarios; openspec show bronze-ingestion --type spec.
- passed: openspec new change hu-4565-normalize-table-name; status e instructions proposal/specs/design/tasks --json en orden de dependencias.
- passed: openspec validate hu-4565-normalize-table-name --strict (Change is valid).
- passed: openspec status --change hu-4565-normalize-table-name --json y estado textual (4/4 done; isPlanningComplete=true).
- passed: git diff --check (sin salida); no prueba archivos untracked, cuya lectura y hashes se guardan en evidencia.
- not_run: pytest específico y suite tests, pendientes de implementación autorizada.
- not_applicable: kit-structure (kit/contexto intactos), bundle-dev (bundle/rutas/resources intactos), runtime Spark (solo lógica de cadenas).

## 5. Hallazgos y siguiente paso

Presentar artefactos a la persona y esperar una NUEVA solicitud humana de apply según openspec-propose. No se ejecutó apply, verify, sync, archive, commit, push ni PR. Al recibir apply, developer usa manifiesto de design.md y registra pruebas; reviewer independiente verifica antes de sync. Archivo/publicación requieren aprobación posterior.

## 6. Configuracion y extensiones usadas

Skill openspec-propose y CLI OpenSpec reales. Sin MCP, hooks ni extensiones adicionales; sin Databricks CLI o runtime. Perfil CREA_DEV/target dev conservados, no utilizados.
