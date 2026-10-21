# Borrador de PR — ingesta-mensual-cotizaciones-bronze

## Identidad y estado

- Repositorio: https://github.com/srinconr-Crea/Naturapet_DLH
- Remoto: origin.
- Origen: feature/hu-cotizaciones-bronze.
- Destino: develop.
- Creación: conector GitHub; solicitada expresamente por la persona el 2026-10-20. Sin merge ni auto-merge.
- Estado previo al commit: revisión y pruebas cerradas; archivo completado el 2026-10-21. Archivo, commit/push y creación del PR aprobados expresamente con «Sí, archivar y publicar el PR». Los recibos de publicación y URL del PR se entregan en la respuesta final.
- La rama incluye dos commits separados de preparación del kit Crea que aún no están en develop: 1b8ea55 y 6029d05. No incluye el cambio funcional de la HU anterior dd96ecd.

## Título previsto

feat: incorporar cotizaciones mensuales a Bronze con cuarentena e idempotencia

## Descripción prevista

La ingesta comercial necesitaba preservar originales y distinguir errores técnicos de alertas de negocio al recibir cotizaciones mensuales. Se incorpora un camino específico para fact_cotizaciones con contrato explícito, merge por cotizacion_id, consolidación de duplicados normalizados idénticos y cuarentena de grupos conflictivos.

Incluye identidad por contenido, evidencia original recuperable, auditoría conciliada, log de archivos fallidos, reintentos por etapas y archivo histórico verificado por checksum. Conserva el camino genérico de las demás entidades y dominios.

Validación local: 102 pruebas aprobadas, bundle dev y OpenSpec estricto aprobados. Pruebas reales Spark/Delta completas: SUCCESS, run 853804030647399 / task 169503786443292, CA01–CA14 passed, DBR16.4/Spark3.5.2/Python3.12.3. Revisión independiente favorable, 16/16 tareas verificadas y 10 specs válidas. Se conservan los dos intentos fallidos y sus correcciones de guardas de pruebas. Specs Bronze y contratos sincronizadas, preservando escenarios vigentes.

Recursos de validación fuera de catálogos NaturaPet: catálogo crea_cotizaciones_test_20261020_01a15a7c con 41 schemas de prueba y 32 tablas externas, raíz aislada aprobada y carpeta de workspace conservados para inspección. Clúster temporal TERMINATED y warehouse preexistente STOPPED, comprobados con API. Inventario, rutas y procedimiento de limpieza en inventario-recursos.md y runtime/inventario.md.

Limitación operativa: una muerte abrupta del driver deja la reserva fail-closed hasta reconciliación autorizada. No existe transacción multi-tabla. Sin despliegue del bundle, cambios a jobs existentes, permisos, credenciales ni catálogos NaturaPet.

## Recibo de aprobación y archivo

Aprobación humana específica recibida para HEAD 6029d05 + los 56 archivos de alcance-publicacion.md y los commits de setup 1b8ea55/6029d05, publicación en origin/feature/hu-cotizaciones-bronze y PR hacia develop con el título/cuerpo presentados. Reviewer archivó en openspec/changes/archive/2026-10-21-ingesta-mensual-cotizaciones-bronze; 10 specs válidas y ningún cambio activo. Principal repitió 102 pruebas locales y verificó los hashes de los 11 módulos y del notebook. Se comprobarán SHA remoto y PR real; los recibos se entregarán en la respuesta final sin editar documentos para insertar su propio SHA. Sin merge ni deploy.
