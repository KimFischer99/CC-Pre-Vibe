#!/usr/bin/env python3
"""Simulate a single coding pre-vibe workflow without calling a live model."""

from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace

from pre_vibe import build_handoff, build_result, estimate_tokens, write_outputs


DEFAULT_TASK = "根据当前项目 PRD，为 pre-vibe plugin 增加 token budget、精简 first prompt，并更新测试。"


def render_report(result, files: dict[str, Path]) -> str:
    prompt = files["prompt"].read_text(encoding="utf-8")
    spec = files["spec"].read_text(encoding="utf-8")
    agents = files["agents"].read_text(encoding="utf-8")
    states = [
        ("generate", "pre-vibe generated three uppercase Markdown files"),
        ("review", "user reviews handbook and init agents guidance"),
        ("approve_clear", "user approves /clear before formal workflow"),
        ("inject", "FIRST-PROMPT.MD is injected as the only initial context"),
        ("start_work", "agent starts with a short plan and budgeted context"),
    ]
    checks = {
        "three_files": all(path.exists() for path in files.values()),
        "uppercase_names": all(path.name == path.name.upper() for path in files.values()),
        "spec_not_in_prompt": "Do not paste the full" in prompt or "不要注入" in prompt,
        "clear_handoff": "/clear" in prompt and "/clear" in build_handoff(result, files),
        "prompt_under_budget": estimate_tokens(prompt) <= result.budget.max_injection_tokens,
        "agents_mentions_global": "Global AGENTS" in agents or "全局 AGENTS" in agents,
        "spec_is_handbook": "handbook" in spec.lower() or "handbook" in prompt.lower() or "handbook" in build_handoff(result, files).lower(),
    }
    lines = [
        "# pre-vibe Coding Workflow Simulation Report",
        "",
        "Offline simulation of the required pre-vibe workflow. No live model call was made.",
        "",
        "## Scenario",
        f"- Task: {result.task}",
        f"- Scenario: {result.scenario}",
        f"- Complexity: {result.complexity}",
        f"- Compression: {result.compression}",
        f"- FIRST-PROMPT token estimate: {estimate_tokens(prompt)}",
        f"- Budget: {result.budget.max_injection_tokens}",
        "",
        "## Workflow States",
    ]
    lines.extend(f"- {name}: {description}" for name, description in states)
    lines.extend(["", "## Checks"])
    lines.extend(f"- {name}: {'PASS' if passed else 'FAIL'}" for name, passed in checks.items())
    lines.extend(
        [
            "",
            "## Generated Files",
            f"- Spec handbook: `{files['spec']}` ({estimate_tokens(spec)} estimated tokens)",
            f"- Init agents: `{files['agents']}` ({estimate_tokens(agents)} estimated tokens)",
            f"- First prompt: `{files['prompt']}` ({estimate_tokens(prompt)} estimated tokens)",
            "",
            "## Handoff",
            "```text",
            build_handoff(result, files),
            "```",
            "",
            "## Result",
            "PASS" if all(checks.values()) else "FAIL",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=".")
    parser.add_argument("--task", default=DEFAULT_TASK)
    parser.add_argument("--output-dir", default="pre-vibe-reports/simulations/coding")
    parser.add_argument("--report", default="pre-vibe-reports/coding-workflow-simulation.md")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ns = SimpleNamespace(
        task=args.task,
        project=str(Path(args.project).resolve()),
        agent="codex",
        mode="standard",
        scenario="coding",
        compression="auto",
        language="auto",
        benchmark_mode="execution",
        output_dir=str(output_dir),
        json=False,
    )
    result = build_result(ns)
    files = write_outputs(result, output_dir)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(result, files), encoding="utf-8")
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
