# Design

## Context

Ver `proposal.md` para motivación. La firma actual es `normalize_table_name(file_name: str, month: str = "") -> str`. El runner importa esta función de `src/common/schema.py` y pasa `source_month or ""`; su salida alimenta tabla, ruta Bronze y validación contra diccionario. La prueba de regresión CSV mensual vive en `tests/test_project_structure.py`; el archivo de pruebas solicitado aún no existe. Se crea este diseño para precisar casos límite y compatibilidad de una función compartida.

## Goals / Non-Goals

**Goals:** comportamiento determinista sobre cadenas, sin dependencias adicionales ni inicialización Spark; mantener firma y retorno. `None` en month conserva el comportamiento falsy existente aunque la anotación siga siendo str.

**Non-Goals:** aceptar file_name None u otros tipos ajenos a la firma; validar rangos de mes, normalizar espacios, convertir caja del nombre o reinterpretar rutas. No consolidar el homónimo de `src/utilities/file_ingestion.py`.

## Decisions

- Comparar únicamente la terminación contra la terna fija de extensiones mediante una copia en minúsculas y recortar la cadena original. Evita alterar mayúsculas; un split por el primer punto perdería puntos internos y un retiro genérico de extensión cambiaría formatos desconocidos. No se necesita regex ni dependencia nueva.
- Procesar extensión una vez antes del bloque mensual existente. Mantener `month` como valor exacto, sin padding ni conversión de caja. Una cadena sin extensión también puede perder el sufijo mensual; una extensión desconocida solo se conserva, no impide quitar un mes realmente final (`Ventas.xlsx_01` → `Ventas.xlsx`).
- Añadir fixtures parametrizadas de cadenas y resultados esperados importando directamente de `src.common.schema`; no usar Spark ni datos externos. Cubrir la matriz de nueve variantes de extensión, casos mensuales y límites del delta, además de llamada con month omitido y nombre sin extensión.
- Actualizar el bloque completo «Nombre de tabla y lectura por formato» vía delta, conservando reglas de detección/lectura y nombres de escenarios previos, con resultados nuevos. Ningún otro requisito cambia.

## Risks / Trade-offs

- [JSON/Parquet/CSV mayúscula ahora resuelven otra clave de diccionario y tabla] → es el cambio solicitado; verificar resultados exactos con nombres de caja mixta. No migrar ni borrar tablas existentes.
- [Homónimo en utilities conserva comportamiento anterior] → límite explícito de la HU; el runner Bronze usa common/schema.py.
- [Pruebas locales no prueban carga Spark] → registrar solo validación de cadenas y regresiones locales. No cambia código Spark, bundle ni llamadas remotas.

## Manifesto de archivos y operaciones

| Etapa/rol | Escrituras permitidas previstas |
| --- | --- |
| Planner | `openspec/changes/hu-4565-normalize-table-name/` y `docs/hu/hu-4565-normalize-table-name/` |
| Developer tras nueva solicitud humana | Modificar solo función objetivo en `src/common/schema.py`; crear `tests/test_normalize_table_name.py`; actualizar tareas/evidencia de esta HU |
| Reviewer tras pruebas favorables | Verify y sync de `openspec/specs/bronze-ingestion/spec.md`, presentar diff; archive únicamente tras aprobación humana explícita |
| Principal tras aprobación de publicación | Entrega Git de rutas aprobadas en feature/hu-4565 a origin hacia develop; GitHub mediante formulario manual |

No modificar detección, lector, rutas, notebooks, jobs, conf, databricks.yml ni resources/. No instalar herramientas ni ejecutar recursos remotos.

## Validation

Entorno local existente `.venv`, Python 3.13.14 / pytest 9.1.1 según contexto; confirmar versiones al ejecutar. Fixtures sintéticos sin archivos de datos.

- `openspec list --json`: check openspec-list aplicable a planificación y reanudación.
- `openspec validate hu-4565-normalize-table-name --strict`: coherencia del cambio.
- `.\.venv\Scripts\python.exe -m pytest tests/test_normalize_table_name.py -q`: casos del delta, después de implementar.
- `.\.venv\Scripts\python.exe -m pytest tests -q`: python-unit obligatorio por cambios src/tests.
- `git diff --check` y revisión de archivos incluidos/untracked: límites del candidato.
- kit-structure no aplica: no se modifica kit, perfiles ni contexto. bundle-dev no aplica: bundle/resources/rutas de notebooks sin cambios. Runtime Spark no aplica: transformación pura de cadenas, sin cambio Spark ni despliegue. No equivalen a checks ejecutados.

## Migration Plan

No hay migración de datos ni ejecución remota en esta HU. Aplicar solo tras nueva solicitud humana, verificar, sincronizar y presentar candidato. Recuperación: revertir únicamente el diff aprobado de función, pruebas y contrato mediante entrega revisada; no modificar datos ni tablas.

Rama preparada por principal desde commit local `22e33e9336c8053b5277b31da8168d22debb9c73`, por autorización humana «si, hasla desde el local». Excepción a base remota: origin/develop verificado por principal en `c5efcf154c7e56101e6dd6c3ea830f6512e6b184`; setup queda en commit separado aún no integrado a develop. Esta autorización no habilita apply, archive o publicación.
