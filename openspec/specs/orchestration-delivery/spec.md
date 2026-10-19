# Orquestación y entrega del lakehouse

## Purpose

Definir las dependencias entre capas, schedules y comportamiento de entrega existentes del lakehouse.

Contrato del comportamiento implementado, documentado mediante lectura estática de `develop@eb35b87b79eb541c4832fccc8f8825412755f498`. Los escenarios describen resultados esperados del código actual; no constituyen evidencia de ejecución de Spark ni de despliegue en Databricks.

## Sources

- [resources/jobs/monthly_data_mesh_refresh.job.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/resources/jobs/monthly_data_mesh_refresh.job.yml)
- [resources/jobs/monthly_file_refresh.job.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/resources/jobs/monthly_file_refresh.job.yml)
- [resources/jobs/monthly_silver_refresh.job.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/resources/jobs/monthly_silver_refresh.job.yml)
- [resources/jobs/monthly_gold_refresh.job.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/resources/jobs/monthly_gold_refresh.job.yml)
- [.github/workflows/databricks-cicd.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/.github/workflows/databricks-cicd.yml)
- [tests/test_project_structure.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/tests/test_project_structure.py)

## Requirements

### Requirement: Secuencia Data Mesh

monthly_data_mesh_refresh SHALL invocar monthly_file_refresh, después monthly_silver_refresh y después monthly_gold_refresh mediante run_job_task y dependencias entre tareas. SHALL usar el service principal referenciado por variable del bundle; su definición actual no SHALL atribuirse un schedule propio.

#### Scenario: Ejecución del orquestador
- **WHEN** se ejecuta monthly_data_mesh_refresh
- **THEN** Silver depende de Bronze y Gold depende de Silver

### Requirement: Schedules y concurrencia de las capas

Los jobs de capa SHALL conservar schedules mensuales el día 1 a las 06:00 Bronze, 06:30 Silver y 07:00 Gold, en America/Bogota, con max_concurrent_runs=1 y queue.enabled=true. Estos horarios independientes no SHALL presentarse como garantía de finalización de la capa previa; esa dependencia existe en el orquestador.

#### Scenario: Silver programado
- **WHEN** se consulta el schedule de monthly_silver_refresh
- **THEN** su expresión es 0 30 6 1 * ? y su zona es America/Bogota

### Requirement: Dependencias internas Gold

Gold SHALL ejecutar marts comercial, operaciones y finanzas antes de kpis_ejecutivos_gold y gold_quality_checks después de los KPIs. Bronze SHALL encadenar carga y archivo por dominio en la definición existente; Silver SHALL mantener los cinco pasos por dominio y las dependencias compartidas declaradas.

#### Scenario: KPI ejecutivo
- **WHEN** se resuelven las dependencias de kpis_ejecutivos_gold
- **THEN** exige las tareas comercial_gold_marts, operaciones_gold_marts y finanzas_objetivos_gold

### Requirement: Eventos y targets CI actuales

El workflow SHALL resolver develop→dev, qa→qa y main→prod. En la revisión fuente SHALL dispararse por push a esas ramas, PR hacia main y workflow_dispatch. SHALL ejecutar pytest y validar el bundle antes del despliegue; en PR hacia main SHALL deshabilitar despliegue. No SHALL atribuirse al workflow actual validación automática de PR hacia develop o pushes feature/*.

#### Scenario: Push a develop
- **WHEN** un merge humano genera un push a develop
- **THEN** el workflow resuelve dev y habilita despliegue después de sus validaciones

#### Scenario: PR hacia main
- **WHEN** el evento es pull_request con base main
- **THEN** se resuelve prod para validación y should_deploy es false

### Requirement: Alcance de las pruebas existentes

La evidencia local SHALL distinguir las pruebas unitarias de utilidades y mocks Delta de una ejecución real del lakehouse. La aprobación y publicación del harness SHALL mantener sus propios controles y pruebas; el workflow cliente no SHALL tomarse como sustituto de la verificación del candidato.

#### Scenario: Suite local satisfactoria
- **WHEN** tests/test_project_structure.py pasa sin Spark ni conexiones Databricks
- **THEN** se acredita únicamente el alcance unitario de esa suite y no el resultado real de notebooks, jobs o tablas


### Requirement: Grafo Bronze por dominios

monthly_file_refresh SHALL encadenar shared_load_to_delta→shared_archive_to_historic→comercial_load_to_delta→comercial_archive_to_historic→finanzas_load_to_delta→finanzas_archive_to_historic→operaciones_load_to_delta→operaciones_archive_to_historic→gobierno_load_to_delta→gobierno_archive_to_historic. Cada tarea SHALL recibir environment, catalog_name, storage_account, storage_container y data_year. No SHALL iniciar carga de otro dominio dentro de este Job antes de su dependencia declarada.

#### Scenario: Archivo comercial fallido
- **WHEN** comercial_load_to_delta termina con excepción
- **THEN** su tarea de archivo y las cargas posteriores dependen del camino fallido; el YAML no declara run_if para continuar ante ese fallo

### Requirement: Paralelismo Silver y referencias shared

Silver SHALL iniciar la estandarización de cada dominio sin dependencia Bronze ni dependencia de otro dominio dentro del Job Silver. Cada dominio SHALL encadenar sus cinco pasos; quality_checks de dominios distintos de shared SHALL depender además de shared_04_business_derivations, sin esperar explícitamente shared_05_quality_checks. Los pasos 01,02,03,05 SHALL usar notebooks shared y el paso 04 el notebook del dominio.

#### Scenario: Inicio Silver comercial
- **WHEN** se inspecciona comercial_01_schema_standardization
- **THEN** no tiene depends_on en el Job Silver y puede iniciar junto a otros dominios

#### Scenario: Calidad de operaciones
- **WHEN** se inspecciona operaciones_05_quality_checks
- **THEN** depende de operaciones_04_business_derivations y shared_04_business_derivations

### Requirement: Concurrencia acotada por Job

max_concurrent_runs=1 y queue.enabled=true SHALL declararse en los cuatro Jobs. Estos límites SHALL aplicarse a cada definición de Job, sin un lock global del lakehouse declarado en el código. Los schedules de capa SHALL estar UNPAUSED en los recursos comunes sin overrides específicos por target; el orquestador SHALL permanecer sin schedule propio.

#### Scenario: Bronze y Silver programados
- **WHEN** se consulta la definición de los dos Jobs
- **THEN** cada uno tiene su propio límite de concurrencia y el YAML no enlaza sus schedules mediante depends_on

#### Scenario: Target qa
- **WHEN** se despliegan los recursos sin overrides adicionales
- **THEN** el schedule de cada capa conserva pause_status=UNPAUSED en su definición

### Requirement: Recursos Jobs e identidad declarada

monthly_data_mesh_refresh SHALL declarar run_as y CAN_MANAGE para github_actions_service_principal_name. Los Jobs Bronze, Silver y Gold no SHALL atribuirse un run_as explícito, permisos propios ni configuración de cluster en los YAML actuales. Ninguno de los cuatro Jobs SHALL atribuirse retry, timeout, notificaciones o health rules configurados en el repositorio; los defaults efectivos de plataforma no se definen aquí. El contrato detallado de entrega SHALL consultarse en deployment y el de recuperación en lakehouse-operations.

#### Scenario: Identidad de una capa
- **WHEN** se consulta monthly_gold_refresh.job.yml
- **THEN** no contiene run_as; el repositorio no garantiza mediante esa definición que sea idéntica a la identidad del orquestador
