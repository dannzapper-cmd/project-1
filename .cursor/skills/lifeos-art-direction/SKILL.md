---
name: lifeos-art-direction
description: Apply Life OS art direction when designing or reviewing UI surfaces, tokens, or visual identity. Use for art direction, Cognitive Glass, white architecture, semantic color.
---

# Life OS Art Direction

## Trigger
Art direction, visual identity, Cognitive Glass, blanco/negro/arcoíris, material decisions.

## Objective
Ensure surfaces align with Danny's direction without breaking architectural invariants.

## Inputs
- Surface name and node
- References (Figma, PDF, brief)
- Current Compose implementation path

## Documents to read
- `docs/design/ART_DIRECTION_MASTER.md`
- `docs/source/raw/design/LifeOS_Sistema_Direccion_Artistica_Fase2_Android_v0_1_1__80c4.md`
- `docs/source/normalized/design/DISENO_PDF_INDEX.md`

## Procedure
1. Read brief and canonical art docs
2. Map node → color semantics → material register (Void vs Living Object)
3. Propose token-level changes only; no domain changes
4. Flag WCAG risks on glass/blur
5. Document decisions for Danny approval

## Outputs
- Art direction notes in brief or PR
- Token proposals in `design-system/tokens/`
- Checkpoint update if block-level

## Limits
- Does not approve final aesthetic — Danny does
- Does not invoke Figma MCP without harvest plan
- Does not copy protected designs literally

## Checklist
- [ ] White predominant, black for precision
- [ ] Rainbow semantic only
- [ ] Reactive light purposeful
- [ ] No government/SaaS generic look
- [ ] Architecture invariant preserved

## Common errors
- Iridescent gradients everywhere
- Glass on dense text lists
- Neumorphism without contrast

## Success criteria
Surface proposal matches SRC-001 and passes red-team contrast check.
