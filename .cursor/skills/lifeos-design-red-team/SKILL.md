---
name: lifeos-design-red-team
description: Adversarial review of Life OS design for generic SaaS drift, contrast failures, and identity loss. Use for design critique or red team review.
---

# Design Red Team

## Trigger
Red team, design critique, anti-patterns, generic SaaS check, collage detection.

## Documents to read
- `docs/design/ART_DIRECTION_MASTER.md`
- `docs/design/DESIGN_AUDIT_PROTOCOL.md`
- SRC-001 art direction doc

## Procedure
1. Ask: Does this look government/bank/clinical/SaaS?
2. Check for style collage (neumo+glass+clay uncontrolled)
3. Verify white architecture not compromised
4. Check rainbow not decorative noise
5. Verify architecture diff is UI-only
6. Report blockers vs nits

## Outputs
- Red team report (blockers / warnings / passes)

## Prohibitions
- Does not implement fixes (delegates to compose-architect)
- Does not override Danny's approved choices

## Success criteria
Honest adversarial report; no silent approval of generic drift.
