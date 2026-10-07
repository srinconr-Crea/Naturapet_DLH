# Spec Delta

## MODIFIED Requirements

### Requirement: Descubrimiento y formatos admitidos

El descubrimiento SHALL considerar archivos directos del directorio anual como load_mode full, y archivos directamente dentro de carpetas 01 a 12 como incremental. SHALL admitir CSV, JSON y Parquet y rechazar Excel y extensiones no soportadas. SHALL ordenar por mes y nombre; no SHALL tratar full como una instrucción de borrado de la tabla.

La normalización del nombre de tabla a partir del nombre de archivo SHALL eliminar primero la extensión final .csv, .json o .parquet, sin distinguir mayúsculas y minúsculas en la extensión. Después SHALL eliminar el sufijo _<month> únicamente si month está informado y coincide exactamente al final del nombre ya sin extensión. SHALL preservar las mayúsculas y minúsculas del nombre de tabla, conservar las extensiones no reconocidas y conservar los puntos internos del nombre. La normalización mantiene la firma vigente, con month opcional y vacío por defecto, y no SHALL alterar la detección de formatos ni la lectura de datos.

#### Scenario: Archivo mensual
- **WHEN** se descubre fact_ventas_cabecera_01.csv dentro de 01
- **THEN** se registra mes 01 y modo incremental, y normalize_table_name devuelve fact_ventas_cabecera

#### Scenario: Excel no admitido
- **WHEN** se intenta detectar el formato de una fuente .xlsx
- **THEN** se genera ValueError y no se considera una fuente soportada

#### Scenario: Extensión CSV con sufijo de mes
- **WHEN** se normaliza fact_ventas_01.csv con month 01
- **THEN** el nombre de tabla resultante es fact_ventas

#### Scenario: Extensión JSON con sufijo de mes
- **WHEN** se normaliza fact_ventas_01.json con month 01
- **THEN** el nombre de tabla resultante es fact_ventas

#### Scenario: Extensión Parquet con sufijo de mes
- **WHEN** se normaliza fact_ventas_01.parquet con month 01
- **THEN** el nombre de tabla resultante es fact_ventas

#### Scenario: Extensión en mayúsculas con nombre en mayúsculas mixtas
- **WHEN** se normaliza Fact_Ventas_01.CSV con month 01
- **THEN** el nombre de tabla resultante es Fact_Ventas y se preservan las mayúsculas del nombre

#### Scenario: Extensión con mayúsculas y minúsculas mezcladas
- **WHEN** se normaliza fact_ventas_01.JsOn con month 01
- **THEN** el nombre de tabla resultante es fact_ventas

#### Scenario: Archivo anual sin month
- **WHEN** se normaliza fact_ventas.PARQUET con month vacío
- **THEN** el nombre de tabla resultante es fact_ventas

#### Scenario: Sufijo distinto del mes informado
- **WHEN** se normaliza fact_ventas_02.csv con month 01
- **THEN** se elimina la extensión, no se elimina _02 y el nombre de tabla resultante es fact_ventas_02

#### Scenario: Month vacío no elimina sufijo numérico
- **WHEN** se normaliza fact_ventas_01.csv con month vacío
- **THEN** se elimina solo la extensión y el nombre de tabla resultante es fact_ventas_01

#### Scenario: Punto interno en el nombre
- **WHEN** se normaliza fact.ventas_01.json con month 01
- **THEN** el nombre de tabla resultante es fact.ventas y se conserva el punto interno

#### Scenario: Extensión no reconocida
- **WHEN** se normaliza fact_ventas_01.xlsx con month 01
- **THEN** el nombre de tabla resultante es fact_ventas_01.xlsx, sin eliminar la extensión ni el sufijo de mes

#### Scenario: Nombre sin extensión
- **WHEN** se normaliza fact_ventas_01 con month 01
- **THEN** se elimina el sufijo de mes y el nombre de tabla resultante es fact_ventas
