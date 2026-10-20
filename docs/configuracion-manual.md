# Configuracion manual — Windows / PowerShell

## 1. Preparar la app y las herramientas

Instala ChatGPT Desktop con la superficie de trabajo Codex disponible para tu cuenta,
inicia sesion y descomprime este ZIP en una carpeta de preparacion, por ejemplo
`C:\Crea\kit`. La carpeta que contiene AGENTS.md es la raiz del kit.
Abre esa carpeta temporal en Codex para preparar herramientas. No inicies aun una HU.

Elige primero proveedor: GitHub o Azure DevOps / Azure Repos. Ambos usan Git.
Para Azure Repos, Git for Windows debe incluir Git Credential Manager; instala tambien
Azure CLI y la extension azure-devops para consultar el repo y crear el PR. GitHub CLI solo hace falta en el camino GitHub.

Puedes pegar esta instruccion al modelo (indica el proveedor que usaras):
> Mi proveedor Git es [GitHub o Azure DevOps]. Prepara Git for Windows con Git Credential
> Manager, Node LTS y la CLI Databricks estable mas reciente para Windows. Si elegi GitHub,
> instala tambien GitHub CLI; si elegi Azure DevOps, instala Azure CLI y la extension
> azure-devops y omite GitHub CLI. El alcance Azure es repositorio y creacion de PR;
> no configurar Boards, pipelines, automatizaciones ni recursos de Azure.
> Revisa lo instalado y las fuentes oficiales. Usa WinGet si esta disponible; instala o
> actualiza solo esas herramientas y reporta versiones. Instala OpenSpec con npm.cmd
> install -g @fission-ai/openspec@latest. No inicialices OpenSpec en esta carpeta temporal,
> no hagas login por mi y no cambies politicas de PowerShell ni configuracion del shell.
> Si falta WinGet o se requieren privilegios que no tienes, indica el paso manual concreto.

Alternativa manual: ejecuta cada instalacion que falte, sin fijar versiones antiguas:
```powershell
winget install --id Git.Git --exact --source winget
winget install --id OpenJS.NodeJS.LTS --exact --source winget
winget install --id Databricks.DatabricksCLI --exact --source winget
```
Solo si elegiste GitHub, agrega:
```powershell
winget install --id GitHub.cli --exact --source winget
```
Solo si elegiste Azure DevOps, agrega (reabre PowerShell despues de instalar Azure CLI):
```powershell
winget install --id Microsoft.AzureCLI --exact --source winget
az version
az extension add --name azure-devops
az extension show --name azure-devops --query version --output tsv
```
Si la extension ya existe, comprueba su version; actualizala solo dentro del setup autorizado.
Para una ya instalada usa `winget upgrade --id ID --exact --source winget`.
Reabre PowerShell y la app para actualizar PATH. OpenSpec requiere Node >=20.19.0;
compara con el requisito de la version que instales. No uses pip install databricks-cli.
```powershell
git --version
node --version
npm.cmd install -g @fission-ai/openspec@latest
openspec.cmd --version
databricks --version
```
Se usa .cmd para npm/openspec si los wrappers .ps1 estan bloqueados por la politica local;
no necesitas cambiar ExecutionPolicy. No ejecutar todos los comandos como un bloque ciego:
si uno falla, resolverlo antes de continuar. Python se instala solo si lo requiere el proyecto.

## 2. Autenticacion — la persona la ejecuta

**GitHub:** ejecuta solo si este es tu proveedor.
```powershell
gh --version
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
gh auth status
```
**Azure DevOps / Azure Repos:** usa Git Credential Manager incluido en Git for Windows.
Comprueba su instalacion y configura OAuth (Microsoft Entra ID):
```powershell
git credential-manager --version
git config --global credential.azreposCredentialType oauth
```
Ese git config solo guarda la preferencia OAuth: no abre login. Verifica el helper:
```powershell
git config --show-origin --get-all credential.helper
```
Si no hay helper configurado, registra GCM con `git config --global credential.helper manager`.
Al clonar o ejecutar `git ls-remote "URL-HTTPS-REAL"`, GCM solicita login/MFA si hace falta;
una sesion valida puede evitar una nueva ventana. No ejecutar desde C:\Windows\System32.

Para la API de Azure DevOps, inicia sesion tambien con Azure CLI:
```powershell
az login --allow-no-subscriptions
az devops configure --defaults organization="https://dev.azure.com/TU-ORGANIZACION" project="TU-PROYECTO"
az repos show --organization "https://dev.azure.com/TU-ORGANIZACION" --project "TU-PROYECTO" --repository "TU-REPOSITORIO" --detect false --query "{id:id,name:name,remoteUrl:remoteUrl,webUrl:webUrl}" --output json
```
Usa `--tenant ID-TENANT` en az login si tu organizacion exige un tenant concreto.
No hace falta una suscripcion Azure para este trabajo en DevOps.
Si tu cuenta es invitada y az login no permite acceso, la documentacion exige
`az devops login --organization "https://dev.azure.com/TU-ORGANIZACION"` con PAT
ingresado solo en el prompt local, con permisos minimos Code Read & Write y segun
la politica corporativa. No guardar el PAT en archivos, comandos ni el chat.
Si tu cuenta es invitada y az login no permite acceso, la documentacion exige
`az devops login --organization "https://dev.azure.com/TU-ORGANIZACION"` con PAT
ingresado solo en el prompt local, con permisos minimos Code Read & Write y segun
la politica corporativa. No guardar el PAT en archivos, comandos ni el chat. Git/GCM y az tienen
flujos de autenticacion separados: el login de uno no acredita el del otro.
Compara remoteUrl con el remoto Git y registra el ID/nombre real del repositorio.
Se necesita acceso de lectura, contribucion a la rama y creacion de PR segun el equipo.
La extension admite Azure DevOps Services; Azure DevOps Server no esta soportado:
en Server conserva Git y usa el formulario web como alternativa, reportando esa limitacion. Si falta credential-manager, revisa la instalacion de Git
for Windows y habilita ese componente antes de clonar. No incrustes tokens en la URL.

**Comun a ambos proveedores: identidad Git y login Databricks.** La identidad de commits
no reemplaza el inicio de sesion remoto.
```powershell
git config --global user.name "TU NOMBRE"
git config --global user.email "TU CORREO DE COMMITS"
databricks auth login --host "https://TU-WORKSPACE" --profile "mi-proyecto-dev"
databricks auth profiles
databricks current-user me --profile "mi-proyecto-dev"
```
Completa el navegador y el SSO que corresponda. Elige explicitamente el perfil/workspace;
no pegues tokens en el chat ni en archivos del kit. Git local y Git folders de Databricks
son conexiones diferentes; configurar una no autentica automaticamente la otra.

## 3. Elegir el repositorio — dos caminos

**A. Remoto existente:** clona antes de copiar archivos al destino.
```powershell
New-Item -ItemType Directory -Path C:\Proyectos -Force
Set-Location C:\Proyectos
```
Elige UNA opcion. En GitHub, copia la URL desde Code. En Azure DevOps, entra a
Repos > Files > Clone y copia la URL HTTPS exacta (incluidos escapes de espacios).

GitHub:
```powershell
git clone "https://github.com/TU-ORG/TU-REPO.git" mi-proyecto
```
Azure DevOps Services / Azure Repos:
```powershell
git clone "https://dev.azure.com/ORGANIZACION/PROYECTO/_git/REPOSITORIO" mi-proyecto
```
Si tu empresa usa Azure DevOps Server con dominio propio o una URL visualstudio.com,
usa la URL exacta del boton Clone; no la conviertas al formato del ejemplo. La cuenta
necesita permiso de lectura sobre el repo. Para Server, sigue el metodo de autenticacion
que admita la instalacion corporativa si no ofrece el login OAuth de Services.

Despues de clonar:
```powershell
Set-Location C:\Proyectos\mi-proyecto
git remote -v
git branch --show-current
```
**B. Proyecto desde cero:** crea el repo local; conectar/publicar el remoto es posterior.
```powershell
New-Item -ItemType Directory -Path C:\Proyectos\mi-proyecto -Force
Set-Location C:\Proyectos\mi-proyecto
git init -b main
```
Si ya creaste un remoto vacio, agrega su URL exacta; por ejemplo, para Azure Repos:
```powershell
git remote add origin "https://dev.azure.com/ORGANIZACION/PROYECTO/_git/REPOSITORIO"
```
Para GitHub usa su URL equivalente. Este comando solo registra el remoto: el login
aparecera cuando una operacion lo contacte. Respeta la rama base del equipo: main en
el ejemplo no obliga a cambiar una rama existente develop u otra. La configuracion inicial no hace push ni crea un repositorio remoto automaticamente.
Antes de la primera HU, debe existir una base versionada local y remota: si usaste git init
con remoto vacio, prepara un commit inicial con los archivos elegidos y publica esa base
de forma explicita. Si copiaste el kit sobre un repo existente, revisa/versiona el setup
como cambio separado antes de iniciar una HU. El flujo exige un checkout limpio y base
remota existente; no mezcla setup sin versionar con una HU ni lo publica implicitamente.
En Azure DevOps Services, el principal crea el PR con `az repos pr create` despues del push verificado y la aprobacion que incluya crear PR; seguir docs/entrega-git.md. En GitHub se conserva el formulario web. No se incluyen Boards, pipelines ni automatizaciones.

## 4. Copiar el kit e inicializar OpenSpec

Copia **el contenido** del ZIP desde C:\Crea\kit a la raiz del repo, incluyendo
`.agents` y `.codex`. En un repo existente revisa y combina AGENTS/configuracion;
no reemplaces instrucciones previas. El ZIP incluye siete skills OpenSpec como snapshot,
pero no incluye openspec/ ni un cambio inventado: el CLI creara el root en el repo correcto.
Abre ahora **C:\Proyectos\mi-proyecto** en Codex.

Instruccion breve para el modelo:
> Inicializa OpenSpec aqui para Codex con idioma espanol. Confirma la raiz del repositorio,
> inspecciona primero integraciones legacy y prompts opsx globales que init pueda retirar;
> si existen, muestra las rutas afectadas antes de continuar. Conserva el AGENTS de Crea
> y el contexto del cliente. Ejecuta openspec.cmd init --tools codex --language Spanish.
> Necesitamos propose, explore, update, apply, verify, sync y archive; comprueba los SKILL.md
> generados, y si falta verify indicame como habilitarlo. Reporta lo creado realmente.

Comando manual, despues de comprobar lo anterior:
```powershell
openspec.cmd init --tools codex --language Spanish
```
Si falta verify, ejecuta `openspec.cmd config profile`: elige cambiar workflows, conserva
los seis core y agrega verify; luego `openspec.cmd update`. Esta seleccion modifica
preferencias globales de OpenSpec; revisala antes de aceptarla. No hace falta ampliar
otros workflows. La skill openspec-update-change revisa un plan; el comando update
anterior actualiza integraciones, son operaciones diferentes.

## 5. Editar solo lo necesario

| Archivo | Que completar o revisar |
| --- | --- |
| docs/contexto-proyecto.md | Objetivo, negocio, flujo, fuentes, entornos, stack, pruebas y restricciones; reemplaza los ejemplos. Agrega secciones si hacen falta. |
| docs/proyecto.json | project.repository.provider/url (github o azure_devops), organization (URL HTTPS)/project/name_or_id si aplican, project.base_branch real y delivery (remoto, prefijo feature y URL web si aplica); inventory.paths con exists real; file_types segun extensiones; databricks con perfil/host/target seleccionados; required_checks reales. Activa setup_complete al terminar. |
| openspec/config.yaml | Conserva schema y configura context/reglas con informacion real. Puedes referenciar los docs del kit. No copiar secretos ni sobrescribir un store existente. |
| AGENTS.md | Ajusta convenciones del cliente y referencias; conserva el flujo y la aprobacion humana de archivo. |
| .gitignore | Combina con el existente; revisa dependencias, secretos y estado local que deben excluirse. |
| .codex/config.toml | Modelo principal/defaults y MCP reales si hacen falta. |
| .codex/agents/*.toml | Los tres perfiles llevan gpt-6.1-sol y medium. Edita model/model_reasoning_effort y las instrucciones por rol si cambian sus alcances. |
| docs/buenas-practicas/*.md | Revisa aplicabilidad por herramienta y documenta excepciones del proyecto. |
| .agents/skills/Project/ | Agrega skills propias reales y registralas en extensions. |

Mantener las skills upstream sin editar; agregar reglas propias en Crea/Project.
No tocar licencias, schema ni manifest para cambiar el contexto del negocio.
No crear src/notebooks/tests/resources solo porque aparecen como ejemplos: ajusta inventario
a tu estructura y crea carpetas cuando el trabajo lo necesite. Los MCP/hooks estan vacios
por defecto; ver extensiones.md para agregarlos.

## 6. Comprobar e iniciar la primera HU

```powershell
Get-Content docs/proyecto.json -Raw | ConvertFrom-Json | Select-Object schema_version,project
openspec.cmd list --json
Get-ChildItem .agents/skills -Filter SKILL.md -Recurse
Get-ChildItem .codex/agents -Filter *.toml
```
Abre una sesion nueva. Pide al modelo leer AGENTS.md, informar instrucciones/perfiles disponibles
y verificar que puede delegar realmente. Las agrupaciones Crea/Project se leen por ruta;
si el selector no las descubre, sigue la alternativa de docs/extensiones.md.
Si las claves nativas no son soportadas por tu version, actualiza la app o revisa su
referencia oficial; no declares configurados agentes solo por existir los archivos.

Primer prompt:
> $crea-orquestador HU: [objetivo]. Criterios: [resultados comprobables]. Usa planner,
> developer y reviewer, ejecuta las pruebas aplicables y solicita mi aprobacion para archivar
> y publicar el alcance revisado mediante commit/push en feature/<hu>. Si el proveedor es Azure DevOps Services, incluye crear el PR con az repos en la aprobacion y entrega su ID/URL; en GitHub entrega el enlace para crearlo.

El planner conserva las pausas de OpenSpec: tras proponer presenta los artefactos y espera
una nueva indicacion tuya, por ejemplo "Inicia apply para <nombre-del-cambio>". Cuando revise
artefactos con update, te pedira las confirmaciones correspondientes antes de escribir.
No basta con pedir "ejecuta toda la HU" en el primer mensaje para saltar estas pausas.

El flujo crea una rama feature/<hu> desde la base remota antes de la primera escritura.
Sincroniza specs tras pasar revision y pruebas, presenta el diff y pide tu aprobacion para
archivar Y publicar los archivos revisados en esa rama. Despues hace commit/push y devuelve
SHA, rama origen y base. En Azure DevOps Services entrega ID/URL del PR creado y verificado
con az repos tras aprobacion expresa; en GitHub entrega el formulario y titulo/cuerpo para
crearlo manualmente. No se completa el PR, no hay merge ni borrado de la rama temporal.
Si apruebas solo archivo, no hay push hasta que autorices la publicacion. No hay force-push,
merge, despliegue o borrado automatico de la rama. Procedimiento: docs/entrega-git.md.

Comprobacion opcional del kit antes de personalizarlo:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\crea\verificar-kit.ps1 -OriginalDistribution
```
Bypass aplica solo a ese proceso, sin cambiar la politica persistente; las directivas
corporativas siguen prevaleciendo. Si no lo permiten, usa los checks manuales anteriores.
Despues de editar, omite -OriginalDistribution: el manifest describe los bytes del ZIP original.

## 7. Configuracion y ampliaciones

Cambios futuros en docs/extensiones.md. Inventario de skills: docs/catalogo-skills.md.
Fuentes consultadas y fecha: docs/fuentes.json. Este kit es un punto de partida manual;
no requiere el paquete Python harness_local.

Fuentes: [CLI Databricks](https://docs.databricks.com/aws/en/dev-tools/cli/install),
[OAuth Databricks](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-u2m),
[GitHub login](https://cli.github.com/manual/gh_auth_login),
[Azure Repos: Credential Manager](https://learn.microsoft.com/en-us/azure/devops/repos/git/set-up-credential-managers?view=azure-devops),
[Azure Repos: clonar](https://learn.microsoft.com/en-us/azure/devops/repos/git/clone?tabs=git-command-line&view=azure-devops),
[OpenSpec instalacion](https://github.com/Fission-AI/OpenSpec/blob/main/docs/installation.md),
[OpenSpec CLI](https://github.com/Fission-AI/OpenSpec/blob/main/docs/cli.md),
[Codex agentes](https://learn.chatgpt.com/docs/agent-configuration/subagents).
