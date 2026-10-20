# Evidencia de HU — hu-4565-normalize-table-name

## 1. Solicitud y criterios

HU-4565 solicita corregir normalize_table_name en src/common/schema.py para quitar una extensión final CSV/JSON/Parquet sin distinguir mayúsculas y luego sufijo _<month> informado con coincidencia exacta. Mantener firma, caja, puntos internos y extensiones desconocidas; pruebas parametrizadas nuevas en tests/test_normalize_table_name.py; delta bronze-ingestion. Detección/lector/rutas/jobs/databricks.yml/resources fuera de alcance.

## 2. Estado y coordinacion

2026-10-19: planner /root/planner_hu4565 realmente delegado por /root, con perfil planner gpt-6.1-sol/low; sin subdelegación. Plan ready, developer/reviewer no ejecutados en esta etapa; cero rondas de corrección de implementación.

### Confirmaciones de planificacion

Principal comunicó autorización humana «si, hasla desde el local» y preparó feature/hu-4565 desde 22e33e9336c8053b5277b31da8168d22debb9c73. Excepción explícita a base remota origin/develop c5efcf154c7e56101e6dd6c3ea830f6512e6b184: setup local en commit separado aún no integrado a develop. No implica apply, archive ni publicación. Propose concluido; nueva solicitud humana de apply PENDIENTE. Explore/update no ejecutados ni necesarios.

## 3. Candidato revisado

Solo planificación sobre HEAD 22e33e9. Archivos nuevos exactos en handoff-planner.md; no código, tests ni specs principales modificados. Huellas de artefactos y handoff se agregan abajo; este registro mutable queda excluido de su propia huella. Cada archivo nuevo contiene su contenido íntegro revisable; git diff --check solo valida cambios tracked, por lo que no acredita contenido untracked.

## 4. Plan y resultados de pruebas

Todos los comandos de esta tabla ejecutados localmente el 2026-10-19 salvo estado explícito distinto. CLI OpenSpec resolvió raíz nearest de este checkout, sin store seleccionado.

| Check/comando | Resultado y evidencia |
| --- | --- |
| openspec list --json | passed, raíz válida, changes inicial [] |
| openspec context --json | passed, root.path checkout, role openspec_root |
| openspec list --specs | passed, bronze-ingestion existente (11 requisitos) |
| openspec show bronze-ingestion --type spec --json --no-scenarios; openspec show bronze-ingestion --type spec | passed, requisito completo anterior inspeccionado |
| openspec new change hu-4565-normalize-table-name | passed, schema spec-driven, scaffold .openspec.yaml |
| openspec instructions proposal/specs/design/tasks --change hu-4565-normalize-table-name --json | passed, cada id ejecutado por separado antes de su escritura; dependencias releídas |
| openspec status --change hu-4565-normalize-table-name --json | passed, revisado tras cada artefacto; final isPlanningComplete=true, cuatro done |
| openspec validate hu-4565-normalize-table-name --strict | passed, Change 'hu-4565-normalize-table-name' is valid |
| openspec status --change hu-4565-normalize-table-name | passed, 4/4 artifacts complete |
| git branch --show-current | passed, feature/hu-4565 |
| git diff --check | passed sin salida; límite: no cubre untracked |
| .\.venv\Scripts\python.exe -m pytest tests/test_normalize_table_name.py -q | not_run, archivo aún no implementado; requiere nueva solicitud humana apply |
| .\.venv\Scripts\python.exe -m pytest tests -q | not_run en planner; requerido tras implementación, no se presume resultado por contexto previo |
| kit-structure | not_applicable, no cambios a kit/perfiles/contexto |
| databricks bundle validate --strict --target dev --profile CREA_DEV | not_applicable, no cambios bundle/resources/rutas notebooks |
| Runtime Spark | not_applicable, cambio puro de cadenas, sin código Spark; no se ejecutaron jobs |

Fixtures definidos en delta/design: nueve variantes de extensión, nombres con caja mixta, month omitido/vacío/None, mes discordante/parcial/interno, desconocidas/compuestas, puntos internos, nombre vacío y eliminación única por fase. Entorno previsto .venv existente (contexto registra Python 3.13.14/pytest 9.1.1; confirmar al ejecutar). No instalación ni recursos externos.

## 5. Revision y sync

not_run: revisión independiente, verify y sync esperan implementación y checks favorables. No se alteró openspec/specs/bronze-ingestion/spec.md.

## 6. Aprobacion humana de archivo y publicacion

PENDIENTE para este cambio/candidato. Sin permiso de commit/push ni PR. Remoto previsto origin, rama feature/hu-4565, destino develop; cualquier publicación exige revisar también commit local del setup separado.

## 7. Archivo y pendientes

Archive not_run. Próximo paso: principal presenta propuesta/diseño/delta/tareas y espera nueva solicitud humana apply. Ningún merge, deploy, ejecución remota o borrado.

## 8. Configuracion y extensiones

Skill real .agents/skills/openspec-propose/SKILL.md; perfil .codex/agents/planner.toml; workflow.skills_by_role y extensions leídos, sin extras. No MCP/hooks. Perfil CREA_DEV/target dev preservados sin uso.

## 9. Huellas SHA256 del plan

- openspec\changes\hu-4565-normalize-table-name\.openspec.yaml: B552AB6519DF8F66B705724100F565C5CD842BC9389AEAA177DA9CEC3D02A685
- openspec\changes\hu-4565-normalize-table-name\design.md: AE4F9D5B6B51BC74EA0656BA6C49B059FE80B896BF0C4D89DC8099963E8063E8
- openspec\changes\hu-4565-normalize-table-name\proposal.md: 3F5AA80E7774371FCFD844712BD4845A0DB7157899575F8D79D514A94950B84B
- openspec\changes\hu-4565-normalize-table-name\tasks.md: 824A76B5664922FED9BB44B1BBAFB5298A9CA29D23D27C9D36CBBBA0A0EBB2A0
- openspec\changes\hu-4565-normalize-table-name\specs\bronze-ingestion\spec.md: 56926423C28CD45A215A40A9C0BA33CFC8D2AB57F9396B4D72DAF2F746103E27
- docs\hu\hu-4565-normalize-table-name\handoff-planner.md: 5FA1B1925CD40BE3EB6CFA8738B3413BAD07FAE0D063E13425CAFA7445A95687

## 10. Reanudacion developer — 2026-10-20

Developer real `/root/developer_hu4565`, rol nativo developer gpt-6.1-sol/low, despachado por principal; sin subdelegacion. Nueva solicitud humana vigente: «aplica el cambio hu-4565-normalize-table-name». Se sustituye el pendiente de apply de la etapa planner; archive/publicacion siguen pendientes.

Preflight antes de implementar: `git branch --show-current` devuelve feature/hu-4565; HEAD esperado 22e33e9336c8053b5277b31da8168d22debb9c73. `git status --porcelain=v1 --untracked-files=all` muestra modificacion ajena `.codex/config.toml` y los siete archivos nuevos del planner. Configuracion ajena preservada y excluida del candidato. `openspec.cmd list --json` devuelve root nearest valido; `openspec.cmd status --change hu-4565-normalize-table-name --json` confirma spec-driven y plan completo; instructions apply devuelve ready, 0/6 tareas. Todos los contextFiles leidos. Manifiesto de design vigente; sin cambio de alcance.

### Resultado developer y checks

Implementado solo el cuerpo de normalize_table_name: comparación case-insensitive de extensión final reconocida, recorte del original, break tras una eliminación; bloque mensual y firma intactos. tests/test_normalize_table_name.py contiene 32 casos con valores literales independientes: las nueve variantes, JSON mensual, month omitido/vacío/None, mes exacto incluso textual con caja, discordancias, puntos internos, desconocidas/compuestas, sin extensión, eliminación única por fase y vacío. No se afirma idempotencia de llamadas sucesivas: el contrato pide una eliminación por llamada. No tipos nuevos ni cambios Spark.

Fecha de comandos: 2026-10-20, entorno local. Versiones observadas: Python 3.13.14, pytest 9.1.1, OpenSpec 1.14.3, git 2.55.0.windows.5.

| Comando exacto | Resultado real |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest tests/test_normalize_table_name.py -q` antes de fix | failed esperado, exit 1: 19 failed, 13 passed, 2 warnings de caché; fallos por conservar extensiones CSV mayúsculas/JSON/Parquet |
| mismo comando tras fix | passed exit 0: 32 passed, 1 PytestCacheWarning por WinError 5 al escribir .pytest_cache |
| `.\.venv\Scripts\python.exe -m pytest tests -q` | passed exit 0: 46 passed, mismo warning de caché |
| `.\.venv\Scripts\python.exe -m pytest tests/test_normalize_table_name.py -q -p no:cacheprovider` | passed exit 0: 32 passed, sin warnings, 0.07s |
| `.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider` | passed exit 0: 46 passed, sin warnings, 0.23s |
| `openspec.cmd list --json` final | passed exit 0: root nearest válido, 4/6 tareas completas |
| `openspec.cmd validate hu-4565-normalize-table-name --strict` | passed exit 0: Change is valid |
| `git diff --check` | passed exit 0, sin salida; no cubre untracked |
| `git diff -- src/common/schema.py` | inspeccionado: único hunk en función objetivo, firma intacta |
| `git diff -- src/utilities/file_ingestion.py src/common/io.py databricks.yml resources conf` | sin salida, exclusiones conservadas |
| `git status --porcelain=v1 --untracked-files=all` | inspeccionado: config ajena preservada; schema modificado y artefactos/tests nuevos según manifiesto |
| `git rev-parse HEAD` | 22e33e9336c8053b5277b31da8168d22debb9c73 |
| `git --version`; `openspec.cmd --version`; `.\.venv\Scripts\python.exe --version`; `.\.venv\Scripts\python.exe -m pytest --version` | versiones indicadas arriba |

Warnings de caché no afectan assertions; repetición sin plugin conserva suite y elimina dependencia de caché, sin cambiar permisos/configuración. No hubo rechazo de auto-review. Check kit-structure not_applicable (config ajena excluida, no se altera kit); bundle-dev y runtime Spark not_applicable por lógica pura de cadenas. Databricks CLI/MCP/jobs/deploy not_run fuera de alcance; no se cargan skills Databricks al no usarse plataforma. Verify/sync/archive/commit/push not_run por responsabilidad y aprobación posterior.

Tareas 1.1, 1.2, 1.3 y 2.1 completas con checks; 2.2 y 2.3 pendientes del reviewer independiente. Estado developer ready. Siguiente paso: reviewer repite checks, verifica delta/manifiesto y decide sync; archive/publicación requieren confirmación humana posterior.

### Huellas SHA256 candidato funcional y tareas

Calculadas con Get-FileHash -Algorithm SHA256, incluyendo tests y tasks untracked. Plan restante conserva huellas de sección 9; evidencia mutable excluida de su propia huella.

- src/common/schema.py: 23D072F906EACDBBA8F6919DE11B9AEAE4A280F15D29B3540A4DD66D68228F27
- tests/test_normalize_table_name.py: 1BC8EC858B5F5907E73D4A12A30D0F60E310EC8B05A7506A8BC63F4A7753B69A
- openspec/changes/hu-4565-normalize-table-name/tasks.md: CAD3F1E90EE0C54A286BBA4A65E8241B47413AB18DC30DEFD3047A94C265E812
- docs/hu/hu-4565-normalize-table-name/handoff-developer.md: 59E605EF72100C23214BCB8F99C8CE3FF06FB35DF7EB9975511FC495F127D1D4

## 11. Revisión independiente y sync — 2026-10-20

Reviewer real /root/reviewer_hu4565; revisión completada con openspec-verify-change y sync con openspec-sync-specs. Estado ready_for_archive, 6/6 tareas. Reporte completo reproducible, scorecard, comandos, salidas y huellas en handoff-reviewer.md.

Repetición local: pytest específico con -p no:cacheprovider 32 passed (0.08s); suite 46 passed (0.29s), ambos sin warnings. OpenSpec list/status/instructions apply y validate cambio --strict passed. Sync semántico del único bloque Nombre de tabla y lectura por formato, dos escenarios actualizados y ocho añadidos; otros requisitos y contrato detector/lector intactos. openspec validate --specs: 10 passed, 0 failed, avisos de longitud >500 del contrato completo y otros requisitos existentes; regla upstream exige preservar MODIFIED completo. git diff --check passed con aviso de conversión LF→CRLF; no error. Hashes funcionales iguales al developer.

SHA256 spec sincronizada: 08A7B3335631CAFE03F37272A53D518337D22FB6C458D927A10A9BD3C805F7A7. Tasks 6/6: FD2AD9037374875FE26E3A3070152C72A373EE13D5280D749DD2D47B948899A7. Función 23D072F906EACDBBA8F6919DE11B9AEAE4A280F15D29B3540A4DD66D68228F27; tests 1BC8EC858B5F5907E73D4A12A30D0F60E310EC8B05A7506A8BC63F4A7753B69A.

Cero hallazgos críticos, advertencias de revisión o sugerencias; diez escenarios completos. Ningún check requerido failed/blocked/not_run. Bundle/kit/runtime Spark no aplican por alcance. Archive, commit/push/PR not_run pendientes de autorización humana y rol correspondiente. .codex/config.toml ajeno preservado y excluido. No ejecución remota, instalación, cambio de permisos ni modificación de candidato/plan.

## 12. Aprobación humana y archivo — 2026-10-20

Principal transmitió respuesta humana «[$crea-orquestador] adelante» a su pregunta explícita «¿Autorizas archivar y hacer commit/push del candidato y archivos detallados en pr.md a origin/feature/hu-4565, hacia develop, incluyendo el commit previo del setup 22e33e9?». Alcance aprobado: archivo del candidato/sync revisado y publicación por principal del manifiesto de pr.md, incluido setup separado. No autoriza merge, deploy ni creación automática de PR GitHub.

Reviewer /root/reviewer_hu4565 reanudado: skill openspec-archive-change real leída, pr.md leído, root nearest comprobado con openspec list --json, instructions archive y status --change hu-4565-normalize-table-name --json passed; artefactos done, 6/6 tareas. Se aplicaron las tres orientaciones archive compatibles (verify/sync previos, evidencia preservada, entrega feature hacia develop por principal). SHA256 de función/tests/spec/tasks coinciden exactamente con handoff-reviewer; resultados revisados no cambiaron. Comparación completa delta-main confirmó bronze-ingestion ya sincronizado.

Archive passed mediante movimiento local de directorio según paso 5 de la skill: rutas absolutas source/target verificadas dentro del checkout y ausencia de colisión, Move-Item -LiteralPath source -Destination target. Ruta final: openspec/changes/archive/2026-10-20-hu-4565-normalize-table-name/. Los cinco archivos .openspec.yaml, proposal.md, design.md, tasks.md y specs/bronze-ingestion/spec.md se conservaron íntegros. openspec archive --help consultado (soporta --skip-specs); no se invocó archive CLI ni --yes porque la skill especifica movimiento directo tras evaluación/aprobación. Sync no repetido.

Postcheck openspec list --json passed: changes [], root válido. Inventario archivado cinco archivos comprobado, git diff --check passed (aviso LF→CRLF sin error), las cuatro huellas siguen idénticas incluida tasks en archivo. No pruebas repetidas porque no cambió código, specs ni resultados. Candidato funcional no modificado; configuración ajena .codex/config.toml preservada. Estado reviewer passed, archivo completado. Commit/push not_run por reviewer: corresponde al principal bajo autorización recibida. PR GitHub manual; sin ejecuciones remotas.

## 13. Preparación de publicación autorizada — 2026-10-20

Principal confirma aprobación humana «adelante» para archivo y commit/push del manifiesto pr.md a origin/feature/hu-4565 hacia develop, incluyendo setup separado 22e33e9. Reviewer /root/reviewer_hu4565 terminó archivo con estado passed. Fetch origin develop aprobado y completado; origin/develop permanece c5efcf154c7e56101e6dd6c3ea830f6512e6b184. git ls-remote --heads origin refs/heads/feature/hu-4565 completado sin coincidencia: rama remota libre. Índice inicialmente vacío. Repetición principal: pytest tests -q -p no:cacheprovider, 46 passed en 0.30s; openspec list --json, changes []; git diff --check aprobado. Los tres hashes funcionales/spec coinciden con reviewer. No cambio funcional tras aprobación.

Commit previsto: fix: normalize table names for HU-4565. Stage solo de las trece rutas del manifiesto, con cinco artefactos en ubicación archive/2026-10-20-hu-4565-normalize-table-name/. .codex/config.toml ajeno excluido. Publicación ordinaria autorizada a origin/feature/hu-4565; GitHub PR manual hacia develop con título/cuerpo de pr.md. SHA local/remoto y resultado de push se reportarán en respuesta final, sin editar evidencia tras commit para registrar su propio SHA.
