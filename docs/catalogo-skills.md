# Catalogo de skills

## 1. OpenSpec y coordinacion
crea-orquestador: .agents/skills/Crea/orquestador/SKILL.md.
Planner usa openspec-explore, openspec-propose, openspec-update-change.
Developer usa openspec-apply-change. Reviewer usa openspec-verify-change,
openspec-sync-specs y openspec-archive-change. Son siete snapshots generados por OpenSpec 1.13.2;
init/update desde la CLI instalada es la via de mantenimiento. No hay cambio de negocio incluido.

## 2. Databricks instaladas en el origen
| Skill | Cuando usarla |
| --- | --- |
| databricks-core | CLI, perfil y autenticacion; entrada antes de las demas. |
| databricks-dabs | Configuracion y validacion de bundles; despliegue solo autorizado. |
| databricks-dbsql | Capacidades y patrones SQL Databricks. |
| databricks-apps-python | Apps Python cuando sea el stack elegido. |
| databricks-model-serving | Endpoints de serving y su operacion. |
| databricks-unity-catalog | Gobierno, objetos y privilegios UC. |

## 3. Complementos incluidos
| Skill | Justificacion |
| --- | --- |
| databricks-jobs | Workflows y tareas de ingenieria de datos. |
| databricks-pipelines | Pipelines declarativos. |
| databricks-python-sdk | Automatizacion con SDK Python. |
| databricks-synthetic-data-gen | Fixtures sinteticos para desarrollo. |
| databricks-mlflow-evaluation | Evaluacion ML/GenAI cuando aplique. |
| databricks-docs | Consulta de documentacion especializada. |
| databricks-data-discovery | Descubrir/consultar datos con Genie; requiere CLI/capacidad compatibles. |
| databricks-apps | Apps AppKit/TypeScript; complementa apps-python. |
| databricks-app-design | Diseno de las Apps; referencias completas. |

Las seis primeras provienen del snapshot ya guardado por el harness; las tres ultimas
del paquete Codex upstream fijado por commit en skills-procedencia.json. Se corrige un unico enlace relativo roto de apps, documentado en patches; las instrucciones se conservan.
La skill propia creating-databricks-agents esta en Crea/creating-databricks-agents y sirve
para Apps que hospedan agentes; no configura los subagentes locales del kit.

## 4. Dependencias opcionales y compatibilidad
Se copian todas las referencias/scripts/assets de cada skill seleccionada. Las menciones a
otras especialidades no incluidas (por ejemplo Lakebase, entrenamiento ML, Vector Search o
dashboards) son rutas opcionales: instalarlas antes de seguir esos flujos, no fingir su presencia.
Las skills tienen versiones/minimos distintos. databricks-data-discovery menciona CLI >=1.9.0
para genie ask; si tu CLI no lo ofrece, seguir su comprobacion/fallback documentados. No asumir
que instalar la ultima CLI garantiza que tu workspace tenga todas las capacidades.

## 5. Configuracion y extensiones
Mantener upstream intacto; registrar overrides en Project y contexto. Para quitar una skill,
revisar dependencias y workflow.skills_by_role. Las skills globales instaladas con igual name
pueden aparecer duplicadas: elegir una fuente o desactivar la global en la configuracion personal.
No introducir datos propios de un cliente en las skills comunes ni en licencias.
