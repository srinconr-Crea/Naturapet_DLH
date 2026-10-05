# Orquestación y entrega del lakehouse

## Purpose

Definir las dependencias entre capas, schedules y comportamiento CI existente que afectan una HU y su PR de preparación.

Base documental sugerida, derivada por lectura de código en `develop@9c48831022a329902f765058de37e6d0a1528eb7`. Requiere revisión humana antes de adoptarse; no acredita ejecución de Spark ni despliegue Databricks.

## Sources

- [resources/jobs/monthly_data_mesh_refresh.job.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/resources/jobs/monthly_data_mesh_refresh.job.yml)
- [resources/jobs/monthly_file_refresh.job.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/resources/jobs/monthly_file_refresh.job.yml)
- [resources/jobs/monthly_silver_refresh.job.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/resources/jobs/monthly_silver_refresh.job.yml)
- [resources/jobs/monthly_gold_refresh.job.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/resources/jobs/monthly_gold_refresh.job.yml)
- [.github/workflows/databricks-cicd.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/.github/workflows/databricks-cicd.yml)
- [tests/test_project_structure.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/9c48831022a329902f765058de37e6d0a1528eb7/tests/test_project_structure.py)

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

