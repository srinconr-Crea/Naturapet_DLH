# Arquitectura y dependencias del lakehouse

## Purpose

Describir la distribución actual de responsabilidades técnicas, productos y dependencias entre dominios y capas.

Contrato del comportamiento implementado, documentado mediante lectura estática de `develop@eb35b87b79eb541c4832fccc8f8825412755f498`. Los escenarios describen resultados esperados del código actual; no constituyen evidencia de ejecución de Spark ni de despliegue en Databricks.

## Sources

- [README.md](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/README.md)
- [databricks.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/databricks.yml)
- [resources/jobs/monthly_data_mesh_refresh.job.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/resources/jobs/monthly_data_mesh_refresh.job.yml)
- [resources/jobs/monthly_file_refresh.job.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/resources/jobs/monthly_file_refresh.job.yml)
- [resources/jobs/monthly_silver_refresh.job.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/resources/jobs/monthly_silver_refresh.job.yml)
- [resources/jobs/monthly_gold_refresh.job.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/resources/jobs/monthly_gold_refresh.job.yml)
- [src/common/notebook_runner.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/src/common/notebook_runner.py)

- [notebooks/comercial/gold/01_comercial_marts.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/comercial/gold/01_comercial_marts.ipynb)
- [notebooks/operaciones/gold/02_operaciones_marts.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/operaciones/gold/02_operaciones_marts.ipynb)
- [notebooks/finanzas/gold/03_finanzas_objetivos.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/finanzas/gold/03_finanzas_objetivos.ipynb)
- [notebooks/shared/gold/04_kpis_ejecutivos.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/shared/gold/04_kpis_ejecutivos.ipynb)
- [notebooks/gobierno/gold/05_quality_checks.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/gobierno/gold/05_quality_checks.ipynb)
- [src/common/delta_load.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/src/common/delta_load.py)
- [src/common/config.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/src/common/config.py)

## Requirements

### Requirement: Separación lógica del mesh

La arquitectura SHALL organizar notebooks por dominio y capa, dentro de un único bundle y un workspace común. Los targets SHALL separar catálogos y raíces Workspace; los schemas SHALL seguir <dominio>_<capa>. shared SHALL concentrar dimensiones reutilizadas por otros dominios, sin atribuirse al repositorio responsables humanos, equipos propietarios ni acuerdos de servicio que no están declarados.

#### Scenario: Resolución de dominio
- **WHEN** una transformación comercial consulta dimensiones compartidas
- **THEN** las resuelve en shared_silver dentro del catálogo recibido por el notebook

### Requirement: Flujo de capas y responsabilidades

Bronze SHALL validar archivos contra el diccionario, añadir trazabilidad, escribir Delta externa y archivar fuentes exitosas. Silver SHALL transformar las tablas Bronze mediante cinco pasos y escribir tablas incrementales y resultados de calidad. Gold SHALL leer tablas Silver y marts Gold para publicar agregados y reportes externos. Las tablas SHALL registrarse en Unity Catalog; el bundle no SHALL describirse como provisión declarativa de catálogos, credenciales de storage o external locations, ya que sus recursos actuales son Jobs.

#### Scenario: Registro de tablas
- **WHEN** el runner Bronze recibe un catálogo existente y un schema ausente
- **THEN** intenta CREATE SCHEMA IF NOT EXISTS y luego registra tablas externas; no crea el catálogo

### Requirement: Dependencias entre dominios

Los marts comerciales SHALL consumir comercial_silver y dimensiones shared_silver. Operaciones Gold SHALL consumir operaciones_silver, shared_silver y ventas de comercial_silver. Finanzas Gold SHALL consumir finanzas_silver, comercial_silver, operaciones_silver y shared_silver. Los KPIs ejecutivos SHALL consumir marts comercial_gold, operaciones_gold y finanzas_gold. Gobierno Gold SHALL conciliar los KPIs shared_gold con comercial_silver y resumen_mensual_validacion de gobierno_silver.

#### Scenario: Finanzas con fuentes comerciales ausentes
- **WHEN** el notebook financiero intenta leer fact_ventas_cabecera de comercial_silver y la tabla no existe
- **THEN** la lectura Spark falla; no existe un fallback a una tabla vacía

#### Scenario: Consumo ejecutivo
- **WHEN** se prepara mart_kpis_ejecutivos_mensual
- **THEN** sus entradas proceden de los marts de las tres áreas y no de una ejecución Bronze directa

### Requirement: Dependencia de metadatos de gobierno

Los runners Bronze SHALL cargar el diccionario desde raw/<env>/gobierno/<año>/data_dictionary.csv cuando hay archivos. El Job Bronze SHALL iniciar por shared y procesar gobierno al final. La disponibilidad del archivo de diccionario en raw SHALL ser un prerrequisito de las cargas con fuentes, independiente de que gobierno ya haya cargado sus tablas.

#### Scenario: Primera carga shared
- **WHEN** hay archivos shared y falta el diccionario de gobierno en raw
- **THEN** la carga del diccionario falla antes de entrar al procesamiento individual de archivos

### Requirement: Límites de aislamiento físico

raw y external SHALL incluir ambiente en sus rutas por defecto; historic SHALL usar historic/<dominio>/<año>[/<mes>] sin segmento de ambiente. Los tres targets SHALL apuntar al mismo host de workspace declarado. Las escrituras de cada tabla y el movimiento de archivos SHALL ser operaciones separadas; no SHALL atribuirse atomicidad global al mesh.

#### Scenario: Histórico entre ambientes
- **WHEN** dev y qa archivan el mismo dominio, año, mes y nombre usando defaults
- **THEN** construyen la misma ruta histórica aunque sus raw y catálogos estén separados
