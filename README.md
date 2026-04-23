# Proyecto base Databricks + ADLS + GitHub

Este repositorio es un esqueleto inicial para un proyecto de Azure Databricks almacenado en GitHub y desplegado con Databricks Asset Bundles.

La base sigue estas decisiones:

- Ambientes operativos: `dev`, `qa`, `prod`
- Ramas de promoción: `develop` -> `dev`, `qa` -> `qa`, `main` -> `prod`
- Frecuencia inicial del proceso: mensual
- Despliegue por GitHub Actions con OIDC o secrets por environment
- Estructura de almacenamiento alineada con ADLS Gen2 bajo `/external/<ambiente>/...`

## Estructura

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
|   |-- area1/
|   |   |-- bronze/
|   |   |-- silver/
|   |   `-- gold/
|   |-- area2/
|   |   |-- bronze/
|   |   |-- silver/
|   |   `-- gold/
|   `-- area3/
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
|-- databricks.yml
`-- .gitignore
```

## Qué debes completar antes de usarlo en cliente

1. Reemplazar valores de ejemplo en `conf/environments/*.yml`.
2. Crear en GitHub los environments `dev`, `qa` y `prod`.
3. Cargar secrets y variables por environment.
4. Ajustar nombres reales de workspace, catálogos, schemas, rutas ADLS y service principal.
5. Validar localmente con Databricks CLI.

## Variables esperadas en GitHub Environments

- `DATABRICKS_HOST`
- `DATABRICKS_CLIENT_ID` o configuración OIDC aprobada
- `DATABRICKS_TENANT_ID` si aplica en tu modelo de autenticación
- `PROJECT_NAME`
- `AREA_NAME`
- `DATA_DOMAIN`
- `STORAGE_ACCOUNT`
- `STORAGE_CONTAINER`

## Flujo recomendado

1. Desarrollo en `develop`.
2. Merge aprobado hacia `qa`.
3. Pruebas y UAT en `qa`.
4. Merge aprobado hacia `main`.
5. Despliegue a `prod` desde GitHub Actions con aprobación del environment.

## Comandos útiles

```powershell
databricks bundle validate --target dev
databricks bundle deploy --target dev
databricks bundle validate --target qa
databricks bundle validate --target prod
```

## Nota importante

Este proyecto deja un job mensual mínimo como punto de partida. La lógica de negocio todavía es placeholder y está preparada para que la completes cuando definas la fuente real de archivos, el patrón de ingesta y las validaciones de negocio.

Los archivos bajo `conf/environments/` quedan como plantilla documental para levantar el proyecto con el cliente, pero el workflow base de GitHub Actions toma sus valores desde variables configuradas en cada GitHub Environment.
