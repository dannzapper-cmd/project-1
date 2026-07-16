---
name: lifeos-haptics-semantics
description: Map interaction events to semantic haptic feedback on Android. Use for haptics, tactile feedback, vibration patterns.
---

# Haptics Semantics

## Trigger
Haptic feedback, tactile response, vibration on interaction.

## Documents to read
- `docs/design/HAPTICS_SYSTEM.md`
- `.cursor/rules/30-motion-haptics.mdc`

## Procedure
1. Map interaction → Haptic family (Contact, Selection, Snap, etc.)
2. Prefer `HapticFeedbackType` system constants
3. Custom effects only with hardware capability check + fallback
4. Never haptic on every scroll item

## Outputs
- Haptic contract per component
- Implementation with graceful degradation

## Success criteria
Haptics reinforce meaning; disabled inappropriately on low-end or user settings.
