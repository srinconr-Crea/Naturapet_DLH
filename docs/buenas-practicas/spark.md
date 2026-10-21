# Buenas practicas de Spark y PySpark

## 1. Alcance
Aplicar a las partes de la HU que usen esta herramienta. Sintesis revisada el 2026-10-16;
comprobar compatibilidad con las versiones del proyecto. Las fuentes son referencia tecnica;
las convenciones Crea se identifican aparte. No son transcripciones de los articulos.

## 2. Practicas y fundamento

- Comparar DataFrames y esquemas con assertDataFrameEqual/assertSchemaEqual cuando la version
  lo soporte; la guia aplica sus ejemplos desde Spark 3.5. Revisar parametros de igualdad,
  orden y tolerancia para que expresen el contrato esperado. [1]
- Reutilizar una SparkSession mediante fixtures y liberar recursos al finalizar. Construir
  entradas pequenas con esquema explicito para comprobar transformaciones. [1]
- Diagnosticar distribucion, shuffle y joins antes de ajustar particiones o hints. AQE puede
  combinar particiones y mitigar skew; comprobar su configuracion real en el runtime. [2]
- Revisar estadisticas del optimizador. Ni broadcast ni un valor universal de particiones
  garantizan mejora para todas las cargas. [2]


## 3. Aplicacion y evidencia Crea

Registrar version Spark/DBR y ejecutar en un entorno compatible cuando cambia semantica Spark.
Fixtures minimos: nulos, duplicados, esquema inesperado, entrada vacia y reejecucion segun el caso.
Un mock local de Spark no valida ejecucion distribuida. Controlar recolecciones al driver:
no traer datasets completos a memoria para inspeccionar resultados; usar muestras acotadas.


## 4. Fuentes consultadas

- [1. Testing PySpark](https://spark.apache.org/docs/latest/api/python/getting_started/testing_pyspark.html).
- [2. Spark SQL Performance Tuning](https://spark.apache.org/docs/latest/sql-performance-tuning.html).


## 5. Configuracion, excepciones y extensiones
Registrar excepciones justificadas en docs/contexto-proyecto.md, comandos en
docs/proyecto.json → validation.required_checks y especialidades en extensions.
Agregar reglas propias aqui con fundamento y evidencia esperada. Una recomendacion
de rendimiento necesita medicion; no cambiar resultados funcionales para acelerarlos.

## 6. Aplicabilidad en NaturaPet — 2026-10-19

Aplica a transformaciones Spark/Delta de Bronze, Silver y Gold. Leer las utilidades
delta_load.py, silver_incremental.py y notebooks afectados antes de cambiar merges,
watermarks, tipos o particiones. El runtime real no esta fijado en resources/jobs/:
registrarlo antes de escoger APIs de prueba. Las pruebas con MagicMock existentes
comprueban contratos locales, no el resultado distribuido. Usar fixtures sinteticos
por HU; no ejecutar jobs ni escribir tablas por el mero hecho de validar el bundle.
