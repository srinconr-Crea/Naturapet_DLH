# Proposal

## Why

Hoy `normalize_table_name()` en `src/common/schema.py` solo elimina la extensión `.csv` en minúsculas. Los archivos `.json` o `.parquet`, o con extensión en mayúsculas (por ejemplo `.CSV`), conservan la extensión en el nombre de tabla y no se asocian al diccionario de datos ni al destino Bronze esperado. La ingesta Bronze ya admite CSV, JSON y Parquet, por lo que la normalización del nombre debe ser coherente con esos formatos.

## What Changes

**Comportamiento actual (evidencia: lectura de `src/common/schema.py`):**
- `normalize_table_name(file_name, month="")` aplica `removesuffix(".csv")`, sensible a mayúsculas y solo para CSV.
- Después elimina el sufijo `_<month>` si `month` está informado y coincide exactamente al final.
- La spec vigente `bronze-ingestion` solo documenta el caso `fact_ventas_cabecera_01.csv` → `fact_ventas_cabecera`. No hay evidencia de pruebas dedicadas a esta función.

**Cambio propuesto:**
- Modificar `normalize_table_name()` para eliminar primero la extensión final `.csv`, `.json` o `.parquet`, sin distinguir mayúsculas.
- Eliminar después el sufijo `_<month>` únicamente si `month` está informado y coincide exactamente al final del nombre ya sin extensión.
- Mantener la firma actual `normalize_table_name(file_name: str, month: str = "") -> str`.
- Preservar las mayúsculas del nombre de tabla, conservar extensiones no reconocidas (por ejemplo `.xlsx`) y conservar los puntos internos del nombre.
- Agregar pruebas parametrizadas en `tests/test_normalize_table_name.py` con datos sintéticos, que cubran los criterios de aceptación (entrada / month / resultado):
  - `fact_ventas_01.csv` / `01` / `fact_ventas`
  - `fact_ventas_01.json` / `01` / `fact_ventas`
  - `fact_ventas_01.parquet` / `01` / `fact_ventas`
  - `Fact_Ventas_01.CSV` / `01` / `Fact_Ventas`
  - `fact_ventas_01.JsOn` / `01` / `fact_ventas`
  - `fact_ventas.PARQUET` / vacío / `fact_ventas`
  - `fact_ventas_02.csv` / `01` / `fact_ventas_02`
  - `fact_ventas_01.csv` / vacío / `fact_ventas_01`
  - `fact.ventas_01.json` / `01` / `fact.ventas`
  - `fact_ventas_01.xlsx` / `01` / `fact_ventas_01.xlsx`
  - `fact_ventas_01` / `01` / `fact_ventas`
- Actualizar la spec `bronze-ingestion` mediante el workflow OpenSpec (delta del requisito de descubrimiento y formatos admitidos).

**Fuera de alcance:**
- Detección de formatos, lectura de datos, rutas, jobs, `databricks.yml` y `resources/`.
- Nuevas reglas de nulos, cantidades, importes, fechas o ratios.
- Ejecución de jobs o pipelines, cambios en tablas o catálogos de NaturaPet, nuevas dependencias y despliegues.

No hay cambios **BREAKING** en la firma. Como efecto observable, los nombres de archivos `.json`, `.parquet` o con extensión en mayúsculas pasan a normalizarse sin extensión.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `bronze-ingestion`: el requisito «Descubrimiento y formatos admitidos» pasa a especificar que `normalize_table_name` elimina la extensión final CSV, JSON o Parquet sin distinguir mayúsculas, preserva mayúsculas del nombre, conserva extensiones no reconocidas y puntos internos, y elimina `_<month>` solo si coincide exactamente al final tras quitar la extensión.

## Impact

- **Capa/dominio:** Bronze, utilidad común compartida entre dominios (`src/common/`). Las capas Silver y Gold no cambian su lógica.
- **Código:** `src/common/schema.py` (solo `normalize_table_name`).
- **Pruebas:** nuevo `tests/test_normalize_table_name.py`; se ejecutará además toda la suite `tests/` en el Job sandbox aislado del harness.
- **Especificación:** delta sobre `bronze-ingestion`.
- **Sin impacto en:** APIs externas, dependencias, jobs, bundle, recursos, datos ni tablas de NaturaPet.
- **Riesgo a validar en diseño:** confirmar en el repositorio los usos de `normalize_table_name` (por ejemplo en `src/common/io.py` y el runner) para asegurar que ningún consumidor dependa de recibir el nombre con extensión no CSV.
- **Entrega:** código, pruebas y OpenSpec se publican juntos en `feature/*` mediante PR hacia `develop`; merge y despliegue permanecen humanos.
