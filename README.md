# Naturapet_DLH

Repositorio base del proyecto `Naturapet_DLH` para Azure Databricks, ADLS Gen2 y GitHub Actions usando Databricks Asset Bundles.

## Configuracion inicial aplicada

- Workspace Databricks: `https://adb-7405606739630987.7.azuredatabricks.net`
- Storage account: `demodldb`
- Contenedor: `democodex`
- Catalogos por ambiente: `naturapet_dev`, `naturapet_qa`, `naturapet_prod`
- Dominios de datos: `comercial`, `finanzas`, `gobierno`, `operaciones`, `shared`
- Schemas por dominio: `*_bronze`, `*_silver`, `*_gold`

## Estructura de almacenamiento

Rutas base configuradas en formato `abfss://`:

- `external`: `abfss://democodex@demodldb.dfs.core.windows.net/external/<ambiente>/<dominio>/<capa>/2026/<mes>`
- `raw`: `abfss://democodex@demodldb.dfs.core.windows.net/raw/<ambiente>/<dominio>/2026/<mes>`
- `historic`: `abfss://democodex@demodldb.dfs.core.windows.net/historic/<dominio>/2026/<mes>`

## Estructura del repositorio

```text
.
|-- .github/
|   `-- workflows/
|       `-- databricks-cicd.yml
|-- conf/
|   |-- environments/
|   |   |-- dev.yml
|   |   |-- qa.yml
|   |   `-- prod.yml
|   `-- jobs/
|       `-- monthly_file_refresh.yml
|-- resources/
|   `-- jobs/
|       `-- monthly_file_refresh.job.yml
|-- notebooks/
|   |-- comercial/
|   |   |-- bronze/
|   |   |-- silver/
|   |   `-- gold/
|   |-- finanzas/
|   |   |-- bronze/
|   |   |-- silver/
|   |   `-- gold/
|   |-- gobierno/
|   |   |-- bronze/
|   |   |-- silver/
|   |   `-- gold/
|   |-- operaciones/
|   |   |-- bronze/
|   |   |-- silver/
|   |   `-- gold/
|   `-- shared/
|       |-- bronze/
|       |-- silver/
|       `-- gold/
|-- src/
|   |-- notebooks/
|   |   `-- monthly_file_refresh.py
|   `-- utilities/
|       `-- file_ingestion.py
|-- tests/
|   `-- test_project_structure.py
`-- databricks.yml
```

## CI/CD esperado

- Push a `develop`: valida y despliega a `dev`
- Push a `qa`: valida y despliega a `qa`
- Pull request hacia `main`: valida el bundle y los tests
- Push a `main` despues de aprobar y hacer merge del PR: valida y despliega a `prod`

La aprobacion humana para produccion queda soportada por la regla del pull request y por las protecciones del environment `prod` en GitHub.

## Secrets requeridos en GitHub Environments

- `DATABRICKS_HOST`
- `DATABRICKS_CLIENT_ID`

## Comandos utiles

```powershell
databricks bundle validate --target dev
databricks bundle deploy --target dev
databricks bundle validate --target qa
databricks bundle deploy --target qa
databricks bundle validate --target prod
databricks bundle deploy --target prod
```

## Carga bronze implementada

Cada dominio tiene dos notebooks en `notebooks/<dominio>/bronze/`:

- `load_to_delta.py`: descubre archivos en `raw/<ambiente>/<dominio>/2026`, hace `merge` incremental para carpetas mensuales (`01`, `02`, `03`) y `merge` completo para archivos ubicados directamente en `2026`.
- `archive_to_historic.py`: mueve a `historic/<dominio>/2026/...` solo los archivos con carga exitosa registrada en la tabla de auditoria `bronze_file_load_audit`.

La logica compartida vive en:

- `notebooks/shared/bronze/_common.py`
- `notebooks/shared/bronze/_load_domain_bronze.py`
- `notebooks/shared/bronze/_archive_domain_raw.py`

### Convenciones de carga

- Tabla destino por archivo fuente, ubicada en el schema bronze del dominio correspondiente.
- Catalogos por ambiente: `naturapet_dev`, `naturapet_qa`, `naturapet_prod`.
- Ruta externa por tabla: `abfss://.../external/<ambiente>/<dominio>/bronze/2026/<tabla>`.
- Archivos mensuales: se identifican por carpeta y por sufijo `_01`, `_02`, `_03`, pero se consolidan en la misma tabla delta.
- Archivos sin carpeta mensual: se cargan como refresco completo tipo upsert, insertando o actualizando solo registros nuevos.
- Llaves de `merge`: se derivan desde `raw/<ambiente>/gobierno/2026/data_dictionary.csv`; si una tabla no tiene PK declarada se usa un hash de fila.
