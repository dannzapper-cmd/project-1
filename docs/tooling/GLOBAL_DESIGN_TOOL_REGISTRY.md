# Global Design Tool Registry

**Verified:** 2026-07-16

| Tool | Publisher | Official source | Function | Maintenance | License | Cost/limits | Cursor Web | Android/Compose | Decision | Verified |
|---|---|---|---|---|---|---|---|---|---|---|
| Figma MCP | Figma | developers.figma.com/docs/figma-mcp-server | Design context harvest | Active | Proprietary service | Starter View/Collab: 6 calls/mo | PREPARE (OAuth) | Indirect (spec→Compose) | PREPARE | 2026-07-16 |
| GitHub MCP | GitHub | github.com/github/github-mcp-server | Repo, issues, PRs | Active | MIT | Free tier limits | Available (env) | N/A | ADOPT_NOW | 2026-07-16 |
| Context7 | Upstash | context7.com | Live library docs | Active | Service | Free tier TBD | PREPARE | Yes (Compose docs) | PREPARE | 2026-07-16 |
| MarkItDown | Microsoft | github.com/microsoft/markitdown | Doc conversion | Active | MIT | Open | PREPARE | N/A | PREPARE | 2026-07-16 |
| MCP Inspector | Anthropic/MCP | github.com/modelcontextprotocol/inspector | MCP debug | Active | MIT | Open | PREPARE | N/A | PREPARE | 2026-07-16 |
| Penpot MCP | Penpot | penpot.app | Open design | Active | MPL-2.0 | Free/OSS | EVALUATE | Indirect | EVALUATE | 2026-07-16 |
| Cursor Rules | Cursor | cursor.com/docs/rules | Agent context | Active | Product | Included | ADOPT_NOW | Yes | ADOPT_NOW | 2026-07-16 |
| Cursor Skills | Cursor | cursor.com/docs/skills | Agent procedures | Active | Product | Included | ADOPT_NOW | Yes | ADOPT_NOW | 2026-07-16 |
| Cursor Subagents | Cursor | cursor.com/docs/subagents | Specialized agents | Active | Product | Included | ADOPT_NOW | Yes | ADOPT_NOW | 2026-07-16 |
| Cursor Hooks | Cursor | cursor.com/docs/hooks | Automation gates | Active | Product | Included | Partial (command only) | Yes | ADOPT_NOW | 2026-07-16 |
| Cursor Plugins | Cursor | cursor.com/docs/reference/plugins | Bundle config | Active | Product | Included | EVALUATE | Yes | EVALUATE | 2026-07-16 |
| Jetpack Compose | Google | developer.android.com/jetpack/compose | UI toolkit | Active | Apache-2.0 | Free | N/A (code) | Yes | ADOPT_NOW | 2026-07-16 |
| Lottie Android | Airbnb | lottie.github.io | Vector animation | Active | Apache-2.0 | Free | N/A | Yes | PREPARE | 2026-07-16 |
| Rive Android | Rive | rive.app/docs/runtimes/android | State machine graphics | Active | Proprietary | Free tier limits | N/A | Yes | EVALUATE | 2026-07-16 |
| Paparazzi | Cash App | github.com/cashapp/paparazzi | Screenshot test | Active | Apache-2.0 | Free | N/A | Yes | EVALUATE | 2026-07-16 |
| Roborazzi | Takahirom | github.com/takahirom/roborazzi | Screenshot test | Active | Apache-2.0 | Free | N/A | Yes | EVALUATE | 2026-07-16 |
| Macrobenchmark | Google | developer.android.com/topic/performance/benchmarking | Perf test | Active | Apache-2.0 | Free | N/A | Yes | PREPARE | 2026-07-16 |
| skill-creator (Anthropic) | Anthropic | github.com/anthropics/skills | Skill authoring ref | Active | Apache-2.0 | Free | REFERENCE_ONLY | N/A | REFERENCE_ONLY | 2026-07-16 |
| compose-skill (aldefy) | Community | github.com/aldefy/compose-skill | Compose patterns | Community | Check repo | Free | REFERENCE_ONLY | Yes | REFERENCE_ONLY | 2026-07-16 |
| Framer Motion | Framer | framer.com/motion | Web animation | Active | MIT | Free | N/A | **No** | REJECT (Android) | 2026-07-16 |
| Tailwind CSS | Tailwind Labs | tailwindcss.com | Web styling | Active | MIT | Free | N/A | **No** | REJECT (Android) | 2026-07-16 |
| Playwright MCP | Microsoft | github.com/microsoft/playwright-mcp | Web QA | Active | Apache-2.0 | Free | EVALUATE | Web only | REFERENCE_ONLY | 2026-07-16 |

## ADOPT_NOW (active minimum)

- GitHub MCP (environment)
- Cursor Rules, Skills, Subagents, Hooks (internal Life OS)
- Jetpack Compose (production code, when repo connected)

## PREPARE (next authorization)

- Figma MCP, Context7, MarkItDown, MCP Inspector, Lottie

## EVALUATE

- Penpot, Rive, Paparazzi, Roborazzi, Cursor plugin packaging

## REJECT (for Life OS Android)

- Framer Motion, Tailwind, React-native-web tooling as app base
