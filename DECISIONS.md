# Life OS · Architectural Decisions

Registro de decisiones para la fase artística de Fase 2.

## Formato

```text
### DEC-NNN · Título
- **Fecha:** YYYY-MM-DD
- **Estado:** accepted | provisional | superseded
- **Contexto:** ...
- **Decisión:** ...
- **Consecuencias:** ...
```

---

### DEC-001 · Infraestructura en repo actual como scaffold

- **Fecha:** 2026-07-16
- **Estado:** provisional
- **Contexto:** Cloud Agent conectado a `project-1` (LeadForge), no Life OS Android.
- **Decisión:** Crear toda la infraestructura documental y Cursor en esta rama para transferencia posterior.
- **Consecuencias:** Baseline Android incompleto; migración requerida al repo correcto.

### DEC-002 · Precedencia Dirección Artística v0.1.1

- **Fecha:** 2026-07-16
- **Estado:** accepted
- **Contexto:** Dos versiones casi idénticas del documento rector.
- **Decisión:** `LifeOS_Sistema_Direccion_Artistica_Fase2_Android_v0_1_1__` es canónico (añade sprint Figma intensivo).
- **Consecuencias:** v0_1_a318 preservado como histórico.

### DEC-003 · Sprint Figma de 6 llamadas en ventana corta

- **Fecha:** 2026-07-16
- **Estado:** accepted
- **Contexto:** Figma Starter View/Collab: 6 tool calls/month (verificado developers.figma.com 2026-07-16).
- **Decisión:** Consumir las 6 llamadas en sprint preparado de 1–pocos días, no mensualmente.
- **Consecuencias:** Preparación exhaustiva antes de cada llamada; 0 llamadas en BLOCK_ART_000.

### DEC-004 · Rechazo stack web del PDF p.17–21

- **Fecha:** 2026-07-16
- **Estado:** accepted
- **Contexto:** DISENO.pdf páginas 17–21 recomiendan React, Tailwind, Framer Motion.
- **Decisión:** Registrar como investigación histórica; Life OS Android usa Kotlin + Jetpack Compose exclusivamente.
- **Consecuencias:** Prompts Figma deben prohibir output web.

### DEC-005 · Plugin interno sin duplicar fuentes de verdad

- **Fecha:** 2026-07-16
- **Estado:** accepted
- **Contexto:** Evaluación plugin `.cursor/plugins/lifeos-art-studio/`.
- **Decisión:** Crear scaffold con manifest; reglas/skills activas permanecen en `.cursor/` raíz. Plugin referencia, no duplica.
- **Consecuencias:** Una sola fuente de verdad por componente.

### DEC-006 · Matriz tooling ADOPT_NOW mínima

- **Fecha:** 2026-07-16
- **Estado:** accepted
- **Contexto:** Global Design Intelligence Stack lista muchos candidatos.
- **Decisión:** ADOPT_NOW limitado a: GitHub (ya disponible), Rules/Skills/Agents propios, documentación en repo. Figma/Context7/MarkItDown = PREPARE (requieren auth).
- **Consecuencias:** Ver `docs/tooling/GLOBAL_DESIGN_TOOL_REGISTRY.md`.

### DEC-007 · Hooks command-based en cloud

- **Fecha:** 2026-07-16
- **Estado:** accepted
- **Contexto:** Cursor Cloud Agents soportan hooks de repo pero no prompt-based ni sessionStart/End.
- **Decisión:** Implementar hooks command en `.cursor/hooks.json`; marcar no soportados como PREPARED_NOT_ACTIVE.
- **Consecuencias:** Ver `.cursor/hooks/HOOKS_STATUS.md`.
