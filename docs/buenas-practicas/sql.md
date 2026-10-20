# Buenas practicas de SQL

## 1. Alcance
Aplicar a las partes de la HU que usen esta herramienta. Sintesis revisada el 2026-10-16;
comprobar compatibilidad con las versiones del proyecto. Las fuentes son referencia tecnica;
las convenciones Crea se identifican aparte. No son transcripciones de los articulos.

## 2. Practicas y fundamento

- Medir con Query Profile: revisar operadores lentos, filas, memoria, lecturas y shuffle;
  buscar joins que multiplican filas y escaneos innecesarios. Guardar ID de consulta y entorno. [1]
- Comparar resultados y metricas bajo condiciones equivalentes. Una respuesta desde cache
  no tiene el mismo valor diagnostico que una ejecucion que procesa datos. [1]
- Elegir estrategia de join con estadisticas y plan real; los hints requieren comprobar
  tamanos y costo. AQE puede ajustar estrategias durante la ejecucion. [2]
- Proyectar columnas necesarias y usar predicados compatibles con el layout; comprobar el
  efecto en el perfil. Evitar convertir consejos generales en optimizaciones supuestas. [1,2]

El articulo secundario del harness propone cache, filtros, broadcast y ajustes de particiones.
Sirve como lista de hipotesis, no como regla. No adoptar cache Delta por defecto, ni un numero
fijo de particiones, ni su afirmacion de que clustering resuelve automaticamente el skew. [3]


## 3. Aplicacion y evidencia Crea

Definir grano y semantica de joins antes de optimizar; probar unicidad, nulos, limites de fecha
y reconciliaciones. No eliminar claves de GROUP BY para ahorrar memoria si cambia el indicador.
Separar sintaxis, correccion funcional y rendimiento como checks distintos. Nombres completos
y quoting deben respetar los identificadores reales; validar dialecto/DBR antes de usar funciones.


## 4. Fuentes consultadas

- [1. Query Profile](https://docs.databricks.com/aws/en/sql/user/queries/query-profile).
- [2. Spark SQL Performance Tuning](https://spark.apache.org/docs/latest/sql-performance-tuning.html).
- [3. Articulo aportado al harness, contrastado con fuentes primarias](https://medium.com/@avinash.narala6814/best-practices-for-writing-efficient-sql-queries-in-databricks-ea5c8d30d29b).


## 5. Configuracion, excepciones y extensiones
Registrar excepciones justificadas en docs/contexto-proyecto.md, comandos en
docs/proyecto.json → validation.required_checks y especialidades en extensions.
Agregar reglas propias aqui con fundamento y evidencia esperada. Una recomendacion
de rendimiento necesita medicion; no cambiar resultados funcionales para acelerarlos.

## 6. Aplicabilidad en NaturaPet — 2026-10-19

Aplica al SQL embebido en notebooks y modulos Spark, aunque no exista una carpeta
sql/ ni archivos .sql independientes en el repositorio base. Respetar catalogos
naturapet_<ambiente> y schemas <dominio>_<capa>. Para marts Gold, preservar grano,
claves, importes y tratamiento de devoluciones; contrastar con las specs vigentes.
No hay warehouse elegido: Query Profile o ejecucion DBSQL requiere definir primero
el recurso y la autorizacion aplicables, sin inventar IDs ni iniciar compute.
