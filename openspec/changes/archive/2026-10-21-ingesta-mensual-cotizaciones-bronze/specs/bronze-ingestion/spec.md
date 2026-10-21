# Spec Delta

## ADDED Requirements

### Requirement: Cotizaciones identificación mensual CA01
La ingesta SHALL asociar fact_cotizaciones_MM.csv exclusivamente en comercial a fact_cotizaciones; SHALL comprobar MM contra carpeta y parámetros de carga y el año contra carpeta y parámetro. SHALL conservar nombre físico original y rechazar discrepancias sin crear tablas mensuales.

#### Scenario: Fuente correcta
- **WHEN** fact_cotizaciones_02.csv está en 2026/02 y los parámetros seleccionan 2026/02
- **THEN** su tabla lógica es fact_cotizaciones y su trazabilidad conserva fact_cotizaciones_02.csv.

#### Scenario: Periodo discrepante
- **WHEN** el sufijo es 01 en carpeta 02 o el año/mes parametrizado difiere
- **THEN** el archivo queda FAILED registrado y sin archivarse, sin inferir año a partir del sufijo MM.

### Requirement: Cotizaciones CSV Unicode CA02
La lectura SHALL preservar campos CSV con comas, comillas escapadas y Unicode válido como tildes, ñ y emojis. SHALL detectar desajustes estructurales sin desplazar columnas ni considerar Unicode válido como error de calidad.

#### Scenario: Campo entrecomillado
- **WHEN** un campo contiene una coma, comillas escapadas, ñ y un emoji
- **THEN** se obtiene un solo campo con los caracteres originales.

#### Scenario: CSV malformado
- **WHEN** hay columnas desplazadas o quoting que impide delimitar registros de forma verificable
- **THEN** se preserva el archivo y se registra rechazo técnico de registro si es delimitable, o FAILED de archivo si no lo es; no se escribe una interpretación silenciosa.

### Requirement: Cotizaciones original recuperable CA03
Cada registro SHALL mantener payload original o referencia verificable a bytes originales y registro estable, incluso tras normalización, consolidación, rechazo, actualización de PK y archivo. SHALL registrar conversiones con campo y valor original; ninguna corrección SHALL destruir evidencia recibida.

#### Scenario: Normalización y posterior actualización
- **WHEN** T001 con espacios se normaliza y la PK recibe una corrección posterior
- **THEN** ambas recepciones originales y sus transformaciones siguen siendo recuperables aunque la principal conserve solo la versión actual.

### Requirement: Cotizaciones IDs técnicos CA04
Los identificadores SHALL conservarse como texto, eliminar espacios externos y convertir cadenas vacías o solo espacios a NULL. No SHALL inventarse IDs ni sustituir claves desconocidas por claves existentes.

#### Scenario: Espacios y ceros
- **WHEN** llegan " T001 ", " 001 " y "   " como IDs
- **THEN** se obtienen T001, 001 y NULL respectivamente y se conserva el original.

### Requirement: Cotizaciones PK y duplicados CA05
Una PK vacía normalizada SHALL ir a cuarentena. La comparación de filas SHALL ocurrir después de normalizar el contrato. Por PK, filas idénticas SHALL consolidarse en una aceptada; si hay contenidos distintos, todas las ocurrencias del grupo SHALL ir a cuarentena con DUPLICATE_PK, sin elegir ganadora ni contar además duplicados consolidados en ese grupo.

#### Scenario: Duplicados equivalentes
- **WHEN** dos filas técnicamente válidas solo difieren en espacios externos de ID o formato admitido de fecha
- **THEN** si sus 20 valores normalizados coinciden se acepta una y se cuenta una consolidada, preservando ambas procedencias.

#### Scenario: Grupo conflictivo
- **WHEN** una PK tiene tres ocurrencias con dos contenidos normalizados distintos
- **THEN** las tres quedan rechazadas con DUPLICATE_PK y el grupo aporta cero consolidadas y cero aceptadas.

#### Scenario: PK vacía
- **WHEN** cotizacion_id es NULL, vacío o espacios
- **THEN** el registro se rechaza sin asignarle una clave de negocio artificial.

### Requirement: Cotizaciones fechas CA06
fecha_cotizacion SHALL admitir solo yyyy-MM-dd, dd/MM/yyyy y yyyy/MM/dd, normalizarse a DATE ISO y registrar conversiones. Fechas vacías, imposibles o fuera del periodo procesado SHALL ir a cuarentena. No SHALL completarse desde otros campos.

#### Scenario: Tres formatos
- **WHEN** llegan 2026-02-03, 03/02/2026 y 2026/02/03 para febrero de 2026
- **THEN** representan la misma fecha y cada conversión queda trazada.

#### Scenario: Fecha inválida
- **WHEN** llega NULL, 31/02/2026 o una fecha de enero para carpeta febrero
- **THEN** cada registro se rechaza con campo y motivo, sin inferir una fecha alternativa.

### Requirement: Cotizaciones coherencia temporal CA07
fecha_id SHALL ser texto de ocho dígitos y corresponder a fecha_cotizacion. mes_carga SHALL tener exactamente yyyy-MM y coincidir con carpeta/parámetros. Los nulos, vacíos y discrepancias de ambos campos SHALL ir a cuarentena sin sustitución por el periodo de carpeta.

#### Scenario: Periodo exacto
- **WHEN** fecha_cotizacion es 2026-02-03, fecha_id es 20260203 y mes_carga es 2026-02
- **THEN** el control temporal acepta la fila para febrero de 2026.

#### Scenario: Nulo o formato extendido
- **WHEN** fecha_id es NULL o mes_carga es NULL o 2026-02-01
- **THEN** se rechaza la fila aunque otros campos permitan reconstruir el valor.

### Requirement: Cotizaciones conversión numérica CA08
La ingesta SHALL aplicar el contrato INT/DECIMAL con conversión segura y original recuperable. SHALL aceptar punto decimal sin miles; texto inválido, overflow y pérdida no autorizada de precisión SHALL producir cuarentena con campo y motivo. No SHALL convertir errores a cero ni a NULL silencioso; nulos admitidos SHALL conservarse.

#### Scenario: Texto numérico inválido
- **WHEN** llegan cinco, 125.000,50 o 19% en campos numéricos
- **THEN** cada registro se rechaza con el campo problemático y su valor original.

#### Scenario: Límites y nulos
- **WHEN** cantidad excede INT o un decimal no cabe en su precisión/escala
- **THEN** se rechaza con error explícito, mientras un campo nullable vacío se conserva NULL sin rellenarse con cero.

### Requirement: Cotizaciones alertas de negocio CA09
Filas técnicamente interpretables SHALL permanecer en Bronze con alertas cuando cantidad o vigencia_dias sean <=0, descuento_pct esté fuera de [0,1], moneda difiera de COP o estado_cotizacion no sea Aceptada, Rechazada o Vencida. Otros nulos permitidos SHALL conservarse con alerta de incompletitud cuando impidan evaluar reglas. Silver decide su corrección/exclusión.

#### Scenario: Alertas sin rechazo
- **WHEN** una fila válida técnicamente contiene cantidad=0, vigencia_dias=-1, descuento_pct=1.1, moneda=USD y estado_cotizacion=Pendiente
- **THEN** permanece aceptada en Bronze con las cinco alertas sin corrección automática.

#### Scenario: Dato incompleto
- **WHEN** descuento_pct o moneda son NULL
- **THEN** no se inventan valores y se registra la regla no evaluable por dato incompleto.

### Requirement: Cotizaciones importes CA10
La ingesta SHALL verificar base_sin_iva=cantidad*precio_unitario-descuento_valor, iva_valor=base_sin_iva*iva_tasa y valor_total_cotizacion=base_sin_iva+iva_valor, redondeando a dos decimales y aceptando desviación absoluta <=0.01 COP. SHALL alertar diferencias y operandos nulos sin recalcular ni reemplazar importes originales.

#### Scenario: Tolerancia
- **WHEN** la desviación es 0.01 y luego 0.02 COP
- **THEN** la primera pasa y la segunda genera alerta, conservándose los importes en ambas.

#### Scenario: Importe ausente
- **WHEN** precio_unitario o descuento_valor son NULL
- **THEN** la fórmula afectada queda no evaluable con alerta de incompletitud y no trata NULL como cero.

### Requirement: Cotizaciones cuarentena CA11
La cuarentena SHALL ser tabla Delta auxiliar con payload/referencia original, identidad estable de registro, archivo, load_id, periodo, instante de procesamiento y lista de errores por campo. Cada registro rechazado SHALL contarse una sola vez aunque tenga varios errores; reintentar contenido idéntico no SHALL duplicar incidencias.

#### Scenario: Varios errores
- **WHEN** un registro tiene PK vacía y fecha imposible
- **THEN** produce un registro de cuarentena con ambos errores y un rechazado.

### Requirement: Cotizaciones merge e identidad CA12
La principal SHALL ser Delta externa con merge por cotizacion_id: actualizar coincidencias, insertar nuevas y conservar ausentes y meses anteriores no reemplazados por esa PK. No SHALL versionar la PK por mes. La identidad de fuente SHALL considerar contenido; reprocesar contenido completado no SHALL duplicar filas/incidencias ni revertir correcciones posteriores.

#### Scenario: Corrección y replay antiguo
- **WHEN** A completa una cotización, B corrige su contenido y después se reenvía A con el mismo contenido
- **THEN** permanece la corrección B y no se duplican cuarentena ni filas por A.

#### Scenario: Archivo corregido
- **WHEN** un nombre ya procesado llega con contenido nuevo y contiene una PK existente y una nueva
- **THEN** se reconoce nuevo contenido, se actualiza/inserta por PK y se conservan las PK ausentes del archivo.

### Requirement: Cotizaciones conciliación y fallos CA13
SUCCESS y archivo SHALL requerir principal, cuarentena y auditoría persistidas y conciliadas por archivo: leídos=aceptados únicos+rechazados por registro+duplicados idénticos consolidados. Los rechazos controlados no SHALL implicar FAILED técnico. Una escritura fallida SHALL impedir archivo y registrar FAILED en log Delta auxiliar; si ese log falla también, la ejecución SHALL fallar visiblemente.

#### Scenario: Carga mixta conciliada
- **WHEN** se leen cinco registros, se aceptan dos únicos, se rechazan dos y se consolida uno
- **THEN** la conciliación permite SUCCESS tras persistir las tres salidas, sin contar dos veces los errores.

#### Scenario: Todo rechazado
- **WHEN** todos los registros van a cuarentena y las salidas concilian
- **THEN** el archivo puede ser SUCCESS con cero aceptados sin equivaler a fallo técnico.

#### Scenario: Fallo de persistencia y del log
- **WHEN** falla cuarentena/auditoría y también la escritura del log de fallos
- **THEN** se propaga fallo visible y no se mueve a histórico, sin afirmar FAILED persistido donde no pudo escribirse.

### Requirement: Cotizaciones recuperación y archivo verificable
El reintento SHALL recuperar persistencias parciales sin pérdida ni duplicación y no permitir que un intento antiguo sobreescriba uno posterior. El archivo SHALL verificar contenido en origen/histórico y conservar versiones físicas distintas sin sobrescribirlas. Una auditoría antigua no SHALL autorizar mover un contenido nuevo con el mismo nombre.

#### Scenario: Histórico preexistente
- **WHEN** la fuente falta y existe un histórico con hash distinto del esperado
- **THEN** el archivo queda fallido, sin confundir existencia con equivalencia.

#### Scenario: Fallo después del merge
- **WHEN** el merge completa pero la auditoría falla
- **THEN** el reintento reanuda el mismo contenido sin duplicaciones y no archiva hasta conciliar.

### Requirement: Cotizaciones alcance y regresión CA14
Las reglas especiales SHALL aplicarse solo a comercial.fact_cotizaciones. Otras entidades comerciales y dominios SHALL conservar lectura, claves, validación, rutas, persistencia y archivo actuales. Las tablas auxiliares de cotizaciones no SHALL convertirse involuntariamente en tablas de negocio de capas siguientes.

#### Scenario: Otra entidad
- **WHEN** se ingiere fact_ventas_cabecera y una entidad de shared
- **THEN** siguen su ruta genérica sin activar reglas ni tablas auxiliares de cotizaciones.

## MODIFIED Requirements

### Requirement: Descubrimiento y formatos admitidos

Para entidades distintas de comercial.fact_cotizaciones se conserva íntegramente el comportamiento siguiente. Para esa entidad SHALL prevalecer los requisitos específicos de cotizaciones añadidos en esta capacidad.

El descubrimiento SHALL considerar archivos directos del directorio anual como load_mode full, y archivos directamente dentro de carpetas 01 a 12 como incremental. SHALL admitir CSV, JSON y Parquet y rechazar Excel y extensiones no soportadas. SHALL ordenar por mes y nombre; no SHALL tratar full como una instrucción de borrado de la tabla.

#### Scenario: Archivo mensual
- **WHEN** se descubre fact_ventas_cabecera_01.csv dentro de 01
- **THEN** se registra mes 01 y modo incremental, y normalize_table_name devuelve fact_ventas_cabecera

#### Scenario: Excel no admitido
- **WHEN** se intenta detectar el formato de una fuente .xlsx
- **THEN** se genera ValueError y no se considera una fuente soportada

### Requirement: Validación previa a la carga

Para entidades distintas de comercial.fact_cotizaciones se conserva íntegramente el comportamiento siguiente. Para esa entidad SHALL prevalecer los requisitos específicos de cotizaciones añadidos en esta capacidad.

El runner SHALL rechazar archivos vacíos, tablas ausentes del diccionario salvo manifest, data_dictionary y resumen_mensual_validacion, y columnas requeridas faltantes. Para tablas del diccionario SHALL seleccionar y convertir sus columnas. Con carpeta mensual y columna mes_carga, SHALL rechazar valores no nulos que no correspondan a año-mes.

#### Scenario: Mes compatible
- **WHEN** la carpeta es 2026/01 y mes_carga es 2026-01, 2026-01-01 o 2026-01 00:00:00
- **THEN** la validación de correspondencia mensual acepta el valor

#### Scenario: Mes distinto o prefijo ambiguo
- **WHEN** la carpeta es 2026/01 y mes_carga es 2026-02, 202601 o 2026-0101
- **THEN** la validación rechaza el valor

#### Scenario: Mes nulo
- **WHEN** mes_carga es NULL
- **THEN** la comprobación de correspondencia mensual no lo rechaza por sí sola

### Requirement: Identidad y carga Delta

Para entidades distintas de comercial.fact_cotizaciones se conserva íntegramente el comportamiento siguiente. Para esa entidad SHALL prevalecer los requisitos específicos de cotizaciones añadidos en esta capacidad.

La carga SHALL añadir metadatos _np_ de dominio, año, mes, fuente, modo e instante de ingesta. La tabla nueva SHALL crearse como Delta externa particionada por _np_source_year y _np_source_month; la existente SHALL hacer MERGE con igualdad null-safe, actualizando coincidencias e insertando claves nuevas.

#### Scenario: Tabla nueva
- **WHEN** la tabla destino todavía no existe
- **THEN** se escribe en target_path con mergeSchema=true y las particiones técnicas de año y mes

#### Scenario: Tabla existente
- **WHEN** existe la tabla y la entrada contiene claves existentes y nuevas
- **THEN** el MERGE actualiza las coincidencias e inserta las nuevas sin configurar autoMerge global de la sesión

### Requirement: Claves y deduplicación de entrada

Para entidades distintas de comercial.fact_cotizaciones se conserva íntegramente el comportamiento siguiente. Para esa entidad SHALL prevalecer los requisitos específicos de cotizaciones añadidos en esta capacidad.

La carga SHALL usar las PK disponibles declaradas por el diccionario o, en su ausencia, _np_record_hash SHA-256 excluyendo _np_ingestion_ts. SHALL seleccionar una fila por clave con prioridad por instante y ruta/nombre de fuente cuando existan; no SHALL prometer desempate entre filas idénticas en todos esos criterios.

#### Scenario: Sin PK declarada
- **WHEN** no hay claves de diccionario disponibles en la entrada
- **THEN** se crea _np_record_hash, se deduplica por ese hash y se usa como clave del MERGE

### Requirement: Auditoría y ausencia de archivos

Para entidades distintas de comercial.fact_cotizaciones se conserva íntegramente el comportamiento siguiente. Para esa entidad SHALL prevalecer los requisitos específicos de cotizaciones añadidos en esta capacidad.

El runner SHALL registrar SUCCESS o FAILED por archivo procesado y emitir un resumen. Sin archivos SHALL registrar NO_DATA con __NO_FILES__. Si existen fallos procesados, SHALL generar RuntimeError después del resumen. La serialización de taskValues SHALL conservar payloads pequeños y compactar los grandes con conteos y muestras.

#### Scenario: Sin archivos nuevos
- **WHEN** el descubrimiento no devuelve fuentes
- **THEN** se registra NO_DATA, no se carga el diccionario y el resumen general es OK con no_data_message

#### Scenario: Resumen grande
- **WHEN** un resumen supera 48 KiB UTF-8
- **THEN** dumps_task_value usa una representación compacta con task_value_truncated y conteos; el caso cubierto por la prueba queda dentro del límite

### Requirement: Histórico solo de cargas exitosas pendientes

Para entidades distintas de comercial.fact_cotizaciones se conserva íntegramente el comportamiento siguiente. Para esa entidad SHALL prevalecer los requisitos específicos de cotizaciones añadidos en esta capacidad.

El archivo SHALL seleccionar auditorías con status SUCCESS y archived_at nulo. SHALL mover la fuente al histórico y actualizar su estado; si la fuente ya no existe pero sí el destino, SHALL registrar éxito. Si ambos faltan, SHALL registrar FAILED de archivo y generar error en el resumen.

#### Scenario: Reanudación de un archivo ya movido
- **WHEN** una auditoría exitosa sigue pendiente, la fuente falta y el histórico existe
- **THEN** se marca el archivo como exitoso sin exigir repetir el movimiento

#### Scenario: Carga fallida
- **WHEN** la auditoría de carga tiene status FAILED
- **THEN** no entra en list_pending_archives

### Requirement: Nombre de tabla y lectura por formato

Para entidades distintas de comercial.fact_cotizaciones se conserva íntegramente el comportamiento siguiente. Para esa entidad SHALL prevalecer los requisitos específicos de cotizaciones añadidos en esta capacidad.

detect_file_format SHALL comparar la extensión final en minúsculas y admitir csv, json y parquet. normalize_table_name SHALL eliminar únicamente el sufijo literal .csv, sensible a mayúsculas, y después el sufijo _<mes> si queda al final. El soporte del lector no SHALL interpretarse como eliminación de extensiones JSON, Parquet o CSV en mayúsculas al resolver tablas. CSV y JSON SHALL leerse con inferencia cuando no hay schema; CSV SHALL usar header=true y Parquet su esquema almacenado.

#### Scenario: Nombre JSON mensual
- **WHEN** se resuelve fact_ventas_01.json con mes 01
- **THEN** el nombre permanece fact_ventas_01.json; no se convierte automáticamente en fact_ventas

#### Scenario: CSV en mayúsculas
- **WHEN** se detecta y normaliza fact_ventas_01.CSV
- **THEN** el lector detecta csv y el normalizador conserva fact_ventas_01.CSV

### Requirement: Diccionario y evolución de columnas Bronze

Para entidades distintas de comercial.fact_cotizaciones se conserva íntegramente el comportamiento siguiente. Para esa entidad SHALL prevalecer los requisitos específicos de cotizaciones añadidos en esta capacidad.

load_data_dictionary SHALL leer CSV con header=true y agrupar sus filas por tabla usando tabla, campo, rol y tipo_dato_csv. conform_to_dictionary SHALL seleccionar únicamente las columnas declaradas y mapear object a string, int64 a long y float64 a double; otros tipos SHALL usar string. Las columnas declaradas faltantes SHALL causar ValueError; las columnas adicionales SHALL descartarse en tablas del diccionario. La tabla nueva SHALL usar mergeSchema=true y el MERGE existente no SHALL añadir explícitamente columnas ni activar autoMerge de sesión.

#### Scenario: Columna extra
- **WHEN** un CSV conocido tiene todas las columnas declaradas y una columna adicional
- **THEN** conform_to_dictionary excluye la adicional antes de la carga

#### Scenario: Tipo no reconocido
- **WHEN** tipo_dato_csv contiene un valor fuera de los tres tipos mapeados
- **THEN** la columna se convierte a string

#### Scenario: Evolución de tabla existente
- **WHEN** la entrada declarada incorpora una nueva columna y la tabla Delta ya existe
- **THEN** el código invoca MERGE sin ALTER TABLE ni configuración global de autoMerge; el resultado depende del esquema y runtime Delta

### Requirement: Relectura e identidad de archivos

Para entidades distintas de comercial.fact_cotizaciones se conserva íntegramente el comportamiento siguiente. Para esa entidad SHALL prevalecer los requisitos específicos de cotizaciones añadidos en esta capacidad.

run_bronze_load SHALL procesar todos los archivos descubiertos aún presentes en raw, sin excluirlos por auditorías SUCCESS anteriores y sin comprobar checksum de archivo. Una nueva lectura SHALL añadir un instante de ingesta nuevo y crear otro load_id. Las PK de diccionario SHALL prevalecer sobre el hash; cuando se usa hash SHALL incluir columnas de negocio y metadatos disponibles excepto _np_ingestion_ts, en el orden de columnas de entrada.

#### Scenario: Archivo exitoso que sigue en raw
- **WHEN** un archivo con auditoría SUCCESS anterior se descubre de nuevo
- **THEN** el runner vuelve a leerlo y realiza la carga por claves; no lo omite basándose en la auditoría

#### Scenario: Misma fila en otra fuente sin PK
- **WHEN** la fila de negocio se presenta con otra ruta y nombre de fuente
- **THEN** los metadatos participan en el hash y no se garantiza la misma identidad que en la fuente anterior

### Requirement: Límites de auditoría y fallos iniciales

Para entidades distintas de comercial.fact_cotizaciones se conserva íntegramente el comportamiento siguiente. Para esa entidad SHALL prevalecer los requisitos específicos de cotizaciones añadidos en esta capacidad.

El manejo por archivo SHALL abarcar validación de tabla, lectura, validaciones de datos, escritura y auditoría de ese archivo. El descubrimiento y la carga del diccionario SHALL ejecutarse antes del try por archivo; los fallos en esas fases no SHALL describirse como registros FAILED por archivo ni como resumen taskValues garantizado. path_exists SHALL devolver false ante cualquier excepción de ls; run_bronze_load SHALL tratar ese resultado como ausencia de fuentes si no falla una operación posterior.

#### Scenario: Formato no soportado descubierto
- **WHEN** discover_area_files encuentra un .xlsx en raw
- **THEN** detect_file_format lanza ValueError antes del bucle por archivo; no se genera el resumen final por ese camino

#### Scenario: Error al listar raw
- **WHEN** dbutils.fs.ls falla dentro de path_exists
- **THEN** path_exists devuelve false y el runner toma el camino sin fuentes; no distingue aquí permisos insuficientes de ruta ausente

### Requirement: Persistencia parcial y movimiento a histórico

Para entidades distintas de comercial.fact_cotizaciones se conserva íntegramente el comportamiento siguiente. Para esa entidad SHALL prevalecer los requisitos específicos de cotizaciones añadidos en esta capacidad.

La escritura de tabla, el append de auditoría y el movimiento a histórico SHALL ejecutarse por separado, sin rollback global. El archivador SHALL construir la carpeta destino y llamar dbutils.fs.mv, sin comparación de checksum ni política explícita de resolución de colisiones. El estado de archivo SHALL actualizarse por load_id; archived_at SHALL fijarse solo para éxitos de archivo.

#### Scenario: Fallo después de una escritura
- **WHEN** la escritura Delta termina y una operación posterior falla
- **THEN** el código no restaura la versión previa de la tabla; los datos escritos pueden permanecer

#### Scenario: Fuente y destino presentes
- **WHEN** el archivador encuentra la fuente y ya existe el destino histórico
- **THEN** invoca mv; no resuelve la colisión ni verifica equivalencia de contenido por su cuenta
