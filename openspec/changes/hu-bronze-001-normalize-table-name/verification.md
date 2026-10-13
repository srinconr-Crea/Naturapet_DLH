# Verificación HU-BRONZE-001-Codex-Local

Fecha: 2026-10-13. Base: `develop@c5efcf154c7e56101e6dd6c3ea830f6512e6b184`.

## Resultado

Solo cambia el cuerpo de `normalize_table_name`; se mantienen firma, capitalización del prefijo y el chequeo mensual exacto. Once casos parametrizados cubren los criterios literales de la HU. La revisión independiente no encontró problemas; comprobó además extensiones dobles, mes sensible a mayúsculas, puntos internos y sufijos repetidos.

| Caso | Run del Job sandbox | Resultado pytest |
| --- | --- | --- |
| Control negativo, código original | 196791846417982 | 6 failed, 5 passed |
| Función corregida, pruebas nuevas | 618095537049869 | 11 passed |
| Función corregida, suite tests/ | 233846238020350 | 25 passed |

El estado SUCCESS del Job indica que el runner terminó; el campo `passed` del resultado distingue la prueba negativa fallida de las verificaciones positivas. `verification.json` conserva los resultados, enlaces, hashes de ZIP y fuentes, correlación run/attempt y revisión.

## Aislamiento

Perfil elegido por el usuario: `CREA_DEV`. Job `611081415041874`, `demo_harness_sandbox`, con identidad `dac4cb01-380f-4af5-b594-132d6d693beb`, distinta de la App `8910cd3e-32f6-4c75-b16f-b5ff3ea258d2`.

Se exportó y comprobó el hash del runner desplegado contra el runner del harness. El ZIP se ejecuta en directorio temporal mediante Python aislado y pytest, con un entorno sin credenciales. Los datos son cadenas y mocks; no se ejecutaron notebooks, bundle, jobs o pipelines cliente ni se escribieron datos de NaturaPet. Solo se escribieron ZIP/resultados en el volumen administrado `demo_harness_sandbox`. Pytest 8.4.1 ya pertenece al entorno del Job; no se agregaron dependencias.

## OpenSpec y límites

Delta del requisito `Nombre de tabla y lectura por formato`, sincronizado conservando los otros diez requisitos, Purpose y fuentes históricas. Los diez main specs y este cambio pasan validación strict. El ciclo remoto negativo/positivo comprueba el fallo y la corrección; no verifica ejecuciones Spark ni ingesta real.

El usuario autorizó explícitamente publicar un PR draft de piloto mediante Git/Codex y conservar los bloqueos. Esta publicación no usa ni certifica el recorrido `harness pr publish`: no hay binding de una HU fuente GitHub, ni las 144 capturas reales de modelos de Local-Harness 06/07, ni evidencia de su reconciliación/reanudación. Se conservan `local_harness_certified=false` y `next_increment_enabled=false`. Merge y despliegue permanecen humanos.
