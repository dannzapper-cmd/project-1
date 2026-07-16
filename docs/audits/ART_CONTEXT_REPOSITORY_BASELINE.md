# Life OS · Art Context Repository Baseline

**Fecha:** 2026-07-16  
**Branch:** `cursor/art-context-tooling-51a8`  
**HEAD base:** `bde704ff5798d2eb04e15bb0936d8e015b6fb957`

---

## Hallazgo crítico P0

El repositorio conectado (`dannzapper-cmd/project-1`) es **LeadForge** — una aplicación web de portfolio (Next.js + FastAPI), **no** Life OS Android.

| Esperado (Life OS) | Encontrado |
|---|---|
| Kotlin + Jetpack Compose | TypeScript + React/Next.js |
| Módulos Gradle Android | `package.json`, `pnpm-lock.yaml` |
| `app/`, `feature-*` Android | `app/`, `components/`, `lib/` web |
| Design system Compose | Tailwind + shadcn/ui |
| 0 referencias Life OS | 0 matches "LifeOS"/"Life OS"/Kotlin |

**Impacto:** La auditoría Android solicitada no puede completarse en este repo. La infraestructura de contexto se crea como scaffold transferible.

---

## Arquitectura detectada (LeadForge — real)

### Frontend

- **Framework:** Next.js (App Router)
- **UI:** React 19, Tailwind CSS, shadcn/ui (`components/ui/`)
- **Estado:** React hooks, client components
- **API:** `lib/api/client.ts` → FastAPI backend

### Backend

- **Framework:** FastAPI (Python)
- **Ubicación:** `backend/app/`
- **Servicios:** pipeline, agents (research, qualifier, strategist, QA), intake, telemetry
- **Tests:** `backend/tests/` (pytest)

### Módulos / estructura

```text
app/           → Next.js pages
components/    → React UI (dashboard, ui primitives)
lib/           → API client, types, metrics, intake, export
backend/       → FastAPI services
docs/          → Portfolio, deployment, architecture
knowledge/     → Sales playbooks (markdown)
data/          → Demo data
```

### Navegación

- Single-page demo dashboard (`app/page.tsx`)
- No Android Navigation Compose

### Estado / persistencia

- Client-side preview state (`lib/intake/preview-state.ts`)
- Backend run services; no Room/DataStore

### Componentes visuales existentes

- shadcn/ui primitives (button, card, table, dialog, etc.)
- Dashboard components (`components/dashboard/`)
- Light theme portfolio styling

### Design tokens actuales

- Tailwind CSS variables en `app/globals.css`, `styles/globals.css`
- `components.json` (shadcn config)
- **No** tokens Life OS (blanco vivo, arcoíris semántico, Cognitive Glass)

### Motion y haptics

- No Framer Motion en dependencias principales detectadas
- **No** haptics (web)
- Spinner/sonner para feedback

### Tests

| Suite | Ubicación | Tipo |
|---|---|---|
| Frontend unit | `lib/**/__tests__/` | Vitest/Jest patterns |
| Backend | `backend/tests/` | pytest |
| Screenshot | `docs/assets/screenshots/` | Evidencia manual portfolio |
| Visual regression | No Paparazzi/Roborazzi | N/A (web) |
| Compose Preview | N/A | — |

### Accesibilidad

- Componentes Radix-based (shadcn) con semantics web básicas
- Sin auditoría TalkBack (Android)

### Performance tooling

- No Macrobenchmark/JankStats
- Next.js build optimization estándar

### Deuda relevante

| ID | Severidad | Item |
|---|---|---|
| D-001 | P0 | Repo incorrecto para Life OS |
| D-002 | P1 | Documentos maestros Life OS ausentes |
| D-003 | P2 | Sin `.cursor/` previo |

### Duplicaciones

- Dos versiones Dirección Artística (v0.1 / v0.1.1) — registradas

### Reglas y tooling existentes

- `.github/` workflows (CI)
- Sin `AGENTS.md`, sin `.cursor/rules/` previos
- `README.md` extenso para portfolio

### Partes que el futuro rediseño Life OS debe proteger

Cuando exista el repo Android real, proteger:

- Navegación y graph
- Owners canónicos por feature
- Reducers, events, mutations, receipts
- Undo / Saver
- Persistencia y migraciones
- Process recreation
- Contratos demo providers
- Consentimiento, permisos, privacidad
- Deep links
- Interfaces futuras backend/sync/IA

### Incompatibilidades documento ↔ código

| Documento | Código actual | Severidad |
|---|---|---|
| Android nativo Kotlin Compose | Next.js TypeScript | P0 |
| Life OS nodos (Salud, Finanzas…) | LeadForge B2B sales | P0 |
| Cognitive Glass design system | shadcn/Tailwind portfolio | P0 |
| Figma → Compose handoff | No design-system/ Android | P1 |

---

## Checklist Android (pendiente — repo Life OS)

Cuando el repo correcto esté conectado, auditar:

- [ ] `settings.gradle.kts` / módulos feature
- [ ] Navigation graph y deep links
- [ ] State holders / ViewModels / reducers
- [ ] Room/DataStore y migraciones
- [ ] `design-system/` o equivalente Compose
- [ ] Motion (Animation APIs, Lottie)
- [ ] Haptics (HapticFeedbackType)
- [ ] Screenshot tests (Paparazzi/Roborazzi)
- [ ] Accessibility (semantics, font scale)
- [ ] Baseline profiles / Macrobenchmark

---

## Siguiente acción

Conectar repositorio Life OS Android y re-ejecutar esta auditoría sobre código real.
