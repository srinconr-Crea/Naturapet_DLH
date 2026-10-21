# Buenas practicas de gobierno de datos

## 1. Alcance
Aplicar a las partes de la HU que usen esta herramienta. Sintesis revisada el 2026-10-16;
comprobar compatibilidad con las versiones del proyecto. Las fuentes son referencia tecnica;
las convenciones Crea se identifican aparte. No son transcripciones de los articulos.

## 2. Practicas y fundamento

- Gestionar identidades y grupos desde el proveedor de identidad a nivel de cuenta.
  Preferir permisos y propiedad por grupos frente a asignaciones individuales. [1]
- Reservar privilegios potentes y propiedad para responsables concretos; usar service
  principals para automatizacion de produccion. Revisar USE CATALOG/SCHEMA y permisos de objetos. [1]
- Organizar catalogos/esquemas segun limites reales de datos, equipos y ambientes. Preferir
  tablas y volumenes administrados cuando cubran la necesidad. No eludir Unity Catalog
  con accesos directos de escritura al almacenamiento subyacente. [1]


## 3. Aplicacion y evidencia Crea

Al usar databricks-unity-catalog, identificar objeto, identidad, permiso solicitado y efecto.
La HU de desarrollo no autoriza por defecto GRANT/REVOKE. Documentar requisitos de datos
sin incluir muestras sensibles. Datos sinteticos para las pruebas del kit.


## 4. Fuentes consultadas

- [1. Unity Catalog best practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices): ampliacion del indice original del harness.


## 5. Configuracion, excepciones y extensiones
Registrar excepciones justificadas en docs/contexto-proyecto.md, comandos en
docs/proyecto.json → validation.required_checks y especialidades en extensions.
Agregar reglas propias aqui con fundamento y evidencia esperada. Una recomendacion
de rendimiento necesita medicion; no cambiar resultados funcionales para acelerarlos.

## 6. Aplicabilidad en NaturaPet — 2026-10-19

Aplica a Unity Catalog y a cualquier cambio de permisos o contrato de datos.
Catalogos existentes en configuracion: naturapet_dev, naturapet_qa y naturapet_prod;
schemas por dominio shared/comercial/finanzas/operaciones/gobierno y capa.
El perfil CREA_DEV autenticado no autoriza GRANT/REVOKE ni cambios de ownership.
Conservar tablas externas y rutas ADLS existentes; no alterar permisos de storage
para resolver errores de pruebas. No copiar datos reales en fixtures ni evidencia.
