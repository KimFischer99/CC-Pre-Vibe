#!/usr/bin/env python3
"""Run a realistic pre-vibe workflow simulation in a child process."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = CASE_DIR / "generated"
FEATURE_DOC = CASE_DIR / "feature-brief.md"
RESULT_JSON = CASE_DIR / "simulation-result.json"
CHILD_LOG = CASE_DIR / "child-process.log"


INITIAL_DOC = """# Feature Brief

Goal: turn a rough project note into a small actionable maintenance item.

Current note:
- The document should say what state this item is in.
- The document should make it easy to verify completion.
- The document should name the person or role responsible for follow-up.
"""


USER_REQUEST = (
    '/prompts:pre-vibe "请把 test/pre-vibe-simulation/feature-brief.md 整理成一个可执行的小功能：'
    '添加状态字段、验收清单和维护者备注，别改其他文件。"'
)


def write_initial_doc() -> None:
    CASE_DIR.mkdir(parents=True, exist_ok=True)
    FEATURE_DOC.write_text(INITIAL_DOC, encoding="utf-8")


def parent_main() -> int:
    write_initial_doc()
    proc = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--worker"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    CHILD_LOG.write_text(
        "STDOUT\n" + proc.stdout + "\nSTDERR\n" + proc.stderr,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)
    return 0


def worker_main() -> int:
    sys.path.insert(0, str(ROOT / "pre-vibe-plugin" / "scripts"))
    from pre_vibe import (
        ARTIFACT_FILENAMES,
        estimate_tokens,
        route_intake,
        to_jsonable,
        write_artifacts,
    )

    decision = route_intake(
        USER_REQUEST,
        ROOT,
        scenario="coding",
        intensity="default",
        language="zh",
    )
    reverse_control = route_intake(
        "我要逆向桌面上的这个东西，要用上pre-vibe",
        ROOT,
        scenario="coding",
        intensity="default",
        language="zh",
    )

    spec = """# Feature Brief 维护手册

## 原始需求

用户希望把 `test/pre-vibe-simulation/feature-brief.md` 整理成一个可执行的小功能，增加状态字段、验收清单和维护者备注，并且不要修改其他文件。

## 标准化目标

本轮只维护一个 Markdown 文档，让它从松散说明变成可以交接、检查和继续跟进的小任务说明。

## 用户场景

- 作为后续维护者，我可以一眼看到这个事项当前处于什么状态。
- 作为执行者，我可以按清单判断这次整理是否完成。
- 作为项目负责人，我可以看到谁负责后续跟进，而不需要追溯聊天记录。

## 范围

本轮包含：编辑 `test/pre-vibe-simulation/feature-brief.md`，增加状态、验收清单和维护者备注。

本轮不包含：修改插件源码、调整测试 runner、改动 README、增加自动化测试框架。

## 需求

- 文档必须保留原始目标说明。
- 文档必须新增 `Status` 信息，说明当前处理阶段。
- 文档必须新增可勾选的验收清单。
- 文档必须新增维护者或维护角色备注。
- 除目标文档外，不应修改其他业务文件。

## 验收标准

- `feature-brief.md` 出现明确的状态字段。
- `feature-brief.md` 出现至少三条可检查的验收项。
- `feature-brief.md` 出现维护者备注。
- 最终 diff 只包含目标文档和本次模拟产物。

## 项目证据

- `README.md` 表明当前仓库是 pre-vibe 插件源码仓库。
- `pre-vibe_PRD.md` 是产品需求来源，说明本轮模拟属于插件工作流验证。
- `test/pre-vibe-simulation/feature-brief.md` 是用户指定的唯一正式编辑目标。
- Codex 环境已安装代码审查能力和项目 AGENTS 指令，应在完成后进行 review。

## 建议

这个任务足够小，不需要架构档位；default 档位可以覆盖项目索引、组件索引和一次正式执行。执行时应先读目标文件，再做最小修改，最后检查是否误改了其他文件。
"""

    agents = """# Project Agent Guidance

- Follow all higher-priority system, developer, user, and global AGENTS instructions.
- Treat `test/pre-vibe-simulation/feature-brief.md` as the only formal task target for this simulation.
- Keep edits small and explainable; do not refactor plugin source while completing the document task.
- Do not read or expose secret-like files, environment values, token stores, or local databases.
- Prefer evidence from files over assumptions.
- Before final handoff, review the diff and report verification results.
"""

    prompt = """# Goal

Complete the simulated user request by editing `test/pre-vibe-simulation/feature-brief.md` only.

# Current Task

Read the target Markdown file, preserve its existing goal and notes, then add:

- a clear status field,
- an acceptance checklist,
- a maintainer or follow-up owner note.

# Hard Constraints

- Do not edit plugin source files during the formal execution step.
- Do not create intake draft files.
- Keep the change beginner-readable and easy to verify.

# Relevant Context

- `PRE_VIBE_SPEC.md` contains the user-facing handbook for the simulated task.
- `PROJECT_AGENTS.md` contains execution guidance and safety boundaries.
- The project has global AGENTS guidance; do not weaken it.

# Done When

- The target file includes status, acceptance checklist, and maintainer note.
- Verification confirms no forbidden cross-reference in the generated handbook/guidance pair.
- Verification confirms no `INTAKE.md` or equivalent draft was written.
"""

    written = write_artifacts(
        OUTPUT_DIR,
        {"spec": spec, "agents": agents, "prompt": prompt},
        {
            "state": decision.state,
            "scenario": decision.scenario,
            "intensity": decision.intensity,
            "slash_invocation": USER_REQUEST,
        },
    )

    updated_doc = INITIAL_DOC.rstrip() + """

Status: Ready for review

## Acceptance Checklist

- [x] The item has a visible status field.
- [x] The completion criteria are listed as checkable items.
- [x] A maintainer or follow-up owner note is present.

## Maintainer Note

Follow-up owner: project maintainer. Revisit this brief after the next workflow test and update the status if the expected behavior changes.
"""
    FEATURE_DOC.write_text(updated_doc, encoding="utf-8")

    spec_text = Path(written["spec"]).read_text(encoding="utf-8")
    agents_text = Path(written["agents"]).read_text(encoding="utf-8")
    final_doc = FEATURE_DOC.read_text(encoding="utf-8")
    intake_files = sorted(path.name for path in CASE_DIR.glob("*INTAKE*.md"))
    checks = {
        "project_index_before_questions": bool(decision.evidence_refs)
        and decision.evidence_refs[0].id == "project_execution_index"
        and decision.state in {"READY_TO_COMPILE", "NEEDS_USER_INPUT"},
        "component_index_present": any(item.id == "codex_component_index" for item in decision.evidence_refs),
        "native_question_control": reverse_control.state == "NEEDS_USER_INPUT"
        and bool(reverse_control.blocking_questions)
        and reverse_control.blocking_questions[0].requires_native_ui,
        "spec_agents_no_cross_reference": "PROJECT_AGENTS.md" not in spec_text
        and "PRE_VIBE_SPEC.md" not in agents_text,
        "no_intake_file": not intake_files,
        "formal_task_done": "Status:" in final_doc
        and "Acceptance Checklist" in final_doc
        and "Maintainer Note" in final_doc,
    }

    token_usage = {
        "pre_vibe_slash_prompt": estimate_tokens(USER_REQUEST),
        "pre_vibe_decision_json": estimate_tokens(json.dumps(decision, ensure_ascii=False, default=to_jsonable)),
        "pre_vibe_artifacts": sum(estimate_tokens(text) for text in (spec, agents, prompt)),
        "formal_first_prompt": estimate_tokens(prompt),
        "formal_target_read_write_context": estimate_tokens(INITIAL_DOC + updated_doc),
    }

    result = {
        "child_process": "worker",
        "user_request": USER_REQUEST,
        "decision": decision,
        "reverse_control_state": reverse_control.state,
        "reverse_control_questions": reverse_control.blocking_questions,
        "written": written,
        "checks": checks,
        "token_usage_estimate": token_usage,
        "token_usage_total_estimate": sum(token_usage.values()),
        "artifact_filenames": ARTIFACT_FILENAMES,
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=to_jsonable), encoding="utf-8")
    print(json.dumps({"checks": checks, "token_usage_estimate": token_usage}, ensure_ascii=False, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    if "--worker" in sys.argv:
        raise SystemExit(worker_main())
    raise SystemExit(parent_main())
