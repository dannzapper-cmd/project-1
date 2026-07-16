# Life OS · Documented Contradictions

Contradicciones registradas. **No resolver silenciosamente.**

## Formato

```text
### CON-NNN · Título
- **Severidad:** P0 | P1 | P2
- **Fuentes en conflicto:** ...
- **Descripción:** ...
- **Estado:** open | resolved | accepted-divergence
- **Resolución propuesta:** ...
```

---

### CON-001 · Repositorio conectado vs producto Life OS

- **Severidad:** P0
- **Fuentes en conflicto:** SUPERPROMPT 001 (Life OS Android) ↔ `git remote` (project-1 LeadForge)
- **Descripción:** Toda la documentación asume app Android modular; el repo contiene portfolio web B2B.
- **Estado:** open
- **Resolución propuesta:** Danny reconecta Cloud Agent al repo Life OS Android; migrar rama `cursor/art-context-tooling-51a8`.

### CON-002 · PDF investigación web vs stack Android

- **Severidad:** P1
- **Fuentes en conflicto:** DISENO.pdf p.17–21 ↔ SRC-001 §4, DEC-004
- **Descripción:** PDF recomienda Framer Motion, Tailwind, React, v0.dev. Life OS exige Compose nativo.
- **Estado:** accepted-divergence
- **Resolución propuesta:** PDF p.1–16 = referencia visual; p.17–21 = histórico descartado para implementación.

### CON-003 · Figma MCP "cosecha mensual" vs sprint intensivo

- **Severidad:** P2
- **Fuentes en conflicto:** SRC-005 (v0.1 §5.3 "cosechas mensuales") ↔ SRC-001 (v0.1.1 §5.1.1 sprint corto)
- **Descripción:** Versiones del mismo documento difieren en cadencia de llamadas Figma.
- **Estado:** resolved
- **Resolución propuesta:** Prevalece SRC-001 v0.1.1 — sprint intensivo en pocos días (DEC-003).

### CON-004 · Plugin naming

- **Severidad:** P2
- **Fuentes en conflicto:** SRC-002 (`lifeos-art-studio`) ↔ SRC-001 §7.3 (`lifeos-art-direction`)
- **Descripción:** Nombres provisionales distintos para plugin interno.
- **Estado:** open
- **Resolución propuesta:** Usar `lifeos-art-studio` como nombre de paquete; Danny decide nombre final.

### CON-005 · Documentos maestros referenciados pero ausentes

- **Severidad:** P1
- **Fuentes en conflicto:** SUPERPROMPT lista 12 fuentes ↔ repo (4 incorporadas)
- **Descripción:** Cognitive Glass DNA, Roadmap Maestro, Principios IA, etc. no disponibles.
- **Estado:** open
- **Resolución propuesta:** Danny proporciona archivos; actualizar SOURCE_IMPORT_MANIFEST.

### CON-006 · LeadForge light theme vs Life OS blanco vivo

- **Severidad:** P2
- **Fuentes en conflicto:** Código LeadForge (portfolio light SaaS) ↔ SRC-001 dirección artística
- **Descripción:** Estética actual del repo no representa Life OS. Irrelevante tras migración de repo.
- **Estado:** open (se resuelve con CON-001)

## Propuesta de actualización

Ninguna contradicción resuelta sin acción de Danny en CON-001 y CON-005.
