# Configuracion del kit manual Crea

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Preparar Naturapet_DLH en esta carpeta desde develop usando el kit Crea 0.1.3.

**Architecture:** Clonar el repositorio y preservar su store OpenSpec y skills. Integrar archivos ausentes y reconciliar configuracion con el contexto real del proyecto.

**Tech Stack:** Git, PowerShell, OpenSpec, Codex y Databricks CLI.

**Spec:** Solicitud humana de esta sesion y docs/configuracion-manual.md del kit; las excepciones humanas prevalecen.

## Global Constraints
- Solo verificar versiones; sin instalar ni actualizar herramientas.
- Git local: srinconr / srinconr@creasistemas.com. Perfil Databricks: CREA_DEV.
- Preservar skills existentes; agregar solo ausentes. No copiar LEEME-CREA.md.
- Combinar .gitignore; preservar specs. Sin commit, push, deploy o ejecucion de jobs.

## Review Focus
- Carpeta inicial con .git vacio: conservar respaldo temporal antes de clonar.
- Skills existentes: comprobar ausencia de diferencias contra HEAD.
- OpenSpec ya configurado: mantener schema, specs y espanol; no sobrescribir con ejemplos.
- Dependencias ausentes: registrarlas sin instalar ni afirmar pruebas realizadas.
- Perfil Databricks: validar identidad, host y target explicitamente.

## Task 1: Preparacion verificable
- [x] Verificar versiones y carpeta destino.
- [x] Clonar develop y configurar identidad Git local.
- [x] Copiar archivos ausentes, excluir LEEME-CREA y combinar ignores.
- [x] Inicializar Codex/OpenSpec y conservar los siete workflows originales.
- [x] Completar contexto, inventario, checks y perfil reales.
- [x] Verificar estructura, integridad de skills, store y bundle dev.
- [x] Documentar limitaciones: pytest ausente, gh no localizado y perfiles nativos pendientes de una sesion nueva.

La persona autorizo continuar si no habia dudas; no se inicia ninguna HU con esta preparacion.
