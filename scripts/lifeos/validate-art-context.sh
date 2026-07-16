#!/usr/bin/env bash
# validate-art-context.sh — BLOCK_ART_000 validation gates
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'
FAIL=0

ok() { echo -e "${GREEN}OK${NC} $1"; }
fail() { echo -e "${RED}FAIL${NC} $1"; FAIL=1; }

echo "=== Life OS Art Context Validation ==="

# Required files
for f in \
  AGENTS.md \
  CURRENT_BUILD.md \
  DECISIONS.md \
  CONTRADICTIONS.md \
  docs/execution/BLOCK_ART_000_CONTEXT_TOOLING_WORKING_CHECKPOINT.md \
  docs/source/SOURCE_INDEX.md \
  docs/source/SOURCE_PRECEDENCE.md \
  docs/source/SOURCE_IMPORT_MANIFEST.md \
  docs/audits/ART_CONTEXT_REPOSITORY_BASELINE.md \
  docs/design/LIFEOS_ART_CONTEXT_MANIFEST.md \
  docs/tooling/GLOBAL_DESIGN_TOOL_REGISTRY.md
do
  [[ -f "$f" ]] && ok "exists: $f" || fail "missing: $f"
done

# Rules count
RULE_COUNT=$(find .cursor/rules -name '*.mdc' 2>/dev/null | wc -l)
[[ "$RULE_COUNT" -ge 9 ]] && ok "rules: $RULE_COUNT .mdc files" || fail "rules: expected >=9, got $RULE_COUNT"

# Skills count
SKILL_COUNT=$(find .cursor/skills -name 'SKILL.md' 2>/dev/null | wc -l)
[[ "$SKILL_COUNT" -ge 10 ]] && ok "skills: $SKILL_COUNT" || fail "skills: expected >=10, got $SKILL_COUNT"

# Agents count
AGENT_COUNT=$(find .cursor/agents -name '*.md' 2>/dev/null | wc -l)
[[ "$AGENT_COUNT" -ge 6 ]] && ok "agents: $AGENT_COUNT" || fail "agents: expected >=6, got $AGENT_COUNT"

# Hooks executable
for h in .cursor/hooks/*.sh; do
  [[ -x "$h" ]] && ok "executable: $h" || fail "not executable: $h"
done

# JSON validate hooks.json
python3 -c "import json; json.load(open('.cursor/hooks.json'))" 2>/dev/null && ok "hooks.json valid JSON" || fail "hooks.json invalid"

# Plugin manifest
python3 -c "import json; json.load(open('.cursor/plugins/lifeos-art-studio/.cursor-plugin/plugin.json'))" 2>/dev/null && ok "plugin.json valid" || fail "plugin.json invalid"

# Secret patterns (basic)
if grep -rE '(api[_-]?key|secret|password|token)\s*=\s*["\x27][^"\x27]{8,}' --include='*.md' --include='*.json' --include='*.sh' .cursor docs AGENTS.md 2>/dev/null | grep -v REDACTED | grep -v 'pending@' | head -1; then
  fail "possible secret in versioned files"
else
  ok "no obvious secrets in checked paths"
fi

# Relative link check (markdown files in docs/source and docs/design)
BROKEN=0
while IFS= read -r -d '' file; do
  while IFS= read -r link; do
    target=$(echo "$link" | sed 's/#.*//')
    [[ -z "$target" || "$target" =~ ^https?:// ]] && continue
    dir=$(dirname "$file")
    if [[ ! -f "$dir/$target" && ! -f "$ROOT/$target" ]]; then
      # allow intentional refs to not-yet-created Life OS paths
      if [[ ! "$target" =~ design-system/ ]]; then
        echo "  broken link in $file -> $target"
        BROKEN=1
      fi
    fi
  done < <(grep -oE '\[[^]]+\]\([^)]+\)' "$file" 2>/dev/null | sed -n 's/.*(\([^)]*\)).*/\1/p')
done < <(find docs/source docs/design -name '*.md' -print0 2>/dev/null)

[[ $BROKEN -eq 0 ]] && ok "relative links check passed" || fail "broken relative links found"

# Source checksums
[[ -f docs/source/raw/CHECKSUMS.sha256 ]] && ok "checksums present" || fail "checksums missing"

echo "=== Result: $([[ $FAIL -eq 0 ]] && echo PASS || echo FAIL) ==="
exit $FAIL
