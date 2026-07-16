# Figma MCP Prompt Template

Copy and fill per call. **Do not execute in BLOCK_ART_000.**

---

## Metadata

- **Sprint:** SPRINT_FIGMA_001
- **Call:** NN / 6
- **Date:** YYYY-MM-DD
- **Figma URL:** 
- **Selection score:** /100
- **Approved by:** Danny

## Scope

List exact frames/components to extract:

1. 
2. 

## Prompt (send to Figma MCP)

```text
You are extracting design context for Life OS, an Android native app built with Kotlin and Jetpack Compose.

STRICT PROHIBITIONS:
- Do NOT output React, JSX, HTML, Tailwind CSS, CSS modules, or Framer Motion code.
- Do NOT assume web viewport or browser APIs.
- Do NOT copy proprietary community designs literally — extract principles and measurements.

REQUIRED OUTPUT FORMAT:
1. Design tokens (color, type, spacing, shape, elevation) as Compose-oriented values
2. Component anatomy with states (default, pressed, focused, disabled, error)
3. Motion intent described in Compose Animation terms (duration, easing, interruptibility)
4. Material notes (glass/neumo/clay) with accessibility contrast warnings
5. Iconography specs (stroke, grid, optical size)

TARGET FRAME SELECTION:
[PASTE FRAME NAMES/IDS]

LIFE OS ART DIRECTION:
- White predominant architecture
- Black for text/precision
- Rainbow semantic color only — not decorative gradients
- Cognitive Glass: selective, not universal transparency
- Reactive light on interaction where appropriate

Save measurements in dp/sp where possible.
```

## Expected artifacts

- [ ] `call_0N_raw_response.md`
- [ ] `call_0N_metadata.md`
- [ ] Normalized doc updated
