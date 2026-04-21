# Mode Matrix Benchmark

This harness compares **Codex token use** against **quality loss** for Caveman modes.

Families:
- `general`: `off`, `lite`, `full`, `full-plus`, `ultra`, `mello-lite`, `mello`, `mello-ultra`
- `dialogue`: `off`, `full`, `full-plus`
- `commit`: `off`, `commit`
- `review`: `off`, `review`
- `compress`: `off`, `compress`

Coverage:
- At least 5 experiments in every family
- `general` covers 5 normal engineering prompts per mode
- `dialogue` covers 5 three-turn follow-up threads per mode
- `commit` covers 5 commit-writing prompts
- `review` covers 5 code-review prompts
- `compress` covers 5 real markdown fixtures

Metrics:
- `general`, `commit`, `review`
  - `output saved vs off`: assistant output-token reduction from Codex `turn.completed.usage`
  - `total saved vs off`: `(input + output)` token reduction from the same Codex usage event
  - `quality loss vs off`: judge score delta relative to `off`
- `dialogue`
  - same metrics, but accumulated across all turns in a thread
  - captures future-turn context carryover from earlier assistant outputs
- `compress`
  - `stored-text saved vs off`: Codex input-token reduction for the original vs compressed fixture text, after subtracting fixed prompt overhead
  - `quality loss vs off`: judge score plus validator penalties
  - Uses existing fixture pairs in `tests/caveman-compress/`, not a live compression run

Run plan only:

```bash
uv run python benchmarks/mode_matrix.py --dry-run
```

Validate config only:

```bash
uv run python benchmarks/mode_matrix.py --validate-only
```

Run full benchmark:

```bash
uv run python benchmarks/mode_matrix.py
```

Run one family:

```bash
uv run python benchmarks/mode_matrix.py --family general
```

Run only selected modes:

```bash
uv run python benchmarks/mode_matrix.py --family general --modes off,mello-lite,mello,mello-ultra
```

Try the experimental `full-plus` compare:

```bash
uv run python benchmarks/mode_matrix.py --family general --modes off,full,full-plus
```

Run the multi-turn carryover benchmark:

```bash
uv run python benchmarks/mode_matrix.py --family dialogue --modes off,full,full-plus
```

Skip judge if you only want token numbers:

```bash
uv run python benchmarks/mode_matrix.py --skip-judge
```

Notes:
- Requires `codex` CLI and an existing login (`~/.codex/auth.json` by default)
- Requires `node` because general-mode prompts are built from real Codex hook output
- `mello` is the canonical runtime label for `mello-full`
- Old `wenyan-*` names remain accepted as backward-compatible aliases
- The harness creates isolated temp `HOME` and `CODEX_HOME` directories so `off` does not accidentally inherit global Caveman skills.
- Temp benchmark roots default to your system temp dir, not the repo. Override with `CAVEMAN_BENCH_TEMP_ROOT=/abs/path/outside/repo`.
- `commit` and `review` mode runs install only the skill under test into the temp home, then invoke it with `/caveman-commit` or `/caveman-review`.
