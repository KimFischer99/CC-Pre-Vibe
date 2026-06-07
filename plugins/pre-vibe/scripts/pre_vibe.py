#!/usr/bin/env python3
"""Compatibility facade for Pre-Vibe workflow utilities.

The implementation is split across focused ``pv_*`` modules. This file keeps the
old import surface stable for the bundled MCP server and for local CLI checks.
"""

from __future__ import annotations

import argparse
import json

from pv_artifacts import (
    ARTIFACT_FILENAMES,
    estimate_tokens,
    redact_secret_like,
    validate_artifact_contents,
    write_artifacts,
)
from pv_compact import (
    compact_claude_environment,
    compact_decision,
    compact_evidence_ref,
    compact_project_context,
    redact_path_for_context,
)
from pv_environment import (
    collect_configured_plugins,
    collect_plugin_names,
    inspect_claude_environment,
)
from pv_models import (
    AWAITING_APPROVAL,
    DONE,
    INTAKE_STARTED,
    INTENSITY_PROFILES,
    NEEDS_CONTEXT,
    NEEDS_USER_INPUT,
    READY_TO_COMPILE,
    READY_TO_INJECT,
    BlockingQuestion,
    ClaudeEnvironment,
    ContextAction,
    AgentInstructionRef,
    EvidenceRef,
    EvidenceItem,
    ExistingContext,
    IntakeDecision,
    IntensityProfile,
    PreVibeSettings,
    ProjectLanguageItem,
    ProjectContext,
    to_jsonable,
)
from pv_questions import (
    clean_header,
    native_question_payload,
    option_objects,
    visible_status_for_state,
)
from pv_routing import (
    assess_risk,
    assess_uncertainty,
    artifact_rules_for,
    blocking_questions_for,
    can_compile_artifacts,
    choose_intensity,
    choose_language,
    classify_scenario,
    component_suggestions_for,
    context_actions_for,
    determine_next_state,
    extract_target_paths,
    has_ambiguous_external_target,
    has_cjk,
    has_target_path,
    is_reverse_engineering_task,
    looks_like_new_product_task,
    prepare_project_start,
    route_intake,
)
from pv_scan import (
    ALLOWLIST_FILENAMES,
    ALLOWLIST_SUFFIXES,
    SECRET_PATTERNS,
    SKIP_DIRS,
    collect_skill_names,
    detect_agent_instruction_map,
    detect_existing_context,
    detect_git_state,
    find_global_agents,
    is_secret_like,
    safe_walk,
    summarize_agents,
)
from pv_settings import (
    get_pre_vibe_settings,
    resolve_requested_intensity,
    set_pre_vibe_intensity,
    update_pre_vibe_settings,
)
from pv_terms import (
    AMBIGUOUS_TARGET_TERMS,
    ARCHITECT_TERMS,
    CODING_TERMS,
    RESEARCH_TERMS,
    REVERSE_TERMS,
    TARGET_PATH_RE,
)


__all__ = [
    "ALLOWLIST_FILENAMES",
    "ALLOWLIST_SUFFIXES",
    "AMBIGUOUS_TARGET_TERMS",
    "ARCHITECT_TERMS",
    "ARTIFACT_FILENAMES",
    "AWAITING_APPROVAL",
    "AgentInstructionRef",
    "BlockingQuestion",
    "CODING_TERMS",
    "ClaudeEnvironment",
    "ContextAction",
    "DONE",
    "EvidenceRef",
    "EvidenceItem",
    "ExistingContext",
    "INTAKE_STARTED",
    "INTENSITY_PROFILES",
    "IntensityProfile",
    "IntakeDecision",
    "NEEDS_CONTEXT",
    "NEEDS_USER_INPUT",
    "ProjectContext",
    "ProjectLanguageItem",
    "PreVibeSettings",
    "READY_TO_COMPILE",
    "READY_TO_INJECT",
    "RESEARCH_TERMS",
    "REVERSE_TERMS",
    "SECRET_PATTERNS",
    "SKIP_DIRS",
    "TARGET_PATH_RE",
    "artifact_rules_for",
    "assess_risk",
    "assess_uncertainty",
    "blocking_questions_for",
    "can_compile_artifacts",
    "choose_intensity",
    "choose_language",
    "classify_scenario",
    "clean_header",
    "collect_configured_plugins",
    "collect_plugin_names",
    "collect_skill_names",
    "compact_claude_environment",
    "compact_decision",
    "compact_evidence_ref",
    "compact_project_context",
    "component_suggestions_for",
    "context_actions_for",
    "determine_next_state",
    "detect_agent_instruction_map",
    "detect_existing_context",
    "detect_git_state",
    "estimate_tokens",
    "extract_target_paths",
    "find_global_agents",
    "get_pre_vibe_settings",
    "has_ambiguous_external_target",
    "has_cjk",
    "has_target_path",
    "inspect_claude_environment",
    "is_reverse_engineering_task",
    "is_secret_like",
    "looks_like_new_product_task",
    "native_question_payload",
    "option_objects",
    "prepare_project_start",
    "redact_path_for_context",
    "redact_secret_like",
    "route_intake",
    "resolve_requested_intensity",
    "safe_walk",
    "set_pre_vibe_intensity",
    "summarize_agents",
    "to_jsonable",
    "update_pre_vibe_settings",
    "validate_artifact_contents",
    "visible_status_for_state",
    "write_artifacts",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect Pre-Vibe routing without generating Markdown templates.")
    parser.add_argument("--task", required=True)
    parser.add_argument("--project", default=".")
    parser.add_argument("--scenario", default="auto", choices=("auto", "general", "research", "coding", "mixed"))
    parser.add_argument("--intensity", default="auto", choices=("auto", "mini", "default", "architect"))
    parser.add_argument("--language", default="auto", choices=("auto", "zh", "en", "bilingual"))
    parser.add_argument("--no-scan", action="store_true", help="Skip the safe project scan; route_intake will return NEEDS_CONTEXT.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    decision = route_intake(
        args.task,
        args.project,
        scenario=args.scenario,
        intensity=args.intensity,
        language=args.language,
        scan=not args.no_scan,
    )
    print(json.dumps(decision, ensure_ascii=False, indent=2, default=to_jsonable))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
