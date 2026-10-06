# Design

## Context

Motivación y alcance: ver `proposal.md` (Why / What Changes). Este documento solo describe cómo implementarlo.

**Estado actual observado en el repositorio:**

- `src/common/schema.py::normalize_table_name(file_name: str, month: str = "") -> str` hace `file_name.removesuffix(".csv")`. Esto es sensible a mayúsculas y solo cubre CSV. Después quita `_<month>` si `month` está informado y el nombre termina exactamente en ese sufijo.
- Único consumidor productivo: `src/common/notebook_runner.py::run_bronze_load`. Llama a `normalize_table_name(source_file["source_file_name"], source_file["source_month"] or "")`. El resultado se usa para:
  - validar el nombre contra el diccionario de datos (`validate_table_known_or_allowed`, `validate_expected_columns`, `conform_to_dictionary`);
  - construir `target_table` y `target_path`;
  - escribir el registro de auditoría.
- `src/common/io.py` no llama a `normalize_table_name`. Solo `detect_file_format` (`rsplit(".", 1)[1].lower()`) y `discover_area_files` lo determinan. Esa lógica admite `csv`, `json` y `parquet` sin distinguir mayúsculas, y se mantiene sin cambios. Los archivos sin extensión fallan en `detect_file_format` antes de llegar al normalizador. El caso `fact_ventas_01` / `01` es por tanto una propiedad de la función pura, no un flujo real del runner.
- `tests/test_project_structure.py` importa la función y cubre solo `fact_ventas_cabecera_01.csv` / `01` → `fact_ventas_cabecera`. No existe prueba dedicada.
- Existe una copia duplicada con el mismo comportamiento solo-CSV en `src/utilities/file_ingestion.py` (firma con `Optional[str] = None`). No es la que usa el runner y queda fuera del alcance de la HU.
- `schema.py` solo importa `typing` y carga `pyspark` de forma perezosa en `_require_pyspark()`. Por eso la función puede probarse sin Spark en el sandbox.

**Restricciones:** firma intacta; sin dependencias nuevas; no tocar `io.py`, jobs, `databricks.yml` ni `resources/`; datos sintéticos; no ejecutar recursos ni escribir en NaturaPet.

## Goals / Non-Goals

**Goals:**

- Que `normalize_table_name` elimine una única extensión final `.csv`, `.json` o `.parquet`, sin distinguir mayúsculas, y luego el sufijo `_<month>` según la regla exacta de la HU.
- Mantener la función pura y determinista, con la misma firma y sin dependencias de Spark.
- Dejar los 11 criterios de aceptación como pruebas parametrizadas ejecutables en el Job sandbox.
- Que la spec `bronze-ingestion` (delta ya preparado en el cambio) describa el comportamiento verificable.

**Non-Goals:**

- Unificar o eliminar el duplicado `src/utilities/file_ingestion.py::normalize_table_name`. Se documenta como riesgo y se propone como HU separada.
- Validar que la extensión coincida con `source_format`, o tocar `detect_file_format` y `SUPPORTED_SOURCE_FORMATS`.
- Migrar o renombrar tablas Bronze ya existentes, o reescribir auditorías históricas.
- Introducir una lista de extensiones configurable en `conf/`. Son tres formatos fijos y ya definidos en el código.
- Reglas nuevas de nulos, cantidades, importes, fechas o ratios.

## Decisions

### D1. Eliminar la extensión con una expresión regular precompilada

Se añade `import re` (stdlib) a `src/common/schema.py` y una constante de módulo:

```python
_RECOGNIZED_EXTENSION = re.compile(r"\.(?:csv|json|parquet)$", re.IGNORECASE | re.ASCII)
```

La función queda así:

1. `table_name = _RECOGNIZED_EXTENSION.sub("", file_name, count=1)`.
2. Si `month` es truthy y `table_name.endswith(f"_{month}")`, devuelve `table_name[: -(len(month) + 1)]`.
3. En otro caso devuelve `table_name`.

Por qué:

- `$` con `re.sub` elimina solo la extensión final. No hay bucle, así que `x.csv.json` → `x.csv` y los puntos internos se conservan (`fact.ventas_01.json` → `fact.ventas`).
- `re.ASCII` evita coincidencias Unicode inesperadas bajo `IGNORECASE` (por ejemplo `ſ` casando con `s` en `csv`). Esto es coherente con `detect_file_format`, que usa `.lower()`.
- El orden extensión → mes se mantiene como en la HU. El nombre que se compara con `_<month>` ya no lleva extensión.
- Las mayúsculas del nombre no se tocan porque solo se sustituye el sufijo.
- Las extensiones no reconocidas (`.xlsx`) no coinciden con el patrón y pasan intactas. El sufijo `_<month>` no se elimina en ese caso porque el nombre termina en `.xlsx`, lo que cubre `fact_ventas_01.xlsx` → `fact_ventas_01.xlsx`.

Alternativas descartadas:

- `file_name.lower().endswith((".csv", ".json", ".parquet"))` y cortar por longitud. Es equivalente, pero requiere ramas y cálculo de longitud por extensión. La regex es más compacta y se verifica mejor por tabla de casos.
- `os.path.splitext` / `pathlib.Path.suffix`. Quitaría cualquier extensión (incluida `.xlsx`), lo que contradice el criterio de conservar extensiones no reconocidas.
- Derivar las extensiones de `SUPPORTED_SOURCE_FORMATS` en `io.py`. Acoplaría `schema.py` a `io.py` (hoy independientes) por una lista estable de tres elementos. Se deja la constante local y la relación se documenta en un comentario breve.

### D2. Firma y semántica de `month` sin cambios

Se conserva `month: str = ""`, con la condición truthy actual. Así `month` vacío no elimina ningún sufijo (`fact_ventas_01.csv` / vacío → `fact_ventas_01`), y un sufijo distinto al del mes informado tampoco (`fact_ventas_02.csv` / `01` → `fact_ventas_02`). No se añaden validaciones de formato de mes: eso corresponde a `MONTH_PATTERN` en `io.py` y queda fuera del alcance.

### D3. Pruebas parametrizadas sin Spark

Se crea `tests/test_normalize_table_name.py` con `pytest.mark.parametrize` sobre `(file_name, month, expected)`. Se importa `from src.common.schema import normalize_table_name`, igual que `tests/test_project_structure.py`, por lo que no hace falta `pyspark` ni fixtures.

Los 11 casos de la HU se cubren literalmente, con ids legibles: csv, json, parquet, `.CSV` con nombre en mayúsculas, `.JsOn`, `.PARQUET` sin mes, sufijo distinto, mes vacío, punto interno, `.xlsx`, sin extensión.

Se añade un pequeño conjunto de casos de borde con datos sintéticos, sin alterar la regla:

- Una sola extensión eliminada: `fact_ventas_01.csv.json` / `01` → `fact_ventas_01.csv`.
- Sufijo de mes solo tras quitar la extensión: `fact_ventas_01.xlsx` / `01` se conserva.

Alternativa descartada: ampliar `tests/test_project_structure.py`. Se prefiere un archivo dedicado, como indica la HU, para no mezclar estructura del proyecto con reglas de normalización. La prueba existente de `fact_ventas_cabecera_01.csv` se mantiene como prueba de regresión.

### D4. Archivos y operaciones previstas (base del manifiesto)

| Operación | Ruta | Contenido |
|---|---|---|
| modify | `src/common/schema.py` | Añadir `import re`, la constante `_RECOGNIZED_EXTENSION` y reescribir el cuerpo de `normalize_table_name`. El resto del módulo no cambia. |
| create | `tests/test_normalize_table_name.py` | Pruebas parametrizadas descritas en D3. |

No se tocan `src/common/io.py`, `src/common/notebook_runner.py`, `src/utilities/`, `conf/`, `resources/`, `databricks.yml` ni notebooks. Los artefactos OpenSpec (`proposal.md`, `design.md`, `tasks.md`, delta de `bronze-ingestion`) los gestiona el Harness por separado y no forman parte del manifiesto.

### D5. Verificación en el sandbox

- Adaptadores: `python_compile` sobre los dos archivos y `pytest_sandbox` sobre `tests/test_normalize_table_name.py`, seguido de la suite completa `tests/` en el Job sandbox aislado del harness.
- Sin dependencias nuevas, sin jobs ni pipelines del cliente y sin lectura o escritura de tablas, catálogos o datos de NaturaPet.
- La verificación con Sonnet y la aprobación humana del plan siguen el flujo del Harness.

### D6. Impacto entre capas y dominios

La utilidad es común (`src/common/`) y la usa la carga Bronze de todos los dominios a través de `run_bronze_load`. Silver y Gold no invocan la función y no cambian. Para archivos CSV en minúsculas el resultado es idéntico al actual (compatibilidad hacia atrás). Cambia solo para nombres con `.json`, `.parquet` o extensión en mayúsculas, que es la corrección buscada.

## Risks / Trade-offs

- [Los archivos `.json`/`.parquet` o con extensión en mayúsculas ya cargados antes generaron tablas Bronze y rutas con la extensión en el nombre, y a partir de ahora apuntarán a tablas con el nombre normalizado] → Es el efecto buscado. Antes de desplegar en un entorno real, un responsable humano debe revisar si hay cargas previas de esos formatos. No se migra ni se borra nada desde esta HU. La reversión de código basta para volver al comportamiento anterior.
- [Al asociarse ahora JSON/Parquet al diccionario de datos, `validate_table_known_or_allowed` y `validate_expected_columns` pueden aplicar reglas que antes no se aplicaban y hacer fallar cargas que antes pasaban] → Es el comportamiento pretendido por la HU. La lógica de `src/common/validation.py` no se ha leído en este diseño y no se modifica. Queda como punto de atención en la revisión del PR.
- [Existe un duplicado solo-CSV en `src/utilities/file_ingestion.py` que puede divergir de `src/common/schema.py`] → No se modifica por estar fuera del alcance aprobado. Se recomienda una HU posterior para unificarlo o eliminarlo. Mientras tanto, nadie en `src/common` depende de él.
- [Un nombre que solo contiene la extensión, o solo `_<month>` más extensión, devuelve cadena vacía] → Es el comportamiento actual para el caso análogo con `.csv`. No se añade regla nueva, y el flujo falla aguas abajo por nombre de tabla desconocido o inválido.
- [La regex duplica conceptualmente la lista de `SUPPORTED_SOURCE_FORMATS` de `io.py`] → Trade-off aceptado para no acoplar módulos. Las pruebas fijan las tres extensiones y hacen visible cualquier divergencia futura.

## Migration Plan

1. Implementar los dos cambios de D4 en una rama `feature/*` y ejecutar las pruebas nuevas y la suite completa en el Job sandbox.
2. Verificar, sincronizar la spec `bronze-ingestion` y archivar el cambio mediante el workflow controlado. Publicar código, pruebas y OpenSpec juntos en un PR hacia `develop`.
3. Merge y despliegue los realiza una persona, fuera de esta HU.

**Reversión:** revertir el commit del PR restaura el comportamiento solo-CSV. La función es pura y no persiste estado, por lo que no hay migración de datos ni esquema que deshacer. Cualquier tabla Bronze creada entre el despliegue y la reversión debe revisarse manualmente por el equipo de ingesta.
