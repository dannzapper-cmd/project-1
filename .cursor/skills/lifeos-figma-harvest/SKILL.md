---
name: lifeos-figma-harvest
description: Prepare and execute Figma MCP harvest calls for Life OS. Use when planning Figma extraction, MCP calls, or design context import.
disable-model-invocation: true
---

# Life OS Figma Harvest

## Trigger
Figma MCP, harvest, design extraction, six-call sprint.

## Objective
Extract maximum value per Figma MCP call; persist raw + normalized context.

## Inputs
- Call number (1–6)
- Figma file URL and frame selection
- `docs/design/figma-harvest/FIGMA_PROMPT_TEMPLATE.md`

## Documents to read
- `docs/design/figma-harvest/FIGMA_SIX_CALL_PLAN.md`
- `docs/design/figma-harvest/FIGMA_SELECTION_CHECKLIST.md`
- `.cursor/rules/60-figma-mcp.mdc`

## Procedure
1. Verify selection checklist complete
2. Confirm call budget (log remaining calls)
3. Run prompt prohibiting web stack output
4. Save to `docs/design/figma-harvest/raw/SPRINT_FIGMA_001/call_NN_*`
5. Normalize to `docs/design/figma-harvest/normalized/`
6. Propose token mappings in `design-system/tokens/`

## Outputs
- Raw response archive
- Normalized markdown contracts
- Metadata with timestamp and selection scope

## Limits
- **BLOCK_ART_000:** 0 calls allowed
- Max 6 calls/month on Starter View/Collab seat
- No exploratory calls without prepared selection

## Checklist
- [ ] Selection scored ≥75/100
- [ ] Frames consolidated in one page
- [ ] Prompt requires Kotlin/Compose
- [ ] Raw + normalized saved
- [ ] License noted for Community files

## Common errors
- Burning calls on unstructured exploration
- Accepting React/Tailwind output verbatim
- Skipping raw archive

## Success criteria
Normalized doc enables Compose implementation without re-calling Figma.
