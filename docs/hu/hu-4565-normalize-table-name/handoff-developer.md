# Handoff — hu-4565-normalize-table-name / developer

## 1. Identidad y estado
- HU/cambio: HU-4565 / hu-4565-normalize-table-name.
- Rol e identificador real: developer /root/developer_hu4565, rol nativo gpt-6.1-sol/low, sin subdelegación.
- Estado: ready para revisión independiente.
- Candidato: HEAD 22e33e9336c8053b5277b31da8168d22debb9c73 más diff funcional src/common/schema.py y alta tests/test_normalize_table_name.py; tareas/evidencia/handoff actualizados. Config ajena .codex/config.toml excluida y preservada.

## 2. Entrada y alcance
Nueva solicitud humana apply transmitida por principal. Rama feature/hu-4565 confirmada y conservada, excepción de base local documentada por planner/principal. Leídos AGENTS.md, .codex/agents/developer.toml completo, docs/proyecto.json/contexto-proyecto.md, generales/python, README.md, conf/environments/dev.yml, conf/jobs/monthly_file_refresh.yml, spec vigente bronze-ingestion, todos contextFiles de instructions apply (proposal/design/delta/tasks), evidencia/handoff planner, docs/entrega-git.md, plantilla handoff, src/common/schema.py y tests/test_project_structure.py.

Rutas permitidas/modificadas exactas por developer:
- src/common/schema.py: solo función normalize_table_name.
- tests/test_normalize_table_name.py: archivo nuevo.
- openspec/changes/hu-4565-normalize-table-name/tasks.md: solo checks 1.1, 1.2, 1.3, 2.1.
- docs/hu/hu-4565-normalize-table-name/evidencia.md: append evidencia developer.
- docs/hu/hu-4565-normalize-table-name/handoff-developer.md: este archivo nuevo.

## 3. Resultado
Una extensión final CSV/JSON/Parquet case-insensitive retirada antes de un único sufijo mensual exacto informado; firma, caja, puntos y desconocidas preservados; sin segundo pase. 32 casos parametrizados/directos contra función real cubren todos los escenarios delta y regresiones de límites. Código fuera de función, homónimo utilities, detector/lector/conf/bundle intactos. Sin nuevas decisiones de requisitos. Tareas developer completas 4/6; reviewer 2.2 y 2.3 pendientes.

## 4. Validacion
Entorno local, 2026-10-20; comandos/resultados/hashes en evidencia.md sección 10. Python 3.13.14, pytest 9.1.1, OpenSpec 1.14.3, Git 2.55.0.windows.5.
- RED: `.\.venv\Scripts\python.exe -m pytest tests/test_normalize_table_name.py -q`: 19 failed, 13 passed contra código anterior, exit 1 por defecto reproducido.
- GREEN mismo comando: 32 passed exit 0. `.\.venv\Scripts\python.exe -m pytest tests -q`: 46 passed exit 0. Ambos muestran warning de permisos de caché.
- Repetición sin caché: añadir `-p no:cacheprovider` a ambos comandos: 32 passed y 46 passed, exit 0, sin warnings.
- `openspec.cmd list --json`: passed, root nearest y 4/6 tareas.
- `openspec.cmd validate hu-4565-normalize-table-name --strict`: passed Change is valid.
- `git diff --check`: passed sin salida; revisar untracked íntegros además, no están cubiertos por ese comando.
- Diff de función y exclusiones inspeccionados; status completo contiene solo candidato y config ajena conocida.
- kit/bundle/runtime Spark: not_applicable por alcance. No instalaciones ni pruebas remotas.

## 5. Hallazgos y siguiente paso
Sin hallazgo funcional pendiente. Reviewer debe seguir verify, revisar función/tests contra cada escenario, repetir pytest específico/suite (usar -p no:cacheprovider si persiste acceso denegado a caché), list/validate/diff check, y verificar hashes e inventario incluyendo untracked. Tras revisión favorable, sync según tarea 2.3. No archive ni publicación sin aprobación humana posterior. No se ejecutaron verify/sync/archive/commit/push, ni cambios de permisos.

## 6. Configuracion y extensiones usadas
Skill openspec-apply-change real; leída crea-orquestador como contexto de coordinación; TDD y verification-before-completion para pruebas y comprobación; perfil developer TOML completo. Workflow.skills_by_role y extensions revisados. Sin skills Databricks adicionales, CLI Databricks ni MCP/hooks; CREA_DEV/dev preservados sin uso.
