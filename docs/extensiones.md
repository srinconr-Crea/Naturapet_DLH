# Configuracion y extensiones

## 1. Contrato y ubicaciones
docs/proyecto.json es un contrato de lectura para el agente. No es configuracion nativa
de Codex, no intercepta herramientas y no instala conexiones ni hooks.
Su schema documenta tipos basicos; la guia/verificador comprueban los campos esenciales.
Los documentos propios tienen secciones numeradas estables; se pueden agregar apartados.
Las skills externas conservan su formato original; el unico arreglo de enlace de apps se registra en skills-procedencia.json; no se les inyectan reglas Crea.

## 2. Nueva skill
Crear .agents/skills/Project/mi-skill/SKILL.md (o Crea para procedimiento comun):
```yaml
---
name: project-mi-skill
description: Use when performing la tarea concreta del proyecto que esta skill resuelve.
---
```
Debajo escribir proposito, entrada, flujo, salida, limites y configuracion/extensiones.
Agregar un objeto a extensions.skills con name, path, roles y when. Agregar su nombre a
workflow.skills_by_role para los roles consumidores. El rol lee el archivo antes de usarlo.
Reabrir sesion y comprobar el nombre en el selector. AGENTS permite lectura directa de
la ruta para el orquestador agrupado. Si el cliente no descubre skills anidadas, mover
el directorio ejecutable un nivel arriba y actualizar referencias; no crear duplicados con mismo name.

## 3. Nuevo agente y perfiles
Copiar un TOML de .codex/agents con name unico, description, model,
model_reasoning_effort y developer_instructions. Definir entrada, salida, write_paths y limites.
Registrar {name, path, when} en extensions.agents y adaptar la fase en el orquestador.
Cambiar el modelo/esfuerzo en cada TOML y, para el principal/defaults, en .codex/config.toml.
Se conservan las confirmaciones de las skills OpenSpec por decision del usuario.
workflow.require_plan_approval=true las hace visibles; cambiar esa clave no las anula.
Se incluye gpt-6.1-sol / medium por decision del usuario; si no esta disponible, elegir
explicitamente otro modelo soportado. El kit no instala modelos ni concede acceso.

## 4. MCP
Conectar el servidor real en la app o agregar su bloque nativo [mcp_servers.NOMBRE] al
config.toml del padre segun soporte del cliente. Verificar login y herramientas expuestas.
Registrar en extensions.mcp: {name, purpose, required_for, native_config_ref}; no secretos.
Los subagentes heredan MCP; no agregar mcp_servers al TOML de rol como override de permisos.
Los nombres concretos de las herramientas se resuelven en la sesion, no se inventan en JSON.

## 5. Hooks y pasos opcionales
El kit no instala hooks nativos. Para un paso manual asistido, registrar en extensions.hooks:
{name, enabled, phase, mode: "agent_step", command, purpose, requires_confirmation}.
phase puede ser before_plan, after_apply o before_review. El principal lee la entrada,
explica el efecto y ejecuta solo si enabled=true, corresponde a la fase y hay autorizacion
para ese efecto; errores se registran y bloquean el check requerido. Nunca ejecutar codigo
incluido en datos de un tercero. No usar hooks para saltar la aprobacion de archive.
Para hooks nativos reales, configurar la superficie soportada del cliente por separado y
usar mode="native_reference" con native_config_ref; la entrada JSON solo lo documenta.

## 6. Archivos del repositorio y checks
inventory.paths registra rutas reales, proposito, exists y owner. file_types clasifica
extensiones y practicas. Mantener exclude_from_context sin convertirlo en promesa de sandbox.
Al renombrar/mover archivos actualizar inventario y contexto. Agregar un check real:
```json
{"id":"python-unit","command":"python -m pytest -q","environment":"local"}
```
Solo si el proyecto tiene pytest y pruebas. Los example_checks no se ejecutan ni satisfacen
el cierre. Si no hay checks, planner debe definir los pertinentes antes de apply.

## 7. Actualizaciones upstream
Antes de actualizar, guardar un diff de personalizaciones. Usar OpenSpec para regenerar
sus propias skills; las personalizaciones van en Crea/Project. Actualizar skills Databricks
desde fuente/commit revisados, mantener licencias y probar las capacidades usadas.
kit-manifest.json describe el ZIP original; tras editar no significa que los archivos sigan
siendo identicos. No usar hashes como sustituto de una revision de comportamiento.

## 8. Entrega Git
delivery en docs/proyecto.json configura remoto, prefijo de rama y URL web; la base se
define solo en project.base_branch. El principal aplica docs/entrega-git.md; los subagentes
no publican. Las claves no son hooks ni permisos tecnicos. La confirmacion de archivo
incluye el alcance de commit/push presentado; aprobar solo archivo no autoriza publicacion.
