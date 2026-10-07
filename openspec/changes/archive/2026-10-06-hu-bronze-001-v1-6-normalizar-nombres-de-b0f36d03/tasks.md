# Tasks

## 1. Implementación de la normalización en src/common/schema.py

- [x] 1.1 Agregar `import re` (stdlib) y la constante de módulo `_RECOGNIZED_EXTENSION = re.compile(r"\.(?:csv|json|parquet)$", re.IGNORECASE | re.ASCII)` en `src/common/schema.py`, con un comentario breve que la relacione con los formatos admitidos de `io.py`. Verificar con `python_compile` sobre `src/common/schema.py` y confirmando que no se añadió ninguna dependencia nueva.
- [x] 1.2 Reescribir el cuerpo de `normalize_table_name(file_name: str, month: str = "") -> str` manteniendo la firma: eliminar primero una única extensión final reconocida con `_RECOGNIZED_EXTENSION.sub("", file_name, count=1)` y después el sufijo `_<month>` solo si `month` está informado y coincide exactamente al final. Preservar mayúsculas, extensiones no reconocidas y puntos internos. Verificar que `git diff` solo muestra cambios en `import re`, la constante y esa función, y que `python_compile` pasa.

## 2. Pruebas parametrizadas de normalize_table_name

- [x] 2.1 Crear `tests/test_normalize_table_name.py` con `pytest.mark.parametrize` sobre `(file_name, month, expected)` que cubra literalmente los 11 criterios de aceptación de la HU (csv, json, parquet, `Fact_Ventas_01.CSV`, `.JsOn`, `.PARQUET` sin month, `fact_ventas_02.csv`, month vacío, `fact.ventas_01.json`, `.xlsx`, sin extensión) con ids legibles e importando `from src.common.schema import normalize_table_name` sin Spark ni fixtures. Verificar que cada caso aparece como prueba individual al ejecutar `pytest tests/test_normalize_table_name.py --collect-only` en el Job sandbox.
- [x] 2.2 Añadir en el mismo archivo casos de borde sintéticos: eliminación de una sola extensión (`fact_ventas_01.csv.json` / `01` → `fact_ventas_01.csv`) y conservación de `fact_ventas_01.xlsx` / `01`. Verificar que `pytest tests/test_normalize_table_name.py` pasa completo en el Job sandbox con la implementación de 1.2.
- [x] 2.3 Confirmar que la prueba existente de `tests/test_project_structure.py` (`fact_ventas_cabecera_01.csv` / `01` → `fact_ventas_cabecera`) sigue pasando como regresión, sin modificar ese archivo. Verificar ejecutando `pytest tests/test_project_structure.py` en el Job sandbox.

## 3. Verificación integral en el sandbox

- [x] 3.1 Ejecutar la suite completa `tests/` con el adaptador `pytest_sandbox` en el Job sandbox aislado del harness, con identidad distinta de la App y datos sintéticos, sin ejecutar jobs ni pipelines ni tocar tablas o catálogos de NaturaPet. Verificar que todas las pruebas pasan. Si falta la herramienta o el permiso del sandbox, declarar el bloqueo sin sustituirlo por credenciales de la App.
- [x] 3.2 Confirmar que no cambiaron `src/common/io.py`, `src/common/notebook_runner.py`, `src/utilities/`, `conf/`, `resources/`, `databricks.yml` ni notebooks, y que no hay dependencias nuevas. Verificar revisando que el diff final solo contiene `src/common/schema.py` y `tests/test_normalize_table_name.py`. Al no cambiar `databricks.yml` ni `resources/`, no se requiere validación del bundle para dev.

## 4. Verificación, sincronización, archivado y PR

- [x] 4.1 Ejecutar la verificación obligatoria con Sonnet sobre el candidato (código, pruebas y artefactos OpenSpec) y verificar que el informe no reporta discrepancias con la spec `bronze-ingestion` ni con los criterios de aceptación de la HU.
- [x] 4.2 Sincronizar el delta de `bronze-ingestion` con `openspec/specs/` mediante el workflow controlado de OpenSpec. Verificar que la spec vigente contiene los escenarios de extensión CSV, JSON y Parquet, mayúsculas, month vacío, sufijo distinto, punto interno, extensión no reconocida y nombre sin extensión.
- [x] 4.3 Archivar el cambio `hu-bronze-001-v1-6-normalizar-nombres-de-b0f36d03` mediante el workflow controlado de OpenSpec. Verificar que queda en `openspec/changes/archive/` y que ya no figura como cambio activo en `openspec list`.
- [x] 4.4 Preparar el PR desde una rama `feature/*` hacia `develop` con código, pruebas y OpenSpec juntos. La descripción debe incluir el riesgo de tablas Bronze previas con extensión en el nombre, el posible efecto de las validaciones de diccionario sobre JSON/Parquet y el duplicado solo-CSV en `src/utilities/file_ingestion.py` como HU futura. Verificar que el PR queda abierto sin merge ni despliegue, que se dejan para una persona.
