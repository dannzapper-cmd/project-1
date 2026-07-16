---
name: lifeos-compose-design-translation
description: Translate approved design specs into Jetpack Compose semantic components and tokens. Use for Compose implementation from design.
---

# Compose Design Translation

## Trigger
Implement surface, translate Figma/tokens to Compose, create semantic components.

## Objective
Faithful Compose implementation preserving state/navigation architecture.

## Inputs
- Approved brief + design spec
- Target screen/component paths
- Token definitions

## Documents to read
- `docs/design/ART_DIRECTION_MASTER.md`
- `docs/design/LIFEOS_ART_CONTEXT_MANIFEST.md`
- `.cursor/rules/20-compose-ui.mdc`

## Procedure
1. Identify owners and state contracts — do not modify
2. Create/update tokens in `design-system/`
3. Build semantic components (Life*)
4. Wire screen with UI models only
5. Add @Preview for all states
6. Run unit/screenshot tests

## Outputs
- Compose components and theme updates
- Preview functions
- Test updates

## Limits
- No reducer/navigation/persistence changes
- No Material clone without Life OS identity

## Checklist
- [ ] Semantic naming
- [ ] State hoisted
- [ ] All visual states previewed
- [ ] Semantics for a11y
- [ ] Tests green

## Common errors
- Styling inside ViewModels
- Hard-coded colors/spacing
- Breaking navigation args

## Success criteria
Pixel-faithful to approved design; architecture diff shows UI layer only.
