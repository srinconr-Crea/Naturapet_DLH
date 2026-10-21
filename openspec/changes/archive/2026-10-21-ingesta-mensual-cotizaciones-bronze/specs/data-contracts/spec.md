# Spec Delta

## ADDED Requirements

### Requirement: Contrato explícito de cotizaciones Bronze
comercial.fact_cotizaciones SHALL usar las 20 columnas del escenario de esquema, con cotizacion_id STRING NOT NULL como única PK. Las otras columnas SHALL admitir NULL en representación técnica; fecha_id, fecha_cotizacion y mes_carga vacíos SHALL rechazarse por reglas de ingesta. Cantidad/vigencia no positivas SHALL generar alertas sin exclusión de Bronze.

#### Scenario: Esquema publicado
- **WHEN** se acepta una cotización y se publica en Bronze
- **THEN** sus columnas de negocio corresponden al siguiente contrato, además de metadatos técnicos y alertas:

| Campo | Tipo | Nullable técnico | Regla |
| --- | --- | --- | --- |
| cotizacion_id | STRING | No | PK, trim, vacío rechazado |
| fecha_id | STRING | Sí | yyyyMMdd correspondiente a fecha, vacío rechazado |
| fecha_cotizacion | DATE | Sí | Tres formatos admitidos, vacío rechazado |
| mes_carga | STRING | Sí | yyyy-MM exacto, vacío rechazado |
| tienda_id | STRING | Sí | Trim, vacío a NULL |
| ciudad_id | STRING | Sí | Trim, vacío a NULL |
| canal_id | STRING | Sí | Trim, vacío a NULL |
| producto_id | STRING | Sí | Trim, vacío a NULL |
| categoria_id | STRING | Sí | Trim, vacío a NULL |
| cantidad | INT | Sí | Entera; <=0 alerta |
| precio_unitario | DECIMAL(18,2) | Sí | Punto decimal, sin miles |
| descuento_pct | DECIMAL(10,4) | Sí | Esperado [0,1]; incumplimiento alerta |
| descuento_valor | DECIMAL(18,2) | Sí | 0 explícito sin descuento |
| base_sin_iva | DECIMAL(18,2) | Sí | Importe original |
| iva_tasa | DECIMAL(10,4) | Sí | 0 explícito cuando no aplica |
| iva_valor | DECIMAL(18,2) | Sí | 0 explícito cuando no aplica |
| valor_total_cotizacion | DECIMAL(18,2) | Sí | Importe original |
| moneda | STRING | Sí | COP esperado; otro valor alerta |
| estado_cotizacion | STRING | Sí | Aceptada, Rechazada, Vencida esperados |
| vigencia_dias | INT | Sí | >0 esperado; <=0 alerta |

#### Scenario: Nulo frente a cero explícito
- **WHEN** descuento_valor o iva_tasa están vacíos y otro registro contiene cero explícito
- **THEN** los primeros permanecen NULL con alerta si impiden evaluar fórmulas; los segundos conservan cero sin imputación.

### Requirement: Contrato de errores y alertas de cotizaciones
Cada error/alerta SHALL identificar código y campo con evidencia recuperable. Los errores técnicos SHALL enviar el registro a cuarentena; alertas de negocio/incompletitud SHALL acompañar registros aceptados. Identificadores de origen y carga no SHALL sustituir la PK de negocio. Las tablas auxiliares SHALL permanecer fuera del inventario de negocio de capas siguientes.

#### Scenario: Error técnico y alerta
- **WHEN** hay precio_unitario no numérico y moneda USD en una misma recepción
- **THEN** se conserva el error de conversión y la evidencia recibida; el registro no entra a principal y se cuenta una sola vez como rechazado.

## MODIFIED Requirements

### Requirement: Contrato externo de diccionario Bronze

Para comercial.fact_cotizaciones en Bronze SHALL prevalecer el contrato explícito añadido en esta capacidad y su PK cotizacion_id. Para las demás entidades y etapas se conserva íntegramente lo siguiente.

El diccionario SHALL obtenerse de la ruta configurada en ADLS, como CSV con tabla, campo, rol y tipo_dato_csv. Las filas SHALL agruparse por tabla, conservando las columnas declaradas para selección y conversión y las entradas rol=PK para claves Bronze. El repositorio no SHALL atribuirse un diccionario exhaustivo de entidades, obligatoriedad funcional, moneda o reglas de negocio adicional al archivo externo y a los mapas versionados.

#### Scenario: PK declarada en diccionario
- **WHEN** una fila tiene tabla=fact_compras, campo=orden_compra_id y rol=PK
- **THEN** build_primary_key_map incorpora orden_compra_id a las claves de esa tabla

#### Scenario: Columna adicional externa
- **WHEN** el diccionario contiene una columna que el archivo no trae
- **THEN** la validación de columnas esperadas la considera faltante, sin inferir que es opcional

### Requirement: Mapas de claves según etapa

Para comercial.fact_cotizaciones en Bronze SHALL prevalecer el contrato explícito añadido en esta capacidad y su PK cotizacion_id. Para las demás entidades y etapas se conserva íntegramente lo siguiente.

Silver SHALL resolver claves con el inventario de esta spec y la precedencia descrita en silver-processing. La calidad Silver SHALL utilizar el mapa de negocio del notebook, que no incluye manifest, data_dictionary ni schema_relationships; su exclusión de ese mapa no SHALL confundirse con exclusión de la comprobación de tabla no vacía. Bronze SHALL usar las PK del diccionario externo en lugar de este mapa Silver.

#### Scenario: Metadatos en calidad
- **WHEN** data_dictionary aparece como tabla de negocio enumerada por quality_checks
- **THEN** se evalúa table_not_empty, pero no se añaden controles PK desde un mapa que no declara esa tabla

#### Scenario: Clave de inventario
- **WHEN** están presentes mes_carga, tienda_id y producto_id
- **THEN** el mapa Silver utiliza los tres componentes
