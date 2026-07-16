#!/usr/bin/env bash
# post-compaction-recovery: print recovery protocol
set -euo pipefail
cat <<'EOF' >&2
[lifeos:post-compaction-recovery] Read AGENTS.md → checkpoint → CURRENT_BUILD.md → DECISIONS.md → CONTRADICTIONS.md
EOF
exit 0
