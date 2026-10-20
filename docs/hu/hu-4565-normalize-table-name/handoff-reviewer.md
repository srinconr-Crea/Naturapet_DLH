# Handoff — hu-4565-normalize-table-name / reviewer

## 1. Identidad y estado
- HU/cambio: hu-4565-normalize-table-name.
- Rol e identificador real: reviewer /root/reviewer_hu4565, sin subdelegación.
- Estado: ready_for_archive.
- Candidato: feature/hu-4565, HEAD 22e33e9336c8053b5277b31da8168d22debb9c73 más diff de src/common/schema.py y archivo nuevo tests/test_normalize_table_name.py; artefactos y documentación de HU incluidos como untracked. .codex/config.toml es ajeno y queda excluido.

## 2. Entrada y alcance
Leídos AGENTS.md, reviewer.toml completo, proyecto.json (workflow/skills_by_role/extensions), contexto-proyecto, prácticas general/python, README, configuración dev y job mensual, entrega-git, plantilla handoff, proposal/design/delta/tasks, evidencia y handoffs previos, función y pruebas completas, src/common/io.py y spec principal. Skills reales openspec-verify-change y openspec-sync-specs. Root nearest confirmado por list/status, sin store.

Rutas modificadas por reviewer: este handoff; evidencia.md (append); openspec/changes/hu-4565-normalize-table-name/tasks.md (solo 2.2/2.3); openspec/specs/bronze-ingestion/spec.md (sync del único bloque). No edición de código/pruebas/plan.

## 3. Resultado
| Dimensión | Resultado |
| --- | --- |
| Completeness | 6/6 tareas al cierre; 1 requisito modificado cubierto |
| Correctness | 1/1 requisito, 10/10 escenarios cubiertos por función/pruebas; detector y lector preservados |
| Coherence | Firma, orden extensión → mes, caja original y eliminación única por fase conformes al diseño y patrones |

CRITICAL: 0. WARNING de revisión: 0. SUGGESTION: 0. Ningún check aplicable omitido. All checks passed. Ready for archive.

Las nueve variantes están parametrizadas; mes omitido/vacío/None, exactitud, desconocidas/compuestas, puntos internos, nombre sin extensión, una sola extensión, un solo mes, orden sin segundo pase y vacío tienen valores esperados literales. CSV mayúscula usa el mismo caso parametrizado con nombre Ventas; el detector se conserva por inspección de io.py. No se afirma runtime Spark.

Sync realizado por merge directo según skill: requisito completo actualizado, dos escenarios existentes actualizados y ocho añadidos, conservando los otros diez requisitos, Purpose, Sources y reglas de detección/lectura. Diff revisado: solo bloque objetivo, sin encabezados delta.

## 4. Validacion
2026-10-20, local .venv Python 3.13.14 / pytest 9.1.1:
- `.\.venv\Scripts\python.exe -m pytest tests/test_normalize_table_name.py -q -p no:cacheprovider`: passed, 32 passed en 0.08s, sin warnings.
- `.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider`: passed, 46 passed en 0.29s, sin warnings.
- `openspec status --change hu-4565-normalize-table-name --json`: passed, spec-driven, root y artifactPaths/contexto confirmados.
- `openspec instructions apply --change hu-4565-normalize-table-name --json`: passed, contexto leído y final 6/6, all_done.
- `openspec list --json`: passed, root nearest válido.
- `openspec validate hu-4565-normalize-table-name --strict`: passed antes y después de sync.
- `openspec instructions specs --change hu-4565-normalize-table-name --json`: passed; snapshot válido con tres reglas aplicado antes de sync.
- `openspec validate --specs`: passed, 10 passed / 0 failed. Advierte longitud >500 en requisitos existentes de varias specs, incluyendo el bloque MODIFIED completo preservado por regla upstream; no falla ni requiere recortar el contrato. No se ejecutó --strict para todas las specs porque no es check requerido.
- `git diff --check`: passed; aviso Git de conversión LF→CRLF sin error. Untracked inspeccionados completos además.
- `git diff -- src/utilities/file_ingestion.py src/common/io.py databricks.yml resources conf`: sin salida.
- `git branch --show-current`, `git rev-parse HEAD`, `git status --porcelain=v1 --untracked-files=all`, `Get-FileHash`: candidato/rama/inventario confirmados; huellas funcionales iguales al handoff developer.

SHA256:
- src/common/schema.py: 23D072F906EACDBBA8F6919DE11B9AEAE4A280F15D29B3540A4DD66D68228F27
- tests/test_normalize_table_name.py: 1BC8EC858B5F5907E73D4A12A30D0F60E310EC8B05A7506A8BC63F4A7753B69A
- openspec/specs/bronze-ingestion/spec.md: 08A7B3335631CAFE03F37272A53D518337D22FB6C458D927A10A9BD3C805F7A7
- tasks.md: FD2AD9037374875FE26E3A3070152C72A373EE13D5280D749DD2D47B948899A7

## 5. Hallazgos y siguiente paso
Sin defectos. Principal presenta candidato/sync y alcance de publicación, incluida excepción del setup local, y solicita aprobación humana de archivo y commit/push origin/feature/hu-4565 hacia develop. Archive not_run: falta aprobación humana explícita. Commit/push/PR not_run: responsabilidad del principal y autorización pendiente. Kit, bundle y runtime Spark not_applicable por alcance puro de cadenas; no recursos remotos ejecutados.

## 6. Configuracion y extensiones usadas
Perfil reviewer real; skills verify/sync locales. Sin MCP, hooks, instalación ni cambio de permisos; CREA_DEV/dev preservados sin uso. No subdelegación, archive ni publicación.

## 7. Reanudación y archivo autorizado — 2026-10-20

Estado final reviewer: passed. Principal citó aprobación humana «[$crea-orquestador] adelante» de archivo y commit/push del candidato/manifiesto pr.md a origin/feature/hu-4565 hacia develop, incluyendo setup 22e33e9. Se leyeron skill archive y pr.md; hashes función/tests/spec/tasks idénticos a sección 4, root válido, 4/4 artefactos done y 6/6 tareas. Delta y requisito main idénticos: sync ya aplicado.

Se ejecutó paso 5 de openspec-archive-change con Move-Item tras resolver/verificar rutas absolutas y ausencia de colisión. Archivo: openspec/changes/archive/2026-10-20-hu-4565-normalize-table-name/. Cinco artefactos íntegros, incluyendo .openspec.yaml. Sin doble sync, --yes ni respuestas automáticas. openspec archive --help leído; CLI archive no ejecutado porque la skill dispone movimiento directo. Commands instructions archive/status/list passed; post-list changes []; git diff --check passed. Hashes posteriores idénticos. Evidencia/recibo en sección 12 de evidencia.md.

Escrituras adicionales solo movimiento de cinco artefactos y append de metadatos en evidencia/handoff reviewer. Código, pruebas y specs preservados. Próximo paso: principal publica el alcance autorizado con commit/push; reviewer no ejecutó commit/push ni PR.
