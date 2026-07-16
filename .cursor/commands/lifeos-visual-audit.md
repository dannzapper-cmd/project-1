---
name: lifeos-visual-audit
description: Run visual audit using red-team and accessibility subagents
---

# Visual Audit

1. Launch `visual-red-team` and `accessibility-auditor` subagents
2. Compare against approved design/brief
3. Check all main states (loading, empty, error, disabled)
4. Document findings in `docs/design/evidence/audit_<surface>.md`
5. Severity: P0/P1/P2

Do not silently fix blockers — report first.
