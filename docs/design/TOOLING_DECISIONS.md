# Life OS · Tooling Decisions

**Date:** 2026-07-16

## Summary

| Decision | Choice |
|---|---|
| Active MCPs (this block) | GitHub only (environment) |
| Figma MCP | PREPARE — 0 calls consumed |
| Context7 | PREPARE — auth TBD |
| MarkItDown | PREPARE |
| Penpot | EVALUATE — plan B |
| Screenshot framework | EVALUATE Paparazzi vs Roborazzi |
| Compose skill external | REFERENCE_ONLY — prefer internal skills |
| Plugin packaging | Scaffold only — no duplicate truth |

## Rationale

Minimal active footprint; maximal documented research. Internal skills > external generic skills (SRC-002 §5).

## Registries

- `docs/tooling/GLOBAL_DESIGN_TOOL_REGISTRY.md`
- `docs/tooling/AI_TOOL_SECURITY_REGISTRY.md`
- `docs/tooling/FREE_TIER_AND_LICENSE_REGISTRY.md`

## Danny authorization queue

1. Connect Life OS Android repository
2. Figma MCP OAuth in Cursor
3. Provide missing master documents (8 files)
4. Approve first Figma call selection
