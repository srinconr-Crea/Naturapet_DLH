# Skills propias del proyecto

Crear cada skill en `<nombre>/SKILL.md`, con frontmatter `name` unico y `description`.
Usar prefijo `project-` en el nombre para evitar colisiones globales. No hay una skill
ejecutable de ejemplo aqui: solo se activan skills con instrucciones reales.
Registrar ruta, proposito y roles consumidores en `docs/proyecto.json → extensions.skills`.
Seguir `docs/extensiones.md`. Reabrir una sesion y comprobar descubrimiento; si la app no
descubre subcarpetas agrupadas, leer por ruta desde AGENTS/orquestador o trasladar el
directorio de skill un nivel arriba y actualizar todas sus referencias.
