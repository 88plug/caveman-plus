<div align="center">

<img src="docs/assets/dancing-rock.svg" width="96" alt="Caveman Plus dancing-rock logo" />

# caveman-plus

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/88plug/caveman-plus)

Token-saving output mode for Claude Code and 30+ other AI coding agents.
Makes the agent answer in compressed "caveman" prose — roughly **75% fewer
output tokens**, full technical accuracy kept.

[![plugin-validate](https://github.com/88plug/caveman-plus/actions/workflows/plugin-validate.yml/badge.svg)](https://github.com/88plug/caveman-plus/actions/workflows/plugin-validate.yml)
[![Docs](https://img.shields.io/badge/docs-online-2ea44f?style=flat)](https://88plug.github.io/caveman-plus/)
[![License: FSL-1.1-ALv2](https://img.shields.io/badge/license-FSL--1.1--ALv2-blue?style=flat)](LICENSE)
[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2?style=flat)](https://github.com/88plug/claude-code-plugins)

</div>

## Install

### Claude Code plugin (recommended)

```bash
claude plugin marketplace add 88plug/claude-code-plugins
claude plugin install caveman-plus@88plug
```

### One-liner for every agent on the machine

```bash
# macOS / Linux / WSL / Git Bash
curl -fsSL https://raw.githubusercontent.com/88plug/caveman-plus/main/install.sh | bash
```

```powershell
# Windows (PowerShell 5.1+)
irm https://raw.githubusercontent.com/88plug/caveman-plus/main/install.ps1 | iex
```

Needs Node 18+. ~30 seconds. Skips agents you do not have. Safe to re-run.
Full matrix and per-agent flags: [INSTALL.md](./INSTALL.md). Docs site:
[88plug.github.io/caveman-plus](https://88plug.github.io/caveman-plus/).

## Multi-agent install

Claude Code loads the **repo-root** plugin (`.claude-plugin/`). The `plugins/caveman/`
tree is a **Codex / multi-agent distribution mirror** (CI-synced skills) — not a second
Claude marketplace package.

| Agent | Command | Auto-activates? |
| --- | --- | :-: |
| **Claude Code** | `claude plugin marketplace add 88plug/claude-code-plugins && claude plugin install caveman-plus@88plug` | Yes |
| **Gemini CLI** | `gemini extensions install https://github.com/88plug/caveman-plus` | Yes |
| **Codex CLI** | `npx skills add 88plug/caveman-plus -a codex` | Per-session `/caveman` |
| **Cursor** | `npx skills add 88plug/caveman-plus -a cursor` | Optional `--with-init` |
| **Windsurf / Cline** | `npx skills add 88plug/caveman-plus -a windsurf` / `-a cline` | Optional `--with-init` |
| **opencode / OpenClaw** | `npx -y github:88plug/caveman-plus -- --only opencode` / `--only openclaw` | Yes |

```bash
# Preview / list / one agent
npx -y github:88plug/caveman-plus -- --dry-run
npx -y github:88plug/caveman-plus -- --list
npx -y github:88plug/caveman-plus -- --only cursor --with-init
```

## Quickstart

1. Type `/caveman` (or say "talk like caveman").
2. Ask a question — reply comes back compressed.
3. Turn off with "normal mode" or "stop caveman".

Verbose:

> The reason your React component is re-rendering is likely because you're creating a new object reference on each render cycle. When you pass an inline object as a prop, React's shallow comparison sees it as a different object every time, which triggers a re-render. I'd recommend using useMemo to memoize the object.

Caveman (same fix):

> New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`.

> [!NOTE]
> caveman-plus changes **output tokens only**. Reasoning and thinking tokens
> are untouched. Wins: readability, speed, lower output cost.

## Modes (intensity levels)

Switch with `/caveman <level>`. Default: **`full-plus`**.

| Level | What it does |
| --- | --- |
| `lite` | Drop filler and hedging; keep articles and full sentences. |
| `full` | Drop articles, fragments OK, short synonyms. Classic caveman. |
| `full-plus` | English-only `full` tuned for artifact-first replies. 88plug default. |
| `ultra` | Abbreviate prose, arrows for causality. Code/errors never abbreviated. |
| `wenyan-lite` / `wenyan-full` / `wenyan-ultra` | Classical Chinese registers, increasing compression. |

## Cavecrew agents

Three caveman subagents — tool results ~60% smaller than vanilla Explore/edit/review:

| Agent | Job |
| --- | --- |
| `cavecrew-investigator` | Read-only code locator (`path:line` table) |
| `cavecrew-builder` | Surgical 1–2 file edit; refuses 3+ files |
| `cavecrew-reviewer` | Diff review; one line per finding, severity-tagged |

Decision guide skill: `cavecrew`. Chain: investigator → builder → reviewer.

## What it does

Drops a skill that strips filler, pleasantries, hedging, and articles while
keeping technical substance byte-exact (code, APIs, paths, errors).

88plug edition ships `full-plus` as the default intensity. Fork of
[JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman). Credit:
Julius Brussee.

## Features

| Feature | What it does |
| --- | --- |
| Session compression | Every reply compressed until you turn it off |
| Seven modes | `/caveman <level>` — lite through wenyan-ultra |
| Slash commands | Commits, PR review, stats, memory-file compression |
| Statusline badge | Claude Code lifetime tokens-saved counter |
| Cavecrew subagents | Investigator / builder / reviewer |
| MCP shrink | Compresses tool descriptions from any MCP server |
| Multi-agent | Claude Code, Codex, Gemini, Cursor, Windsurf, Cline, Copilot, 30+ |

## Commands and skills

| Command / skill | What it does |
| --- | --- |
| `/caveman [level]` | Compress every reply at the chosen intensity |
| `/caveman-commit` | Conventional Commit messages, 50-char subject |
| `/caveman-review` | One-line PR comments, e.g. `L42: bug: user null. Add guard.` |
| `/caveman-stats` | Session tokens, lifetime savings, USD |
| `/caveman-compress <file>` | Rewrite a memory file into caveman-speak |
| `caveman-shrink` | MCP middleware — [npm](https://www.npmjs.com/package/caveman-shrink) |
| `cavecrew-*` | Caveman subagents (investigator, builder, reviewer) |

<details>
<summary>Statusline badge</summary>

Claude Code statusline: `[CAVEMAN] 12.4k` for lifetime tokens saved. Updates
on each `/caveman-stats` run. Silence with `CAVEMAN_STATUSLINE_SAVINGS=0`.

</details>

## How it works

- Install drops a skill file into each agent.
- Skill: drop filler, keep substance, use fragments.
- Claude Code SessionStart hook writes a flag so the first message is already caveman.
- `/caveman-stats` reads the session log and updates the statusline.
- `caveman-compress` rewrites memory files so every future session starts smaller.

Maintainer detail: [CLAUDE.md](./CLAUDE.md).

## Benchmarks

Real Claude API token counts. ~65% average output reduction across 10 prompts
(range 22–87%).

| Task | Saved |
| --- | ---: |
| Explain React re-render bug | 87% |
| Fix auth middleware token expiry | 83% |
| Set up PostgreSQL connection pool | 84% |
| Implement React error boundary | 87% |
| Average (10 prompts) | 65% |

Raw data: [`benchmarks/`](./benchmarks/). Eval harness: [`evals/`](./evals/).

> [!TIP]
> `caveman-compress` cuts about **46%** of input tokens from memory files on
> average, and that saving repeats every session. Receipts in
> [`benchmarks/`](./benchmarks/).

## Documentation

- [Docs site](https://88plug.github.io/caveman-plus/) — install, modes, cavecrew, quickstart
- [INSTALL.md](./INSTALL.md) — full install matrix, all flags, per-agent detail
- [CLAUDE.md](./CLAUDE.md) — maintainer guide (hooks, file ownership, CI)
- [docs/](./docs/) — Windows install and more
- [Issues](https://github.com/88plug/caveman-plus/issues)

## Contributing

Patches welcome. See [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

[FSL-1.1-ALv2](LICENSE). Fork of
[JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman); original by
Julius Brussee.
