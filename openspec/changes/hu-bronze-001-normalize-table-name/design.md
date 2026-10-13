# Design

## Context

Base `develop@c5efcf154c7e56101e6dd6c3ea830f6512e6b184`. El usuario proporcionó el algoritmo, once criterios, alcance, pruebas y publicación autorizados. Este diseño concreta ese alcance sin ampliarlo.

## Decisions

Separar el último punto mediante `rpartition`. Comparar solo la extensión con `lower()` y retirar una extensión reconocida. Mantener la capitalización y los puntos internos del prefijo. Después aplicar la condición mensual existente, sensible a coincidencia exacta. Mantener firma y retorno `str`.

No introducir normalización de meses, extensiones desconocidas, entradas nulas ni nuevas reglas de negocio. El contrato actual recibe cadenas; el mes vacío conserva el sufijo mensual.

## Manifiesto de operaciones y archivos

- Modificar únicamente el cuerpo de `normalize_table_name` en `src/common/schema.py`.
- Crear `tests/test_normalize_table_name.py` con los once criterios literales de la HU.
- Crear propuesta, diseño, delta, tareas y evidencia dentro de este cambio OpenSpec; sincronizar solo el requisito afectado de `openspec/specs/bronze-ingestion/spec.md`; archivar el cambio verificado.
- Ejecutar pytest focalizado y toda `tests/` en Job `611081415041874`, perfil `CREA_DEV`; solo transportar un ZIP de fuentes sintéticas al volumen sandbox. No ejecutar bundle ni recursos cliente.
- Publicar en `feature/hu-bronze-001-normalize-table-name` mediante PR hacia `develop`; no merge ni despliegue.

## Verification

TDD: capturar fallos esperados sobre la implementación original antes del cambio y verificar los once criterios después. Ejecutar también la suite existente en sandbox. Sus operaciones Spark/Delta están simuladas mediante mocks; las rutas de cliente se comparan como cadenas. El proceso de pytest no recibe credenciales de la App.

Conservar IDs de ejecución, SHA-256 del ZIP y resultados. Esta HU no certifica las evaluaciones pendientes de Local-Harness 06/07 ni habilita automáticamente el incremento 08.

## Recovery

El cambio mantiene la firma. Los consumidores JSON/Parquet recibirán ahora el nombre sin extensión conforme a la HU. La recuperación consiste en revertir el commit del PR; no existen cambios ni migraciones de datos.
