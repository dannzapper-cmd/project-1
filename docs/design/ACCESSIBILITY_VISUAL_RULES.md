# Life OS · Accessibility Visual Rules

## Contrast

- Normal text: ≥4.5:1; large text: ≥3:1
- Glass/blur backgrounds: verify worst-case content behind
- Emergency: maximum contrast, no transparency on critical text

## Touch

- Minimum 48×48dp touch targets
- One-handed reachable zones for primary actions

## Motion

- Reduce Motion → static equivalent for all non-essential animation
- No motion-only state communication

## TalkBack

- `contentDescription` on icon-only controls
- Custom semantics for composite widgets (LifeWidget, QuickDial)
- Logical focus order

## Font scale

- Layouts survive 200% without clipping critical actions
- Tabular figures for financial data

## Color

- Never color-alone for status — pair with icon/text/haptic

## Reference

Android a11y docs, SRC-001, WCAG 2.1 AA target
