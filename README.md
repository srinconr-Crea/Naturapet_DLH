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

## Pendiente funcional

La logica del job `monthly_file_refresh` sigue siendo un placeholder tecnico. Falta reemplazarla por la lectura real de archivos Naturapet, reglas de transformacion y validaciones de negocio antes de usarlo en productivo.
