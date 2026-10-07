# Despliegue y entrega del bundle

## Purpose

Documentar empaquetado, autenticación, validaciones y despliegue que el workflow actual ejecuta, junto con los límites de la configuración versionada.

Contrato del comportamiento implementado, documentado mediante lectura estática de `develop@eb35b87b79eb541c4832fccc8f8825412755f498`. Los escenarios describen resultados esperados del código actual; no constituyen evidencia de ejecución de Spark ni de despliegue en Databricks.

## Sources

- [databricks.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/databricks.yml)
- [.github/workflows/databricks-cicd.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/.github/workflows/databricks-cicd.yml)
- [README.md](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/README.md)
- [resources/jobs/monthly_data_mesh_refresh.job.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/resources/jobs/monthly_data_mesh_refresh.job.yml)
- [conf/environments/dev.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/conf/environments/dev.yml)
- [conf/environments/qa.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/conf/environments/qa.yml)
- [conf/environments/prod.yml](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/conf/environments/prod.yml)
- [tests/test_project_structure.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/tests/test_project_structure.py)

## Requirements

### Requirement: Bundle y artefactos de entrega

El bundle SHALL llamarse Naturapet_DLH, incluir recursos desde resources/**/*.yml y declarar sync.include para notebooks, src, conf y resources. Sus recursos declarados SHALL ser los cuatro Jobs de capa/orquestación. Los targets SHALL usar /Workspace/Naturapet_BI/<target>, catálogos naturapet_dev/naturapet_qa/naturapet_prod y el mismo host versionado. dev SHALL ser el target default; qa y prod SHALL declarar mode=production. No SHALL atribuirse a sync.include el significado de una lista exclusiva de todos los archivos sincronizados por la CLI.

#### Scenario: Target prod
- **WHEN** se resuelve databricks.yml para prod
- **THEN** usa mode=production, naturapet_prod y /Workspace/Naturapet_BI/prod

#### Scenario: Recursos externos
- **WHEN** se inspeccionan los recursos versionados
- **THEN** no contienen provisión de credenciales ADLS, external locations ni catálogos UC

### Requirement: Resolución de eventos y promoción por ramas

El workflow SHALL dispararse por push a develop, qa y main, pull_request con base main y workflow_dispatch. SHALL resolver develop→dev, qa→qa, main→prod mediante la rama del evento, usando base_ref para PR y GITHUB_REF_NAME en los demás casos. Otras ramas SHALL terminar con error Unsupported branch. El repositorio no SHALL atribuirse promoción automática develop→qa→main ni validación CI de PR hacia develop/qa o push feature/*.

#### Scenario: Dispatch sobre feature
- **WHEN** workflow_dispatch se ejecuta sobre una rama feature
- **THEN** resolve-target falla por rama no soportada

#### Scenario: Push qa
- **WHEN** un push alcanza qa
- **THEN** resuelve environment qa y target qa sin promover automáticamente main

### Requirement: Validaciones previas al despliegue

La etapa validate SHALL hacer checkout, instalar Python 3.11, actualizar pip e instalar pytest, ejecutar python -m pytest tests, instalar Databricks CLI 0.297.2 y ejecutar bundle validate --target <target>. No SHALL atribuirse --strict, validación OpenSpec, bundle plan, pruebas Spark, smoke de Jobs ni pruebas end-to-end a esa etapa actual. El Job deploy SHALL depender de resolve-target y validate.

#### Scenario: Pruebas fallidas
- **WHEN** python -m pytest tests termina con error
- **THEN** validate falla y deploy no tiene sus dependencias satisfechas

#### Scenario: Specs modificadas
- **WHEN** un commit contiene cambios OpenSpec
- **THEN** el workflow actual no ejecuta openspec validate por ese hecho

### Requirement: Autenticación e identidades CI

El workflow SHALL pedir permisos id-token:write y contents:read, leer DATABRICKS_HOST y DATABRICKS_CLIENT_ID de secrets del environment resuelto y fijar DATABRICKS_AUTH_TYPE=github-oidc en validate y deploy. Los secrets SHALL referenciarse sin valores inline. github_actions_service_principal_name SHALL ser una variable del bundle usada por el orquestador para run_as y CAN_MANAGE; su default no SHALL probar que coincide con el secreto del environment. El repositorio no SHALL atribuirse provisión de federación OIDC, grants UC o permisos ADLS a estos YAML.

#### Scenario: Environment dev
- **WHEN** el evento resuelve dev
- **THEN** validate y deploy referencian el environment dev y sus secrets

#### Scenario: Identidad del orquestador
- **WHEN** se resuelve run_as de monthly_data_mesh_refresh
- **THEN** se obtiene github_actions_service_principal_name, sin validación de igualdad contra DATABRICKS_CLIENT_ID en el workflow

### Requirement: Despliegue automático condicionado por evento

deploy SHALL habilitarse cuando should_deploy=true y el evento no sea pull_request; SHALL ejecutar bundle deploy --target <target> después de las validaciones. Los pushes y dispatch sobre las tres ramas admitidas SHALL habilitarlo. PR hacia main SHALL validar prod con should_deploy=false. La definición del workflow no SHALL atribuirse aprobación manual explícita dentro de sus pasos; las protecciones o revisores configurados fuera del repositorio en GitHub Environments no se acreditan por este archivo.

#### Scenario: Commit documental en develop
- **WHEN** un push a develop modifica únicamente specs
- **THEN** el workflow se dispara igualmente y habilita deploy después de validate, ya que no tiene filtro paths

#### Scenario: PR main
- **WHEN** el evento es pull_request hacia main
- **THEN** validate resuelve prod y deploy queda deshabilitado

### Requirement: Alcance posterior al despliegue y rollback

El workflow SHALL finalizar su acción de entrega con bundle deploy; no SHALL ejecutar bundle run, consultas de datos, verificación de tablas ni rollback automático. El repositorio SHALL distinguir el éxito de validación/despliegue del resultado de los Jobs y de la calidad de sus datos. README SHALL conservar el perfil CREA_DEV para comandos locales y la aprobación humana indicada para deploy/run manuales; esa guía no añade un paso manual al workflow.

#### Scenario: Deploy exitoso
- **WHEN** bundle deploy termina sin error
- **THEN** el workflow no ejecuta después monthly_data_mesh_refresh ni verifica sus tablas

#### Scenario: Deploy fallido
- **WHEN** bundle deploy produce error
- **THEN** el workflow termina fallido sin un paso de restauración de versión anterior

### Requirement: Prerrequisitos operativos y límites de evidencia

Los notebooks SHALL necesitar acceso al catálogo, creación/uso de schemas, lectura de tablas y escritura de Delta externa y auditorías; Bronze SHALL requerir lectura raw y movimiento a historic. El bundle no SHALL declarar la creación del catálogo, credenciales de storage, permisos UC/ADLS ni selección de compute de las tareas notebook. La configuración versionada no SHALL presentarse como evidencia de que tales prerrequisitos están provisionados o de que las siete skills OpenSpec hayan sido ejecutadas.

#### Scenario: Sin permisos de schema
- **WHEN** CREATE SCHEMA IF NOT EXISTS es rechazado por la plataforma
- **THEN** el notebook falla; el bundle no provisiona un grant para subsanar ese error
