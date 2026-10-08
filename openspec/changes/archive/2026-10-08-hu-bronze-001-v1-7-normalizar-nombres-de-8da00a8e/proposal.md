# Proposal

## Why

Hoy `normalize_table_name()` (`src/common/schema.py`) solo elimina el sufijo literal `.csv`, sensible a mayúsculas, aunque Bronze ya admite lectura de CSV, JSON y Parquet. Por eso un archivo como `fact_ventas_01.json` o `Fact_Ventas_01.CSV` conserva su extensión en el nombre resuelto y no se asocia a la tabla ni al diccionario de datos. La HU-BRONZE-001-V1.7 corrige esta asimetría para que los tres formatos admitidos se normalicen igual.

## What Changes

**Comportamiento actual (evidencia: spec `bronze-ingestion` y búsqueda estática de `normalize_table_name`)**
- `normalize_table_name(file_name, month)` elimina únicamente `.csv` en minúsculas y después el sufijo `_<month>` si queda al final.
- La spec vigente describe expresamente que `fact_ventas_01.json` permanece como `fact_ventas_01.json` y que `fact_ventas_01.CSV` conserva `.CSV`.
- `detect_file_format` ya compara la extensión final en minúsculas y admite csv, json y parquet.
- `tests/test_project_structure.py` cubre el caso CSV mensual. No se ha ejecutado ninguna prueba como parte de esta propuesta, por lo que no hay evidencia de ejecución.

**Cambio propuesto**
- Modificar `normalize_table_name()` en `src/common/schema.py`, con la firma actual `normalize_table_name(file_name: str, month: str = "") -> str`, para que:
  - elimine primero la extensión final `.csv`, `.json` o `.parquet`, sin distinguir mayúsculas;
  - elimine después el sufijo `_<month>` solo si `month` está informado y coincide exactamente al final del nombre ya sin extensión;
  - preserve las mayúsculas del nombre de tabla;
  - conserve extensiones no reconocidas (por ejemplo `.xlsx`) y los puntos internos del nombre.
- Agregar pruebas parametrizadas en `tests/test_normalize_table_name.py` con datos sintéticos que cubran los criterios de aceptación:

| Entrada | month | Resultado |
| --- | --- | --- |
| `fact_ventas_01.csv` | `01` | `fact_ventas` |
| `fact_ventas_01.json` | `01` | `fact_ventas` |
| `fact_ventas_01.parquet` | `01` | `fact_ventas` |
| `Fact_Ventas_01.CSV` | `01` | `Fact_Ventas` |
| `fact_ventas_01.JsOn` | `01` | `fact_ventas` |
| `fact_ventas.PARQUET` | vacío | `fact_ventas` |
| `fact_ventas_02.csv` | `01` | `fact_ventas_02` |
| `fact_ventas_01.csv` | vacío | `fact_ventas_01` |
| `fact.ventas_01.json` | `01` | `fact.ventas` |
| `fact_ventas_01.xlsx` | `01` | `fact_ventas_01.xlsx` |
| `fact_ventas_01` | `01` | `fact_ventas` |

- Actualizar la spec `bronze-ingestion` mediante el workflow OpenSpec: el requisito «Nombre de tabla y lectura por formato» y sus escenarios («Nombre JSON mensual», «CSV en mayúsculas») dejan de describir el comportamiento previo.

**Exclusiones**
- No se modifica la detección de formatos, la lectura de datos, rutas, jobs, `databricks.yml` ni `resources/`.
- No se añaden dependencias ni reglas nuevas de nulos, cantidades, importes, fechas o ratios.
- No hay cambios **BREAKING** de firma. Sí cambia el resultado para JSON, Parquet y CSV en mayúsculas, que antes conservaban la extensión; este es el efecto buscado.
- Existe otra función homónima en `src/utilities/file_ingestion.py` (firma con `Optional[str]`). Queda fuera del alcance de la HU, que solo nombra `src/common/schema.py`; su eventual alineación debe decidirse aparte.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities
- `bronze-ingestion`: el requisito «Nombre de tabla y lectura por formato» cambia. `normalize_table_name` pasa a eliminar la extensión final CSV, JSON o Parquet sin distinguir mayúsculas, antes del sufijo `_<mes>`, y a conservar extensiones no reconocidas, puntos internos y mayúsculas del nombre.

## Impact

- **Capa y dominios:** Bronze (ingesta). Afecta de forma transversal a los dominios que usan el runner (shared, comercial, finanzas, operaciones, gobierno) por la resolución del nombre de tabla y la consulta al diccionario en `src/common/notebook_runner.py`, que invoca `normalize_table_name`.
- **Código:** `src/common/schema.py` (modificación) y `tests/test_normalize_table_name.py` (nuevo). La prueba existente de `tests/test_project_structure.py` para CSV en minúsculas debe seguir siendo válida.
- **Especificación:** delta sobre `bronze-ingestion`.
- **APIs y dependencias:** firma pública sin cambios; sin dependencias nuevas.
- **Riesgo a considerar:** las tablas de archivos JSON/Parquet que antes se resolvían con la extensión en el nombre pasarán a resolverse sin ella, lo que podría coincidir con tablas ya existentes. No se asumen reglas de migración; se señala para la revisión del diseño.
- **Verificación:** ejecutar las pruebas nuevas y toda la suite `tests/` en el Job sandbox aislado del harness, con datos sintéticos, sin ejecutar jobs ni tocar tablas o catálogos de NaturaPet. Código, pruebas y OpenSpec se publican juntos en `feature/*` mediante PR hacia `develop`; merge y despliegue permanecen humanos.
