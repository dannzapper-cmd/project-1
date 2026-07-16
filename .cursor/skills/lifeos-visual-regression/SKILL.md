---
name: lifeos-visual-regression
description: Set up and run visual regression tests for Compose UI. Use for screenshot tests, Paparazzi, Roborazzi, visual diff.
---

# Visual Regression

## Trigger
Screenshot test, visual regression, Paparazzi, Roborazzi, before/after evidence.

## Documents to read
- `docs/design/DESIGN_AUDIT_PROTOCOL.md`
- `docs/tooling/GLOBAL_DESIGN_TOOL_REGISTRY.md` (Paparazzi/Roborazzi)

## Procedure
1. Confirm framework decision (Paparazzi vs Roborazzi — EVALUATE)
2. Capture baseline for approved states
3. Run on CI or local; store in `docs/design/evidence/`
4. Review diffs; Danny approves intentional changes

## Outputs
- Screenshot baselines
- Diff report

## Limits
- No sensitive user data in captures
- Evidence at gates only

## Success criteria
Regressions caught before merge; intentional diffs documented.
