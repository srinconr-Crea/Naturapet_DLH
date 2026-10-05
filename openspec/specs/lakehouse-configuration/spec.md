# Configuración del lakehouse

## Purpose

Definir ambientes, dominios, capas y resolución de rutas para interpretar una HU sin confundir datos cliente con recursos del harness.

Base documental sugerida, derivada por lectura de código en `develop@9c48831022a329902f765058de37e6d0a1528eb7`. Requiere revisión humana antes de adoptarse; no acredita ejecución de Spark ni despliegue Databricks.

## Sources

- [src/common/config.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/src/common/config.py)
- [databricks.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/databricks.yml)
- [README.md](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/README.md)
- [tests/test_project_structure.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/tests/test_project_structure.py)

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

