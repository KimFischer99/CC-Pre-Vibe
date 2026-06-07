"""Task routing, question selection, and workflow state decisions."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from pv_environment import inspect_codex_environment
from pv_models import (
    INTENSITY_PROFILES,
    NEEDS_CONTEXT,
    NEEDS_USER_INPUT,
    READY_TO_COMPILE,
    BlockingQuestion,
    CodexEnvironment,
    ContextAction,
    EvidenceRef,
    IntakeDecision,
    ProjectContext,
)
from pv_scan import safe_walk
from pv_terms import (
    AMBIGUOUS_TARGET_TERMS,
    ARCHITECT_TERMS,
    CODING_TERMS,
    RESEARCH_TERMS,
    REVERSE_TERMS,
    TARGET_PATH_RE,
)


def has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def choose_language(task: str, requested: str = "auto") -> str:
    if requested != "auto":
        return requested
    return "zh" if has_cjk(task) else "en"


def classify_scenario(task: str, requested: str = "auto") -> str:
    if requested != "auto":
        return requested
    lower = task.lower()
    coding_hit = any(token in lower for token in CODING_TERMS)
    research_hit = any(token in lower for token in RESEARCH_TERMS)
    if coding_hit and research_hit:
        return "mixed"
    if coding_hit:
        return "coding"
    if research_hit:
        return "research"
    return "general"


def is_reverse_engineering_task(task: str) -> bool:
    lower = task.lower()
    return any(term in lower for term in REVERSE_TERMS)


def extract_target_paths(task: str) -> list[str]:
    paths: list[str] = []
    for match in TARGET_PATH_RE.finditer(task):
        value = match.group(0).strip("`")
        paths.append(value)
    return paths


def has_target_path(task: str) -> bool:
    return bool(extract_target_paths(task))


def has_ambiguous_external_target(task: str) -> bool:
    lower = task.lower()
    return (
        is_reverse_engineering_task(task)
        and any(term in lower for term in AMBIGUOUS_TARGET_TERMS)
        and not has_target_path(task)
    )


def looks_like_new_product_task(task: str) -> bool:
    lower = task.lower()
    return any(
        term in lower
        for term in (
            "build",
            "create",
            "make",
            "mvp",
            "app",
            "website",
            "site",
            "做一个",
            "搭建",
            "开发",
            "网站",
            "应用",
            "小程序",
        )
    )


def choose_intensity(task: str, scenario: str, requested: str = "auto") -> str:
    if requested != "auto":
        if requested not in INTENSITY_PROFILES:
            raise ValueError(f"unknown intensity: {requested}")
        return requested
    lower = task.lower()
    if scenario == "general":
        return "mini"
    if any(term in lower for term in ARCHITECT_TERMS):
        return "architect"
    if scenario in {"coding", "mixed"} and any(term in lower for term in ("mvp", "新项目", "完整")):
        return "architect"
    return "default"


def assess_risk(task: str, scenario: str) -> str:
    lower = task.lower()
    high_terms = (
        "deploy",
        "production",
        "migration",
        "delete",
        "payment",
        "auth",
        "逆向",
        "反编译",
        "部署",
        "生产",
        "迁移",
        "删除",
        "支付",
        "权限",
    )
    if is_reverse_engineering_task(task) or any(term in lower for term in high_terms):
        return "high"
    if scenario in {"coding", "mixed", "research"}:
        return "medium"
    return "low"


def assess_uncertainty(task: str) -> str:
    lower = task.lower()
    vague_terms = (
        "something",
        "stuff",
        "this thing",
        "whatever",
        "make it better",
        "优化一下",
        "搞一下",
        "这个东西",
        "随便",
        "不太清楚",
    )
    if has_ambiguous_external_target(task) or any(term in lower for term in vague_terms):
        return "high"
    if len(task.strip()) < 40:
        return "medium"
    return "low"


def component_suggestions_for(
    task: str,
    scenario: str,
    environment: CodexEnvironment,
) -> tuple[list[str], list[str]]:
    lower = task.lower()
    installed = {name.lower() for name in environment.installed_skills + environment.installed_plugins}
    suggestions: list[str] = []
    missing: list[str] = []

    if scenario in {"coding", "mixed"}:
        suggestions.append("Use project AGENTS guidance, repo-local scripts, and built-in code review before final handoff.")

    if scenario in {"research", "mixed"}:
        suggestions.append("Use live web/source lookup for current facts and cite primary sources in the handbook.")

    if "openai" in lower or "codex" in lower or "plugin" in lower:
        if any("openai-docs" in name for name in installed):
            suggestions.append("Use the installed openai-docs skill for official OpenAI/Codex behavior before making product claims.")
        else:
            missing.append("Search official OpenAI/Codex docs and consider installing an OpenAI-docs helper before relying on product behavior.")

    if any(term in lower for term in ("ui", "frontend", "界面", "前端", "dashboard", "landing", "web app")):
        if any("ui-ux" in name or "ui-styling" in name for name in installed):
            suggestions.append("Use the installed UI/UX styling guidance for layout, responsive states, and accessibility checks.")
        else:
            missing.append("Consider installing a UI/UX or frontend design skill/plugin if the task needs polished interface decisions.")

    if any(term in lower for term in ("image", "banner", "logo", "brand", "视觉", "图片", "海报", "品牌")):
        if any("imagegen" in name or "design" in name or "brand" in name for name in installed):
            suggestions.append("Use installed image/design guidance only for visual assets that the task explicitly needs.")
        else:
            missing.append("Consider a design/image generation component if the deliverable needs visual assets.")

    if is_reverse_engineering_task(task):
        suggestions.append("Use only read-only target identification first; require explicit target path and authorization before deeper analysis.")

    return suggestions[:10], missing[:10]


def blocking_questions_for(task: str, scenario: str, intensity: str, language: str) -> list[BlockingQuestion]:
    profile = INTENSITY_PROFILES[intensity]
    if profile.max_questions <= 0:
        return []
    zh = language in {"zh", "bilingual"}
    questions: list[BlockingQuestion] = []
    if has_ambiguous_external_target(task):
        questions.append(
            BlockingQuestion(
                "target_path_and_authorization",
                "目标确认" if zh else "Target",
                (
                    "请提供要分析对象的绝对路径、文件/应用名、文件类型，并确认你有权分析它。"
                    if zh
                    else "Provide the target's absolute path, file/app name, type, and confirm you are authorized to analyze it."
                ),
                "The target and authorization determine whether any reverse-analysis workflow is allowed.",
                ["提供路径和授权确认", "仅做通用方法说明", "暂停逆向任务"] if zh else ["Provide path and authorization", "General method only", "Pause reverse task"],
            )
        )
    if scenario in {"coding", "mixed"} and looks_like_new_product_task(task):
        questions.append(
            BlockingQuestion(
                "core_user_flow",
                "核心流程" if zh else "Core Flow",
                (
                    "这个版本最核心的用户流程是什么？请用一句话说明用户输入什么、系统处理什么、最终输出什么。"
                    if zh
                    else "What is the core user flow for this version? In one sentence: what does the user input, what does the system process, and what is the final output?"
                ),
                "The core flow determines product scope, UI states, data handling, and acceptance criteria.",
                ["一句话说明核心流程", "由现有文档推断", "先做最小可运行流程"] if zh else ["Describe the core flow", "Infer from docs", "Start with the smallest runnable flow"],
            )
        )
        if any(term in task.lower() for term in ("ai", "简历", "resume", "upload", "上传", "用户", "账号")):
            questions.append(
                BlockingQuestion(
                    "data_and_account_boundary",
                    "数据边界" if zh else "Data Boundary",
                    (
                        "本轮是否需要账号、文件上传/存储、第三方 AI API，还是只做本地/演示版流程？"
                        if zh
                        else "Does this round need accounts, file upload/storage, or a third-party AI API, or should it stay a local/demo flow?"
                    ),
                    "Data, accounts, and AI dependencies change security, privacy, implementation, and verification.",
                    ["本地/演示版", "需要上传/存储", "需要账号或第三方 API"] if zh else ["Local/demo only", "Needs upload/storage", "Needs account or API"],
                )
            )
        questions.append(
            BlockingQuestion(
                "delivery_boundary",
                "交付标准" if zh else "Delivery",
                (
                    "本轮完成标准是可点击原型、可运行 MVP，还是生产可部署版本？"
                    if zh
                    else "Should this round deliver a clickable prototype, runnable MVP, or production-deployable version?"
                ),
                "The delivery level changes implementation depth and validation.",
                ["可运行 MVP", "可点击原型", "生产可部署版本"] if zh else ["Runnable MVP", "Clickable prototype", "Production-deployable"],
            )
        )
    if scenario == "research" and intensity != "mini":
        questions.append(
            BlockingQuestion(
                "research_decision",
                "研究决策" if zh else "Decision",
                (
                    "这次研究最终要支持什么决策？例如选型、市场判断、竞品比较、还是实施方案。"
                    if zh
                    else "What decision should this research support: tool choice, market judgment, competitor comparison, or implementation plan?"
                ),
                "The decision determines source selection and output structure.",
                ["实施方案", "选型判断", "竞品/市场比较"] if zh else ["Implementation plan", "Tool choice", "Market/competitor comparison"],
            )
        )
    if scenario in {"coding", "mixed"} and ("deploy" in task.lower() or "部署" in task):
        questions.append(
            BlockingQuestion(
                "deployment_boundary",
                "部署权限" if zh else "Deploy",
                "本轮是否允许真实部署，还是只准备部署方案和本地验证？" if zh else "Is live deployment allowed, or should this only prepare a deployment plan and local verification?",
                "Deployment permissions change risk, approvals, and verification.",
                ["只准备方案和本地验证", "允许真实部署", "先询问每个部署动作"] if zh else ["Plan and local verify only", "Live deploy allowed", "Ask before each deploy action"],
            )
        )
    return questions[: profile.max_questions]


def context_actions_for(
    task: str,
    scenario: str,
    intensity: str,
    project_context: ProjectContext | None = None,
    codex_environment: CodexEnvironment | None = None,
) -> list[ContextAction]:
    profile = INTENSITY_PROFILES[intensity]
    actions: list[ContextAction] = []
    if not project_context or not project_context.scan_performed:
        actions.append(
            ContextAction(
                "project_execution_index",
                "local_scan",
                "Build a safe project execution index before asking blocking questions.",
            )
        )
    if not codex_environment:
        actions.append(
            ContextAction(
                "codex_component_index",
                "environment",
                "Inspect AGENTS guidance and installed Codex components before asking questions.",
            )
        )
    if scenario in {"research", "mixed"} and profile.allow_fetch:
        actions.append(
            ContextAction(
                "source_map",
                "fetch_plan",
                "Create or perform a source map only when external facts materially change the task.",
                required=False,
            )
        )
    if is_reverse_engineering_task(task) and has_target_path(task):
        actions.append(
            ContextAction(
                "reverse_target_identification",
                "local_inspection",
                "Run read-only target identification such as path, size, file type, hash, and platform metadata.",
            )
        )
    return actions


def artifact_rules_for(language: str) -> list[str]:
    if language in {"zh", "bilingual"}:
        return [
            "三份 Markdown 必须围绕用户任务和项目证据定制写作。",
            "最终产物不得出现 pre-vibe、插件实现、MCP server 或 workflow 内部表述，除非用户任务本身就是开发该工具。",
            "PRE_VIBE_SPEC.md 面向初级用户，是项目 handbook；包含目标、用户场景、范围、需求、验收、边界、风险、建议、组件使用建议和下一步。",
            "PROJECT_AGENTS.md 和 FIRST_PROMPT.md 面向 Codex；只保留执行规则、约束、文件指针、验收标准和必要操作边界。",
            "PROJECT_AGENTS.md 必须参考全局 AGENTS.md；不得加入与全局指令冲突或削弱全局指令的规则。",
            "PRE_VIBE_SPEC.md 与 PROJECT_AGENTS.md 必须彼此独立；任一文件不得出现另一文件的文件名或路径。FIRST_PROMPT.md 可以引用必要文件。",
            "问题必须通过 Codex 原生提问/审批 UI 展示；不得把阻塞问题直接写在普通聊天消息中。",
            "信息不足时先询问或补上下文，不得用模板语言填空。",
        ]
    return [
        "All three Markdown files must be custom-written from the user's task and project evidence.",
        "Final artifacts must not mention pre-vibe, plugin implementation, MCP server, or workflow internals unless the user is building this tool.",
        "PRE_VIBE_SPEC.md is a beginner-friendly project handbook with goal, user scenarios, scope, requirements, acceptance criteria, boundaries, risks, suggestions, component recommendations, and next steps.",
        "PROJECT_AGENTS.md and FIRST_PROMPT.md are agent-facing and should contain only execution rules, constraints, file pointers, acceptance criteria, and necessary operation boundaries.",
        "PROJECT_AGENTS.md must account for global AGENTS.md and must not conflict with or weaken global instructions.",
        "PRE_VIBE_SPEC.md and PROJECT_AGENTS.md must be standalone; neither file may mention the other file's filename or path. FIRST_PROMPT.md may reference necessary files.",
        "Blocking questions must be shown through Codex's native question/approval UI, not as ordinary chat text.",
        "When context is missing, ask or acquire context; never fill gaps with template language.",
    ]


def determine_next_state(
    questions: Iterable[BlockingQuestion],
    actions: Iterable[ContextAction],
    evidence_refs: Iterable[EvidenceRef] | None = None,
) -> str:
    evidence_ids = {evidence.id for evidence in evidence_refs or []}
    for action in actions:
        if action.required and action.id not in evidence_ids:
            return NEEDS_CONTEXT
    if list(questions):
        return NEEDS_USER_INPUT
    return READY_TO_COMPILE


def route_intake(
    task: str,
    project: str | Path = ".",
    *,
    scenario: str = "auto",
    intensity: str = "auto",
    language: str = "auto",
    evidence_refs: Iterable[EvidenceRef] | None = None,
    scan: bool = True,
) -> IntakeDecision:
    selected_scenario = classify_scenario(task, scenario)
    selected_language = choose_language(task, language)
    selected_intensity = choose_intensity(task, selected_scenario, intensity)
    profile = INTENSITY_PROFILES[selected_intensity]
    project_context: ProjectContext | None = None
    if scan and profile.allow_default_scan:
        project_context = safe_walk(Path(project).expanduser().resolve(), profile.max_scanned_files, selected_scenario)
    codex_environment = inspect_codex_environment()
    suggestions, missing_suggestions = component_suggestions_for(
        task,
        selected_scenario,
        codex_environment,
    )
    questions = blocking_questions_for(task, selected_scenario, selected_intensity, selected_language)
    actions = context_actions_for(
        task,
        selected_scenario,
        selected_intensity,
        project_context,
        codex_environment,
    )
    evidence = list(evidence_refs or [])
    evidence_ids = {item.id for item in evidence}
    if project_context and project_context.scan_performed and "project_execution_index" not in evidence_ids:
        evidence.append(
            EvidenceRef(
                "project_execution_index",
                project_context.root,
                f"Scanned {len(project_context.scanned_files)} allowlisted files and {len(project_context.key_dirs)} top-level directories.",
            )
        )
        evidence_ids.add("project_execution_index")
    if codex_environment and "codex_component_index" not in evidence_ids:
        evidence.append(
            EvidenceRef(
                "codex_component_index",
                codex_environment.codex_home or "Codex home",
                f"Indexed {len(codex_environment.installed_plugins)} plugins and {len(codex_environment.installed_skills)} standalone skills.",
            )
        )
    state = determine_next_state(questions, actions, evidence)
    assumptions = []
    if selected_intensity == "mini":
        assumptions.append("Use the smallest useful preparation path unless the user asks for deeper planning.")
    return IntakeDecision(
        raw_input=task,
        scenario=selected_scenario,
        intensity=selected_intensity,
        language=selected_language,
        risk=assess_risk(task, selected_scenario),
        uncertainty=assess_uncertainty(task),
        state=state,
        blocking_questions=questions,
        context_actions=actions,
        assumptions=assumptions,
        artifact_rules=artifact_rules_for(selected_language),
        evidence_refs=evidence,
        project_context=project_context,
        codex_environment=codex_environment,
        component_suggestions=suggestions,
        missing_component_suggestions=missing_suggestions,
    )


def prepare_project_start(
    task: str,
    project: str | Path = ".",
    *,
    scenario: str = "auto",
    intensity: str = "auto",
    language: str = "auto",
    evidence_refs: Iterable[EvidenceRef] | None = None,
    scan: bool = True,
) -> dict[str, object]:
    from pv_compact import compact_decision

    decision = route_intake(
        task,
        project,
        scenario=scenario,
        intensity=intensity,
        language=language,
        evidence_refs=evidence_refs,
        scan=scan,
    )
    return compact_decision(decision)


def can_compile_artifacts(decision: IntakeDecision) -> bool:
    return decision.state == READY_TO_COMPILE
