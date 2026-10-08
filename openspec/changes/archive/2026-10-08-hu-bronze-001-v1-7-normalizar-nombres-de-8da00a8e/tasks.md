# Tasks

## 1. Pruebas parametrizadas de normalize_table_name

- [x] 1.1 Revisar `tests/test_project_structure.py` y la configuración de pytest del repositorio para reutilizar el mecanismo de importación de `src.common.schema`, y verificar que queda anotado en la descripción del PR que no se añade configuración nueva ni dependencias (si hiciera falta configuración nueva, detener y replantear el plan en lugar de ampliar el alcance).
- [x] 1.2 Crear `tests/test_normalize_table_name.py` con una prueba `pytest.mark.parametrize` de las 11 tuplas (entrada, month, esperado) de los criterios de aceptación, con ids legibles y solo cadenas sintéticas, sin Spark ni datos de NaturaPet. Verificar que `pytest tests/test_normalize_table_name.py --collect-only` lista los 11 casos y que, antes del cambio en `schema.py`, fallan los casos de `.json`, `.parquet` y variantes de mayúsculas.

## 2. Implementación en src/common/schema.py

- [x] 2.1 Modificar `normalize_table_name` en `src/common/schema.py`: añadir la constante de módulo `_RECOGNIZED_EXTENSIONS = (".csv", ".json", ".parquet")`, eliminar una sola extensión final comparando en minúsculas pero recortando sobre el nombre original (preserva mayúsculas) y después eliminar `_<month>` solo si `month` está informado y coincide exactamente al final. Mantener la firma `normalize_table_name(file_name: str, month: str = "") -> str`, conservar extensiones no reconocidas y puntos internos, y no tocar `detect_file_format`, lectura, rutas ni nuevas importaciones. Verificar que `python -m py_compile src/common/schema.py` termina sin errores.
- [x] 2.2 Actualizar el docstring de `normalize_table_name` para describir el orden (extensión primero, sufijo de mes después), las extensiones admitidas y la preservación de mayúsculas. Verificar que el docstring coincide con los escenarios del delta de la spec `bronze-ingestion`.
- [x] 2.3 Ejecutar `tests/test_normalize_table_name.py` y verificar que pasan los 11 casos de aceptación, incluidos `Fact_Ventas_01.CSV` → `Fact_Ventas`, `fact_ventas_02.csv` (month `01`) → `fact_ventas_02`, `fact_ventas_01.xlsx` → `fact_ventas_01.xlsx` y `fact_ventas_01` (month `01`) → `fact_ventas`.
- [x] 2.4 Ejecutar la prueba existente de `tests/test_project_structure.py` que cubre el caso CSV mensual en minúsculas y verificar que sigue pasando sin modificarla (regresión de compatibilidad).

## 3. Verificación en el Job sandbox

- [x] 3.1 Ejecutar en el Job sandbox aislado del harness (identidad distinta de la App) los adaptadores `python_compile` sobre `src/common/schema.py` y `pytest_sandbox` sobre `tests/test_normalize_table_name.py`, y verificar que ambos terminan en verde. Si falta la herramienta o el permiso del Job sandbox, declarar el bloqueo sin sustituirlo por credenciales de la App ni ejecutar localmente como alternativa.
- [x] 3.2 Ejecutar toda la suite `tests/` con `pytest_sandbox` en el Job sandbox y verificar que no hay fallos ni regresiones. No ejecutar jobs ni pipelines y no escribir datos ni tablas de NaturaPet.
- [x] 3.3 Confirmar que el diff contiene únicamente `src/common/schema.py` y `tests/test_normalize_table_name.py` como código y pruebas, sin cambios en `databricks.yml`, `resources/`, `src/utilities/file_ingestion.py` ni nuevas dependencias. Como no cambia `databricks.yml` ni `resources/`, no se requiere validación del bundle para dev; verificarlo revisando el listado del diff.
- [x] 3.4 Completar la verificación obligatoria con Sonnet sobre el candidato (código, pruebas y artefactos OpenSpec) y verificar que el resultado no reporta hallazgos bloqueantes frente a los criterios de aceptación; resolver cualquier hallazgo antes de continuar.

## 4. Sincronización, archivado y PR

- [x] 4.1 Sincronizar el delta de la spec `bronze-ingestion` con `openspec/specs/` mediante el workflow OpenSpec controlado y verificar con `openspec validate` que la spec principal queda válida y refleja el requisito «Nombre de tabla y lectura por formato» con sus escenarios.
- [x] 4.2 Archivar el cambio mediante el workflow OpenSpec (`openspec/changes/archive/`) y verificar que ya no figura entre los cambios activos de `openspec list`.
- [x] 4.3 Preparar el PR desde una rama `feature/*` hacia `develop` que incluya juntos código, pruebas y OpenSpec, con descripción que enumere el resultado de la suite en el Job sandbox, el riesgo de tablas Bronze JSON/Parquet cuyo nombre resuelto cambia y el seguimiento de la función homónima de `src/utilities/file_ingestion.py` (fuera de alcance). Verificar que el PR apunta a `develop` y que el merge y el despliegue quedan para revisión humana.
