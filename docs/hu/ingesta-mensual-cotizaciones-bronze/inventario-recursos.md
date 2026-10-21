# Inventario de recursos — cotizaciones Bronze

Estado verificado al finalizar las pruebas del 2026-10-20. Inventario incremental, recibos, rutas, tablas, limpieza y límites: [registro completo](runtime/inventario.md).

| Recurso | Resultado | Persistencia |
| --- | --- | --- |
| Catálogo crea_cotizaciones_test_20261020_01a15a7c | 41 schemas de prueba + default/information_schema, 32 tablas EXTERNAL | Conservado, fuera de catálogos NaturaPet |
| Raíz abfss://demo@demodldb.dfs.core.windows.net/_tests/cotizaciones/20261020_01a15a7c | Fixtures, originales, evidencia, Delta auxiliares, logs e histórico de intentos1/3 | Conservada; sin limpieza general |
| Workspace /Users/srinconr@creasistemas.com/crea_tests/20261020_01a15a7c | 11 archivos Python y 2 notebooks de pruebas/inventario | Conservado |
| Clúster temporal 1020-210854-9y22c5h7 | DBR16.4, Standard_D4ads_v6; estado TERMINATED comprobado | Cómputo terminado; definición aún conservada |
| Warehouse preexistente naturapet_serverless_wh / dd74907a9f5cb481 | Utilizado para creación/verificaciones SQL; estado final STOPPED, configuración original | Conservado |
| Ejecuciones únicas e historial | Intentos1/2 fallidos; intento3 SUCCESS, 14 criterios passed; inspecciones1/3 SUCCESS | Historial administrado por Databricks; sin job guardado ni schedule |

Resultado canónico: [matriz CA01–CA14](runtime/validated-result.json). Recursos exactos: [resumen de inspección final](runtime/resource-summary-attempt03.json). Recibos: [clúster terminado](runtime/cluster-status.json) y [warehouse detenido](runtime/warehouse-final-state.json).

No se modificaron recursos de catálogos naturapet*, ubicaciones externas, credenciales, grants ni jobs existentes. Eliminar el catálogo en el futuro no eliminará los archivos de tablas externas; la raíz y carpeta workspace requieren limpieza separada y explícita. No se ejecutó esa limpieza.
