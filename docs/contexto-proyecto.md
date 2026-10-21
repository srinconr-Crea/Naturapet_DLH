# Contexto del proyecto NaturaPet

## Identidad, objetivo y alcance
NaturaPet Data Lakehouse consolida datos del retail de mascotas en Colombia para consumo analitico. Repositorio GitHub: srinconr-Crea/Naturapet_DLH; rama base: develop. Fuentes: README.md, databricks.yml, conf/ y openspec/specs/.

## Dominio y contratos
Dominios: shared, comercial, finanzas, operaciones y gobierno. El flujo mensual ingiere archivos raw, publica Delta y produce marts e indicadores. Recuperar claves, tipos, nulos, fechas e importes del codigo y specs para cada HU; no inventar reglas ni propietarios. Los datos se organizan por ambiente, dominio, anio y mes.

## Arquitectura y fuentes
Azure Databricks, ADLS Gen2, Unity Catalog y Databricks Asset Bundles. Bronze carga y audita; Silver estandariza y controla calidad; Gold genera marts y KPIs. src/common/ y src/utilities/ contienen utilidades; notebooks/<dominio>/<capa>/ los notebooks; conf/ la configuracion y resources/jobs/ los cuatro jobs de refresco. README.md contiene el detalle y los consumidores analiticos.

## Entornos y conexiones
Perfil elegido: CREA_DEV; identidad verificada: srinconr@creasistemas.com. Host: https://adb-7405606739630987.7.azuredatabricks.net. Targets: dev, qa y prod. Solo se valida dev, catalogo naturapet_dev, schema parametrizado ${var.domain_name}_${var.data_layer}, ruta /Workspace/Naturapet_BI/dev. Storage demodldb, contenedor democodex. Warehouse y runtime no seleccionados; no se requieren para este setup. Credenciales exclusivamente en el perfil local.

## Stack, versiones y convenciones
Python, notebooks ipynb, Spark/Delta y YAML. Verificado el 2026-10-19: Git 2.55.0.windows.5, GCM 2.9.1, Node 24.20.0, npm 11.19.0, OpenSpec 1.14.3, Databricks CLI 1.21.0 y Python local 3.13.14. El CI usa Python 3.11 y Databricks CLI 0.297.2; no se modifica. Git local: srinconr / srinconr@creasistemas.com. OpenSpec en espanol.

## Desarrollo y validacion
Checks en docs/proyecto.json: verificador del kit, openspec list, .\.venv\Scripts\python.exe -m pytest tests -q y validacion estricta del bundle dev con CREA_DEV. pytest 9.1.1 instalado en .venv por solicitud humana; dependencia registrada en requirements-dev.txt. Mocks y pruebas locales no acreditan Spark; definir pruebas de runtime para cambios Spark y obtener autorizacion antes de cualquier ejecucion remota.

## Operacion y recuperacion
Jobs definidos: monthly_file_refresh, monthly_silver_refresh, monthly_gold_refresh y monthly_data_mesh_refresh. No se ejecutan ni despliegan en este setup. El CI existente despliega con push a develop, qa o main; publicar requiere revision y autorizacion. Recuperar el setup revisando el diff contra origin/develop y retirando solo los cambios aprobados; no hay cambios de datos ni recursos remotos.

## Restricciones, HU y terminado
Este checkout usa el kit manual Crea 0.1.3, sin App, Job sandbox ni paquete Python del harness externo. Leer AGENTS.md y docs/proyecto.json. Planner prepara artefactos; nueva indicacion humana habilita apply; developer implementa; reviewer verifica y sincroniza; la persona autoriza archivo y publicacion. Entrega en feature/<hu> hacia develop con PR manual de GitHub. Preparacion local sin commit ni push: versionar por separado antes de la primera HU.

## Extensiones y practicas
Se conservan las siete skills OpenSpec existentes y se agregan solo las ausentes del kit. Se excluye LEEME-CREA.md. No se agregan MCP ni hooks. Aplicar buenas practicas segun la herramienta de cada HU; no crear recursos de ejemplo. Los tres perfiles nativos estan configurados en archivos; comprobar su descubrimiento en una sesion nueva antes de afirmar delegacion real.

## Pendientes operativos
pytest resuelto en .venv (14 pruebas aprobadas); GitHub CLI no localizado en PATH ni ruta estandar; versionar este setup antes de iniciar una HU y comprobar los perfiles nativos en una sesion nueva. El setup inicial no instalo herramientas; posteriormente se autorizo e instalo pytest en .venv. Sin login nuevo, ejecuciones de jobs o publicacion.

## Ajustes del paso 5 — 2026-10-19

Principal gpt-6.1-sol con esfuerzo medium; planner, developer y reviewer con el
mismo modelo y esfuerzo low. Configuracion en .codex/config.toml y .codex/agents/.
La comprobacion de carga efectiva de los roles corresponde a una sesion nueva.

Los contratos tecnicos se recuperan de src/common/config.py y validation.py,
conf/environments/ y openspec/specs/. El diccionario se resuelve por defecto en
raw/<ambiente>/gobierno/<anio>/data_dictionary.csv. No se leyó el contenido de datos.
El bundle usa comercial/bronze por defecto, mientras get_config() usa shared si
no recibe AREA: respetar el contexto del llamador y no igualar defaults por inferencia.
No hay version DBR/Spark fijada en los jobs YAML; registrarla antes de validar runtime.

La matriz de aplicabilidad y excepciones esta en docs/buenas-practicas/README.md y
en la seccion 6 de cada practica. Delta externa es contrato actual; Terraform no
aplica. SQL esta embebido, sin carpeta sql/ independiente. No se elige warehouse
para completar campos que no son requisitos de este setup. No se agregan skills
Project ni se modifica .gitignore en esta segunda pasada.

La configuracion permite preparar la primera propuesta. Antes de iniciar apply:
versionar este setup por separado y disponer de checkout limpio. Los checks Python
se ejecutan con el interprete de .venv, donde pytest ya esta instalado. Los permisos o datos de runtime se
acuerdan por HU. setup_complete=true describe configuracion, no pruebas aprobadas.

## Preparar y ejecutar pruebas locales

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests -q
```

No hace falta activar el entorno ni cambiar ExecutionPolicy. .venv esta ignorado
por Git. Verificacion: 14 pruebas aprobadas y pip check sin dependencias rotas.
Esto comprueba las pruebas locales existentes, no el runtime Spark remoto.
