# Validacion del kit manual Crea 0.1.3

## 1. Alcance y resultado

Revision del 2026-10-16. Se comprobo el paquete como artefacto portable y se ejecuto
OpenSpec 1.13.2 en una carpeta temporal separada. No se instalaron herramientas globales,
no se autentico Git/Databricks y no se desplegaron recursos durante esta preparacion.

## 2. Comprobaciones realizadas

- Los cuatro TOML propios parsean; tres roles tienen nombre, descripcion, instrucciones,
  modelo gpt-6.1-sol y esfuerzo medium. No se usan overrides de permisos inefectivos en roles.
- Todos los JSON parsean; proyecto.json cumple su schema Draft 2020-12.
- Veinticuatro skills tienen nombres unicos y frontmatter con nombre/descripcion. Las siete
  skills OpenSpec referenciadas por el workflow existen. Las rutas comunes de contexto y practicas existen.
- Se compararon 152 archivos locales de skills byte por byte con sus fuentes. Las tres
  skills adicionales remotas se descargaron con recursos completos y commit fijado.
- Se reparo un enlace relativo roto de la skill Apps; el cambio esta declarado en
  skills-procedencia.json. No se modificaron sus instrucciones de comportamiento.
- La prueba real de OpenSpec hizo init con perfil core y update con perfil custom temporal
  de siete workflows. Se creo openspec/config.yaml; se preservaron AGENTS.md y Crea;
  list --json devolvio el root correcto. Configuracion/data XDG de prueba aisladas.
- Un revisor independiente detecto la contradiccion entre avance automatico y las pausas
  de OpenSpec. Tras eleccion expresa del usuario, se conservaron las confirmaciones de
  propose/update/explore. El revisor comprobo la correccion sin bloqueadores restantes.
- Verificador PowerShell: estructura valida; pruebas negativas rechazan desactivar archivo
  manual y rutas de contexto que escapan del repo. En Windows PowerShell 5.1 se uso Bypass
  solo en el proceso de prueba porque su politica por defecto bloquea archivos .ps1.
- ZIP: prueba CRC, archivos ocultos/con punto presentes y hashes SHA256 de cada entrada
  contrastados con kit-manifest.json. El manifest describe la distribucion antes de personalizarla.

### Actualizacion 0.1.1 — Azure Repos
Guia ampliada con autenticacion Git Credential Manager/OAuth, clonacion y alta de remoto
Azure Repos; GitHub CLI es condicional a GitHub. No se instala Azure CLI ni azure-devops.
Contexto e inventario JSON incluyen proveedor, URL, organizacion/proyecto y rama base real.
Se revalidaron JSON/schema, perfiles TOML e integridad del ZIP. Los perfiles y skills no
cambiaron respecto de 0.1.0, donde se ejecuto la prueba OpenSpec descrita arriba.
No se realizo login ni clonacion contra una organizacion Azure DevOps real.

### Actualizacion 0.1.3 — Azure CLI y PR
Instalacion condicional de Azure CLI + azure-devops, login separado de Git/GCM,
consulta del repo y creacion de PR Azure DevOps Services desde rama temporal con aprobacion.
Orquestador, roles, contrato JSON/schema, plantillas y verificador actualizados.
Sin Boards, pipelines, automatizaciones, merge, auto-complete ni borrado de ramas.
Verificacion local: estructura y JSON/TOML, contrato de entrega en JSON/schema,
rechazo de configuraciones inseguras por PowerShell, integridad SHA256 y ZIP.
No se ejecuto un motor general de JSON Schema ni una prueba remota de creacion del PR.
No se instalaron herramientas ni se hizo login, push o PR contra Azure real al preparar el kit.
La verificacion local no acredita permisos ni comportamiento de una organizacion real.
Las notas 0.1.0–0.1.2 anteriores describen sus versiones historicas.

## 3. Lo que debe comprobarse en el destino

Disponibilidad de la app/modelo, descubrimiento nativo de agentes y skills agrupadas,
delegacion efectiva, permisos, MCP, autenticacion y comandos del runtime del cliente.
No se simulo una HU completa de negocio ni se afirmo ejecucion de estos perfiles dentro
de la cuenta futura. Los checks del kit no sustituyen las pruebas del proyecto.

## 4. Configuracion y extensiones

Editar contexto/inventario y checks segun la guia. Usar el verificador con
-OriginalDistribution antes de editar; despues omitir esa opcion. Cualquier nueva extension
necesita comprobacion de sus capacidades reales, ademas del archivo de configuracion.

## 5. Actualizacion 0.1.2 — entrega en rama feature
Se agrego contrato delivery, procedimiento Git, plantilla de PR y coordinacion del principal
para rama por HU, commit/push acotado y enlace web. Configuracion/schema/TOML/ZIP se
revalidaron. La forma de URL Azure Repos y GitHub se contrasto con documentacion oficial;
no se ejecuto commit/push ni se abrio un PR en un proveedor remoto durante el empaquetado.
La prueba OpenSpec original sigue correspondiendo a 0.1.0; no cambiaron sus siete skills.
