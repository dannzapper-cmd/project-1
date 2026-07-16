---
name: lifeos-motion-choreography
description: Design and implement motion for Life OS surfaces using Compose Animation. Use for animations, transitions, reactive light.
---

# Motion Choreography

## Trigger
Motion, animation, transitions, reactive light, shared element transitions.

## Objective
Causal, interruptible motion within performance budgets.

## Documents to read
- `docs/design/MOTION_SYSTEM.md`
- `docs/design/PERFORMANCE_VISUAL_BUDGETS.md`
- `.cursor/rules/30-motion-haptics.mdc`

## Procedure
1. Classify motion family (press, nav, expand, LIAH, etc.)
2. Define duration/easing tokens
3. Implement with Compose; fallback for Reduce Motion
4. Pause off-screen; measure jank
5. Document motion role on component

## Outputs
- Motion specs + implementation
- Reduce Motion static equivalents

## Limits
- No infinite decorative loops
- No Lottie for navigation/layout
- Sound comes after motion+haptics

## Success criteria
Motion interruptible; Reduce Motion respected; no jank regression on mid device.
