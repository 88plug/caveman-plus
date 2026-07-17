# Full-Plus Final Benchmark Summary

Date: `2026-04-20`

This branch captures the final benchmark pass for the current `full-plus` tuning, plus Claude Code standalone parity changes so standalone hooks read the same source-of-truth `SKILL.md` as the plugin path.

## Commands Run

```bash
python3 tests/verify_repo.py
python3 benchmarks/mode_matrix.py --family general
timeout 2400s python3 benchmarks/mode_matrix.py --family dialogue
python3 benchmarks/mode_matrix.py --family commit
python3 benchmarks/mode_matrix.py --family review
python3 benchmarks/mode_matrix.py --family compress
```

## Proof Files

- `benchmarks/results/mode_matrix_20260420_074817.json`
- `benchmarks/results/mode_matrix_20260420_083035.json`
- `benchmarks/results/mode_matrix_20260420_081134.json`
- `benchmarks/results/mode_matrix_20260420_081553.json`
- `benchmarks/results/mode_matrix_20260420_081737.json`

## Fresh Results

### General

Source: `mode_matrix_20260420_074817.json`

- `off`: `0.0%` total savings, `quality loss 0.00`
- `lite`: `+5.3%`, `0.00`
- `full`: `+25.1%`, `0.00`
- `full-plus`: `+44.1%`, `-0.20`
- `ultra`: `+31.0%`, `-0.20`
- `wenyan-lite`: `+11.0%`, `-0.20`
- `wenyan`: `+32.0%`, `-0.20`
- `wenyan-ultra`: `+12.7%`, `0.20`

Winner: `full-plus`

### Dialogue

Source: `mode_matrix_20260420_083035.json`

- `off`: `0.0%` total savings, `quality loss 0.00`
- `full`: `+30.2%`, `-0.20`
- `full-plus`: `+45.5%`, `0.00`

Winner for efficiency: `full-plus`

### Commit

Source: `mode_matrix_20260420_081134.json`

- `off`: `0.0%` total savings, `quality loss 0.00`
- `commit`: `+24.9%`, `-0.20`

Winner: `commit`

### Review

Source: `mode_matrix_20260420_081553.json`

- `off`: `0.0%` total savings, `quality loss 0.00`
- `review`: `+13.7%`, `0.40`

Recommendation: keep review effectively off.

### Compress

Source: `mode_matrix_20260420_081737.json`

- `off`: `0.0%` stored-text savings, `quality loss 0.00`
- `compress`: `+49.1%`, `2.60`

Recommendation: keep compress explicit-only.

## Before / After

Before: `full` was the safe default because earlier `full-plus` variants were unstable and sometimes lost on total tokens in multi-turn threads.

After: current `full-plus` wins the fresh final suite on the two important general-purpose families:

- `general`: `+44.1%` total savings with better-than-`off` judged quality
- `dialogue`: `+45.5%` total savings with neutral judged quality vs `off`

Why this is better: `full-plus` now gives the largest consistent token savings while avoiding the quality regressions that made earlier variants unusable as a default.

## Recommended Routing

- Normal prompts: `full-plus`
- Commit-message tasks: `commit`
- Review tasks: off
- Compress: manual only

## Claude Code Parity

- Verified against Anthropic Claude Code hooks docs: `SessionStart` and `UserPromptSubmit` stdout are injected as hidden context, which is the mechanism caveman relies on.
- Standalone `hooks/install.sh` / `hooks/install.ps1` now copy `skills/caveman/SKILL.md` into `~/.claude/skills/caveman/SKILL.md`.
- `hooks/caveman-activate.js` now reads that standalone skill copy when running outside the plugin bundle.
- `hooks/caveman-mode-tracker.js` now emits `full-plus`-specific per-turn reinforcement aligned with the Codex tuning.
- `tests/verify_repo.py` covers install, activation, `full-plus` tracking, statusline, and uninstall for the standalone Claude path.

## Contribution Note

Per `CONTRIBUTING.md`, source of truth for prompt changes remains `skills/caveman/SKILL.md`. This branch also includes synced mirror copies and `caveman.skill` so the verification snapshot is self-consistent.
