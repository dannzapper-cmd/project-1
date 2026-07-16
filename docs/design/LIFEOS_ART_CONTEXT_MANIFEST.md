# Life OS Art Context Manifest

**Version:** 0.1 · 2026-07-16

Maps task types → documents, rules, skills, agents, MCPs, protected owners, tests, evidence, DoD.

## Task: Incorporación documentos (BLOCK_ART_000)

| Item | Reference |
|---|---|
| Docs obligatorios | SOURCE_INDEX, SOURCE_IMPORT_MANIFEST, checkpoint |
| Docs opcionales | Todos los maestros pendientes |
| Rules | 00, 70, 80 |
| Skills | — |
| Subagentes | — |
| MCPs | GitHub (read) |
| Owners protegidos | Todos |
| Pruebas | validate-art-context.sh |
| Evidencia | Manifest + checksums |
| DoD | Adjuntos incorporados o bloqueados honestamente |

## Task: Brief artístico

| Item | Reference |
|---|---|
| Docs | ART_DIRECTION_MASTER, SRC-001, DISENO PDF index |
| Rules | 00, 10 |
| Skills | lifeos-art-direction, lifeos-node-art-identity |
| Subagentes | art-director |
| MCPs | — |
| Pruebas | — |
| Evidencia | `docs/design/evidence/brief_*.md` |
| DoD | Danny approval recorded |

## Task: Figma harvest (per call)

| Item | Reference |
|---|---|
| Docs | FIGMA_SIX_CALL_PLAN, FIGMA_SELECTION_CHECKLIST, FIGMA_PROMPT_TEMPLATE |
| Rules | 60, 70 |
| Skills | lifeos-figma-harvest |
| Subagentes | art-director (readonly) |
| MCPs | Figma official (1 call) |
| Pruebas | — |
| Evidencia | raw/ + normalized/ per call |
| DoD | Raw saved, normalized, Compose-oriented, license noted |

## Task: Implementar superficie

| Item | Reference |
|---|---|
| Docs | Brief aprobado, tokens, NODE_ART_IDENTITIES |
| Rules | 00, 10, 20, 30, 40, 50 |
| Skills | lifeos-compose-design-translation, motion, haptics |
| Subagentes | compose-architect |
| MCPs | Context7 (optional, docs) |
| Owners protegidos | ViewModels, reducers, nav, persistence |
| Pruebas | Unit, screenshot, a11y matrix |
| Evidencia | before/after, main states |
| DoD | Manifest surface DoD in AGENTS.md |

## Task: Auditoría visual

| Item | Reference |
|---|---|
| Docs | DESIGN_AUDIT_PROTOCOL |
| Rules | 10, 40, 50 |
| Skills | lifeos-design-red-team, lifeos-accessibility-audit, lifeos-performance-art |
| Subagentes | visual-red-team, accessibility-auditor, performance-auditor, motion-director |
| Pruebas | Visual regression if baselines exist |
| Evidencia | audit report |
| DoD | No P0 open; P1s documented |

## Task: Cerrar bloque

| Item | Reference |
|---|---|
| Rules | 80 |
| Commands | lifeos-close-block |
| Evidencia | Checkpoint actualizado |
| DoD | Siguiente acción exacta definida |

## MCP matrix

| MCP | Tasks | Classification |
|---|---|---|
| GitHub | All | ADOPT_NOW |
| Figma | Harvest only | PREPARE (auth required) |
| Context7 | Implement, docs | PREPARE |
| MarkItDown | PDF import | PREPARE |
| MCP Inspector | Security review | PREPARE |
