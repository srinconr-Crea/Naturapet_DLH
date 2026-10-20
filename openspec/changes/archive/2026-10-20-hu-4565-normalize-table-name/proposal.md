# Proposal

## Why

HU-4565: Bronze admite CSV, JSON y Parquet, pero `src/common/schema.py` solo elimina `.csv` literal. Esto deja extensiones JSON, Parquet y CSV en mayúsculas en la clave usada para resolver tabla y diccionario.

## What Changes

- Eliminar una única extensión final `.csv`, `.json` o `.parquet`, sin distinguir mayúsculas; preservar las mayúsculas del nombre restante y sus puntos internos.
- Después eliminar una única terminación `_<month>` solo si `month` está informado y coincide exactamente al final; mantener firma actual.
- Conservar extensiones no reconocidas y nombres sin extensión; agregar pruebas parametrizadas en `tests/test_normalize_table_name.py` (archivo nuevo).
- Sustituir mediante delta el contrato anterior de normalización en `bronze-ingestion`, preservando detección y lectura.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `bronze-ingestion`: modificar «Nombre de tabla y lectura por formato» para normalizar los tres formatos admitidos y explicitar orden, coincidencia mensual exacta y conservación del nombre.

## Impact

- Código futuro: únicamente `normalize_table_name()` en `src/common/schema.py`; pruebas nuevas en `tests/test_normalize_table_name.py`.
- Bronze compartido por los cinco dominios; el runner ya consume este nombre para tabla, ruta y consulta al diccionario. No cambia claves ni contenido del diccionario.
- Fuera de alcance: homónimo de `src/utilities/file_ingestion.py`, detección de formatos, lectura, rutas, notebooks, jobs, `databricks.yml`, `resources/`, Silver y Gold.
- Criterios: extensiones reconocidas en minúsculas/mayúsculas/mezcladas, preservación de caja, eliminación mensual en el orden indicado, ausencia/discordancia de mes, extensiones desconocidas y puntos internos cubiertos con fixtures sintéticos locales.
- Evidencia actual: lectura estática del código y spec; no se afirma implementación ni runtime Spark verificado.
