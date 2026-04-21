#!/usr/bin/env python3
"""Compare Caveman mode Codex token use against quality loss."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_VERSION = "2.0.0"
SCRIPT_DIR = Path(__file__).parent
REPO_DIR = SCRIPT_DIR.parent
RESULTS_DIR = SCRIPT_DIR / "results"
EXPERIMENTS_PATH = SCRIPT_DIR / "mode_matrix_experiments.json"
SOURCE_CODEX_HOME = Path(
    os.environ.get("CAVEMAN_BENCH_SOURCE_CODEX_HOME", str(Path.home() / ".codex"))
)
SOURCE_AUTH_PATH = SOURCE_CODEX_HOME / "auth.json"
ACTIVATE_HOOK = REPO_DIR / "hooks" / "codex-caveman-activate.js"
TRACKER_HOOK = REPO_DIR / "hooks" / "codex-caveman-mode-tracker.js"
HOOK_SUPPORT_FILES = ["caveman-config.js", "codex-caveman-activate.js", "codex-caveman-mode-tracker.js"]
GENERAL_MODE_ORDER = [
    "off",
    "lite",
    "full",
    "full-plus",
    "ultra",
    "mello-lite",
    "mello",
    "mello-ultra",
]
SPECIAL_MODE_ORDER = {
    "dialogue": ["off", "full", "full-plus"],
    "commit": ["off", "commit"],
    "review": ["off", "review"],
    "compress": ["off", "compress"],
}
DEFAULT_MODEL = "gpt-5.4"
DEFAULT_JUDGE_MODEL = "gpt-5.4-mini"
STORAGE_PROBE_TEMPLATE = (
    "Read memory file content below. Reply with OK only.\n\n"
    "<memory-file>\n{body}\n</memory-file>"
)
JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "overall": {"type": "integer", "minimum": 0, "maximum": 5},
        "correctness": {"type": "integer", "minimum": 0, "maximum": 5},
        "coverage": {"type": "integer", "minimum": 0, "maximum": 5},
        "format": {"type": "integer", "minimum": 0, "maximum": 5},
        "major_issues": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["overall", "correctness", "coverage", "format", "major_issues"],
    "additionalProperties": False,
}


def get_temp_root() -> Path:
    raw = os.environ.get(
        "CAVEMAN_BENCH_TEMP_ROOT",
        str(Path(tempfile.gettempdir()) / "caveman-bench"),
    )
    root = Path(raw).expanduser().resolve()
    try:
        root.relative_to(REPO_DIR.resolve())
    except ValueError:
        pass
    else:
        raise RuntimeError(
            f"CAVEMAN_BENCH_TEMP_ROOT must stay outside the repo: {root}"
        )
    root.mkdir(parents=True, exist_ok=True)
    return root


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_experiments() -> dict[str, Any]:
    data = json.loads(EXPERIMENTS_PATH.read_text())
    validate_experiments(data)
    return data


def validate_experiments(data: dict[str, Any]) -> None:
    if data.get("version") != 1:
        raise ValueError("mode matrix experiments must use version=1")

    families = data.get("families", {})
    required = {
        "general": GENERAL_MODE_ORDER,
        "dialogue": SPECIAL_MODE_ORDER["dialogue"],
        "commit": SPECIAL_MODE_ORDER["commit"],
        "review": SPECIAL_MODE_ORDER["review"],
        "compress": SPECIAL_MODE_ORDER["compress"],
    }
    for family, modes in required.items():
        if family not in families:
            raise ValueError(f"missing family {family}")
        experiments = families[family].get("experiments", [])
        if len(experiments) < 5:
            raise ValueError(f"{family} needs at least 5 experiments")
        if families[family].get("modes") != modes:
            raise ValueError(f"{family} modes must equal {modes}")
        for experiment in experiments:
            if "id" not in experiment:
                raise ValueError(f"{family} experiment missing id: {experiment}")
            if family == "compress":
                rel = experiment.get("original_path")
                if not rel:
                    raise ValueError(f"{family}:{experiment['id']} missing original_path")
                if not (REPO_DIR / rel).exists():
                    raise ValueError(f"{family}:{experiment['id']} missing file {rel}")
                compressed = (REPO_DIR / rel).with_name(
                    Path(rel).name.replace(".original.md", ".md")
                )
                if not compressed.exists():
                    raise ValueError(
                        f"{family}:{experiment['id']} missing compressed fixture {compressed}"
                    )
            elif family == "compress":
                rel = experiment.get("original_path")
                if not rel:
                    raise ValueError(f"{family}:{experiment['id']} missing original_path")
                if not (REPO_DIR / rel).exists():
                    raise ValueError(f"{family}:{experiment['id']} missing file {rel}")
                compressed = (REPO_DIR / rel).with_name(
                    Path(rel).name.replace(".original.md", ".md")
                )
                if not compressed.exists():
                    raise ValueError(
                        f"{family}:{experiment['id']} missing compressed fixture {compressed}"
                    )
            elif family == "dialogue":
                turns = experiment.get("turns", [])
                if len(turns) < 3:
                    raise ValueError(f"{family}:{experiment['id']} needs at least 3 turns")
            else:
                if not experiment.get("prompt"):
                    raise ValueError(f"{family}:{experiment['id']} missing prompt")
            if len(experiment.get("rubric", [])) < 3:
                raise ValueError(
                    f"{family}:{experiment['id']} needs at least 3 rubric bullets"
                )


def ensure_runtime(validate_only: bool = False) -> None:
    if shutil.which("node") is None:
        raise RuntimeError("node is required to build Codex hook contexts")
    get_temp_root()
    if validate_only:
        return
    if shutil.which("codex") is None:
        raise RuntimeError("codex CLI is required for non-dry benchmark runs")
    if not SOURCE_AUTH_PATH.exists():
        raise RuntimeError(
            f"missing Codex auth at {SOURCE_AUTH_PATH}; run `codex login` or set CAVEMAN_BENCH_SOURCE_CODEX_HOME"
        )


def mode_label(mode: str) -> str:
    if mode == "mello":
        return "mello / mello-full"
    return mode


def normalize_benchmark_mode(mode: str) -> str:
    raw = str(mode or "").strip().lower()
    if raw == "mello-full":
        return "mello"
    if raw == "wenyan-lite":
        return "mello-lite"
    if raw in {"wenyan", "wenyan-full"}:
        return "mello"
    if raw == "wenyan-ultra":
        return "mello-ultra"
    return raw


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def fmt_num(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}"


def average(values: list[float]) -> float | None:
    if not values:
        return None
    return statistics.mean(values)


def median(values: list[float]) -> float | None:
    if not values:
        return None
    return statistics.median(values)


def copy_skill_dir(skill_name: str, home_dir: Path) -> None:
    src = REPO_DIR / "skills" / skill_name
    if not src.exists():
        raise RuntimeError(f"missing skill directory {src}")
    dst = home_dir / ".agents" / "skills" / skill_name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, dirs_exist_ok=True)


def install_hooks(codex_home: Path) -> None:
    hooks_dir = codex_home / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    for name in HOOK_SUPPORT_FILES:
        shutil.copy2(REPO_DIR / "hooks" / name, hooks_dir / name)

    start_cmd = f'node "{hooks_dir / "codex-caveman-activate.js"}"'
    prompt_cmd = f'node "{hooks_dir / "codex-caveman-mode-tracker.js"}"'
    hooks_payload = {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "startup|resume",
                    "hooks": [
                        {
                            "type": "command",
                            "command": start_cmd,
                            "timeout": 5,
                        }
                    ],
                }
            ],
            "UserPromptSubmit": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": prompt_cmd,
                            "timeout": 5,
                        }
                    ]
                }
            ],
        }
    }
    (codex_home / "hooks.json").write_text(json.dumps(hooks_payload, indent=2) + "\n")


def write_config(codex_home: Path, *, hooks_enabled: bool) -> None:
    config = "[features]\n"
    config += f"codex_hooks = {'true' if hooks_enabled else 'false'}\n"
    (codex_home / "config.toml").write_text(config)


def parse_jsonl_events(stdout: str) -> dict[str, Any]:
    final_text = ""
    usage: dict[str, Any] | None = None
    events = []
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"non-JSON line from codex --json: {raw_line}") from exc
        events.append(event)
        if event.get("type") == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "agent_message":
                final_text = item.get("text", "")
        elif event.get("type") == "turn.completed":
            usage = event.get("usage", {})

    if usage is None:
        raise RuntimeError(f"missing turn.completed event in codex output:\n{stdout}")

    return {
        "text": final_text.strip(),
        "usage": {
            "input_tokens": int(usage.get("input_tokens", 0)),
            "cached_input_tokens": int(usage.get("cached_input_tokens", 0)),
            "output_tokens": int(usage.get("output_tokens", 0)),
        },
        "events": events,
    }


def run_codex_exec(
    prompt: str,
    *,
    model: str,
    hooks_enabled: bool,
    skill_names: tuple[str, ...] = (),
    default_mode: str | None = None,
    output_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(
        prefix="mode-matrix-",
        dir=get_temp_root(),
    ) as tmp:
        root = Path(tmp)
        home_dir = root / "home"
        codex_home = root / "codex"
        workdir = root / "workdir"
        home_dir.mkdir(parents=True)
        codex_home.mkdir(parents=True)
        workdir.mkdir(parents=True)

        auth_path = codex_home / "auth.json"
        shutil.copy2(SOURCE_AUTH_PATH, auth_path)
        os.chmod(auth_path, 0o600)
        write_config(codex_home, hooks_enabled=hooks_enabled)
        if hooks_enabled:
            install_hooks(codex_home)
        for skill_name in skill_names:
            copy_skill_dir(skill_name, home_dir)

        schema_path = None
        if output_schema is not None:
            schema_path = root / "schema.json"
            schema_path.write_text(json.dumps(output_schema))

        cmd = [
            "codex",
            "-a",
            "never",
            "exec",
            "--json",
            "--ephemeral",
            "--skip-git-repo-check",
            "-C",
            str(workdir),
            "-s",
            "read-only",
            "-m",
            model,
        ]
        if schema_path is not None:
            cmd += ["--output-schema", str(schema_path)]
        cmd.append("-")

        env = os.environ.copy()
        env["HOME"] = str(home_dir)
        env["CODEX_HOME"] = str(codex_home)
        if default_mode is not None:
            env["CAVEMAN_DEFAULT_MODE"] = default_mode

        result = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(
                "codex exec failed\n"
                f"cmd: {' '.join(cmd)}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        parsed = parse_jsonl_events(result.stdout)
        return {
            "text": parsed["text"],
            "input_tokens": parsed["usage"]["input_tokens"],
            "cached_input_tokens": parsed["usage"]["cached_input_tokens"],
            "output_tokens": parsed["usage"]["output_tokens"],
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


def build_judge_prompt(
    *,
    family: str,
    experiment: dict[str, Any],
    output_text: str,
    reference_text: str | None = None,
    validator_summary: dict[str, Any] | None = None,
) -> str:
    lines = [
        f"Family: {family}",
        f"Experiment: {experiment['id']}",
        "",
    ]

    if family == "compress":
        original_text = (REPO_DIR / experiment["original_path"]).read_text()
        lines += [
            "Original text:",
            original_text,
            "",
            "Compressed candidate:",
            output_text,
            "",
        ]
    else:
        lines += [
            "Task prompt:",
            experiment["prompt"],
            "",
            "Candidate output:",
            output_text,
            "",
        ]
        if reference_text is not None:
            lines += [
                "Reference off-mode output:",
                reference_text,
                "",
            ]

    lines.append("Rubric:")
    for item in experiment["rubric"]:
        lines.append(f"- {item}")
    lines.append("")

    if validator_summary is not None:
        lines.append("Validator summary:")
        lines.append(json.dumps(validator_summary, indent=2))
        lines.append("")

    lines += [
        "Score the candidate's technical substance and task fitness.",
        "Do not punish brevity by itself.",
        "Penalize wrong facts, missing critical content, and broken required format.",
        "",
        "Use these score meanings:",
        "- 5 = excellent, no meaningful loss",
        "- 4 = minor loss",
        "- 3 = noticeable but usable loss",
        "- 2 = major loss",
        "- 1 = severe failure",
        "- 0 = unusable",
    ]
    return "\n".join(lines)


def judge_output(
    *,
    judge_model: str,
    family: str,
    experiment: dict[str, Any],
    output_text: str,
    reference_text: str | None = None,
    validator_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    prompt = build_judge_prompt(
        family=family,
        experiment=experiment,
        output_text=output_text,
        reference_text=reference_text,
        validator_summary=validator_summary,
    )
    response = run_codex_exec(
        prompt,
        model=judge_model,
        hooks_enabled=False,
        output_schema=JUDGE_SCHEMA,
    )
    parsed = json.loads(response["text"])
    return {
        "overall": int(parsed["overall"]),
        "correctness": int(parsed["correctness"]),
        "coverage": int(parsed["coverage"]),
        "format": int(parsed["format"]),
        "major_issues": list(parsed.get("major_issues", [])),
        "judge_input_tokens": response["input_tokens"],
        "judge_cached_input_tokens": response["cached_input_tokens"],
        "judge_output_tokens": response["output_tokens"],
        "raw": response["text"],
    }


def import_validate_module():
    sys.path.insert(0, str(REPO_DIR / "caveman-compress"))
    from scripts.validate import validate  # type: ignore

    return validate


def validate_pair(original_text: str, compressed_text: str) -> dict[str, Any]:
    validate = import_validate_module()
    with tempfile.TemporaryDirectory(
        prefix="compress-validate-",
        dir=get_temp_root(),
    ) as tmp:
        root = Path(tmp)
        original = root / "original.md"
        compressed = root / "compressed.md"
        original.write_text(original_text)
        compressed.write_text(compressed_text)
        result = validate(original, compressed)
    return {
        "is_valid": result.is_valid,
        "errors": list(result.errors),
        "warnings": list(result.warnings),
    }


def storage_probe_prompt(body: str) -> str:
    return STORAGE_PROBE_TEMPLATE.format(body=body)


def measure_storage_tokens(text: str, *, model: str, baseline_input_tokens: int) -> tuple[int, dict[str, int]]:
    response = run_codex_exec(
        storage_probe_prompt(text),
        model=model,
        hooks_enabled=False,
    )
    net = max(response["input_tokens"] - baseline_input_tokens, 0)
    return net, {
        "probe_input_tokens": response["input_tokens"],
        "probe_cached_input_tokens": response["cached_input_tokens"],
        "probe_output_tokens": response["output_tokens"],
    }


def general_mode_prompt(experiment: dict[str, Any], mode: str) -> str:
    return experiment["prompt"]


def dialogue_turn_prompt(turns: list[str], history: list[dict[str, str]], turn_index: int) -> str:
    current = turns[turn_index]
    if not history:
        return current

    lines = [
        "Continue this conversation. Keep prior context and do not restart from scratch.",
        "",
        "Conversation so far:",
    ]
    for item in history:
        lines.append(f"{item['role'].capitalize()}:")
        lines.append(item["text"])
        lines.append("")
    lines += [
        "Next user message:",
        current,
    ]
    return "\n".join(lines)


def special_mode_prompt(family: str, experiment: dict[str, Any], mode: str) -> str:
    if mode == "off":
        return experiment["prompt"]
    prefix = {
        "commit": "/caveman-commit",
        "review": "/caveman-review",
    }[family]
    return f"{prefix}\n\n{experiment['prompt']}"


def run_generation_family(
    *,
    family_name: str,
    family: dict[str, Any],
    model: str,
    judge_model: str,
    skip_judge: bool,
) -> dict[str, Any]:
    rows = []
    experiments = family["experiments"]
    modes = family["modes"]

    for index, experiment in enumerate(experiments, 1):
        print(
            f"[{family_name}] experiment {index}/{len(experiments)} {experiment['id']}",
            file=sys.stderr,
        )
        outputs: dict[str, Any] = {}
        for mode in modes:
            print(f"  mode={mode}", file=sys.stderr)
            if family_name == "general":
                prompt = general_mode_prompt(experiment, mode)
                outputs[mode] = run_codex_exec(
                    prompt,
                    model=model,
                    hooks_enabled=(mode != "off"),
                    default_mode=(mode if mode != "off" else None),
                )
            else:
                prompt = special_mode_prompt(family_name, experiment, mode)
                outputs[mode] = run_codex_exec(
                    prompt,
                    model=model,
                    hooks_enabled=False,
                    skill_names=((f"caveman-{family_name}",) if mode != "off" else ()),
                )

        off_output = outputs["off"]["text"]
        judged: dict[str, Any] = {}
        if not skip_judge:
            for mode in modes:
                judged[mode] = judge_output(
                    judge_model=judge_model,
                    family=family_name,
                    experiment=experiment,
                    output_text=outputs[mode]["text"],
                    reference_text=(off_output if mode != "off" else None),
                )

        off_total = outputs["off"]["input_tokens"] + outputs["off"]["output_tokens"]
        off_output_tokens = outputs["off"]["output_tokens"]

        for mode in modes:
            row = {
                "family": family_name,
                "mode": mode,
                "experiment_id": experiment["id"],
                "input_tokens": outputs[mode]["input_tokens"],
                "cached_input_tokens": outputs[mode]["cached_input_tokens"],
                "output_tokens": outputs[mode]["output_tokens"],
                "total_tokens": outputs[mode]["input_tokens"] + outputs[mode]["output_tokens"],
                "output_savings_vs_off": (
                    1 - outputs[mode]["output_tokens"] / off_output_tokens
                    if off_output_tokens
                    else 0.0
                ),
                "total_savings_vs_off": (
                    1 - (outputs[mode]["input_tokens"] + outputs[mode]["output_tokens"]) / off_total
                    if off_total
                    else 0.0
                ),
                "text": outputs[mode]["text"],
            }
            if judged:
                row["judge"] = judged[mode]
                row["quality_score"] = judged[mode]["overall"]
                row["quality_loss_vs_off"] = judged["off"]["overall"] - judged[mode]["overall"]
            rows.append(row)

    return {"family": family_name, "modes": modes, "rows": rows}


def run_dialogue_family(
    *,
    family: dict[str, Any],
    model: str,
    judge_model: str,
    skip_judge: bool,
) -> dict[str, Any]:
    rows = []
    experiments = family["experiments"]
    modes = family["modes"]

    for index, experiment in enumerate(experiments, 1):
        print(
            f"[dialogue] experiment {index}/{len(experiments)} {experiment['id']}",
            file=sys.stderr,
        )
        turns = experiment["turns"]
        outputs: dict[str, Any] = {}
        final_outputs: dict[str, str] = {}

        for mode in modes:
            print(f"  mode={mode}", file=sys.stderr)
            history: list[dict[str, str]] = []
            turn_rows = []
            for turn_index, _ in enumerate(turns, 1):
                prompt = dialogue_turn_prompt(turns, history, turn_index - 1)
                result = run_codex_exec(
                    prompt,
                    model=model,
                    hooks_enabled=(mode != "off"),
                    default_mode=(mode if mode != "off" else None),
                )
                turn_rows.append({
                    "turn_index": turn_index,
                    "prompt": prompt,
                    "input_tokens": result["input_tokens"],
                    "cached_input_tokens": result["cached_input_tokens"],
                    "output_tokens": result["output_tokens"],
                    "text": result["text"],
                })
                history.append({"role": "user", "text": turns[turn_index - 1]})
                history.append({"role": "assistant", "text": result["text"]})
            outputs[mode] = turn_rows
            final_outputs[mode] = turn_rows[-1]["text"]

        judged: dict[str, Any] = {}
        if not skip_judge:
            for mode in modes:
                judged[mode] = judge_output(
                    judge_model=judge_model,
                    family="dialogue",
                    experiment={
                        "id": experiment["id"],
                        "prompt": "\n\n".join(f"Turn {i+1}: {turn}" for i, turn in enumerate(turns)),
                        "rubric": experiment["rubric"],
                    },
                    output_text=final_outputs[mode],
                    reference_text=(final_outputs["off"] if mode != "off" else None),
                )

        off_total = sum(row["input_tokens"] + row["output_tokens"] for row in outputs["off"])
        off_output = sum(row["output_tokens"] for row in outputs["off"])

        for mode in modes:
            total_tokens = sum(row["input_tokens"] + row["output_tokens"] for row in outputs[mode])
            output_tokens = sum(row["output_tokens"] for row in outputs[mode])
            row = {
                "family": "dialogue",
                "mode": mode,
                "experiment_id": experiment["id"],
                "turns": outputs[mode],
                "final_text": final_outputs[mode],
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "output_savings_vs_off": (1 - output_tokens / off_output) if off_output else 0.0,
                "total_savings_vs_off": (1 - total_tokens / off_total) if off_total else 0.0,
            }
            if judged:
                row["judge"] = judged[mode]
                row["quality_score"] = judged[mode]["overall"]
                row["quality_loss_vs_off"] = judged["off"]["overall"] - judged[mode]["overall"]
            rows.append(row)

    return {"family": "dialogue", "modes": modes, "rows": rows}


def run_compress_family(
    *,
    family: dict[str, Any],
    model: str,
    judge_model: str,
    skip_judge: bool,
) -> dict[str, Any]:
    rows = []
    baseline_probe = run_codex_exec(
        storage_probe_prompt(""),
        model=model,
        hooks_enabled=False,
    )
    baseline_input_tokens = baseline_probe["input_tokens"]

    for index, experiment in enumerate(family["experiments"], 1):
        print(
            f"[compress] experiment {index}/{len(family['experiments'])} {experiment['id']}",
            file=sys.stderr,
        )
        original_path = REPO_DIR / experiment["original_path"]
        compressed_path = original_path.with_name(
            original_path.name.replace(".original.md", ".md")
        )
        original_text = original_path.read_text()
        compressed_text = compressed_path.read_text()

        original_tokens, original_probe = measure_storage_tokens(
            original_text,
            model=model,
            baseline_input_tokens=baseline_input_tokens,
        )
        compressed_tokens, compressed_probe = measure_storage_tokens(
            compressed_text,
            model=model,
            baseline_input_tokens=baseline_input_tokens,
        )
        validation = validate_pair(original_text, compressed_text)

        off_row = {
            "family": "compress",
            "mode": "off",
            "experiment_id": experiment["id"],
            "stored_text_tokens": original_tokens,
            "stored_text_savings_vs_off": 0.0,
            "probe": original_probe,
            "text": original_text,
        }
        rows.append(off_row)

        row = {
            "family": "compress",
            "mode": "compress",
            "experiment_id": experiment["id"],
            "stored_text_tokens": compressed_tokens,
            "stored_text_savings_vs_off": (
                1 - compressed_tokens / original_tokens if original_tokens else 0.0
            ),
            "probe": compressed_probe,
            "validator": validation,
            "text": compressed_text,
        }
        if not skip_judge:
            judge = judge_output(
                judge_model=judge_model,
                family="compress",
                experiment=experiment,
                output_text=compressed_text,
                validator_summary=validation,
            )
            penalty = min(3, 2 * len(validation["errors"]) + len(validation["warnings"]))
            adjusted = max(0, judge["overall"] - penalty)
            row["judge"] = judge
            row["quality_score"] = adjusted
            row["quality_loss_vs_off"] = 5 - adjusted
            off_row["quality_score"] = 5
            off_row["quality_loss_vs_off"] = 0
        rows.append(row)

    return {"family": "compress", "modes": family["modes"], "rows": rows}


def summarize_family(result: dict[str, Any]) -> dict[str, Any]:
    family = result["family"]
    rows = result["rows"]
    by_mode: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_mode.setdefault(row["mode"], []).append(row)

    ordered_modes = result.get(
        "modes",
        GENERAL_MODE_ORDER if family == "general" else SPECIAL_MODE_ORDER[family],
    )

    summary_rows = []
    for mode in ordered_modes:
        mode_rows = by_mode.get(mode, [])
        if family == "compress":
            savings_key = "stored_text_savings_vs_off"
        else:
            savings_key = "output_savings_vs_off"
        savings = [float(row[savings_key]) for row in mode_rows if savings_key in row]
        quality = [float(row["quality_score"]) for row in mode_rows if "quality_score" in row]
        loss = [float(row["quality_loss_vs_off"]) for row in mode_rows if "quality_loss_vs_off" in row]

        summary = {
            "mode": mode,
            "experiments": len(mode_rows),
            "mean_savings_vs_off": average(savings),
            "median_savings_vs_off": median(savings),
            "mean_quality_score": average(quality),
            "mean_quality_loss_vs_off": average(loss),
        }
        if family != "compress":
            total_savings = [
                float(row["total_savings_vs_off"])
                for row in mode_rows
                if "total_savings_vs_off" in row
            ]
            summary["mean_total_savings_vs_off"] = average(total_savings)
            summary["median_total_savings_vs_off"] = median(total_savings)
        else:
            valid = [
                1.0 if row.get("validator", {}).get("is_valid") else 0.0
                for row in mode_rows
                if row["mode"] == "compress"
            ]
            summary["validator_pass_rate"] = average(valid)
        summary_rows.append(summary)

    return {
        "family": family,
        "modes": result.get("modes"),
        "summary_rows": summary_rows,
        "rows": rows,
    }


def markdown_summary(family_summary: dict[str, Any], *, skip_judge: bool) -> str:
    family = family_summary["family"]
    title = family.capitalize()
    lines = [f"## {title}", ""]
    if family == "compress":
        lines.append(
            "| Mode | Experiments | Mean stored-text saved vs off | Mean quality loss vs off |"
        )
        lines.append(
            "|------|------------:|-------------------------------:|-------------------------:|"
        )
        for row in family_summary["summary_rows"]:
            lines.append(
                f"| {mode_label(row['mode'])} | {row['experiments']} | "
                f"{fmt_pct(row['mean_savings_vs_off'])} | "
                f"{fmt_num(row['mean_quality_loss_vs_off']) if not skip_judge else 'n/a'} |"
            )
    else:
        lines.append(
            "| Mode | Experiments | Mean output saved vs off | Mean total saved vs off | Mean quality loss vs off |"
        )
        lines.append(
            "|------|------------:|--------------------------:|------------------------:|-------------------------:|"
        )
        for row in family_summary["summary_rows"]:
            lines.append(
                f"| {mode_label(row['mode'])} | {row['experiments']} | "
                f"{fmt_pct(row['mean_savings_vs_off'])} | "
                f"{fmt_pct(row['mean_total_savings_vs_off'])} | "
                f"{fmt_num(row['mean_quality_loss_vs_off']) if not skip_judge else 'n/a'} |"
            )
    lines.append("")
    return "\n".join(lines)


def save_results(payload: dict[str, Any]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"mode_matrix_{timestamp}.json"
    path.write_text(json.dumps(payload, indent=2))
    return path


def dry_run(data: dict[str, Any], families: list[str], skip_judge: bool) -> None:
    family_map = data["families"]
    print("Mode matrix benchmark plan")
    print(f"Families: {', '.join(families)}")
    print()

    total_generation = 0
    total_judges = 0
    total_storage_probes = 0
    for family in families:
        experiments = family_map[family]["experiments"]
        modes = family_map[family]["modes"]
        print(f"[{family}] {len(experiments)} experiments x {len(modes)} modes")
        for experiment in experiments:
            print(f"  - {experiment['id']}")
        if family == "compress":
            total_storage_probes += 1 + len(experiments) * 2
        else:
            total_generation += len(experiments) * len(modes)
        if not skip_judge:
            total_judges += len(experiments) * len(modes)
        print()

    print(f"Codex generation runs: {total_generation}")
    print(f"Codex judge runs:      {total_judges}")
    print(f"Codex storage probes:  {total_storage_probes}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark Caveman modes for Codex token savings vs quality loss"
    )
    parser.add_argument(
        "--family",
        default="all",
        choices=["all", "general", "dialogue", "commit", "review", "compress"],
        help="Family to run",
    )
    parser.add_argument("--model", default=os.environ.get("CAVEMAN_BENCH_MODEL", DEFAULT_MODEL))
    parser.add_argument(
        "--judge-model",
        default=os.environ.get("CAVEMAN_BENCH_JUDGE_MODEL", DEFAULT_JUDGE_MODEL),
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate config, no Codex runs")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate experiment matrix and local prerequisites only",
    )
    parser.add_argument(
        "--skip-judge",
        action="store_true",
        help="Measure token usage only",
    )
    parser.add_argument(
        "--modes",
        help="Comma-separated subset of modes to run for the selected family",
    )
    args = parser.parse_args()

    data = load_experiments()
    ensure_runtime(validate_only=args.validate_only or args.dry_run)
    families = (
        ["general", "dialogue", "commit", "review", "compress"]
        if args.family == "all"
        else [args.family]
    )
    requested_modes = None
    if args.modes:
        requested_modes = [
            normalize_benchmark_mode(part)
            for part in args.modes.split(",")
            if part.strip()
        ]
        if not requested_modes:
            raise ValueError("--modes provided but no modes parsed")
        if args.family == "all":
            raise ValueError("--modes requires a specific --family")

    if args.validate_only:
        print("Mode matrix config OK")
        print(f"Families: {', '.join(families)}")
        if requested_modes:
            print(f"Modes: {', '.join(requested_modes)}")
        return

    if args.dry_run:
        dry_run(data, families, args.skip_judge)
        return

    payload: dict[str, Any] = {
        "metadata": {
            "script_version": SCRIPT_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "backend": "codex",
            "model": args.model,
            "judge_model": args.judge_model,
            "skip_judge": args.skip_judge,
            "experiments_sha256": sha256_file(EXPERIMENTS_PATH),
            "activate_hook_sha256": sha256_file(ACTIVATE_HOOK),
            "tracker_hook_sha256": sha256_file(TRACKER_HOOK),
        },
        "families": {},
    }

    markdown_sections = []
    for family_name in families:
        family = dict(data["families"][family_name])
        if requested_modes is not None:
            allowed = set(family["modes"])
            missing = [mode for mode in requested_modes if mode not in allowed]
            if missing:
                raise ValueError(f"{family_name} does not support mode(s): {', '.join(missing)}")
            family["modes"] = requested_modes
        if family_name == "compress":
            result = run_compress_family(
                family=family,
                model=args.model,
                judge_model=args.judge_model,
                skip_judge=args.skip_judge,
            )
        elif family_name == "dialogue":
            result = run_dialogue_family(
                family=family,
                model=args.model,
                judge_model=args.judge_model,
                skip_judge=args.skip_judge,
            )
        else:
            result = run_generation_family(
                family_name=family_name,
                family=family,
                model=args.model,
                judge_model=args.judge_model,
                skip_judge=args.skip_judge,
            )
        summarized = summarize_family(result)
        payload["families"][family_name] = summarized
        markdown_sections.append(markdown_summary(summarized, skip_judge=args.skip_judge))

    results_path = save_results(payload)
    print(f"\nResults saved to {results_path}", file=sys.stderr)
    print("\n".join(markdown_sections))


if __name__ == "__main__":
    main()
