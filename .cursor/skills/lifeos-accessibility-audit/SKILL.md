---
name: lifeos-accessibility-audit
description: Audit Life OS UI for accessibility — TalkBack, contrast, font scale, touch targets. Use for a11y audit or WCAG review.
---

# Accessibility Audit

## Trigger
Accessibility audit, TalkBack, WCAG, font scale, contrast review.

## Documents to read
- `docs/design/ACCESSIBILITY_VISUAL_RULES.md`
- `.cursor/rules/40-accessibility.mdc`

## Procedure
1. Run matrix: compact/expanded, 100/130/200% font, TalkBack, Reduce Motion
2. Check contrast on all materials (especially glass)
3. Verify touch targets and focus order
4. File findings P0/P1/P2
5. Propose fixes UI-layer only

## Outputs
- Audit report with severity
- Fix list or PR comments

## Success criteria
No P0 a11y blockers; P1s documented with plan.
