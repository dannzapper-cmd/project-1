# Life OS Hooks Status

**Updated:** 2026-07-16

## Active (command hooks in `.cursor/hooks.json`)

| Hook | Script | Cloud support |
|---|---|---|
| license-check | `license-check.sh` | ✅ beforeShellExecution |
| post-token-change | `post-token-change.sh` | ✅ afterFileEdit |
| post-component-change | `post-component-change.sh` | ✅ afterFileEdit |
| visual-evidence-gate | `visual-evidence-gate.sh` | ✅ preToolUse |
| pre-session-end | `pre-session-end.sh` | ✅ stop |
| post-compaction-recovery | `post-compaction-recovery.sh` | ✅ preCompact |

## PREPARED_NOT_ACTIVE

| Hook | Reason |
|---|---|
| pre-design-block | No dedicated hook event; use `/lifeos-prepare-brief` command |
| pre-implementation | Use command + checkpoint protocol |
| pre-commit | Requires git hook or `beforeShellExecution` on `git commit` — add locally |
| post-test | Run via CI; no cloud Tab hook |
| beforeMCPExecution | Not supported in Cloud Agents |
| sessionStart / sessionEnd | Not supported in Cloud Agents |

## Requirements

- Scripts must be executable: `chmod +x .cursor/hooks/*.sh`
- Fast (<15s), deterministic, non-destructive
- Exit 0 = allow; exit 2 = block (where supported)
