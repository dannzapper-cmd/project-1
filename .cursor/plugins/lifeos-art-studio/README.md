# Life OS Art Studio Plugin

**Status:** Scaffold — references root `.cursor/` to avoid duplicate sources of truth (DEC-005).

## Decision

Plugin manifest points to parent directories (`../../rules`, etc.) rather than copying configuration. Active truth remains:

- `.cursor/rules/`
- `.cursor/skills/`
- `.cursor/agents/`
- `.cursor/commands/`
- `.cursor/hooks.json`

## When to fully package

When Life OS repo is stable and Danny approves distribution as installable plugin — copy pinned versions into plugin subfolders.

## Install test

Local path: `~/.cursor/plugins/local/lifeos-art-studio/` (desktop only)
