# Proposal

## Why

Incorporar cotizaciones comerciales mensuales a Bronze con trazabilidad del original, rechazo técnico controlado e idempotencia. El flujo compartido actual infiere CSV, convierte tipos y escoge una fila por PK; no ofrece cuarentena por registro ni conciliación por contenido de archivo.

## What Changes

- Especializar exclusivamente `comercial.fact_cotizaciones`, mediante contrato versionado de 20 campos y dispatch por entidad antes de inferir o convertir. Mantener intacto el comportamiento de las demás entidades y dominios (CA14).
- Resolver `fact_cotizaciones_MM.csv` al nombre lógico único, cotejando carpeta y parámetros de año/mes; preservar nombre físico (CA01).
- Leer CSV Unicode con quoting explícito, conservar archivo/payload original e identidad estable por registro, limpiar IDs y convertir fechas/números con errores observables (CA02–04, CA06–08).
- Cuarentenar PK vacías y grupos conflictivos; comparar después de normalizar y consolidar duplicados idénticos. Registrar todos los errores de cada registro sin duplicar rechazados (CA05, CA11).
- Conservar alertas de negocio e importes originales, incluidos cantidad/vigencia no positivas y nulos admitidos; no completar con cero (CA09–10).
- Hacer merge por `cotizacion_id`: actualizar existentes, insertar nuevas y conservar ausentes, sin versiones mensuales de una misma cotización. Identificar contenido y evitar repetición de cuarentena (CA12).
- Persistir principal, cuarentena, auditoría conciliada y log Delta auxiliar de fallos; permitir SUCCESS/archivo solo al completar persistencia. Reintentos recuperables, incluidos fallos del log y colisiones de histórico (CA13).

## Capabilities

### New Capabilities

Ninguna: reutilizar límites existentes de ingesta y contratos.

### Modified Capabilities

- `bronze-ingestion`: excepción acotada para lectura, validación, deduplicación, merge, identidad, conciliación y recuperación de cotizaciones.
- `data-contracts`: contrato explícito de cotizaciones y precedencia sobre el diccionario genérico únicamente para esa entidad Bronze.

## Impact

Extensión prevista en `src/common/` con módulos específicos y puntos de integración en runner/config/archivo; pruebas sintéticas locales y notebook de integración dedicado. No cambiar normalizador genérico, utilidades alternativas, Silver, Gold, jobs, bundle, CI ni datos externos durante planificación. Las specs actuales documentan comportamiento genérico: sus escenarios se preservan y las excepciones se nombran expresamente. No incluye deploy, ejecución remota, permisos, archivo OpenSpec o publicación sin aprobación posterior.

La propuesta define decisiones técnicas revisables en design.md; no acredita implementación ni runtime. La implementación fue autorizada posteriormente y se encuentra en validación; sus resultados reales se registran en evidencia.md.

### Validación aislada autorizada — 2026-10-20

La persona autorizó actualizar este plan y continuar la adaptación de guardas/pruebas: catálogo nuevo `crea_cotizaciones_test_20261020_01a15a7c`, storage `abfss://demo@demodldb.dfs.core.windows.net/_tests/cotizaciones/20261020_01a15a7c`, warehouse existente `naturapet_serverless_wh` y clúster clásico temporal compatible con Python/RDD. Prohibidas escrituras en catálogos `naturapet*`. Crear solo recursos de prueba dentro del aislamiento aprobado, sin external locations, credenciales o permisos nuevos. Entregar inventario de recursos, persistencia y limpieza; terminar el clúster al final y conservar warehouse, catálogo, fixtures y workspace para inspección. La persona pidió crear el PR al terminar; se mantiene la aprobación específica posterior de archive del candidato final.
