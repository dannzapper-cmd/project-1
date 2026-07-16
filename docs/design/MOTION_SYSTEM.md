# Life OS · Motion System

## Implementation order

1. Static aesthetics
2. Visual states
3. Interaction/gestures
4. Motion
5. Haptics
6. Sound (deferred)

## Families

press/release · selection · navigation · expansion · transform · drag/snap · loading · confirmation · error · protection · LIAH presence · voice visualization · screen continuity

## Tools

| Use case | Tool |
|---|---|
| Structural UI motion | Compose Animation, Transition, AnimatedContent |
| Shared elements | Shared transition APIs |
| Reactive light | graphicsLayer, Brush, Canvas, selective AGSL |
| Closed vector loops | Lottie Android |
| Complex interactive | Rive (EVALUATE) |

## Rules

- Interruptible and causal
- Reduce Motion respected
- Pause off-screen
- No decorative mass infinite loops
- Measure jank

## Infinite animations allowed when

Listening · processing · real progress · active state · minimal LIAH breathing

## Reference

SRC-001 §10, Android Compose animation docs
