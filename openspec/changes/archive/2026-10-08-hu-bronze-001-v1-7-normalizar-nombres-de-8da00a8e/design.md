# Design

## Context

Ver proposal.md - Why para la motivación. Estado actual relevante, observado en `src/common/schema.py`:

```python
def normalize_table_name(file_name: str, month: str = "") -> str:
    table_name = file_name.removesuffix(".csv")
    if month and table_name.endswith(f"_{month}"):
        return table_name[: -(len(month) + 1)]
    return table_name
```

- La función es pura (sin Spark ni E/S). El módulo importa PySpark de forma perezosa en `_require_pyspark()`, por lo que `normalize_table_name` es importable y testeable en el sandbox sin Spark.
- Solo elimina `.csv` en minúsculas (`removesuffix` distingue mayúsculas) y después el sufijo `_<month>`.
- Según la propuesta, `src/common/notebook_runner.py` invoca esta función para resolver el nombre de tabla y consultar el diccionario de datos. Esa referencia procede de la propuesta y no se ha releído en este diseño; el cambio no la modifica.
- Existe una función homónima en `src/utilities/file_ingestion.py` (firma con `Optional[str]`), fuera del alcance de la HU.
- `tests/test_project_structure.py` ya cubre el caso CSV mensual en minúsculas y debe seguir siendo válido. No se ha ejecutado ninguna prueba en esta fase; no hay evidencia de ejecución.
- No existe `tests/test_normalize_table_name.py`; se crea.

Restricciones: firma pública intacta, sin dependencias nuevas, sin tocar detección de formatos, lectura, rutas, jobs, `databricks.yml` ni `resources/`. Las pruebas usan solo cadenas sintéticas y corren en el Job sandbox aislado del harness.

## Goals / Non-Goals

**Goals:**
- Que `normalize_table_name` quite la extensión final `.csv`, `.json` o `.parquet` sin distinguir mayúsculas, y después el sufijo `_<month>` solo si `month` está informado y coincide exactamente al final.
- Preservar las mayúsculas del nombre, las extensiones no reconocidas y los puntos internos.
- Cubrir los 11 criterios de aceptación con una prueba parametrizada y sintética.
- Mantener la implementación local, pura y sin efectos laterales.

**Non-Goals:**
- No unificar ni alinear la función homónima de `src/utilities/file_ingestion.py`; queda como decisión separada.
- No reutilizar ni refactorizar `detect_file_format`, ni crear un registro central de formatos admitidos.
- No introducir migración, renombrado de tablas existentes ni reglas nuevas de nulos, cantidades, importes, fechas o ratios.
- No eliminar extensiones múltiples encadenadas (por ejemplo `.csv.json`): solo la extensión final y una sola vez.
- No validar el contenido de `month` (formato, longitud) más allá de «informado o vacío».

## Decisions

### D1. Constante local de extensiones reconocidas y comparación en minúsculas

Se define en `src/common/schema.py` una constante de módulo, por ejemplo `_RECOGNIZED_EXTENSIONS = (".csv", ".json", ".parquet")`. La función compara `file_name.lower().endswith(ext)` y, si coincide, recorta `len(ext)` caracteres del `file_name` original. Así se detecta sin distinguir mayúsculas pero se preservan las mayúsculas del nombre de tabla (`Fact_Ventas_01.CSV` → `Fact_Ventas`).

- *Por qué:* es la mínima expresión del requisito, no depende de que `.lower()` cambie la longitud (las extensiones son ASCII y recortar por longitud sobre el original es seguro) y mantiene el módulo sin nuevas importaciones.
- *Alternativas:*
  - `os.path.splitext`: descartada, trata como extensión cualquier sufijo tras el último punto (`.xlsx`) y obligaría a una lista blanca adicional; además complica `fact.ventas_01` sin extensión.
  - Regex `re.sub(r"\.(csv|json|parquet)$", "", ..., flags=re.I)`: equivalente, pero añade `import re` y es menos legible para tres literales.
  - Reutilizar la lista de `detect_file_format`: acopla `schema.py` a otro módulo y la HU prohíbe modificar la detección; se acepta la duplicación de tres literales a cambio de aislamiento. Si en el futuro se centraliza, es un cambio independiente.

### D2. Orden: extensión primero, sufijo de mes después

Tras recortar la extensión, se aplica la lógica existente: si `month` es truthy y el nombre resultante termina en `_<month>`, se elimina ese sufijo. Se conserva la condición «exactamente al final» (`endswith`), de modo que `fact_ventas_02.csv` con month `01` da `fact_ventas_02`, y `fact.ventas_01.json` da `fact.ventas`.

- *Por qué:* es el orden fijado por la HU y evita que `_01.json` impida detectar el sufijo.
- *Alternativa:* quitar el mes antes que la extensión; descartada, no coincidiría con el sufijo al final del nombre completo.

### D3. Se elimina una sola extensión, la final

Una única comprobación sobre el final del nombre (primera coincidencia). No hay bucle. `fact_ventas_01.xlsx` no coincide y se devuelve intacto (con el sufijo `_01` también intacto, porque el nombre no termina en `_01`). Un nombre sin extensión (`fact_ventas_01`, month `01`) pasa directamente a la regla del sufijo y da `fact_ventas`.

- *Alternativa:* bucle que quita extensiones repetidas; descartada por no pedirse y por riesgo de alterar nombres legítimos.

### D4. Firma, tipos y semántica de `month` sin cambios

Se mantiene `normalize_table_name(file_name: str, month: str = "") -> str`. `month` vacío significa «no aplicar sufijo». No se añaden validaciones ni excepciones nuevas, para no introducir reglas no pedidas.

### D5. Estrategia de pruebas

Nuevo archivo `tests/test_normalize_table_name.py`:
- Una prueba `pytest.mark.parametrize` con las 11 tuplas (entrada, month, esperado) de los criterios de aceptación, con ids legibles.
- Casos adicionales sintéticos opcionales de borde que no contradicen la HU, por ejemplo `.Parquet` mixto o nombre vacío de mes; solo si no amplían el comportamiento más allá de lo especificado.
- Importa `normalize_table_name` desde `src.common.schema` siguiendo el mecanismo de importación que ya usen las pruebas existentes de `tests/` (se confirmará al implementar leyendo `tests/test_project_structure.py` y la configuración de pytest, sin asumirlo aquí). No requiere Spark ni datos de NaturaPet.
- Adaptador de verificación: `pytest_sandbox`, ejecutando el archivo nuevo y toda la suite `tests/` en el Job sandbox aislado, más `python_compile` del módulo modificado. No se ejecutan jobs, pipelines ni `databricks_bundle_validate`, porque no se tocan `databricks.yml` ni `resources/`.

### D6. Archivos y operaciones previstos (manifiesto de código y pruebas)

| Operación | Ruta | Propósito |
| --- | --- | --- |
| modify | `src/common/schema.py` | Nueva lógica de `normalize_table_name` y constante de extensiones |
| create | `tests/test_normalize_table_name.py` | Pruebas parametrizadas de los criterios de aceptación |

Los artefactos OpenSpec (delta de `bronze-ingestion`) los gestiona el Harness por separado y no forman parte del manifiesto.

### D7. Impacto entre capas y dominios, y compatibilidad

- *Capa/dominios:* solo Bronze, vía el runner compartido; los dominios shared, comercial, finanzas, operaciones y gobierno obtienen el nuevo nombre de forma transversal. Silver y Gold no cambian de código, pero consumen tablas Bronze cuyos nombres pueden cambiar para JSON/Parquet (ver riesgos).
- *Compatibilidad:* CSV en minúsculas se comporta igual que antes (regresión cubierta por la prueba existente y por los casos nuevos). Cambian los resultados para `.json`, `.parquet` y `.CSV`/variantes de mayúsculas, que es el efecto buscado y no un cambio de firma.
- *Recuperación:* el cambio es una modificación acotada de una función pura; se revierte revirtiendo el commit/PR sin efectos sobre datos.

## Risks / Trade-offs

- [Tablas JSON/Parquet existentes se resolvían con la extensión en el nombre y ahora coincidirían con otro nombre, posiblemente ya existente] → No se asume migración. Se señala en la revisión humana del PR; antes del despliegue (humano) conviene comprobar fuera de esta HU si existen tablas Bronze con nombres afectados. No se ejecuta nada contra recursos de NaturaPet.
- [Divergencia con la función homónima de `src/utilities/file_ingestion.py`, que seguiría con el comportamiento anterior] → Queda fuera de alcance por la HU; se documenta como seguimiento y no se modifica.
- [Duplicar la lista de extensiones respecto a `detect_file_format` puede desincronizarse si se añade un formato] → Aceptado por aislamiento y por la restricción de no tocar la detección; la constante es única y fácil de localizar. Un formato nuevo exigirá actualizar ambos sitios.
- [Nombre que termina en extensión reconocida pero es en realidad parte del nombre de tabla (p. ej. una tabla llamada `x.json`)] → Es la semántica pedida por la HU; no se mitiga más.
- [Importación de la prueba depende de cómo estén configurados `sys.path`/pytest en el repo] → Se confirma al implementar siguiendo las pruebas existentes; si hiciera falta configuración nueva, se detiene y se replantea el plan en lugar de ampliar el alcance.
- [No hay evidencia de ejecución previa de pruebas] → La verificación obligatoria (pruebas nuevas y suite completa en el Job sandbox) debe pasar antes de sincronizar, archivar y publicar el PR.

## Migration Plan

1. Implementar el cambio en `src/common/schema.py` y crear `tests/test_normalize_table_name.py` tras la aprobación humana del plan y el manifiesto.
2. Verificar: pruebas nuevas y toda la suite `tests/` en el Job sandbox aislado; verificación Sonnet obligatoria.
3. Sincronizar la spec `bronze-ingestion` y archivar el cambio mediante el workflow OpenSpec.
4. Publicar código, pruebas y OpenSpec juntos en una rama `feature/*` con PR hacia `develop`. Merge y despliegue permanecen humanos.

Rollback: revertir el PR (o el commit). No hay migración de datos, ni cambios de esquema, configuración o recursos, por lo que no se requiere recuperación de datos.
