# Proposal

## Why

HU-BRONZE-001-Codex-Local: el normalizador actual solo retira `.csv` en minúsculas. JSON, Parquet y CSV con otras capitalizaciones quedan asociados a nombres incorrectos para el diccionario Bronze.

## What Changes

- Retirar una extensión final CSV, JSON o Parquet sin distinguir mayúsculas; preservar el nombre original.
- Después retirar únicamente el sufijo mensual exacto cuando se informa `month`.
- Agregar pruebas parametrizadas de los once criterios proporcionados por el responsable.
- Actualizar el contrato `bronze-ingestion` mediante delta, verificación, sincronización y archivo OpenSpec.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `bronze-ingestion`: normalización del nombre de tabla y sus escenarios; conservar el contrato de detección y lectura.

## Impact

Solo `normalize_table_name` en `src/common/schema.py`, el nuevo `tests/test_normalize_table_name.py` y artefactos OpenSpec. Sin dependencias nuevas. Excluidos detección, lectores, rutas, jobs, `databricks.yml` y `resources/`. Pruebas sintéticas en el Job aislado del harness; PR `feature/*` hacia `develop`, con merge y despliegue humanos.
