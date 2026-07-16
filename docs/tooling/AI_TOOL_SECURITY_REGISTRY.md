# AI Tool Security Registry

**Updated:** 2026-07-16

## Threat model

- Prompt injection via Skills/MCPs
- Malicious or abandoned community Skills
- Over-privileged MCP scopes
- Secret exfiltration via hooks/scripts
- Supply-chain in dependencies
- License-incompatible assets

## Protocol (mandatory before adopt)

1. Verify publisher and official repository
2. Read LICENSE and SECURITY policy
3. Pin version/commit
4. Review permissions and data egress
5. Static review of install scripts
6. Test in isolated branch
7. Allowlist paths for filesystem MCPs
8. No secrets in repo — use Cursor dashboard secrets
9. Register decision in this file
10. Periodic re-review

## Registered tools

| Tool | Publisher verified | Repo | License OK | Permissions | Telemetry | Scripts reviewed | Decision |
|---|---|---|---|---|---|---|---|
| GitHub MCP | ✅ GitHub | github/github-mcp-server | ✅ MIT | Repo scope | Policy reviewed | N/A | ADOPT_NOW |
| Figma MCP | ✅ Figma | Official docs | ✅ ToS | OAuth file access | Figma policy | N/A | PREPARE |
| Context7 | ✅ Upstash | Official | TBD | API key | TBD | N/A | PREPARE |
| MarkItDown | ✅ Microsoft | microsoft/markitdown | ✅ MIT | Local files | None expected | PREPARE | PREPARE |
| Internal Skills | ✅ Life OS | This repo | N/A | Read/write repo | None | ✅ | ADOPT_NOW |
| compose-skill external | ⚠️ Community | aldefy/compose-skill | Check | N/A | N/A | Not installed | REFERENCE_ONLY |
| awesome-android-agent-skills | ⚠️ Community | Various | Various | N/A | N/A | Not installed | REFERENCE_ONLY |

## Rejected patterns

- Auto-install from awesome lists without review
- Community Figma files without license check
- MCPs without identifiable publisher
- Remote code execution without inspection

## Incident response

1. Disable tool in Cursor settings
2. Document in this registry
3. Rotate any exposed secrets
4. Update DECISIONS.md
