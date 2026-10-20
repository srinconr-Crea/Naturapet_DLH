# Borrador de PR — <change>

## 1. Identidad y enlace
- Rama origen: feature/<hu>
- Rama destino: valor real de project.base_branch
- Remoto y repositorio web:
- Proveedor y modo (Azure CLI aprobado / formulario web):
- Enlace previsto al repo/formulario:
- Estado: borrador hasta comprobar el push; un enlace no es un PR creado.

## 2. Titulo para copiar
Describir el cambio funcional concreto en una linea.

## 3. Descripcion para copiar
Problema, comportamiento resultante y alcance. Referenciar HU y cambio OpenSpec archivado.
Incluir pruebas realmente ejecutadas, resultado y limitaciones pendientes; no secretos.

## 4. Configuracion y extensiones
Adaptar al template real del repositorio si existe. El principal prepara este archivo antes
del commit. El SHA y el recibo de push van en la respuesta final para evitar modificar
archivos despues de versionarlos. Azure: el principal crea el PR aprobado y entrega ID/URL y verificacion en la respuesta final.
GitHub: la persona crea el PR desde el formulario. No guardar como creado un PR aun no confirmado.
