# Life OS · Haptics System

## Philosophy

Haptics are **semantic** — reinforce meaning, not noise.

## Families

| Family | Use |
|---|---|
| Contact | Initial touch on meaningful control |
| Selection | Toggle, pick, tab |
| Snap | Drag release, dial detent |
| Confirmation | Action accepted |
| Transform | State change completed |
| Warning | Reversible risk |
| Error | Failed action |
| Protection | Privacy/security action |
| Emergency | Critical alert |

## Implementation

- Prefer `HapticFeedbackType` system constants
- Custom `VibrationEffect` only with capability detection
- Graceful degradation on hardware without actuator
- Not every tap

## Pairing

| Visual | Haptic |
|---|---|
| Snap animation end | Snap |
| Confirmation flash | Confirmation |
| Error shake | Error |
| LIAH listening start | Contact (subtle) |

## Reference

Android haptics docs, SRC-001 §11
