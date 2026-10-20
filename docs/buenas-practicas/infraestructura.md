# Buenas practicas de infraestructura y bundles

## 1. Alcance
Aplicar a las partes de la HU que usen esta herramienta. Sintesis revisada el 2026-10-16;
comprobar compatibilidad con las versiones del proyecto. Las fuentes son referencia tecnica;
las convenciones Crea se identifican aparte. No son transcripciones de los articulos.

## 2. Practicas y fundamento

- Versionar definiciones de recursos junto al codigo cuando facilite trazabilidad. Usar IaC
  y parametrizar recursos por ambiente; separar pruebas, validacion y despliegue. [1]
- Identificar artefactos desplegados con versiones/commit y conservar un procedimiento de
  recuperacion. Para CI/CD, preferir federacion de identidad cuando este disponible. [1]
- Definir targets separados y variables para reutilizar configuracion sin mezclar dev y prod.
  Validar el bundle antes de desplegar y probar la integracion tras el despliegue autorizado. [2]
- Usar rutas de workspace propias o del equipo y permisos explicitos; en produccion evaluar
  ejecucion como service principal. El bundle no sustituye una revision de cambios. [2]


## 3. Aplicacion y evidencia Crea

Planner declara recursos/targets afectados; developer prepara configuracion; reviewer examina diff
y validacion. bundle validate no demuestra ejecucion correcta ni autoriza deploy. Conservar fuera
del kit las credenciales y estado local. Terraform solo cuando el proyecto lo use; documentar
su plan/revision y backend en contexto. No se crea infraestructura al copiar este ZIP.


## 4. Fuentes consultadas

- [1. CI/CD workflows](https://docs.databricks.com/aws/en/dev-tools/ci-cd/flows).
- [2. Bundles: preguntas y practicas](https://docs.databricks.com/aws/en/dev-tools/bundles/faqs).


## 5. Configuracion, excepciones y extensiones
Registrar excepciones justificadas en docs/contexto-proyecto.md, comandos en
docs/proyecto.json → validation.required_checks y especialidades en extensions.
Agregar reglas propias aqui con fundamento y evidencia esperada. Una recomendacion
de rendimiento necesita medicion; no cambiar resultados funcionales para acelerarlos.

## 6. Aplicabilidad en NaturaPet — 2026-10-19

Aplica a databricks.yml, resources/jobs/ y conf/. Bundle Naturapet_DLH, targets
dev/qa/prod, ruta /Workspace/Naturapet_BI/<target>. Check de configuracion:
databricks bundle validate --strict --target dev --profile CREA_DEV.
No hay Terraform en el repositorio base; esas practicas no aplican actualmente.
El CI existente despliega con push a develop/qa/main: no usar esas ramas para
publicar una HU ni cambiar el workflow durante esta preparacion. Las diferencias
entre CLI local 1.21.0 y CI 0.297.2 se conservan y se revisan si afectan un cambio.
