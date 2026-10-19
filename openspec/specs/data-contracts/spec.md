# Contratos de datos y derivaciones

## Purpose

Registrar los esquemas, claves, conversiones y reglas de columnas que el código actual declara. El diccionario de negocio completo se lee desde ADLS y no está versionado en este repositorio; este contrato no inventa su contenido.

Contrato del comportamiento implementado, documentado mediante lectura estática de `develop@eb35b87b79eb541c4832fccc8f8825412755f498`. Los escenarios describen resultados esperados del código actual; no constituyen evidencia de ejecución de Spark ni de despliegue en Databricks.

## Sources

- [src/common/schema.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/src/common/schema.py)
- [src/common/silver_incremental.py](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/src/common/silver_incremental.py)
- [notebooks/shared/silver/01_schema_standardization.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/shared/silver/01_schema_standardization.ipynb)
- [notebooks/shared/silver/02_null_corrections.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/shared/silver/02_null_corrections.ipynb)
- [notebooks/shared/silver/03_domain_normalization.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/shared/silver/03_domain_normalization.ipynb)
- [notebooks/shared/silver/04_business_derivations.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/shared/silver/04_business_derivations.ipynb)
- [notebooks/shared/silver/05_quality_checks.ipynb](https://github.com/srinconr-Crea/Naturapet_DLH/blob/eb35b87b79eb541c4832fccc8f8825412755f498/notebooks/shared/silver/05_quality_checks.ipynb)

## Claves configuradas Silver

| Tabla | Columnas PK |
| --- | --- |
| dim_fecha | fecha_id |
| dim_ciudad | ciudad_id |
| dim_tienda | tienda_id |
| dim_area_negocio | area_id |
| dim_centro_costo | centro_costo_id |
| dim_categoria_producto | categoria_id |
| dim_producto | producto_id |
| dim_proveedor | proveedor_id |
| bridge_producto_proveedor | producto_id, proveedor_id |
| dim_cliente | cliente_id |
| dim_empleado | empleado_id |
| dim_canal_venta | canal_id |
| dim_metodo_pago | metodo_pago_id |
| dim_campana_marketing | campana_id |
| dim_transportista | transportista_id |
| dim_motivo_devolucion | motivo_devolucion_id |
| fact_ventas_cabecera | venta_id |
| fact_ventas_detalle | detalle_venta_id |
| fact_devoluciones | devolucion_id |
| fact_marketing | marketing_id |
| fact_inventario_mensual | mes_carga, tienda_id, producto_id |
| fact_ajustes_inventario | ajuste_id |
| fact_compras | orden_compra_id |
| fact_logistica_entregas | entrega_id |
| fact_costos_mensual | costo_id |
| fact_presupuesto_mensual | presupuesto_id |
| fact_objetivos_mensuales | objetivo_id |
| fact_calidad_datos_carga | control_id |
| resumen_mensual_validacion | mes_carga |
| manifest | archivo |
| data_dictionary | tabla, campo |
| schema_relationships | tabla_origen, campo_origen, tabla_destino, campo_destino |

## Grupos de conversión de estandarización

Las listas siguientes se evalúan en el orden fecha, booleano, decimal(18,2), decimal(10,4), long y double. Las demás columnas terminadas en _id, sku y moneda se convierten a string; las restantes conservan su tipo previo.

| Tipo destino | Columnas declaradas |
| --- | --- |
| date mediante to_date | fecha, fecha_apertura, fecha_alta, fecha_registro, fecha_venta, fecha_devolucion, fecha_compra, fecha_ajuste, fecha_solicitud, fecha_prometida, fecha_entrega, fecha_inicio, fecha_fin, fecha_ingreso, fecha_generacion |
| boolean | es_fin_de_semana, es_festivo_colombia, es_ciudad_principal, permite_domicilio, atiende_b2b, controla_inventario, consentimiento_marketing, cliente_activo, requiere_logistica, requiere_revision_calidad, activa, es_proveedor_principal |
| decimal(18,2) | precio_lista, costo_estandar, valor_bruto, descuento_total, iva_total, valor_total, costo_total, margen_bruto, precio_unitario, descuento_valor, base_sin_iva, iva_valor, valor_total_linea, costo_total_linea, margen_bruto_linea, valor_reintegrado, gasto_marketing, ventas_atribuidas_valor, valor_impacto_costo, costo_unitario, subtotal_sin_iva, valor_total_compra, valor_inventario_costo, monto_presupuestado, monto_real, monto_presupuesto, monto_ejecutado, variacion_presupuesto, meta_ventas, meta_margen_bruto, salario_base_mensual, costo_negociado, costo_base_envio, costo_envio |
| decimal(10,4) | iva_tasa, descuento_pct, roas, costo_transaccion_pct, margen_objetivo, peso_demanda, factor_demanda, calificacion_servicio, calificacion_promedio, descuento_base_pct, meta_tasa_devolucion |
| long | fecha_id, anio, mes_numero, trimestre, semana_iso, dia_mes, metros_cuadrados, vida_util_dias, lead_time_promedio_dias, lead_time_dias, cantidad_minima_pedido, numero_lineas, linea_numero, cantidad, cantidad_devuelta, impresiones, clics, leads, conversiones_atribuidas, stock_inicial, entradas_compras, salidas_ventas, ajuste_unidades, merma_unidades, stock_final, punto_reorden, stock_seguridad, cobertura_dias, cantidad_comprada, dias_prometidos, dias_reales_entrega, dias_retraso, filas_carga, valores_nulos_o_blancos, errores_fk_detectados, duplicados_detectados, ventas, devoluciones, meta_tickets, meta_nps, meta_entregas |
| double | latitud, longitud, peso_estimado_kg, ticket_promedio |

## Códigos y valores permitidos

| Columna original | Columna de código |
| --- | --- |
| estado_venta | estado_venta_codigo |
| estado_linea | estado_linea_codigo |
| tipo_pedido | tipo_pedido_codigo |
| tipo_solucion | tipo_solucion_codigo |
| estado_devolucion | estado_devolucion_codigo |
| medio_principal | medio_principal_codigo |
| motivo_ajuste | motivo_ajuste_codigo |
| estado_ajuste | estado_ajuste_codigo |
| estado_orden | estado_orden_codigo |
| motivo_compra | motivo_compra_codigo |
| estado_stock | estado_stock_codigo |
| estado_entrega | estado_entrega_codigo |
| tipo_vehiculo | tipo_vehiculo_codigo |
| tipo_registro | tipo_registro_codigo |
| fuente_registro | fuente_registro_codigo |
| tipo_presupuesto | tipo_presupuesto_codigo |
| estado_sede | estado_sede_codigo |
| tipo_sede | tipo_sede_codigo |
| especie | especie_codigo |
| unidad_medida | unidad_medida_codigo |
| nivel_rotacion | nivel_rotacion_codigo |
| estado_producto | estado_producto_codigo |
| tipo_cliente | tipo_cliente_codigo |
| genero | genero_codigo |
| segmento_cliente | segmento_cliente_codigo |
| tipo_mascota_principal | tipo_mascota_codigo |
| nivel_fidelidad | nivel_fidelidad_codigo |
| rango_edad | rango_edad_codigo |
| cargo | cargo_codigo |
| tipo_contrato | tipo_contrato_codigo |
| estado_empleado | estado_empleado_codigo |
| nivel_experiencia | nivel_experiencia_codigo |
| tipo_proveedor | tipo_proveedor_codigo |
| estado_proveedor | estado_proveedor_codigo |
| tipo_campana | tipo_campana_codigo |
| moneda | moneda_codigo |

| Columna validada | Valores admitidos, sensibles a mayúsculas |
| --- | --- |
| estado_venta | Emitida, Facturada |
| estado_devolucion | Aprobada, En revision, Rechazada |
| estado_orden | Parcial, Pendiente, Recibida |
| estado_stock | Bajo, Normal, Sobrestock |
| estado_entrega | Cancelado en ruta, Entregado, Entregado tarde, Intento fallido |

## Derivaciones por tabla

En las fórmulas siguientes, dividir significa safe_divide: NULL para denominador cero o NULL y cociente en los demás casos. Las comparaciones y operaciones conservan la semántica de NULL de Spark; no hay sustitución global por cero.

| Tabla | Columnas derivadas y regla |
| --- | --- |
| dim_producto | margen_lista_pct=(precio_lista-costo_estandar)/precio_lista. |
| fact_ventas_cabecera | base_neta_sin_iva=valor_bruto-descuento_total; margen_pct=margen_bruto/base_neta_sin_iva; descuento_pct_real=descuento_total/valor_bruto; ticket_lineas_promedio=valor_total/numero_lineas; tiene_campana=campana_id no nulo. |
| fact_ventas_detalle | precio_neto_unitario_sin_iva=base_sin_iva/cantidad; precio_unitario_con_iva=valor_total_linea/cantidad; margen_linea_pct=margen_bruto_linea/base_sin_iva; descuento_aplicado=descuento_valor>0. |
| fact_devoluciones | devolucion_finalizada para Aprobada/Rechazada; devolucion_en_revision para En revision; dias_hasta_devolucion=datediff(fecha_devolucion,fecha_venta de cabecera) solo si existe la tabla de ventas del mismo schema. |
| fact_marketing | ctr=clics/impresiones; conversion_rate=conversiones_atribuidas/leads; cpc=gasto_marketing/clics; cpl=gasto_marketing/leads; roas_calculado=ventas_atribuidas_valor/gasto_marketing. |
| fact_inventario_mensual | stock_promedio=(stock_inicial+stock_final)/2; alerta_reorden=stock_final<=punto_reorden; alerta_stock_seguridad=stock_final<=stock_seguridad; rotacion_estimada=salidas_ventas/stock_promedio. |
| fact_ajustes_inventario | impacto_merma=merma_unidades>0. |
| fact_compras | costo_compra_promedio_sin_iva=subtotal_sin_iva/cantidad_comprada; costo_compra_promedio_con_iva=valor_total_compra/cantidad_comprada; iva_pct_real=iva_valor/subtotal_sin_iva; orden_recibida para Recibida; orden_abierta para Pendiente/Parcial. |
| fact_logistica_entregas | entrega_a_tiempo para Entregado con fecha_entrega no nula y dias_retraso<=0; entrega_tardia para Entregado tarde o fecha no nula con dias_retraso>0; entrega_fallida para Intento fallido; entrega_cancelada para Cancelado en ruta; entrega_pendiente=fecha_entrega nula; tipo_entrega_operativa=Interna si empleado_repartidor_id no nulo, Tercero en otro caso; costo_por_kg=costo_envio/peso_estimado_kg. |
| fact_costos_mensual | variacion_costo=monto_real-monto_presupuestado; variacion_costo_pct=variacion_costo/monto_presupuestado. |
| fact_presupuesto_mensual | ejecucion_presupuesto_pct=monto_ejecutado/monto_presupuesto. |

## Requirements

### Requirement: Contrato externo de diccionario Bronze

El diccionario SHALL obtenerse de la ruta configurada en ADLS, como CSV con tabla, campo, rol y tipo_dato_csv. Las filas SHALL agruparse por tabla, conservando las columnas declaradas para selección y conversión y las entradas rol=PK para claves Bronze. El repositorio no SHALL atribuirse un diccionario exhaustivo de entidades, obligatoriedad funcional, moneda o reglas de negocio adicional al archivo externo y a los mapas versionados.

#### Scenario: PK declarada en diccionario
- **WHEN** una fila tiene tabla=fact_compras, campo=orden_compra_id y rol=PK
- **THEN** build_primary_key_map incorpora orden_compra_id a las claves de esa tabla

#### Scenario: Columna adicional externa
- **WHEN** el diccionario contiene una columna que el archivo no trae
- **THEN** la validación de columnas esperadas la considera faltante, sin inferir que es opcional

### Requirement: Mapas de claves según etapa

Silver SHALL resolver claves con el inventario de esta spec y la precedencia descrita en silver-processing. La calidad Silver SHALL utilizar el mapa de negocio del notebook, que no incluye manifest, data_dictionary ni schema_relationships; su exclusión de ese mapa no SHALL confundirse con exclusión de la comprobación de tabla no vacía. Bronze SHALL usar las PK del diccionario externo en lugar de este mapa Silver.

#### Scenario: Metadatos en calidad
- **WHEN** data_dictionary aparece como tabla de negocio enumerada por quality_checks
- **THEN** se evalúa table_not_empty, pero no se añaden controles PK desde un mapa que no declara esa tabla

#### Scenario: Clave de inventario
- **WHEN** están presentes mes_carga, tienda_id y producto_id
- **THEN** el mapa Silver utiliza los tres componentes

### Requirement: Tipos y normalización declarados

La estandarización SHALL aplicar los grupos de conversión anteriores solo a columnas presentes. domain_normalization SHALL añadir las columnas de código del inventario anterior y flags <columna_codigo>_valido solo para los cinco catálogos indicados. La ausencia de una columna no SHALL crear automáticamente todas las columnas del contrato; su tratamiento depende de las expresiones y etapa que la use.

#### Scenario: Identificador de fecha
- **WHEN** fecha_id y tienda_id están presentes
- **THEN** fecha_id se convierte a long por su grupo y tienda_id a string por su sufijo

#### Scenario: Flag no configurado
- **WHEN** moneda está presente
- **THEN** se añade moneda_codigo, sin flag de catálogo porque moneda no está en ALLOWED_VALUES

### Requirement: Fórmulas y flags sin filtro de filas

business_derivations SHALL implementar el inventario anterior sin eliminar filas por sus flags ni multiplicar ratios por 100. Las fórmulas SHALL ser de fila; los agregados y ratios Gold SHALL seguir el contrato gold-marts. Las fechas de entrega y estados pueden activar varios flags simultáneos; estos flags no SHALL describirse como clasificación mutuamente excluyente.

#### Scenario: Entrega cancelada pendiente
- **WHEN** estado_entrega es Cancelado en ruta y fecha_entrega es NULL
- **THEN** entrega_cancelada y entrega_pendiente son true simultáneamente

#### Scenario: Rotación de inventario
- **WHEN** stock_inicial=10, stock_final=30 y salidas_ventas=8
- **THEN** stock_promedio=20 y rotacion_estimada=0.4
