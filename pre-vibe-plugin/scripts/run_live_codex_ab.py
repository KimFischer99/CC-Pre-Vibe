#!/usr/bin/env python3
"""Run live Codex A/B checks for raw prompts versus pre-vibe prompts.

This script invokes `codex exec`, so it requires a working Codex login and may
consume model tokens. It keeps the agent sandbox read-only and asks for planning
or final text deliverables rather than repository mutation.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

from pre_vibe import build_result, estimate_tokens, write_outputs


SCENARIOS = [
    {
        "name": "general",
        "task": "帮我准备一个下周团队复盘会的议程和行动项模板。",
        "baseline": "帮我准备一个下周团队复盘会的议程和行动项模板。请直接给出可使用的最终结果。不要修改文件，只在最终回答中交付。",
        "success_terms": ["议程", "行动项", "负责人", "时间", "复盘"],
    },
    {
        "name": "research",
        "task": "调研 prompt optimization 开源项目，判断 pre-vibe 应该如何差异化。",
        "baseline": "调研 prompt optimization 开源项目，判断 pre-vibe 应该如何差异化。请给出结论、理由和建议。不要修改文件，只在最终回答中交付。",
        "success_terms": ["差异化", "来源", "竞品", "建议", "风险"],
    },
    {
        "name": "coding",
        "task": "根据当前项目 PRD，评估如何搭建 pre-vibe Codex plugin MVP，并给出架构和测试计划。",
        "baseline": "根据当前项目 PRD，评估如何搭建 pre-vibe Codex plugin MVP，并给出架构和测试计划。不要修改文件，只在最终回答中交付。",
        "success_terms": ["Codex plugin", "架构", "测试", "AGENTS", "风险"],
    },
]


def parse_events(stdout: str) -> tuple[dict[str, int], str]:
    usage: dict[str, int] = {}
    messages: list[str] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "turn.completed":
            usage = event.get("usage", {})
        if event.get("type") == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "agent_message":
                messages.append(item.get("text", ""))
    return usage, "\n".join(messages)


def live_score(text: str, terms: list[str]) -> int:
    lower = text.lower()
    score = 0
    score += sum(2 for term in terms if term.lower() in lower)
    score += 2 if any(marker in lower for marker in ["验收", "acceptance", "完成标准"]) else 0
    score += 2 if any(marker in lower for marker in ["风险", "risk"]) else 0
    score += 2 if any(marker in lower for marker in ["步骤", "计划", "plan"]) else 0
    score += 2 if any(marker in lower for marker in ["验证", "test", "检查"]) else 0
    return score


def run_codex(prompt: str, project: Path, output_file: Path) -> dict[str, object]:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "codex",
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--json",
        "-C",
        str(project),
        "--sandbox",
        "read-only",
        "-o",
        str(output_file),
        prompt,
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, stdin=subprocess.DEVNULL, timeout=240, check=False)
    usage, message = parse_events(proc.stdout)
    if output_file.exists() and not message:
        message = output_file.read_text(encoding="utf-8")
    return {
        "returncode": proc.returncode,
        "usage": usage,
        "message": message,
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-8:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-8:]),
    }


def display_path(path: Path, project: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(project))
    except ValueError:
        return str(resolved)


def build_pre_vibe_prompt(task: str, project: Path, scenario: str, context_dir: Path) -> str:
    args = SimpleNamespace(
        task=task,
        project=str(project),
        agent="codex",
        mode="standard",
        scenario=scenario,
        compression="auto",
        language="auto",
        benchmark_mode="final-answer-only",
        output_dir=str(context_dir),
        json=False,
    )
    result = build_result(args)
    files = write_outputs(result, context_dir)
    spec_path = display_path(files["spec"], project)
    prompt_path = display_path(files["prompt"], project)
    first_prompt = files["prompt"].read_text(encoding="utf-8")
    return (
        f"Use the pre-vibe context package at `{spec_path}`.\n\n"
        f"Inject only `{prompt_path}`. Do not load the full spec unless it is necessary.\n\n"
        "Evaluation constraint: do not edit or write files. Produce the requested final deliverable in your final answer only.\n\n"
        f"{first_prompt}"
    )


def render(results: list[dict[str, object]]) -> str:
    lines = [
        "# pre-vibe Live Codex A/B Report",
        "",
        "Live `codex exec --json` comparison. All runs used read-only sandbox and ephemeral sessions.",
        "",
        "| Scenario | Variant | CLI return | Input tokens | Output tokens | Reasoning tokens | Score | Output file |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in results:
        usage = row["usage"]
        lines.append(
            f"| {row['scenario']} | {row['variant']} | {row['returncode']} | "
            f"{usage.get('input_tokens', 0)} | {usage.get('output_tokens', 0)} | "
            f"{usage.get('reasoning_output_tokens', 0)} | {row['score']} | `{row['output_file']}` |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Scores are heuristic checks for expected scenario terms, risks, planning, verification, and acceptance framing.",
            "- Token usage comes from Codex JSON `turn.completed.usage` events.",
            "- Because live model outputs are nondeterministic, rerun this script before making benchmark claims.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=".")
    parser.add_argument("--output-dir", default="pre-vibe-reports/live")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    output_root = Path(args.output_dir).resolve()
    results: list[dict[str, object]] = []
    for case in SCENARIOS:
        scenario = str(case["name"])
        terms = list(case["success_terms"])
        baseline_file = output_root / scenario / "baseline.md"
        baseline = run_codex(str(case["baseline"]), project, baseline_file)
        results.append(
            {
                "scenario": scenario,
                "variant": "baseline",
                "returncode": baseline["returncode"],
                "usage": baseline["usage"],
                "score": live_score(str(baseline["message"]), terms),
                "output_file": baseline_file,
            }
        )

        context_dir = output_root / scenario / "pre-vibe-context"
        pre_prompt = build_pre_vibe_prompt(str(case["task"]), project, scenario, context_dir)
        pre_file = output_root / scenario / "pre-vibe.md"
        pre = run_codex(pre_prompt, project, pre_file)
        results.append(
            {
                "scenario": scenario,
                "variant": "pre-vibe",
                "returncode": pre["returncode"],
                "usage": pre["usage"],
                "score": live_score(str(pre["message"]), terms),
                "output_file": pre_file,
                "prompt_estimated_tokens": estimate_tokens(pre_prompt),
            }
        )

    report = output_root / "live-codex-ab-report.md"
    report.write_text(render(results), encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
