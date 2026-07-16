---
name: lifeos-performance-art
description: Audit visual performance impact of art changes — jank, recomposition, GPU, battery. Use for performance audit of UI/motion.
---

# Performance Art Audit

## Trigger
Performance audit, jank, recomposition, GPU, battery impact of visual changes.

## Documents to read
- `docs/design/PERFORMANCE_VISUAL_BUDGETS.md`
- `.cursor/rules/50-performance.mdc`

## Procedure
1. Identify expensive effects (blur, shaders, infinite animations)
2. Profile recomposition count on target screen
3. Test mid-tier device or emulator
4. Compare against budgets
5. Propose fallbacks

## Outputs
- Performance report with metrics
- Budget compliance table

## Success criteria
Within documented budgets or approved exception with fallback.
