# Figma Six Call Plan · SPRINT_FIGMA_001

**Status:** PREPARED — NOT EXECUTED  
**Calls consumed:** 0 / 6

## Sprint policy

Consume all 6 calls in a short intensive window after preparation (DEC-003). Not monthly pacing.

---

## Call 1 · Foundations

| Field | Value |
|---|---|
| **Objective** | Palette, typography, scale, spacing, radii, shadows, borders, materials, icon grid, density |
| **Selection** | Consolidated foundation page in Figma |
| **Expected output** | Token-ready spec in Compose terms |
| **Android prompt** | Kotlin + Jetpack Compose Color/Type/Shape tokens |
| **Destination** | `raw/.../call_01_*` → `normalized/FIGMA_FOUNDATION.md` → `design-system/tokens/` |
| **Success** | Complete token map implementable without re-call |
| **If incomplete** | Manual variable export + supplement in call 6 |

## Call 2 · Primitives

| **Objective** | Buttons, inputs, chips, toggles, sliders, tabs, nav chrome, all interaction states |
| **Destination** | `normalized/FIGMA_COMPONENTS.md` |
| **Success** | State matrix: default/pressed/focused/disabled/error |

## Call 3 · Widgets & Dashboards

| **Objective** | Card anatomy, charts, hierarchies, compact/expanded, data density |
| **Destination** | `normalized/FIGMA_WIDGETS.md` |
| **Success** | Widget contracts for LifeWidget, LifeMetric |

## Call 4 · LIAH + Quick Dial

| **Objective** | Orb states, geometry, light layers, transforms, motion intent, gestures |
| **Destination** | `normalized/FIGMA_LIAH_QUICK_DIAL.md` |
| **Success** | LiahOrb + QuickDial semantic spec with motion notes |

## Call 5 · Node Identities

| **Objective** | Salud, Finanzas, Personal, Hogar, Movilidad, Mundo, Profesión, Mis Datos, Emergencia |
| **Destination** | `normalized/FIGMA_NODE_IDENTITIES.md` |
| **Success** | Per-node accent semantics without breaking white architecture |

## Call 6 · Flow / Audit / Gap fill

| **Objective** | Key end-to-end flow OR audit gap from calls 1–5 OR priority re-extraction |
| **Destination** | `normalized/FIGMA_FLOW_CONTRACTS.md` |
| **Success** | No critical foundation gap remains |

---

## Per-call file template

```text
raw/SPRINT_FIGMA_001/
├── call_0N_prompt.md
├── call_0N_selection.md
├── call_0N_raw_response.md
├── call_0N_metadata.md
└── call_0N_screenshot.png (if available)
```

## Authorization gate

Danny approves selection + call timing before any MCP invocation.
