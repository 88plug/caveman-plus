<div align="center">

<img src="docs/assets/dancing-rock.svg" width="96" alt="Caveman Plus dancing-rock logo" />

# caveman-plus

Token-saving output mode for Claude Code and 30+ other AI coding agents: it makes the agent answer in compressed "caveman" prose, cutting roughly 75% of output tokens while keeping full technical accuracy.

[![plugin-validate](https://github.com/88plug/caveman-plus/actions/workflows/plugin-validate.yml/badge.svg)](https://github.com/88plug/caveman-plus/actions/workflows/plugin-validate.yml)
[![Docs](https://img.shields.io/badge/docs-online-2ea44f?style=flat)](https://88plug.github.io/caveman-plus/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue?style=flat)](LICENSE)
[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2?style=flat)](https://github.com/88plug/claude-code-plugins)

</div>

## Install

Install as a Claude Code plugin:

```bash
claude plugin marketplace add 88plug/caveman-plus
claude plugin install caveman-plus@caveman-plus
```

Or install for every supported agent with one script:

```bash
# macOS / Linux / WSL / Git Bash
curl -fsSL https://raw.githubusercontent.com/88plug/caveman-plus/main/install.sh | bash
```

```powershell
# Windows (PowerShell 5.1+)
irm https://raw.githubusercontent.com/88plug/caveman-plus/main/install.ps1 | iex
```

The script needs Node 18 or newer, takes about 30 seconds, skips agents you do not have, and is safe to re-run. Full matrix and per-agent flags are in [INSTALL.md](./INSTALL.md).

## Quickstart

After install, turn it on in any session:

- Type `/caveman` (or say "talk like caveman").
- Ask a question. The reply comes back compressed.
- Turn it off with "normal mode" or "stop caveman".

The result is visible in the first reply. A verbose answer like this:

> The reason your React component is re-rendering is likely because you're creating a new object reference on each render cycle. When you pass an inline object as a prop, React's shallow comparison sees it as a different object every time, which triggers a re-render. I'd recommend using useMemo to memoize the object.

becomes this, with the same fix:

> New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`.

Same answer, far fewer tokens.

> [!NOTE]
> caveman-plus changes output tokens only. Reasoning and thinking tokens are untouched, so the model is not made less capable. The main wins are readability, speed, and lower output cost.

## What it does

caveman-plus installs a skill that instructs the agent to drop filler, pleasantries, hedging, and articles while keeping every piece of technical substance: code blocks, function names, API names, paths, and error strings stay byte-exact. You get the same correctness in a fraction of the words.

This is the 88plug edition. It ships `full-plus` as the default intensity, an English-only mode tuned for artifact-first replies (newest ask only, one default path, smallest usable artifact, plain prose for explainers, direct root-cause-plus-fix for bugs).

It is a fork of [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman). Credit for the original caveman goes to Julius Brussee.

## Features

- Compresses every reply until you turn it off; the chosen intensity persists for the session.
- Seven intensity levels, switchable with one command.
- Slash commands for commits, PR review, session stats, and memory-file compression.
- Statusline badge in Claude Code showing lifetime tokens saved.
- Caveman subagents that keep your main context window lasting longer.
- MCP middleware that compresses tool descriptions from any MCP server.
- Works across Claude Code, Codex, Gemini, Cursor, Windsurf, Cline, Copilot, and 30+ more agents.

## Intensity levels

Switch with `/caveman <level>`. Levels stick until the session ends.

| Level | What it does |
|---|---|
| `lite` | Drop filler and hedging; keep articles and full sentences. Professional but tight. |
| `full` | Drop articles, allow fragments, use short synonyms. Classic caveman. |
| `full-plus` | English-only `full` tuned for artifact-first replies. 88plug edition default. |
| `ultra` | Abbreviate prose words, strip conjunctions, use arrows for causality, one word where one word works. Code and error strings never abbreviated. |
| `wenyan-lite` | Semi-classical Chinese register; keep grammar, drop filler. |
| `wenyan-full` | Maximum classical Chinese terseness (文言文), 80-90% character reduction. |
| `wenyan-ultra` | Extreme classical-Chinese abbreviation. Maximum compression. |

Auto-activation is built in for Claude Code, Codex, and Gemini. Cursor, Windsurf, Cline, and Copilot get always-on rule files via `--with-init`. Other agents activate per session with `/caveman`.

## Commands and skills

| Command / skill | What it does |
|---|---|
| `/caveman [level]` | Compress every reply at the chosen intensity level. |
| `/caveman-commit` | Conventional Commit messages, 50-char subject, why over what. |
| `/caveman-review` | One-line PR comments, for example `L42: bug: user null. Add guard.` |
| `/caveman-stats` | Session token usage, lifetime savings, and USD. `--share` prints a one-liner. |
| `/caveman-compress <file>` | Rewrite a memory file (e.g. `CLAUDE.md`) into caveman-speak; saves input tokens every session. Code, URLs, and paths preserved byte-exact. |
| `caveman-shrink` | MCP middleware that wraps any MCP server and compresses tool descriptions. See [npm](https://www.npmjs.com/package/caveman-shrink). |
| `cavecrew-*` | Caveman subagents (investigator, builder, reviewer) that use fewer tokens than the defaults. |

<details>
<summary>Statusline badge</summary>

In Claude Code, the statusline shows a badge like `[CAVEMAN] 12.4k` for lifetime tokens saved. It updates on each `/caveman-stats` run. Set `CAVEMAN_STATUSLINE_SAVINGS=0` to silence it.

</details>

## How it works

- Install drops a skill file into each agent.
- The skill tells the agent to drop filler, keep substance, and use fragments.
- In Claude Code, a SessionStart hook writes a small flag file so the agent talks caveman from the first message, with no need to type `/caveman`.
- The stats command reads the Claude Code session log, counts tokens saved, and writes the number to the statusline.
- The `caveman-compress` sub-skill rewrites memory files so each session starts with a smaller context, saving tokens on every session rather than one reply.

Maintainer detail (hook architecture, file ownership, CI sync) lives in [CLAUDE.md](./CLAUDE.md).

## Benchmarks

Real token counts from the Claude API, averaging about 65% output reduction across 10 prompts (range 22-87%).

| Task | Saved |
|---|---:|
| Explain React re-render bug | 87% |
| Fix auth middleware token expiry | 83% |
| Set up PostgreSQL connection pool | 84% |
| Implement React error boundary | 87% |
| Average (10 prompts) | 65% |

Raw data and reproduction script are in [`benchmarks/`](./benchmarks/). A three-arm eval harness (baseline / terse / skill) lives in [`evals/`](./evals/); caveman is compared against an explicit "Answer concisely." instruction, not the verbose default, so the delta is honest.

> [!TIP]
> `caveman-compress` cuts about 46% of input tokens from memory files on average, and that saving repeats every session. See receipts in [`benchmarks/`](./benchmarks/).

## Documentation

- [INSTALL.md](./INSTALL.md) — full install matrix, all flags, per-agent detail
- [CLAUDE.md](./CLAUDE.md) — maintainer guide (file ownership, hook architecture, CI)
- [docs/](./docs/) — extra guides, including Windows install
- [Issues](https://github.com/88plug/caveman-plus/issues) — bugs, features, questions

## Contributing

Patches are welcome. See [CONTRIBUTING.md](./CONTRIBUTING.md) for how to send one.

## License

[MIT](LICENSE). Fork of [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman); original by Julius Brussee.
