# Crea — instrucciones del proyecto

## 0. Convenciones NaturaPet

Repositorio GitHub `srinconr-Crea/Naturapet_DLH`; rama base `develop`.
Datos y contratos por dominio `shared`, `comercial`, `finanzas`, `operaciones`, `gobierno`
y por capa `bronze`, `silver`, `gold`. Revisar `README.md`, `conf/` y `openspec/specs/`
antes de asumir reglas nuevas. Utilidades en `src/common/` y `src/utilities/`, notebooks
`.ipynb` en `notebooks/<dominio>/<capa>/`, jobs en `resources/jobs/`.

Perfil seleccionado: `CREA_DEV`; host y target `dev` en `docs/proyecto.json`.
No cambiar perfil, target, catalogo, contratos o rutas de storage por inferencia.
El contexto local de este kit no requiere la App ni el Job sandbox del harness externo.
La preparacion inicial debe versionarse como cambio separado antes de la primera HU;
no mezclar sus archivos sin commit con una rama de desarrollo.

Principal: `gpt-6.1-sol` / `medium`. Planner, developer y reviewer:
`gpt-6.1-sol` / `low`, segun los TOML locales. Confirmar carga real en una sesion nueva;
los archivos por si solos no demuestran que se haya ejecutado delegacion.
No hay skills personalizadas de Project ni MCP/hooks adicionales configurados.

## 1. Inicio y fuentes de contexto

Al iniciar o reanudar una historia de usuario (HU), leer y seguir
`.agents/skills/Crea/orquestador/SKILL.md` (skill `crea-orquestador`).
Esta instruccion autoriza la delegacion local a planner, developer y reviewer dentro
del alcance pedido por la persona. Para preguntas informativas no iniciar una HU.

Leer primero `docs/proyecto.json` y `docs/contexto-proyecto.md`; comprobar rutas
contra el checkout real. Leer `docs/buenas-practicas/general.md` y solo las practicas
de las herramientas afectadas. No cargar el catalogo completo de skills ni datos.
Leer project.repository y project.base_branch antes de operaciones Git; no inferir GitHub
por defecto. Azure Repos usa Git/GCM para clone/fetch/commit/push y Azure CLI con azure-devops para
consultar el repo y crear el PR en Services. Instalar solo durante el setup autorizado.
No invocar gh para Azure Repos. Sin Boards, pipelines, automatizaciones ni recursos Azure.
Si setup_complete=false, completar los datos imprescindibles antes de aplicar cambios;
se permite explorar y proponer sin inventar configuracion del cliente.

## 2. Flujo y responsabilidades

HU → planner → presentacion de artefactos → nueva indicacion humana de apply → developer
→ reviewer → autorizacion humana de archivo/publicacion → archive → commit/push en feature → PR con az repos en Azure DevOps Services o enlace para crear PR en GitHub.
Principal: coordina y conserva decisiones; prepara rama de HU antes de la primera escritura
y realiza la entrega Git tras revision/archivo aprobados. No simula subagentes ejecutados.
Planner: explore opcional, propose o update del cambio existente; nunca codigo.
Developer: apply de OpenSpec, implementacion y pruebas del candidato; no archiva.
Reviewer: revision independiente, pruebas pertinentes y verify. Tras resultado favorable
ejecuta sync, presenta su diff y solicita aprobacion manual de archive a traves del principal.
Archive solo tras respuesta humana explicita para ese cambio/candidato.
Si las pruebas requeridas estan failed/blocked/not_run, no sincronizar ni archivar.

## 3. Reglas permanentes

- Un agente activo por vez; un escritor por archivo. Los roles no subdelegan.
- Respetar cambios previos y reglas del cliente; no sobrescribir configuracion ajena.
- No cambiar criterios para hacer pasar una prueba ni ocultar defectos.
- No incluir secretos, credenciales, salidas sensibles ni datos productivos en Git.
- Perfil Databricks elegido expresamente por la persona; comprobar identidad/host.
- Distinguir pruebas locales de ejecucion Spark/Databricks; un mock no prueba el runtime.
- No hacer deploy, push, merge, permisos ni escrituras remotas sin alcance autorizado.
- No instalar herramientas ni modificar configuracion global como parte implicita de una HU.
- Handoff con archivos, criterios, comandos, resultados y pendientes. Nunca afirmar passed sin evidencia.

## 4. Skills y contexto especializados

OpenSpec: seguir el SKILL.md real de cada operacion. `openspec update` actualiza
integraciones; `openspec-update-change` modifica artefactos del cambio, nunca codigo.
Conservar las pausas humanas de las skills: propose termina con artefactos y requiere una
nueva solicitud humana antes de apply; update-change pide confirmar sus revisiones antes de
escribirlas; explore pide confirmar la captura de artefactos salvo peticion explicita que la autorice.
El principal transmite estas solicitudes a la persona y espera su respuesta; su propio despacho
no constituye esa confirmacion. require_plan_approval no permite saltar guardrails upstream.
Si falta una skill requerida, detener esa fase y seguir la guia de configuracion.
Databricks: cargar databricks-core antes de CLI; especializar con dbsql, dabs, jobs,
pipelines, unity-catalog, python-sdk, apps o model-serving segun la tarea.
Consultar `docs/catalogo-skills.md`; no usar nombres de herramientas MCP supuestos.

## 5. Configuracion y extensiones

Fuente de rutas, checks y extensiones: `docs/proyecto.json`.
Modelos/esfuerzos: `.codex/config.toml` y `.codex/agents/*.toml`.
Skills comunes: `.agents/skills/Crea/`; propias: `.agents/skills/Project/`.
Agregar skills/agentes/MCP/hooks siguiendo `docs/extensiones.md` y actualizar el inventario.
El JSON orienta al agente; no es una barrera tecnica de permisos ni registra hooks nativos.
Las skills upstream se conservan sin cambios; overrides propios se documentan en Crea o Project.

## 6. Cierre y reanudacion

Guardar evidencia en `docs/hu/<change>/evidencia.md`, sin secretos. Usar plantillas
de `docs/plantillas/`. Reanudar desde artefactos y estado real, no desde tareas imaginadas.
Tras dos rondas fallidas de correccion, informar el bloqueo y pedir una decision concreta.
Seguir docs/entrega-git.md y delivery en docs/proyecto.json. El alcance maximo configurado
es commit y push en una rama feature/<hu>, con creacion de PR por az repos en Azure DevOps Services tras aprobacion expresa; en GitHub, enlace y borrador manual.
Con delivery.enabled=true, antes de la primera escritura principal prepara la rama desde la base remota real con un
checkout limpio. No trabajar ni publicar en project.base_branch ni ramas protegidas.
La confirmacion manual debe nombrar archivo, diff/candidato, remoto, rama origen/destino y
publicacion commit/push y creacion del PR Azure con titulo/cuerpo previstos. Si la persona aprueba solo archivo, no inferir permiso para publicar.
No usar git add . ni incluir cambios ajenos; no force-push, merge, borrado de ramas o despliegue.
En Azure comprobar ID, URL, estado y ramas con az repos pr show antes de afirmar PR creado.
En GitHub el enlace solo abre el formulario. No completar PR ni activar auto-complete. La rama temporal se conserva
hasta que la persona complete el PR; no se borra durante el cierre de la HU.
