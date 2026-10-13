## MODIFIED Requirements

### Requirement: Nombre de tabla y lectura por formato

detect_file_format SHALL comparar la extensión final en minúsculas y admitir csv, json y parquet. normalize_table_name SHALL eliminar una única extensión final .csv, .json o .parquet sin distinguir mayúsculas, preservando la capitalización del nombre de tabla y sus puntos internos. Después SHALL eliminar el sufijo _<mes> únicamente si month está informado y coincide exactamente al final del nombre restante. SHALL conservar extensiones no reconocidas y el sufijo mensual cuando el mes está vacío o no coincide. CSV y JSON SHALL leerse con inferencia cuando no hay schema; CSV SHALL usar header=true y Parquet su esquema almacenado.

#### Scenario: Nombre JSON mensual
- **WHEN** se resuelve fact_ventas_01.json con mes 01
- **THEN** el nombre es fact_ventas

#### Scenario: CSV en mayúsculas
- **WHEN** se detecta y normaliza fact_ventas_01.CSV con mes 01
- **THEN** el lector detecta csv y el normalizador devuelve fact_ventas

#### Scenario: Formatos mensuales admitidos
- **WHEN** se normaliza fact_ventas_01.csv o fact_ventas_01.parquet con mes 01
- **THEN** el nombre es fact_ventas

#### Scenario: Capitalización preservada
- **WHEN** se normaliza Fact_Ventas_01.CSV con mes 01
- **THEN** el nombre es Fact_Ventas

#### Scenario: Extensión mixta
- **WHEN** se normaliza fact_ventas_01.JsOn con mes 01
- **THEN** el nombre es fact_ventas

#### Scenario: Parquet sin mes
- **WHEN** se normaliza fact_ventas.PARQUET sin mes informado
- **THEN** el nombre es fact_ventas

#### Scenario: Mes diferente
- **WHEN** se normaliza fact_ventas_02.csv con mes 01
- **THEN** el nombre es fact_ventas_02

#### Scenario: Sufijo mensual sin mes informado
- **WHEN** se normaliza fact_ventas_01.csv con mes vacío
- **THEN** el nombre es fact_ventas_01

#### Scenario: Puntos internos
- **WHEN** se normaliza fact.ventas_01.json con mes 01
- **THEN** el nombre es fact.ventas

#### Scenario: Extensión no reconocida
- **WHEN** se normaliza fact_ventas_01.xlsx con mes 01
- **THEN** el nombre es fact_ventas_01.xlsx

#### Scenario: Nombre sin extensión
- **WHEN** se normaliza fact_ventas_01 con mes 01
- **THEN** el nombre es fact_ventas
