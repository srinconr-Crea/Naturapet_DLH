# Buenas practicas de Python

## 1. Alcance
Aplicar a las partes de la HU que usen esta herramienta. Sintesis revisada el 2026-10-16;
comprobar compatibilidad con las versiones del proyecto. Las fuentes son referencia tecnica;
las convenciones Crea se identifican aparte. No son transcripciones de los articulos.

## 2. Practicas y fundamento

- Usar entornos virtuales para aislar dependencias del proyecto; declarar las versiones
  compatibles y poder reconstruirlas. No versionar el entorno virtual. [1]
- Extraer funciones reutilizables fuera del notebook y declarar dependencias compatibles con
  el entorno Databricks: mejora mantenimiento y permite pruebas fuera de la interfaz. [2]
- Diseñar funciones con una salida predecible y tipos coherentes; evita mezclar indicadores
  de error con valores de negocio ambiguos. Probar unidades pequenas antes de integrarlas. [3]
- Para Python en notebooks, mantener funciones y tests en archivos separados cuando sea viable;
  permite reutilizar y ejecutar con un framework de pruebas. [3]


## 3. Aplicacion y evidencia Crea

Elegir convenciones de nombres/tipos y formateador segun el repositorio; no introducir una
herramienta nueva solo por preferencia. Probar casos normales, invalidos y limites. Evitar
efectos remotos al importar modulos; inyectar configuracion y dependencias cuando simplifique
las pruebas. Son convenciones de este kit, no citas textuales de las fuentes.


## 4. Fuentes consultadas

- [1. Python: entornos y paquetes](https://docs.python.org/3/tutorial/venv.html): fuente complementaria para Python, categoria sin enlace propio en el inventario original.
- [2. Notebooks: modulos y dependencias](https://learn.microsoft.com/es-es/azure/databricks/notebooks/best-practices).
- [3. Pruebas de notebooks](https://docs.databricks.com/aws/en/notebooks/testing).


## 5. Configuracion, excepciones y extensiones
Registrar excepciones justificadas en docs/contexto-proyecto.md, comandos en
docs/proyecto.json → validation.required_checks y especialidades en extensions.
Agregar reglas propias aqui con fundamento y evidencia esperada. Una recomendacion
de rendimiento necesita medicion; no cambiar resultados funcionales para acelerarlos.

## 6. Aplicabilidad en NaturaPet — 2026-10-19

Aplica a src/common/, src/utilities/ y tests/test_project_structure.py.
Convenciones actuales: funciones/modulos snake_case y utilidades compartidas fuera
del notebook. No imponer formateadores nuevos. Pruebas existentes:
.\.venv\Scripts\python.exe -m pytest tests -q.
CI usa Python 3.11; .venv local usa Python 3.13.14. pytest 9.1.1 esta instalado
y registrado en requirements-dev.txt. Recrear con el interprete de .venv y
-m pip install -r requirements-dev.txt. Las pruebas locales no acreditan
compatibilidad con el runtime remoto.
