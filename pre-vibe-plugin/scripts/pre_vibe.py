#!/usr/bin/env python3
"""Generate a budgeted pre-vibe intake package.

pre-vibe v0.1.1 is a context optimizer, not a context expander. It writes
three project-facing Markdown files and keeps the executable prompt compact.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


OUTPUT_SPEC = "PRE-VIBE-SPEC.MD"
OUTPUT_AGENTS = "INIT-AGENTS.MD"
OUTPUT_PROMPT = "FIRST-PROMPT.MD"

SECRET_PATTERNS = (
    ".env",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    "id_rsa",
    "id_ed25519",
    "token",
    "secret",
    "credential",
    "credentials",
    "database.sqlite",
    ".db",
    ".dump",
    ".log",
)

ALLOWLIST_FILENAMES = {
    "README.md",
    "README.zh.md",
    "README.en.md",
    "AGENTS.md",
    "CLAUDE.md",
    "package.json",
    "pnpm-lock.yaml",
    "package-lock.json",
    "yarn.lock",
    "pyproject.toml",
    "requirements.txt",
    "Cargo.toml",
    "go.mod",
    "Makefile",
}

SKIP_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    ".cache",
}


@dataclass(frozen=True)
class BudgetPolicy:
    name: str
    max_questions: int
    max_fetches: int
    max_scanned_files: int
    max_injection_tokens: int
    default_compression: str


BUDGETS = {
    "micro": BudgetPolicy("micro", 0, 0, 0, 800, "terse"),
    "standard": BudgetPolicy("standard", 3, 2, 10, 1800, "balanced"),
    "deep": BudgetPolicy("deep", 6, 5, 30, 3500, "balanced"),
    "architect": BudgetPolicy("architect", 10, 8, 80, 6000, "full"),
}

COMPRESSION_MAX = {
    "terse": 700,
    "balanced": 1500,
    "full": 4000,
}

MODE_ALIASES = {
    "quick": "micro",
}


@dataclass
class ProjectContext:
    root: str
    scanned_files: list[str]
    skipped_secret_like: list[str]
    key_dirs: list[str]
    signals: dict[str, str]
    relevant_pointers: list[str]
    do_not_touch: list[str]
    global_agents_path: str | None
    global_agents_summary: list[str]
    project_agents_path: str | None
    project_agents_summary: list[str]


@dataclass
class QualityScores:
    clarity: int
    specificity: int
    context: int
    completeness: int
    structure: int

    @property
    def overall(self) -> float:
        return round(
            (self.clarity + self.specificity + self.context + self.completeness + self.structure) / 5,
            1,
        )


@dataclass
class IntakeResult:
    task: str
    scenario: str
    complexity: str
    compression: str
    language: str
    agent: str
    benchmark_mode: str
    output_dir: str
    normalized_goal: str
    current_task: str
    quality_scores: QualityScores
    blocking_questions: list[str]
    assumptions: list[str]
    acceptance_criteria: list[str]
    hard_constraints: list[str]
    search_plan: list[str]
    context_completion: list[str]
    tutorial_suggestions: list[str]
    project_context: ProjectContext
    budget: BudgetPolicy
    brief_token_estimate: int
    budget_warnings: list[str]


def normalize_mode(mode: str, scenario: str, task: str) -> str:
    if mode in MODE_ALIASES:
        return MODE_ALIASES[mode]
    if mode != "auto":
        return mode
    lower = task.lower()
    if scenario == "general":
        return "micro"
    if any(word in lower for word in ("architecture", "architect", "系统设计", "重构", "新项目")):
        return "architect"
    if scenario in {"coding", "mixed"} and any(word in lower for word in ("mvp", "plugin", "多文件", "项目", "repo")):
        return "deep"
    return "standard"


def has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def choose_language(task: str, requested: str) -> str:
    if requested != "auto":
        return requested
    return "zh" if has_cjk(task) else "en"


def classify_task(task: str, requested: str) -> str:
    if requested != "auto":
        return requested
    lower = task.lower()
    coding = (
        "code",
        "repo",
        "bug",
        "fix",
        "api",
        "frontend",
        "backend",
        "test",
        "deploy",
        "plugin",
        "mvp",
        "代码",
        "搭建",
        "修复",
        "前端",
        "后端",
        "测试",
        "部署",
    )
    research = (
        "research",
        "compare",
        "sources",
        "paper",
        "market",
        "分析",
        "调研",
        "研究",
        "资料",
        "论文",
        "竞品",
    )
    coding_hit = any(token in lower for token in coding)
    research_hit = any(token in lower for token in research)
    if coding_hit and research_hit:
        return "mixed"
    if coding_hit:
        return "coding"
    if research_hit:
        return "research"
    return "general"


def estimate_tokens(text: str) -> int:
    cjk_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    other_chars = max(len(text) - cjk_chars, 0)
    return max(1, int(cjk_chars / 1.7 + other_chars / 4))


def bullet(items: Iterable[str]) -> str:
    values = list(items)
    return "\n".join(f"- {item}" for item in values) if values else "- None"


def is_secret_like(path: Path) -> bool:
    lowered = path.name.lower()
    full = str(path).lower()
    return any(pattern in lowered or pattern in full for pattern in SECRET_PATTERNS)


def summarize_agents(path: Path | None, max_lines: int = 18) -> list[str]:
    if not path or not path.exists() or is_secret_like(path):
        return []
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line:
            continue
        line = line.lstrip("#").strip()
        if not line:
            continue
        line = re.sub(r"\s+", " ", line)
        lines.append(line[:180])
        if len(lines) >= max_lines:
            break
    return lines


def find_global_agents() -> Path | None:
    candidates: list[Path] = []
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        candidates.append(Path(codex_home) / "AGENTS.md")
    candidates.append(Path.home() / ".codex" / "AGENTS.md")
    for path in candidates:
        if path.exists():
            return path
    return None


def safe_walk(root: Path, max_files: int, scenario: str) -> ProjectContext:
    scanned: list[str] = []
    skipped: list[str] = []
    dirs: list[str] = []
    signals: dict[str, str] = {}
    pointers: list[str] = []
    do_not_touch: list[str] = []
    global_agents = find_global_agents()
    project_agents = root / "AGENTS.md"

    if not root.exists():
        return ProjectContext(
            str(root),
            [],
            [],
            [],
            {"warning": "project root not found"},
            [],
            [],
            str(global_agents) if global_agents else None,
            summarize_agents(global_agents),
            None,
            [],
        )

    if max_files <= 0:
        return ProjectContext(
            str(root),
            [],
            [],
            [],
            {"scan": "skipped by micro budget"},
            [],
            ["secret files", "generated files", "vendor/dependency directories"],
            str(global_agents) if global_agents else None,
            summarize_agents(global_agents),
            str(project_agents) if project_agents.exists() else None,
            summarize_agents(project_agents if project_agents.exists() else None),
        )

    for entry in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if entry.name in SKIP_DIRS:
            do_not_touch.append(entry.name + "/")
            continue
        if is_secret_like(entry):
            skipped.append(entry.name)
            do_not_touch.append(entry.name)
            continue
        if entry.is_dir():
            dirs.append(entry.name)
            if entry.name in {"src", "app", "lib", "tests", "test", "docs", "components", "pre-vibe-plugin"}:
                signals[f"dir:{entry.name}"] = "present"
                pointers.append(f"{entry.name}/ - likely relevant directory")
            continue
        if entry.name in ALLOWLIST_FILENAMES or entry.suffix in {".md", ".toml", ".json"}:
            scanned.append(entry.name)
            if entry.name == "package.json":
                signals["stack"] = "JavaScript/TypeScript project signal"
                pointers.append("package.json - scripts and dependencies")
            elif entry.name == "pyproject.toml":
                signals["stack"] = "Python project signal"
                pointers.append("pyproject.toml - Python package metadata")
            elif entry.name == "AGENTS.md":
                signals["agents_guidance"] = "project AGENTS.md present"
                pointers.append("AGENTS.md - project agent guidance")
            elif entry.name == "CLAUDE.md":
                signals["claude_memory"] = "CLAUDE.md present"
                pointers.append("CLAUDE.md - Claude Code memory")
            elif entry.name.lower().startswith("readme"):
                pointers.append(f"{entry.name} - project overview")
            elif scenario in {"coding", "mixed"} and "prd" in entry.name.lower():
                pointers.append(f"{entry.name} - product requirements")
        if len(scanned) >= max_files:
            signals["scan_limit"] = f"stopped after {max_files} files"
            break

    return ProjectContext(
        str(root),
        scanned,
        skipped,
        dirs[:40],
        signals,
        pointers[:12],
        do_not_touch[:12],
        str(global_agents) if global_agents else None,
        summarize_agents(global_agents),
        str(project_agents) if project_agents.exists() else None,
        summarize_agents(project_agents if project_agents.exists() else None),
    )


def evaluate_prompt_quality(task: str, language: str) -> QualityScores:
    lower = task.lower()
    words = re.findall(r"\w+", task)
    cjk = has_cjk(task)
    clarity = 5
    specificity = 5
    context = 5
    completeness = 5
    structure = 5

    vague = ("thing", "stuff", "something", "随便", "一些", "东西", "优化一下", "搞一下")
    if any(term in lower for term in vague):
        clarity -= 2
    if any(term in lower for term in ("what", "how", "why", "build", "fix", "create", "生成", "搭建", "修复", "调研")):
        clarity += 2

    word_count = len(words) + len(re.findall(r"[\u4e00-\u9fff]", task)) // 2
    if word_count < 8:
        specificity -= 2
    elif word_count > 18:
        specificity += 1
    if any(char.isdigit() for char in task):
        specificity += 1

    if any(term in lower for term in ("because", "for", "context", "prd", "based on", "根据", "为了", "背景")):
        context += 2
    else:
        context -= 1

    if any(term in lower for term in ("report", "plan", "test", "markdown", "json", "报告", "计划", "测试", "文档")):
        completeness += 1
    if any(term in lower for term in ("must", "avoid", "不能", "必须", "不要", "要求")):
        completeness += 1

    if "\n" in task or ":" in task or "：" in task or any(mark in task for mark in ("1.", "①", "- ")):
        structure += 2
    elif word_count < 12:
        structure -= 1

    return QualityScores(
        max(0, min(10, clarity)),
        max(0, min(10, specificity)),
        max(0, min(10, context)),
        max(0, min(10, completeness)),
        max(0, min(10, structure)),
    )


def normalize_goal(task: str, scenario: str, language: str) -> str:
    if language in {"zh", "bilingual"}:
        return f"把原始需求压缩成适合 agent 开始工作的最小必要上下文，场景为 {scenario}。"
    return f"Compress the raw request into the minimum useful first-turn context for a {scenario} agent workflow."


def current_task_for(task: str, scenario: str, language: str) -> str:
    if language in {"zh", "bilingual"}:
        if scenario == "general":
            return "直接交付用户要的最终文本或操作方案，不做项目扫描。"
        if scenario == "research":
            return "先明确研究问题、证据要求和 source map，再按需检索。"
        if scenario == "coding":
            return "先读取少量相关文件并提出计划，再执行最小安全改动。"
        return "先澄清本轮交付物和必要上下文，再进入执行。"
    if scenario == "general":
        return "Deliver the requested text or action plan directly without project scanning."
    if scenario == "research":
        return "Define research questions, evidence rules, and source map before reading sources."
    if scenario == "coding":
        return "Read a small set of relevant files, propose a plan, then make the smallest safe change."
    return "Clarify the deliverable and minimum useful context before execution."


def blocking_questions_for(scenario: str, language: str, budget: BudgetPolicy) -> list[str]:
    if budget.max_questions <= 0:
        return []
    zh = language in {"zh", "bilingual"}
    bank = {
        "general": [
            ("最终交付格式是否必须是表格、邮件、清单或正式文档？", "Must the final deliverable be a table, email, checklist, or formal document?"),
            ("是否有不可违反的语气、截止时间或受众限制？", "Are there non-negotiable tone, deadline, or audience constraints?"),
        ],
        "research": [
            ("这项研究要支持什么具体决策？", "What concrete decision should this research support?"),
            ("是否必须只使用官方/一手来源？", "Must the answer use only official or primary sources?"),
            ("是否需要当前最新信息？", "Does the answer require current information?"),
        ],
        "coding": [
            ("本轮是否允许修改文件，还是只生成计划？", "Is this run allowed to edit files, or should it only produce a plan?"),
            ("哪些验证命令或人工检查必须通过？", "Which verification commands or manual checks must pass?"),
            ("有没有明确禁止触碰的目录、数据或接口？", "Are any directories, data, or APIs explicitly off limits?"),
        ],
        "mixed": [
            ("需要先研究再执行，还是只补齐背景后直接执行？", "Should the agent research first, or only fill context gaps before execution?"),
            ("最终验收标准是什么？", "What acceptance criteria define success?"),
            ("是否涉及不可逆或高风险操作？", "Does the task involve irreversible or high-risk actions?"),
        ],
    }
    return [q[0] if zh else q[1] for q in bank.get(scenario, bank["general"])[: budget.max_questions]]


def assumptions_for(scenario: str, language: str, benchmark_mode: str) -> list[str]:
    if language in {"zh", "bilingual"}:
        assumptions = [
            "非阻塞未知项默认写入假设，不通过追问消耗上下文。",
            "完整 spec 只作为 handbook，不进入正式执行上下文。",
            "正式执行只注入 FIRST-PROMPT.MD 中的精简 brief。",
        ]
        if benchmark_mode == "final-answer-only":
            assumptions.append("本次为 benchmark 模式，agent 不修改文件，只在最终回答中交付。")
        if scenario == "coding":
            assumptions.append("默认不读取 secret 文件，不触碰生成物和依赖目录。")
        if scenario == "research":
            assumptions.append("外部事实需要按 source map 逐项验证，不把长引用摘要注入首轮。")
        return assumptions
    assumptions = [
        "Non-blocking unknowns become assumptions instead of clarification turns.",
        "The full spec is a handbook and is not injected into the execution context.",
        "Formal execution injects only the compact brief in FIRST-PROMPT.MD.",
    ]
    if benchmark_mode == "final-answer-only":
        assumptions.append("Benchmark mode: do not edit files; deliver in the final answer only.")
    if scenario == "coding":
        assumptions.append("Secret files, generated artifacts, and dependency directories are off limits by default.")
    if scenario == "research":
        assumptions.append("External facts should be verified via the source map; long source summaries stay out of first prompt.")
    return assumptions


def constraints_for(scenario: str, language: str, benchmark_mode: str) -> list[str]:
    if language in {"zh", "bilingual"}:
        constraints = [
            "不要把 PRE-VIBE-SPEC.MD 全文复制进正式 workflow。",
            "不要读取 `.env`、私钥、token、数据库 dump 或生产日志。",
            "只问会改变执行路径的 blocking questions。",
        ]
        if benchmark_mode == "final-answer-only":
            constraints.append("不要写文件；只在最终回答中交付。")
        if scenario == "coding":
            constraints.append("先读最少相关文件，再提出计划；不要总结整个仓库。")
        if scenario == "research":
            constraints.append("只在回答具体研究问题时读取对应来源。")
        return constraints
    constraints = [
        "Do not paste the full PRE-VIBE-SPEC.MD into the formal workflow.",
        "Do not read `.env`, private keys, tokens, database dumps, or production logs.",
        "Ask only blocking questions that would change execution.",
    ]
    if benchmark_mode == "final-answer-only":
        constraints.append("Do not write files; deliver in the final answer only.")
    if scenario == "coding":
        constraints.append("Read the smallest relevant file set before planning; do not summarize the whole repo.")
    if scenario == "research":
        constraints.append("Open sources only when answering a specific research question.")
    return constraints


def acceptance_for(scenario: str, language: str) -> list[str]:
    if language in {"zh", "bilingual"}:
        base = [
            "目标、当前任务、硬约束、关键假设和完成标准清楚。",
            "正式执行上下文不包含完整 spec 或长背景。",
            "下一步操作需要用户批准 `/clear` 和注入 FIRST-PROMPT.MD。",
        ]
        if scenario == "coding":
            base.append("包含少量相关文件指针、禁止触碰区域和验证建议。")
        if scenario == "research":
            base.append("包含研究问题、source map 和证据要求。")
        return base
    base = [
        "Goal, current task, hard constraints, assumptions, and done-when criteria are clear.",
        "Formal execution context excludes the full spec and long background.",
        "Next step requires user approval for `/clear` and FIRST-PROMPT.MD injection.",
    ]
    if scenario == "coding":
        base.append("Include relevant file pointers, do-not-touch areas, and verification hints.")
    if scenario == "research":
        base.append("Include research questions, source map, and evidence requirements.")
    return base


def search_plan_for(scenario: str, language: str, budget: BudgetPolicy) -> list[str]:
    if budget.max_fetches <= 0:
        return []
    if language in {"zh", "bilingual"}:
        if scenario == "research":
            return [
                "优先检索官方文档、一手 repo、release notes 或论文；记录访问日期。",
                "只把 source map 写入 FIRST-PROMPT.MD，不注入长摘要。",
                f"最多处理 {budget.max_fetches} 个来源，超出部分进入 backlog。",
            ]
        if scenario == "coding":
            return [
                "只有 API/依赖版本不确定且会阻塞实现时才搜索。",
                "优先官方文档；不要默认搜索普通教程。",
            ]
        return ["仅当当前事实会改变最终交付时才搜索。"]
    if scenario == "research":
        return [
            "Prefer official docs, primary repos, release notes, or papers; record access dates.",
            "Put only a source map in FIRST-PROMPT.MD; keep long summaries out.",
            f"Process at most {budget.max_fetches} sources; backlog the rest.",
        ]
    if scenario == "coding":
        return [
            "Search only when API/dependency uncertainty blocks implementation.",
            "Prefer official docs; do not default to tutorials.",
        ]
    return ["Search only when current facts would change the final deliverable."]


def context_completion_for(result_language: str, ctx: ProjectContext) -> list[str]:
    if result_language in {"zh", "bilingual"}:
        items = []
        if ctx.global_agents_path:
            items.append(f"已参考全局 AGENTS: {ctx.global_agents_path}")
        else:
            items.append("未发现 Codex 全局 AGENTS.md；INIT-AGENTS.MD 将只生成项目级建议。")
        if ctx.project_agents_path:
            items.append(f"已发现项目 AGENTS: {ctx.project_agents_path}，建议人工合并而非覆盖。")
        if ctx.skipped_secret_like:
            items.append("发现 secret-like 文件并已跳过。")
        return items
    items = []
    if ctx.global_agents_path:
        items.append(f"Global AGENTS consulted: {ctx.global_agents_path}")
    else:
        items.append("No Codex global AGENTS.md found; INIT-AGENTS.MD contains project guidance only.")
    if ctx.project_agents_path:
        items.append(f"Project AGENTS found: {ctx.project_agents_path}; merge manually instead of overwriting blindly.")
    if ctx.skipped_secret_like:
        items.append("Secret-like files were detected and skipped.")
    return items


def tutorial_suggestions(scenario: str, language: str) -> list[str]:
    if language in {"zh", "bilingual"}:
        tips = [
            "把 handbook、项目规则和正式注入 prompt 分开。",
            "用文件/source 指针替代长摘要。",
            "如果 FIRST-PROMPT 超预算，先删 rationale 和例子。",
        ]
        if scenario == "general":
            tips.append("日常事务默认不要扫描项目。")
        if scenario == "research":
            tips.append("研究任务默认生成检索计划，不预先塞入长引用摘要。")
        if scenario == "coding":
            tips.append("coding 任务首轮只告诉 agent 第一批该读哪些文件。")
        return tips
    tips = [
        "Separate handbook, durable agent guidance, and executable prompt.",
        "Use file/source pointers instead of long summaries.",
        "If FIRST-PROMPT exceeds budget, remove rationale and examples first.",
    ]
    if scenario == "general":
        tips.append("General tasks should skip project scanning by default.")
    if scenario == "research":
        tips.append("Research tasks should create a search plan, not inject long source summaries.")
    if scenario == "coding":
        tips.append("Coding first prompts should tell the agent which files to read first.")
    return tips


def build_result(args: argparse.Namespace) -> IntakeResult:
    language = choose_language(args.task, args.language)
    scenario = classify_task(args.task, args.scenario)
    complexity = normalize_mode(args.mode, scenario, args.task)
    budget = BUDGETS[complexity]
    requested_compression = getattr(args, "compression", "auto")
    benchmark_mode = getattr(args, "benchmark_mode", "execution")
    compression = budget.default_compression if requested_compression == "auto" else requested_compression
    quality = evaluate_prompt_quality(args.task, language)
    ctx = safe_walk(Path(args.project).resolve(), budget.max_scanned_files, scenario)
    result = IntakeResult(
        task=args.task,
        scenario=scenario,
        complexity=complexity,
        compression=compression,
        language=language,
        agent=args.agent,
        benchmark_mode=benchmark_mode,
        output_dir=str(Path(args.output_dir).resolve()),
        normalized_goal=normalize_goal(args.task, scenario, language),
        current_task=current_task_for(args.task, scenario, language),
        quality_scores=quality,
        blocking_questions=blocking_questions_for(scenario, language, budget),
        assumptions=assumptions_for(scenario, language, benchmark_mode),
        acceptance_criteria=acceptance_for(scenario, language),
        hard_constraints=constraints_for(scenario, language, benchmark_mode),
        search_plan=search_plan_for(scenario, language, budget),
        context_completion=[],
        tutorial_suggestions=tutorial_suggestions(scenario, language),
        project_context=ctx,
        budget=budget,
        brief_token_estimate=0,
        budget_warnings=[],
    )
    result.context_completion = context_completion_for(language, ctx)
    brief = build_first_prompt(result)
    result.brief_token_estimate = estimate_tokens(brief)
    result.budget_warnings = budget_warnings(result, brief)
    return result


def budget_warnings(result: IntakeResult, brief: str) -> list[str]:
    warnings: list[str] = []
    max_tokens = min(result.budget.max_injection_tokens, COMPRESSION_MAX[result.compression])
    actual = estimate_tokens(brief)
    if actual > max_tokens:
        warnings.append(f"FIRST-PROMPT estimate {actual} exceeds {max_tokens}; narrow scope before injection.")
    if result.complexity == "micro" and result.project_context.scanned_files:
        warnings.append("micro mode should not scan files.")
    return warnings


def heading(language: str, zh: str, en: str) -> str:
    if language == "en":
        return en
    if language == "bilingual":
        return f"{zh} / {en}"
    return zh


def build_spec(result: IntakeResult) -> str:
    lang = result.language
    ctx = result.project_context
    spec_path = Path(result.output_dir) / OUTPUT_SPEC
    if lang in {"zh", "bilingual"}:
        replace = (
            f"> 路径指引：本文件是 handbook，建议保存在 `{spec_path}`。"
            f"不要把本文件全文复制进正式 workflow；正式执行只注入 `{OUTPUT_PROMPT}`。"
        )
    else:
        replace = (
            f"> Path guide: keep this handbook at `{spec_path}`. "
            f"Do not paste the full file into the formal workflow; inject only `{OUTPUT_PROMPT}`."
        )
    return f"""# {OUTPUT_SPEC}
{replace}

## 0. {heading(lang, "任务路由", "Task Routing")}
- Scenario: {result.scenario}
- Complexity: {result.complexity}
- Compression: {result.compression}
- Target agent: {result.agent}
- Budget: max_questions={result.budget.max_questions}, max_scan={result.budget.max_scanned_files}, max_fetch={result.budget.max_fetches}, max_injection_tokens={result.budget.max_injection_tokens}
- Brief token estimate: {result.brief_token_estimate}
- Quality score: {result.quality_scores.overall}/10

## 1. {heading(lang, "原始输入", "Raw User Input")}
> {result.task}

## 2. {heading(lang, "标准化目标", "Normalized Goal")}
{result.normalized_goal}

## 3. {heading(lang, "当前任务", "Current Task")}
{result.current_task}

## 4. {heading(lang, "Blocking Questions", "Blocking Questions")}
{bullet(result.blocking_questions)}

## 5. {heading(lang, "假设", "Assumptions")}
{bullet(result.assumptions)}

## 6. {heading(lang, "硬约束", "Hard Constraints")}
{bullet(result.hard_constraints)}

## 7. {heading(lang, "Context Index", "Context Index")}
- Project root: `{ctx.root}`
- Relevant pointers:
{bullet(ctx.relevant_pointers)}
- Do not touch:
{bullet(ctx.do_not_touch)}
- Scanned files: {", ".join(ctx.scanned_files) if ctx.scanned_files else "None"}
- Skipped secret-like files: {", ".join(ctx.skipped_secret_like) if ctx.skipped_secret_like else "None"}
- Signals: {json.dumps(ctx.signals, ensure_ascii=False)}

## 8. {heading(lang, "拓展搜索计划", "Extended Search Plan")}
{bullet(result.search_plan)}

## 9. {heading(lang, "上下文补全", "Context Completion")}
{bullet(result.context_completion)}

## 10. {heading(lang, "完成标准", "Done When")}
{bullet(result.acceptance_criteria)}

## 11. {heading(lang, "Token Discipline Notes", "Token Discipline Notes")}
{bullet(result.tutorial_suggestions)}

## 12. {heading(lang, "预算警告", "Budget Warnings")}
{bullet(result.budget_warnings)}
"""


def build_agents(result: IntakeResult) -> str:
    lang = result.language
    ctx = result.project_context
    project_path = str(Path(ctx.root) / "AGENTS.md")
    if lang in {"zh", "bilingual"}:
        replace = (
            f"> 替换路径指引：人工确认后，可复制本文件内容到项目级 `{project_path}`。"
            "不要覆盖 Codex 全局 AGENTS；本文件只补充项目级规则。"
        )
        global_label = "全局 AGENTS 摘要"
        project_label = "现有项目 AGENTS 摘要"
        no_global = "全局 AGENTS.md 不存在或没有可摘要的规则。"
        durable = [
            "正式执行前先给出短计划。",
            "不要默认读取 secret 文件、生产日志、数据库 dump 或 token cache。",
            f"pre-vibe 只注入 `{OUTPUT_PROMPT}`，不要注入 `{OUTPUT_SPEC}` 全文。",
            "遇到非阻塞未知项，用假设继续；只问 blocking questions。",
            "完成后报告修改/产物、验证结果、剩余风险。",
        ]
    else:
        replace = (
            f"> Replacement guide: after review, copy this file into project-level `{project_path}`. "
            "Do not overwrite global Codex AGENTS; this file only adds project guidance."
        )
        global_label = "Global AGENTS Summary"
        project_label = "Existing Project AGENTS Summary"
        no_global = "Global AGENTS.md not found or has no summarizable rules."
        durable = [
            "Propose a short plan before formal execution.",
            "Do not read secret files, production logs, database dumps, or token caches by default.",
            f"pre-vibe injects only `{OUTPUT_PROMPT}`; do not inject the full `{OUTPUT_SPEC}`.",
            "Continue with assumptions for non-blocking unknowns; ask only blocking questions.",
            "Report deliverables/changes, verification results, and remaining risks.",
        ]
    return f"""# {OUTPUT_AGENTS}
{replace}

## {global_label}
- Source: `{ctx.global_agents_path or "not found"}`
{bullet(ctx.global_agents_summary or [no_global])}

## {project_label}
- Source: `{ctx.project_agents_path or "not found"}`
{bullet(ctx.project_agents_summary or ["No existing project AGENTS.md found."])}

## Conflict Policy
- Global/personal Codex instructions remain higher priority than this generated project guidance.
- Do not add rules that contradict security, sandbox, approval, or tool-use instructions.
- Keep one-off task details in `{OUTPUT_SPEC}`, not in project-level AGENTS.

## Durable Project Guidance
{bullet(durable)}
"""


def first_prompt_lines(result: IntakeResult, terse: bool = False) -> list[str]:
    lang = result.language
    ctx = result.project_context
    spec_path = Path(result.output_dir) / OUTPUT_SPEC
    agents_path = Path(result.output_dir) / OUTPUT_AGENTS
    if lang in {"zh", "bilingual"}:
        lines = [
            f"# {OUTPUT_PROMPT}",
            f"> 注入路径指引：用户批准后执行 `/clear`，然后只把本文件作为新 session 的初始上下文注入。不要注入 `{OUTPUT_SPEC}` 全文。",
            "",
            "## Goal",
            result.normalized_goal,
            "",
            "## Current Task",
            result.current_task,
            "",
            "## Hard Constraints",
            bullet(result.hard_constraints[:5 if terse else 7]),
            "",
            "## Key Assumptions",
            bullet(result.assumptions[:3 if terse else 5]),
            "",
            "## Relevant Context",
            f"- Handbook: `{spec_path}` (read only if needed)",
            f"- Suggested project AGENTS: `{agents_path}` (user may review/copy manually)",
        ]
        if ctx.relevant_pointers:
            lines.extend(f"- {item}" for item in ctx.relevant_pointers[:4 if terse else 8])
        if result.search_plan and not terse:
            lines.extend(["", "## Search Policy", bullet(result.search_plan[:3])])
        lines.extend(
            [
                "",
                "## Done When",
                bullet(result.acceptance_criteria[:4 if terse else 6]),
                "",
                "## Operating Mode",
                "Start with a short plan. Do not read unrelated files. Ask only blocking questions. Prefer the smallest safe next action.",
            ]
        )
        return lines
    lines = [
        f"# {OUTPUT_PROMPT}",
        f"> Injection guide: after user approval, run `/clear`, then inject only this file as the initial context. Do not inject the full `{OUTPUT_SPEC}`.",
        "",
        "## Goal",
        result.normalized_goal,
        "",
        "## Current Task",
        result.current_task,
        "",
        "## Hard Constraints",
        bullet(result.hard_constraints[:5 if terse else 7]),
        "",
        "## Key Assumptions",
        bullet(result.assumptions[:3 if terse else 5]),
        "",
        "## Relevant Context",
        f"- Handbook: `{spec_path}` (read only if needed)",
        f"- Suggested project AGENTS: `{agents_path}` (user may review/copy manually)",
    ]
    if ctx.relevant_pointers:
        lines.extend(f"- {item}" for item in ctx.relevant_pointers[:4 if terse else 8])
    if result.search_plan and not terse:
        lines.extend(["", "## Search Policy", bullet(result.search_plan[:3])])
    lines.extend(
        [
            "",
            "## Done When",
            bullet(result.acceptance_criteria[:4 if terse else 6]),
            "",
            "## Operating Mode",
            "Start with a short plan. Do not read unrelated files. Ask only blocking questions. Prefer the smallest safe next action.",
        ]
    )
    return lines


def build_first_prompt(result: IntakeResult) -> str:
    strict_limit = min(result.budget.max_injection_tokens, COMPRESSION_MAX[result.compression])
    text = "\n".join(first_prompt_lines(result, terse=result.compression == "terse")) + "\n"
    if estimate_tokens(text) <= strict_limit:
        return text
    text = "\n".join(first_prompt_lines(result, terse=True)) + "\n"
    if estimate_tokens(text) <= strict_limit:
        return text
    lines = first_prompt_lines(result, terse=True)
    compressed = []
    skip_sections = {"## Search Policy"}
    skipping = False
    for line in lines:
        if line in skip_sections:
            skipping = True
            continue
        if skipping and line.startswith("## "):
            skipping = False
        if not skipping:
            compressed.append(line)
    return "\n".join(compressed) + "\n"


def write_outputs(result: IntakeResult, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    result.output_dir = str(output_dir.resolve())
    brief = build_first_prompt(result)
    result.brief_token_estimate = estimate_tokens(brief)
    result.budget_warnings = budget_warnings(result, brief)
    files = {
        "spec": output_dir / OUTPUT_SPEC,
        "agents": output_dir / OUTPUT_AGENTS,
        "prompt": output_dir / OUTPUT_PROMPT,
    }
    files["spec"].write_text(build_spec(result), encoding="utf-8")
    files["agents"].write_text(build_agents(result), encoding="utf-8")
    files["prompt"].write_text(brief, encoding="utf-8")
    return files


def build_handoff(result: IntakeResult, files: dict[str, Path]) -> str:
    if result.language in {"zh", "bilingual"}:
        return "\n".join(
            [
                "",
                "NEXT STEP",
                f"1. 请用户查看/修改 `{files['spec']}` 和 `{files['agents']}`。",
                "2. 询问用户：是否批准执行 `/clear` 并将 FIRST-PROMPT.MD 作为新 session 初始上下文注入？",
                f"3. 用户批准后，只注入 `{files['prompt']}`，不要注入完整 spec。",
                f"4. FIRST-PROMPT token estimate: {result.brief_token_estimate}; budget: {result.budget.max_injection_tokens}.",
            ]
        )
    return "\n".join(
        [
            "",
            "NEXT STEP",
            f"1. Ask the user to review/edit `{files['spec']}` and `{files['agents']}`.",
            "2. Ask for approval to run `/clear` and inject FIRST-PROMPT.MD as the new session's initial context.",
            f"3. After approval, inject only `{files['prompt']}`, not the full spec.",
            f"4. FIRST-PROMPT token estimate: {result.brief_token_estimate}; budget: {result.budget.max_injection_tokens}.",
        ]
    )


def run_interactive_handoff(result: IntakeResult, files: dict[str, Path]) -> None:
    print(build_handoff(result, files))
    answer = input("\nApprove /clear and FIRST-PROMPT.MD injection? [y/N] ").strip().lower()
    if answer not in {"y", "yes"}:
        print("Not approved. Review or edit the generated Markdown files before starting the formal workflow.")
        return
    print("\nAPPROVED: run /clear in the conversation UI, then inject the following FIRST-PROMPT.MD content.")
    print("\n--- FIRST-PROMPT.MD START ---")
    print(files["prompt"].read_text(encoding="utf-8"))
    print("--- FIRST-PROMPT.MD END ---")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a budgeted pre-vibe context intake package.")
    parser.add_argument("--task", required=True, help="Raw user task.")
    parser.add_argument("--project", default=".", help="Project or workspace root to scan safely.")
    parser.add_argument("--agent", default="codex", choices=("codex", "claude-code", "generic"))
    parser.add_argument(
        "--mode",
        default="auto",
        choices=("auto", "quick", "micro", "standard", "deep", "architect"),
        help="Context budget mode. quick is a compatibility alias for micro.",
    )
    parser.add_argument("--scenario", default="auto", choices=("auto", "general", "research", "coding", "mixed"))
    parser.add_argument("--compression", default="auto", choices=("auto", "terse", "balanced", "full"))
    parser.add_argument("--language", default="auto", choices=("auto", "zh", "en", "bilingual"))
    parser.add_argument(
        "--benchmark-mode",
        default="execution",
        choices=("execution", "final-answer-only"),
        help="Use final-answer-only for fair token tests that must not edit files.",
    )
    parser.add_argument("--output-dir", default=".", help="Directory where the three uppercase Markdown files are written.")
    parser.add_argument("--interactive", action="store_true", help="Ask for /clear and FIRST-PROMPT.MD injection approval.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable result metadata.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_result(args)
    files = write_outputs(result, Path(args.output_dir))
    if args.json:
        payload = {
            "result": asdict(result),
            "files": {key: str(path) for key, path in files.items()},
            "handoff": build_handoff(result, files),
        }
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"pre-vibe generated 3 Markdown files in {Path(args.output_dir).resolve()}")
        for label, path in files.items():
            print(f"- {label}: {path}")
        if args.interactive:
            run_interactive_handoff(result, files)
        else:
            print(build_handoff(result, files))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
