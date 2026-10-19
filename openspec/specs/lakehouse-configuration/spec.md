# Configuración del lakehouse

## Purpose

Definir ambientes, dominios, capas y resolución de rutas para interpretar una HU sin confundir datos cliente con recursos del harness.

Contrato del comportamiento implementado, documentado mediante lectura estática de `develop@eb35b87b79eb541c4832fccc8f8825412755f498`. Los escenarios describen resultados esperados del código actual; no constituyen evidencia de ejecución de Spark ni de despliegue en Databricks.

## Sources

- [src/common/config.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/src/common/config.py)
- [databricks.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/databricks.yml)
- [README.md](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/README.md)
- [tests/test_project_structure.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/tests/test_project_structure.py)

- [src/common/notebook_entry.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/src/common/notebook_entry.py)
- [notebooks/shared/bronze/load_to_delta.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/shared/bronze/load_to_delta.ipynb)
- [notebooks/shared/silver/01_schema_standardization.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/shared/silver/01_schema_standardization.ipynb)
- [notebooks/comercial/gold/01_comercial_marts.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/comercial/gold/01_comercial_marts.ipynb)
- [conf/environments/dev.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/conf/environments/dev.yml)
- [conf/environments/qa.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/conf/environments/qa.yml)
- [conf/environments/prod.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/conf/environments/prod.yml)
- [resources/jobs/monthly_file_refresh.job.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/resources/jobs/monthly_file_refresh.job.yml)

## Requirements

### Requirement: Resolución de ambiente y catálogo

La configuración común SHALL resolver el ambiente desde APP_ENV, después ENV y por defecto dev; SHALL aceptar dev, qa y prod y rechazar otros valores. Sin override CATALOG, SHALL seleccionar naturapet_dev, naturapet_qa o naturapet_prod respectivamente.

#### Scenario: Configuración por defecto de comercial
- **WHEN** APP_ENV es dev, el área es comercial y no se sobrescriben año ni rutas
- **THEN** el catálogo es naturapet_dev, el esquema Bronze es comercial_bronze y el año es 2026

#### Scenario: Ambiente inválido
- **WHEN** se solicita un ambiente que no pertenece a dev, qa o prod
- **THEN** get_config genera ValueError

### Requirement: Separación por dominio y capa

La organización del cliente SHALL conservar los dominios shared, comercial, finanzas, operaciones y gobierno y las capas bronze, silver y gold. Los nombres de esquemas SHALL seguir <dominio>_<capa>; el bundle SHALL resolver el catálogo y la raíz Workspace por target.

#### Scenario: Target qa
- **WHEN** se resuelve el target qa del bundle
- **THEN** su catálogo es naturapet_qa y su raíz es /Workspace/Naturapet_BI/qa

### Requirement: Contratos de rutas Bronze y de histórico

Sin overrides, el módulo común SHALL resolver raw/<env>/<dominio>/<año>, external/<env>/<dominio>/bronze/<año>/<tabla> e historic/<dominio>/<año>[/<mes>]/<archivo> bajo la URI ADLS configurada. La construcción de rutas raw SHALL convertir separadores Windows a /. El diccionario SHALL resolverse por defecto en raw/<env>/gobierno/<año>/data_dictionary.csv.

#### Scenario: Archivo mensual
- **WHEN** se construye el histórico de fact_ventas_cabecera_01.csv para comercial, año 2026 y mes 01
- **THEN** la ruta termina en historic/comercial/2026/01/fact_ventas_cabecera_01.csv

#### Scenario: Diferencia entre ruta de variable y ruta de tabla
- **WHEN** una HU consulta las variables external_base_path del bundle y el destino Bronze del módulo común
- **THEN** se conserva que la variable del bundle incluye mes, mientras build_bronze_table_path sitúa la tabla bajo año/tabla y su escritura particiona por metadatos de año y mes


### Requirement: Precedencia de widgets y variables de entorno

El bootstrap Bronze SHALL leer los widgets environment, catalog_name y data_year, asignar APP_ENV, AREA y DATA_YEAR al proceso y asignar CATALOG únicamente cuando catalog_name no esté vacío. El área SHALL proceder del notebook que invoca el runner. get_config SHALL resolver las rutas desde los overrides de entorno RAW_ENV_ROOT, EXTERNAL_ENV_ROOT, HISTORIC_ROOT y sus variantes por área/año antes de usar sus defaults; DATA_DICTIONARY_PATH y AUDIT_TABLE_PATH SHALL permitir overrides independientes.

#### Scenario: Parámetros Bronze
- **WHEN** el notebook comercial recibe environment=qa, catalog_name=naturapet_qa y data_year=2027
- **THEN** bootstrap_runtime fija APP_ENV=qa, AREA=comercial, DATA_YEAR=2027 y CATALOG=naturapet_qa antes de get_config

#### Scenario: Catálogo vacío
- **WHEN** catalog_name está vacío y el proceso ya tiene CATALOG configurado
- **THEN** bootstrap_runtime no borra CATALOG; get_config conserva ese override

### Requirement: Resolución distinta de storage entre capas

Bronze SHALL usar STORAGE_URI=abfss://democodex@demodldb.dfs.core.windows.net como default del módulo común. Su bootstrap SHALL consumir solo environment, catalog_name y data_year; los parámetros storage_account y storage_container enviados por el Job no modifican esa URI. Silver y Gold SHALL construir su URI a partir de esos dos widgets. Cambiar las variables del bundle por sí solo no SHALL describirse como cambio uniforme de storage de todas las capas.

#### Scenario: Storage personalizado por Job
- **WHEN** el Job envía otra cuenta y contenedor sin overrides de rutas de entorno Bronze
- **THEN** Silver y Gold construyen su URI con esos widgets y Bronze conserva los defaults del módulo común

### Requirement: Configuraciones declarativas y raíces Workspace

databricks.yml SHALL incluir resources/**/*.yml y fijar /Workspace/Naturapet_BI/<target> como root_path. Los YAML de conf/environments SHALL conservar los valores descriptivos existentes: ~/.bundle/Naturapet_DLH/dev para dev y /Workspace/Shared/Naturapet_DLH/<target> para qa/prod. El workflow y los módulos comunes actuales no SHALL atribuirse lectura automática de esos YAML. Silver SHALL añadir /Workspace/Naturapet_BI/<environment>/files a sys.path; Bronze SHALL buscar un ancestro del directorio de ejecución que contenga src/common/config.py.

#### Scenario: Raíz efectiva del bundle
- **WHEN** se consulta el target dev de databricks.yml
- **THEN** su root_path es /Workspace/Naturapet_BI/dev, aunque conf/environments/dev.yml conserve otra raíz

#### Scenario: Importación Bronze sin raíz
- **WHEN** ningún ancestro del directorio actual contiene src/common/config.py
- **THEN** add_repo_root genera RuntimeError

### Requirement: Año fijo y ausencia de selector mensual de runtime

El bundle y los widgets SHALL tener data_year=2026 como default. data_month SHALL existir como variable del bundle con default 01 para sus rutas base; los Jobs actuales no SHALL transmitir un widget de selección mensual. Bronze SHALL explorar el directorio anual y sus carpetas mensuales, y Gold SHALL leer las tablas fuente completas sin filtro por data_year o data_month; data_year en Gold determina la raíz física de salida.

#### Scenario: Ejecución de un mes posterior
- **WHEN** se ejecuta el Job en otro mes sin modificar parámetros
- **THEN** data_year conserva su valor configurado y Bronze descubre los archivos disponibles bajo el año; la fecha del schedule no selecciona automáticamente un mes
