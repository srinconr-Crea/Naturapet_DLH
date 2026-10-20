# Tasks

## 1. Implementación y pruebas de normalización (developer tras nueva solicitud humana)

- [x] 1.1 Confirmar nueva solicitud humana de apply, rama feature/hu-4565 y manifiesto vigente; verificar con `git branch --show-current`, `git status --porcelain=v1 --untracked-files=all` y `openspec status --change hu-4565-normalize-table-name --json`, registrando evidencia antes de implementar.
- [x] 1.2 Modificar únicamente normalize_table_name en src/common/schema.py y crear tests/test_normalize_table_name.py con pytest parametrizado para las nueve variantes de extensión reconocida, caja del nombre, mes omitido/vacío/None, coincidencia exacta y discordante, puntos internos, desconocidas/compuestas, sin extensión, una sola eliminación y cadena vacía; verificar `.\.venv\Scripts\python.exe -m pytest tests/test_normalize_table_name.py -q` y registrar resultado real en evidencia.
- [x] 1.3 Revisar firma y orden extensión → mes contra todos los escenarios del delta, documentar los archivos/casos en handoff y evidencia; verificar diff limitado a función objetivo y archivo nuevo, sin cambios al homónimo utilities ni a detección/lector/configuración.

## 2. Regresión y revisión del candidato

- [x] 2.1 Ejecutar `.\.venv\Scripts\python.exe -m pytest tests -q`, `openspec list --json`, `openspec validate hu-4565-normalize-table-name --strict` y `git diff --check`; registrar versiones, comandos, resultados y hashes del candidato incluyendo archivos nuevos en docs/hu/hu-4565-normalize-table-name/evidencia.md. Mantener blocked/not_run ante falta de entorno, sin instalar herramientas implícitamente.
- [x] 2.2 Reviewer independiente: seguir openspec-verify-change y contrastar función/pruebas contra cada escenario y manifiesto; repetir pruebas pertinentes y entregar hallazgos y evidencia, sin passed si algún check requerido está failed/blocked/not_run.
- [x] 2.3 Solo tras revisión favorable, reviewer seguir openspec-sync-specs para sincronizar el requisito completo en openspec/specs/bronze-ingestion/spec.md y presentar diff; validar contrato preservado de detección/lectura y registrar resultado de sync.

## Workflow follow-up

- Principal preparar borrador de PR con plantilla docs/plantillas/pr.md, rutas, candidato, remoto origin, feature/hu-4565 → develop y commits que incluiría la entrega; presentar excepción del setup local separado.
- Solicitar aprobación humana explícita de archive y, por separado en su alcance, commit/push. No inferir publicación de una aprobación solo de archivo.
- Reviewer archivar únicamente el candidato aprobado siguiendo openspec-archive-change; principal verificar resultado final y ejecutar solo publicación expresamente autorizada. GitHub recibe enlace/formulario manual, sin crear PR automáticamente.
- Mantener rama feature; no merge, deploy, jobs, force-push ni borrado. kit-structure, bundle-dev y runtime Spark no aplican por los motivos documentados en design.md.
