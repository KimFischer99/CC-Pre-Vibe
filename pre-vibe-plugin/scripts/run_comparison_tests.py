#!/usr/bin/env python3
"""Run deterministic comparison tests for pre-vibe intervention.

This is not a replacement for live agent A/B testing. It measures prompt token
cost and an implementation-readiness rubric that can be run offline.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from types import SimpleNamespace

from pre_vibe import build_result, estimate_tokens, write_outputs


SCENARIOS = [
    {
        "name": "general",
        "task": "帮我准备一个下周团队复盘会的议程和行动项模板",
        "expected_terms": ["目标", "验收", "假设", "交付", "review", "action"],
    },
    {
        "name": "research",
        "task": "调研 prompt optimization 开源项目，告诉我 pre-vibe 应该怎么差异化",
        "expected_terms": ["来源", "调研", "证据", "决策", "source", "research"],
    },
    {
        "name": "coding",
        "task": "根据当前项目 PRD 搭建一个 Codex plugin MVP，并给出测试报告",
        "expected_terms": ["AGENTS", "验证", "文件", "测试", "secret", "plan"],
    },
]


def readiness_score(text: str, expected_terms: list[str]) -> int:
    lower = text.lower()
    score = 0
    sections = ["goal", "目标", "acceptance", "验收", "assumption", "假设", "risk", "风险", "verify", "验证"]
    score += sum(1 for term in sections if term.lower() in lower)
    score += sum(2 for term in expected_terms if term.lower() in lower)
    score += 3 if "pre-vibe-spec.md" in lower or "pre-vibe-spec" in lower else 0
    score += 3 if "first-prompt.md" in lower or "first-prompt" in lower else 0
    return score


def run_case(case: dict[str, object], project: Path) -> dict[str, object]:
    raw_task = str(case["task"])
    baseline_tokens = estimate_tokens(raw_task)
    baseline_score = readiness_score(raw_task, list(case["expected_terms"]))
    with tempfile.TemporaryDirectory() as tmp:
        args = SimpleNamespace(
            task=raw_task,
            project=str(project),
            agent="codex",
            mode="standard",
            scenario=str(case["name"]),
            compression="auto",
            language="auto",
            benchmark_mode="final-answer-only",
            output_dir=tmp,
            json=False,
        )
        result = build_result(args)
        files = write_outputs(result, Path(tmp))
        prompt = files["prompt"].read_text(encoding="utf-8")
        spec = files["spec"].read_text(encoding="utf-8")
        agents = files["agents"].read_text(encoding="utf-8")
        combined = spec + "\n" + agents + "\n" + prompt
        return {
            "scenario": case["name"],
            "baseline_tokens": baseline_tokens,
            "pre_vibe_first_prompt_tokens": estimate_tokens(prompt),
            "pre_vibe_total_artifact_tokens": estimate_tokens(combined),
            "baseline_readiness_score": baseline_score,
            "pre_vibe_readiness_score": readiness_score(combined, list(case["expected_terms"])),
            "landing_effect": "higher readiness" if readiness_score(combined, list(case["expected_terms"])) > baseline_score else "no improvement",
        }


def render_report(results: list[dict[str, object]]) -> str:
    lines = [
        "# pre-vibe Comparison Test Report",
        "",
        "Deterministic offline comparison of raw task prompts versus pre-vibe generated context packages.",
        "",
        "| Scenario | Raw tokens | FIRST-PROMPT tokens | Full artifact tokens | Raw readiness | pre-vibe readiness | Landing effect |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in results:
        lines.append(
            f"| {row['scenario']} | {row['baseline_tokens']} | {row['pre_vibe_first_prompt_tokens']} | "
            f"{row['pre_vibe_total_artifact_tokens']} | {row['baseline_readiness_score']} | "
            f"{row['pre_vibe_readiness_score']} | {row['landing_effect']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Raw token cost is lower because no context engineering is performed.",
            "- pre-vibe stores all three artifacts on disk, but the formal injection is the budgeted FIRST-PROMPT only.",
            "- Landing effect is measured by a local readiness rubric: goal, assumptions, acceptance criteria, risks, verification, and scenario terms.",
            "- A live model A/B/C test is still required before claiming real-world task completion improvements.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=".")
    parser.add_argument("--output", default="pre-vibe-reports/comparison-report.md")
    args = parser.parse_args()
    results = [run_case(case, Path(args.project).resolve()) for case in SCENARIOS]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(results), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
