# caveman-plus

Token-saving output mode for Claude Code and 30+ other AI coding agents.
Makes the agent answer in compressed "caveman" prose — roughly **75% fewer
output tokens**, full technical accuracy kept.

[![plugin-validate](https://github.com/88plug/caveman-plus/actions/workflows/plugin-validate.yml/badge.svg)](https://github.com/88plug/caveman-plus/actions/workflows/plugin-validate.yml)
[![Docs](https://img.shields.io/badge/docs-online-2ea44f?style=flat)](https://88plug.github.io/caveman-plus/)
[![License: FSL-1.1-ALv2](https://img.shields.io/badge/license-FSL--1.1--ALv2-blue?style=flat)](https://github.com/88plug/caveman-plus/blob/main/LICENSE)
[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2?style=flat)](https://github.com/88plug/claude-code-plugins)

## Install

### Claude Code plugin (recommended)

```bash
claude plugin marketplace add 88plug/claude-code-plugins
claude plugin install caveman-plus@88plug
```

Or inside Claude Code:

```text
/plugin marketplace add 88plug/claude-code-plugins
/plugin install caveman-plus@88plug
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

The script needs Node 18 or newer. ~30 seconds. Skips agents you do not have.
Safe to re-run. Preview first with `--dry-run`:

```bash
curl -fsSL https://raw.githubusercontent.com/88plug/caveman-plus/main/install.sh | bash -s -- --dry-run
```

!!! note
    Full matrix, every flag, and per-agent detail live in
    [INSTALL.md](https://github.com/88plug/caveman-plus/blob/main/INSTALL.md).
    Windows manual fallback: [Windows install](install-windows.md).

## Multi-agent install

One installer covers Claude Code, Codex, Gemini, Cursor, Windsurf, Cline,
Copilot, opencode, OpenClaw, and 20+ more. Use the one-liner above, or target
a single agent:

| Agent | Command | Auto-activates? |
| --- | --- | :-: |
| **Claude Code** | `claude plugin marketplace add 88plug/claude-code-plugins && claude plugin install caveman-plus@88plug` | Yes |
| **Gemini CLI** | `gemini extensions install https://github.com/88plug/caveman-plus` | Yes |
| **Codex CLI** | `npx skills add 88plug/caveman-plus -a codex` | Per-session `/caveman` |
| **Cursor** | `npx skills add 88plug/caveman-plus -a cursor` | Optional `--with-init` |
| **Windsurf** | `npx skills add 88plug/caveman-plus -a windsurf` | Optional `--with-init` |
| **Cline** | `npx skills add 88plug/caveman-plus -a cline` | Optional `--with-init` |
| **opencode** | `npx -y github:88plug/caveman-plus -- --only opencode` | Yes |
| **OpenClaw** | `npx -y github:88plug/caveman-plus -- --only openclaw` | Yes |
| **Copilot** | `npx -y github:88plug/caveman-plus -- --only copilot --with-init` | Via instructions file |

Useful flags for the unified installer (`node bin/install.js` or
`npx -y github:88plug/caveman-plus -- …`):

| Flag | What |
| --- | --- |
| `--all` | Plugin + hooks + statusline + MCP shrink + per-repo rules |
| `--only <id>` | One agent (repeatable) |
| `--dry-run` | Print commands, write nothing |
| `--with-init` | Always-on rule files into the current repo |
| `--minimal` | Plugin / extension only |
| `--uninstall` | Remove hooks, plugin, extension, flag files |

List every supported id:

```bash
npx -y github:88plug/caveman-plus -- --list
```

!!! tip
    Agents without hooks (Cursor, Windsurf, Cline, Copilot) stay silent until
    you type `/caveman` or pass `--with-init` for always-on rule files.

## Quickstart

After install, in any session:

1. Type `/caveman` (or say "talk like caveman").
2. Ask a question — reply comes back compressed.
3. Turn off with "normal mode" or "stop caveman".

Verbose answer:

> The reason your React component is re-rendering is likely because you're creating a new object reference on each render cycle. When you pass an inline object as a prop, React's shallow comparison sees it as a different object every time, which triggers a re-render. I'd recommend using useMemo to memoize the object.

Same fix, caveman:

> New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`.

Same answer. Far fewer tokens.

!!! note
    caveman-plus changes **output tokens only**. Reasoning and thinking tokens
    are untouched — the model is not less capable. Wins: readability, speed,
    lower output cost.

## Modes (intensity levels)

Switch with `/caveman <level>`. Level sticks until the session ends.
Default for this edition: **`full-plus`**.

| Level | What it does |
| --- | --- |
| `lite` | Drop filler and hedging; keep articles and full sentences. Professional but tight. |
| `full` | Drop articles, allow fragments, short synonyms. Classic caveman. |
| `full-plus` | English-only `full` tuned for artifact-first replies. 88plug default. |
| `ultra` | Abbreviate prose, strip conjunctions, arrows for causality. Code/errors never abbreviated. |
| `wenyan-lite` | Semi-classical Chinese register; keep grammar, drop filler. |
| `wenyan-full` | Maximum classical Chinese terseness (文言文), ~80–90% character reduction. |
| `wenyan-ultra` | Extreme classical-Chinese abbreviation. |

Same question at each English level — "Why React component re-render?":

| Level | Sample reply |
| --- | --- |
| `lite` | Your component re-renders because you create a new object reference each render. Wrap it in `useMemo`. |
| `full` | New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`. |
| `full-plus` | New obj ref each render. `memo` alone no help. Fix: `useMemo`; if static, move obj outside component. |
| `ultra` | Inline obj prop → new ref → re-render. `useMemo`. |

`full-plus` habits: newest ask only, one default path, smallest usable
artifact, plain mechanism prose for explainers, direct root-cause-plus-fix
for bugs.

Auto-activation is built in for Claude Code, Codex, and Gemini. Cursor /
Windsurf / Cline / Copilot get always-on rules via `--with-init`. Everyone else
activates per session with `/caveman`.

## Cavecrew agents

Three caveman-style subagents. Same jobs as vanilla Explore / edit / review —
tool results injected back into main context are ~60% smaller. Main context
lasts longer across long sessions.

| Agent | Job | When to spawn |
| --- | --- | --- |
| `cavecrew-investigator` | Read-only code locator | "Where is X defined?", "what calls Y?", map a directory |
| `cavecrew-builder` | Surgical 1–2 file edit | Typo, single-function rewrite, mechanical rename; refuses 3+ files |
| `cavecrew-reviewer` | Diff / branch / file review | PR audit; one line per finding, severity-tagged, no praise |

Decision guide skill: `cavecrew` — tells the main thread *when* to delegate
instead of working inline.

### Output contracts

**Investigator** — file-path first, backticked symbols:

```text
Defs:
path/to/file.ts:42 — `authToken` — expiry check
totals: 1 def, 3 refs.
```

**Builder** — diff receipt only:

```text
src/auth.ts:18-24 — use `<=` for expiry.
verified: re-read OK.
```

**Reviewer** — findings only:

```text
src/auth.ts:42: 🔴 bug: expiry uses `<` not `<=`. Off-by-one.
totals: 1🔴 0🟡 0🔵 0❓
```

### Common chain

1. `cavecrew-investigator` → site list.
2. Main thread picks 1–2 sites → `cavecrew-builder`.
3. `cavecrew-reviewer` audits the diff.

!!! tip
    Rule of thumb: want the subagent's output in ~1/3 the tokens → cavecrew.
    Want prose / architecture commentary → vanilla Explore / Code Reviewer.

## What it does

Install drops a skill that tells the agent to drop filler, pleasantries,
hedging, and articles — while keeping every technical bit: code blocks,
function names, API names, paths, and error strings stay **byte-exact**.

This is the **88plug edition**. Default intensity is `full-plus`. Fork of
[JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman); credit to
Julius Brussee for the original.

## Features

| Feature | What it does |
| --- | --- |
| Session compression | Compresses every reply until you turn it off; intensity persists |
| Seven modes | `/caveman <level>` — lite through wenyan-ultra |
| Slash commands | Commits, PR review, session stats, memory-file compression |
| Statusline badge | Claude Code badge with lifetime tokens saved |
| Cavecrew subagents | Investigator / builder / reviewer — smaller tool results |
| MCP shrink | Middleware that compresses tool descriptions from any MCP server |
| Multi-agent | Claude Code, Codex, Gemini, Cursor, Windsurf, Cline, Copilot, 30+ more |

## Commands and skills

| Command / skill | What it does |
| --- | --- |
| `/caveman [level]` | Compress every reply at the chosen intensity |
| `/caveman-commit` | Conventional Commit messages, 50-char subject, why over what |
| `/caveman-review` | One-line PR comments, e.g. `L42: bug: user null. Add guard.` |
| `/caveman-stats` | Session tokens, lifetime savings, USD. `--share` prints a one-liner |
| `/caveman-compress <file>` | Rewrite a memory file (e.g. `CLAUDE.md`) into caveman-speak |
| `caveman-shrink` | MCP middleware for tool-description compression — [npm](https://www.npmjs.com/package/caveman-shrink) |
| `cavecrew-*` | Caveman subagents (investigator, builder, reviewer) |

<details>
<summary>Statusline badge</summary>

In Claude Code the statusline shows something like `[CAVEMAN] 12.4k` for
lifetime tokens saved. Updates on each `/caveman-stats` run. Silence with
`CAVEMAN_STATUSLINE_SAVINGS=0`.

</details>

## How it works

- Install drops a skill file into each agent.
- Skill tells the agent: drop filler, keep substance, use fragments.
- Claude Code SessionStart hook writes a flag file so the first message is
  already caveman — no need to type `/caveman`.
- `/caveman-stats` reads the Claude Code session log, counts tokens saved,
  updates the statusline.
- `caveman-compress` rewrites memory files so every future session starts
  smaller (input tokens, not just output).

Maintainer detail (hooks, file ownership, CI sync):
[CLAUDE.md](https://github.com/88plug/caveman-plus/blob/main/CLAUDE.md).

## Benchmarks

Real token counts from the Claude API. ~65% average output reduction across
10 prompts (range 22–87%).

| Task | Saved |
| --- | ---: |
| Explain React re-render bug | 87% |
| Fix auth middleware token expiry | 83% |
| Set up PostgreSQL connection pool | 84% |
| Implement React error boundary | 87% |
| Average (10 prompts) | 65% |

Raw data and reproduction script:
[`benchmarks/`](https://github.com/88plug/caveman-plus/tree/main/benchmarks).
Three-arm eval harness (baseline / terse / skill):
[`evals/`](https://github.com/88plug/caveman-plus/tree/main/evals).
Caveman is compared against an explicit "Answer concisely." instruction —
not the verbose default — so the delta is honest.

!!! tip
    `caveman-compress` cuts about **46%** of input tokens from memory files
    on average, and that saving repeats every session. Receipts in
    [`benchmarks/`](https://github.com/88plug/caveman-plus/tree/main/benchmarks).

## Documentation

- [INSTALL.md](https://github.com/88plug/caveman-plus/blob/main/INSTALL.md) — full install matrix, flags, per-agent detail
- [CLAUDE.md](https://github.com/88plug/caveman-plus/blob/main/CLAUDE.md) — maintainer guide (hooks, file ownership, CI)
- [Windows install](install-windows.md) — manual fallback when `irm | iex` fails
- [Issues](https://github.com/88plug/caveman-plus/issues) — bugs, features, questions

## Contributing

Patches welcome. See
[CONTRIBUTING.md](https://github.com/88plug/caveman-plus/blob/main/CONTRIBUTING.md).

## License

[FSL-1.1-ALv2](https://github.com/88plug/caveman-plus/blob/main/LICENSE).
Fork of [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman);
original by Julius Brussee.
