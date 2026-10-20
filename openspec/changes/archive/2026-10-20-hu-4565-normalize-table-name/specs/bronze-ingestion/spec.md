## MODIFIED Requirements

### Requirement: Nombre de tabla y lectura por formato

detect_file_format SHALL comparar la extensión final en minúsculas y admitir csv, json y parquet. normalize_table_name SHALL eliminar una única extensión final .csv, .json o .parquet sin distinguir mayúsculas, preservar la caja y puntos internos del nombre y conservar extensiones desconocidas. Después SHALL eliminar una única terminación _<month> solo si month está informado y coincide exactamente al final. CSV y JSON SHALL leerse con inferencia cuando no hay schema; CSV SHALL usar header=true y Parquet su esquema almacenado.

#### Scenario: Nombre JSON mensual
- **WHEN** se resuelve fact_ventas_01.json con mes 01
- **THEN** el nombre es fact_ventas

#### Scenario: CSV en mayúsculas
- **WHEN** se detecta y normaliza fact_ventas_01.CSV con mes 01
- **THEN** el lector detecta csv y el normalizador devuelve fact_ventas

#### Scenario: Formatos y variantes de caja
- **WHEN** se normaliza Ventas_01 con extensión final .csv, .CSV, .CsV, .json, .JSON, .JsOn, .parquet, .PARQUET o .PaRqUeT y mes 01
- **THEN** el nombre es Ventas, preservando su mayúscula inicial

#### Scenario: Mes ausente
- **WHEN** se normaliza Ventas_01.JSON sin informar month, con month vacío o con month None
- **THEN** se obtiene Ventas_01 sin eliminar el sufijo mensual

#### Scenario: Coincidencia mensual exacta
- **WHEN** se normaliza Ventas_01.parquet con mes 1 o 02, Ventas_010.csv con mes 01, o Ventas_01_extra.csv con mes 01
- **THEN** se obtienen respectivamente Ventas_01, Ventas_010 y Ventas_01_extra, conservando los sufijos que no coinciden exactamente

#### Scenario: Extensión desconocida o compuesta
- **WHEN** se normalizan Ventas_01.xlsx, Ventas_01.csv.gz y Ventas_01.csv.backup con mes 01
- **THEN** los nombres se conservan completos porque su extensión final no es reconocida y no terminan en _01

#### Scenario: Puntos internos y una sola extensión
- **WHEN** se normalizan Ventas.v2_01.JsOn y Ventas.csv.json con mes 01
- **THEN** se obtienen Ventas.v2 y Ventas.csv respectivamente

#### Scenario: Nombre sin extensión
- **WHEN** se normalizan Ventas_01 y Ventas_01_01 con mes 01
- **THEN** se obtienen Ventas y Ventas_01 respectivamente, retirando solo el último sufijo mensual

#### Scenario: Orden de eliminación sin segundo pase
- **WHEN** se normalizan Ventas.csv_01 y Ventas.xlsx_01 con mes 01
- **THEN** se obtienen Ventas.csv y Ventas.xlsx; la fase de extensión no se repite después de retirar el mes

#### Scenario: Nombre vacío
- **WHEN** se normaliza la cadena vacía con month vacío o 01
- **THEN** se devuelve la cadena vacía
