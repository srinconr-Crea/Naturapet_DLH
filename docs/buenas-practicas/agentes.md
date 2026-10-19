# Buenas practicas de agentes, skills y contexto

## 1. Alcance
Aplicar a las partes de la HU que usen esta herramienta. Sintesis revisada el 2026-10-16;
comprobar compatibilidad con las versiones del proyecto. Las fuentes son referencia tecnica;
las convenciones Crea se identifican aparte. No son transcripciones de los articulos.

## 2. Practicas y fundamento

- Dar a cada agente una responsabilidad estrecha, entradas y salida comprobables; delegar
  trabajo independiente cuando compense la coordinacion. Subagentes tienen contexto propio. [1]
- Fijar modelo y esfuerzo por rol y verificar disponibilidad. Los agentes personalizados
  heredan permisos y MCP del padre: un TOML de rol no crea privilegios separados. [1]
- Separar reglas permanentes de procedimientos reutilizables. Mantener instrucciones
  breves y consultar referencias segun la necesidad de cada tarea. [2]
- Usar nombres y descripciones de skill precisos para que se seleccionen por su proposito.
  Las skills pueden incluir referencias y scripts; leer instrucciones no implica ejecutar scripts. [3]


## 3. Aplicacion y evidencia Crea

Crea usa un principal y tres roles secuenciales: planner define, developer implementa, reviewer
verifica. La revision puede escribir evidencia/specs, por lo que "no editar codigo" es una
regla de procedimiento. No fingir sandbox read-only. Un escritor por ruta y aprobacion humana
antes de archive son decisiones de esta configuracion. Verificar agentes con una HU real al instalar.


## 4. Fuentes consultadas

- [1. Subagentes](https://learn.chatgpt.com/docs/agent-configuration/subagents).
- [2. Customization](https://learn.chatgpt.com/docs/customization/overview).
- [3. Build skills](https://learn.chatgpt.com/docs/build-skills).


## 5. Configuracion, excepciones y extensiones
Registrar excepciones justificadas en docs/contexto-proyecto.md, comandos en
docs/proyecto.json → validation.required_checks y especialidades en extensions.
Agregar reglas propias aqui con fundamento y evidencia esperada. Una recomendacion
de rendimiento necesita medicion; no cambiar resultados funcionales para acelerarlos.

## 6. Aplicabilidad en NaturaPet — 2026-10-19

Principal gpt-6.1-sol / medium; planner, developer y reviewer gpt-6.1-sol / low.
Los TOML de .codex/agents/ y el default de .codex/config.toml mantienen esos valores.
Un subagente ejecutandose por vez, sin subdelegacion. Comprobar descubrimiento y
modelo/esfuerzo efectivos al iniciar una sesion nueva; un TOML parseable no prueba
que se haya lanzado el rol. No hay skills Project, MCP ni hooks propios que activar.
Las claves se contrastaron con la referencia oficial de configuracion y subagentes
el 2026-10-19: https://learn.chatgpt.com/docs/config-file/config-reference y
https://learn.chatgpt.com/docs/agent-configuration/subagents.
