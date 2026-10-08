# Spec Delta

## MODIFIED Requirements

### Requirement: Nombre de tabla y lectura por formato

detect_file_format SHALL comparar la extensión final en minúsculas y admitir csv, json y parquet. normalize_table_name SHALL conservar su firma actual y resolver el nombre de tabla en este orden: primero SHALL eliminar la extensión final .csv, .json o .parquet sin distinguir mayúsculas de minúsculas; después SHALL eliminar el sufijo _<mes> únicamente si el mes está informado (no vacío) y coincide exactamente al final del nombre ya sin extensión. SHALL preservar las mayúsculas y minúsculas del nombre de tabla, SHALL conservar las extensiones no reconocidas (por ejemplo .xlsx) y los puntos internos del nombre, y SHALL eliminar como máximo una extensión (la final). Un nombre sin extensión SHALL tratarse igual que uno con extensión reconocida en cuanto al sufijo _<mes>. La normalización no SHALL modificar la detección de formatos ni la lectura de datos. CSV y JSON SHALL leerse con inferencia cuando no hay schema; CSV SHALL usar header=true y Parquet su esquema almacenado.

#### Scenario: Nombre JSON mensual
- **WHEN** se resuelve fact_ventas_01.json con mes 01
- **THEN** el nombre resuelto es fact_ventas

#### Scenario: Nombre Parquet mensual
- **WHEN** se resuelve fact_ventas_01.parquet con mes 01
- **THEN** el nombre resuelto es fact_ventas

#### Scenario: CSV mensual en minúsculas
- **WHEN** se resuelve fact_ventas_01.csv con mes 01
- **THEN** el nombre resuelto es fact_ventas

#### Scenario: CSV en mayúsculas
- **WHEN** se detecta y normaliza Fact_Ventas_01.CSV con mes 01
- **THEN** el lector detecta csv y el normalizador devuelve Fact_Ventas, preservando las mayúsculas del nombre de tabla

#### Scenario: Extensión con mayúsculas y minúsculas mezcladas
- **WHEN** se resuelve fact_ventas_01.JsOn con mes 01
- **THEN** el nombre resuelto es fact_ventas

#### Scenario: Archivo anual sin mes informado
- **WHEN** se resuelve fact_ventas.PARQUET con mes vacío
- **THEN** el nombre resuelto es fact_ventas

#### Scenario: Sufijo distinto del mes informado
- **WHEN** se resuelve fact_ventas_02.csv con mes 01
- **THEN** el nombre resuelto es fact_ventas_02, porque _02 no coincide con el mes informado

#### Scenario: Mes vacío conserva el sufijo
- **WHEN** se resuelve fact_ventas_01.csv con mes vacío
- **THEN** el nombre resuelto es fact_ventas_01, porque no se elimina ningún sufijo _<mes>

#### Scenario: Puntos internos preservados
- **WHEN** se resuelve fact.ventas_01.json con mes 01
- **THEN** el nombre resuelto es fact.ventas, conservando el punto interno

#### Scenario: Extensión no reconocida
- **WHEN** se resuelve fact_ventas_01.xlsx con mes 01
- **THEN** el nombre resuelto es fact_ventas_01.xlsx, sin eliminar la extensión ni el sufijo _01

#### Scenario: Nombre sin extensión
- **WHEN** se resuelve fact_ventas_01 con mes 01
- **THEN** el nombre resuelto es fact_ventas

#### Scenario: Orden de eliminación
- **WHEN** el sufijo _<mes> aparece antes de la extensión, como en fact_ventas_01.csv con mes 01
- **THEN** primero se elimina la extensión y después el sufijo, sin eliminar el sufijo cuando éste no queda al final tras quitar la extensión
