# Base OpenSpec sugerida para NaturaPet

Este paquete documenta un mínimo funcional para preparar el cliente antes de las primeras HUs. Sus specs pertenecen a **NaturaPet**, no al producto harness; aquí se guardan como referencia para incorporarlas al PR humano de preparación del cliente.

Fuente: [develop en 9c48831022a329902f765058de37e6d0a1528eb7](https://github.com/srinconr-Crea/Naturapet_DLH/tree/9c48831022a329902f765058de37e6d0a1528eb7), consultado el 5 de octubre de 2026. Se consultó el SHA remoto y se leyeron los archivos de ese commit mediante Git en el checkout local coincidente, incluidos módulos comunes, notebooks Silver/Gold, recursos de jobs, bundle, workflow CI y pruebas. No se usaron los cambios OpenSpec locales como evidencia de funcionamiento.

## Mínimos sugeridos

| Spec | Alcance |
| --- | --- |
| [lakehouse-configuration](specs/lakehouse-configuration/spec.md) | Ambientes, catálogo, dominios, capas y rutas. |
| [bronze-ingestion](specs/bronze-ingestion/spec.md) | Descubrimiento, diccionario, mes, identidad, Delta, auditoría e histórico. |
| [silver-processing](specs/silver-processing/spec.md) | Watermarks, pasos, nulos, MERGE y división segura en compras. |
| [gold-marts](specs/gold-marts/spec.md) | Productos, granularidades y fórmulas mínimas, objetivos y staging. |
| [data-quality](specs/data-quality/spec.md) | PK/FK, consistencia aritmética, conciliación y significado de PASS/FAIL. |
| [orchestration-delivery](specs/orchestration-delivery/spec.md) | Dependencias, schedules y efectos de CI sobre publicación y despliegue. |

## Cómo adoptarlas

1. Comparar el SHA fuente con la base actual del cliente y revisar diferencias si ha avanzado.
2. Revisar con responsables funcionales los requisitos extraídos. SHALL expresa el contrato propuesto para preservar el comportamiento observado, no una aprobación ya otorgada.
3. Copiar los seis directorios de specs/ a openspec/specs/ del cliente, sin sobrescribir specs existentes. Copiar este README como openspec/BASELINE.md para conservar procedencia y límites. Los enlaces relativos de este documento siguen funcionando en ese destino.
4. Validar con OpenSpec 1.13.2, revisar configuración y siete skills, y publicar todo en el PR feature/prepare-openspec hacia develop. Esperar integración humana antes de las HUs.

El paso completo y los comandos están en el paso 4 de la guía de preparación del harness, docs/preparacion-cliente-naturapet.md. Esa guía pertenece al repositorio del harness; no es un archivo esperado dentro del cliente.

## Evidencia y límites

El formato se validó en un fixture local aislado con OpenSpec 1.13.2 mediante `validate --specs --strict --no-interactive --json`: **6 specs válidas, 0 issues**, con **27 requisitos y 46 escenarios**. Se comprobó que las 25 rutas fuente enlazadas existen en el commit indicado. El `config.yaml` de la guía también pasó el esquema de esa versión. Estas comprobaciones son documentales.

La suite existente tests/test_project_structure.py se ejecutó localmente: **14 passed**, el 5 de octubre de 2026, con pytest, plugins externos desactivados y escritura de bytecode/cache desactivada. Comprueba configuración/rutas, nombre y formato de fuentes, validación textual de mes, compactación de taskValues y llamadas a escritura/MERGE Bronze mediante mocks. Esta ejecución no usa Spark ni conexiones Databricks.

El resto de requisitos se deriva de lectura estática; los escenarios son criterios para futuras pruebas, no resultados de pruebas ejecutadas. Antes de cambiar una capacidad, añadir o seleccionar pruebas pertinentes en la HU y su manifiesto aprobado. Validar el formato OpenSpec no prueba fórmulas Spark ni datos reales.

Aspectos que deben mantenerse visibles al revisar la base:

- safe_divide devuelve NULL para cero o NULL; los negativos se dividen. No existe en esa función una prohibición general de cantidades negativas.
- Los controles Silver omiten FK cuando faltan referencias y no cuentan FK nulas. Sus comparaciones aritméticas tampoco sustituyen controles de completitud.
- Un FAIL de calidad se registra y muestra; el código actual no lanza una excepción por ese estado. Cambiarlo a gate exige una HU explícita.
- Los _pct representan cocientes, sin multiplicación automática por 100.
- Gold usa staging y overwrite por mart, sin demostrar una transacción global ni rollback de todo el refresco.
- Los schedules de capa son independientes; la secuencia Bronze→Silver→Gold se asegura en el orquestador por dependencias.
- El workflow actual valida PR hacia main, pero no PR hacia develop. Integrar en develop activa su flujo de despliegue a dev.
- Las rutas del bundle incluyen mes, mientras los destinos de tablas del código suelen organizarse por año/tabla; no unificar esas convenciones sin revisar sus usos.

Esta base no contiene el diccionario completo de columnas ni todas las fórmulas o catálogos de valores de los notebooks. Para HUs fuera de los requisitos recogidos, leer las fuentes pertinentes y completar la spec. En especial, normalización de mes_carga en Spark, dominios permitidos, deduplicación y cardinalidad de joins requieren escenarios específicos; no inferir corrección desde las 14 pruebas unitarias.

## Contexto que consume el harness

exploration_context lee openspec/config.yaml y el contenido de cada spec listada por la CLI; con este paquete integrado tendrá esos seis contratos funcionales al explorar. El resto del contexto procede de HU/aclaraciones, skills de fase, instrucciones y dependencias OpenSpec, y lecturas autorizadas del repositorio. No hereda automáticamente el chat ni este paquete de ejemplos: los archivos deben estar integrados en la rama base cliente.
