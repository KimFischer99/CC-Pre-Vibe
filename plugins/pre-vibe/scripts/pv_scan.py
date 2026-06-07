"""Safe project and local component scanning helpers."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Iterable

from pv_models import AgentInstructionRef, ExistingContext, ProjectContext


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
    ".sqlite",
    ".db",
    ".dump",
    ".log",
)

ALLOWLIST_FILENAMES = {
    "README.md",
    "README.zh.md",
    "README.en.md",
    "AGENTS.md",
    "PROJECT_AGENTS.md",
    "FIRST_PROMPT.md",
    "PROJECT_INDEX.md",
    "AGENT.md",
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

ALLOWLIST_SUFFIXES = {
    ".md",
    ".toml",
    ".json",
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
    claude_home = os.environ.get("CLAUDE_HOME")
    if claude_home:
        candidates.append(Path(claude_home) / "AGENTS.md")
    candidates.append(Path.home() / ".claude" / "AGENTS.md")
    for path in candidates:
        if path.exists():
            return path
    return None


def relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def detect_existing_context(root: Path) -> ExistingContext:
    required = [
        "PRE_VIBE_SPEC.md",
        "FIRST_PROMPT.md",
    ]
    agent_options = ["PROJECT_AGENTS.md", "AGENTS.md"]
    optional = ["AGENT.md", "PROJECT_INDEX.md"]
    existing = [name for name in required + agent_options + optional if (root / name).exists()]
    for entry in sorted(root.iterdir(), key=lambda path: path.name.lower()) if root.exists() else []:
        lowered = entry.name.lower()
        if entry.is_file() and entry.suffix.lower() == ".md" and any(
            marker in lowered for marker in ("prd", "architecture", "review", "modification", "audit")
        ):
            existing.append(entry.name)
    has_required_context = any((root / name).exists() for name in required)
    has_project_agents_handoff = (root / "PROJECT_AGENTS.md").exists()
    has_agent_handoff = has_project_agents_handoff or (
        has_required_context and (root / "AGENTS.md").exists()
    )
    missing = [name for name in required if not (root / name).exists()]
    if not has_agent_handoff:
        missing.append("AGENTS.md or PROJECT_AGENTS.md")
    required_count = len([name for name in required if name in existing])
    has_all = not missing
    has_partial = 0 < (required_count + int(has_agent_handoff)) < len(required) + 1
    if has_all:
        action = "reuse_update_or_compare"
        options = [
            "Reuse and update existing context",
            "Regenerate from current request",
            "Compare old context before deciding",
        ]
    elif has_partial:
        action = "complete_missing_context"
        options = [
            "Complete missing starting documents",
            "Regenerate all starting documents",
            "Compare existing files before deciding",
        ]
    else:
        action = "create_new_context"
        options = []
    return ExistingContext(
        existing_files=existing,
        missing_files=missing,
        has_pre_vibe_docs=has_all,
        has_partial_pre_vibe_docs=has_partial,
        recommended_action=action,
        recovery_options=options,
    )


def detect_git_state(root: Path) -> str:
    if not (root / ".git").exists():
        return "not_git_repo"
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    if result.returncode != 0:
        return "unknown"
    return "dirty" if result.stdout.strip() else "clean"


def detect_agent_instruction_map(root: Path, max_nested: int = 24) -> list[AgentInstructionRef]:
    refs: list[AgentInstructionRef] = []
    seen: set[str] = set()

    def add(path: Path, kind: str, priority: str) -> None:
        rel = relative_path(path, root)
        if rel in seen:
            return
        seen.add(rel)
        scope = "." if path.parent == root else relative_path(path.parent, root)
        refs.append(AgentInstructionRef(rel, scope, priority, kind))

    for name, kind, priority in (
        ("AGENTS.md", "agents", "root"),
        ("AGENT.md", "legacy_agents", "legacy"),
        ("CLAUDE.md", "claude_memory", "tool_specific"),
        (".github/copilot-instructions.md", "copilot", "tool_specific"),
    ):
        path = root / name
        if path.exists() and not is_secret_like(path):
            add(path, kind, priority)

    cursor_rules = root / ".cursor" / "rules"
    if cursor_rules.exists() and not is_secret_like(cursor_rules):
        add(cursor_rules, "cursor_rules", "tool_specific")

    for path in sorted(root.glob("*/AGENTS.md"), key=lambda p: str(p).lower()):
        if len(refs) >= max_nested:
            break
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not is_secret_like(path):
            add(path, "agents", "nearest-wins")
    return refs


def safe_walk(
    root: Path,
    max_files: int,
    scenario: str,
    skip_reason: str = "scan skipped by intensity profile",
) -> ProjectContext:
    scanned: list[str] = []
    skipped: list[str] = []
    dirs: list[str] = []
    signals: dict[str, str] = {}
    pointers: list[str] = []
    do_not_touch: list[str] = []
    global_agents = find_global_agents()
    project_agents = root / "AGENTS.md"
    existing_context = detect_existing_context(root)
    agent_map = detect_agent_instruction_map(root)
    git_state = detect_git_state(root)

    if not root.exists():
        return ProjectContext(
            str(root),
            False,
            "project root missing",
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
            [],
            existing_context,
            git_state,
        )

    if max_files <= 0:
        return ProjectContext(
            str(root),
            False,
            skip_reason,
            [],
            [],
            [],
            {"scan": skip_reason},
            [],
            ["secret files", "generated files", "vendor/dependency directories"],
            str(global_agents) if global_agents else None,
            summarize_agents(global_agents),
            str(project_agents) if project_agents.exists() else None,
            summarize_agents(project_agents if project_agents.exists() else None),
            agent_map,
            existing_context,
            git_state,
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
            if entry.name in {"src", "app", "lib", "tests", "test", "docs", "components", ".claude"}:
                signals[f"dir:{entry.name}"] = "present"
                pointers.append(f"{entry.name}/ - inspect only if the task points there")
            continue
        if entry.name in ALLOWLIST_FILENAMES or entry.suffix in ALLOWLIST_SUFFIXES:
            scanned.append(entry.name)
            if entry.name == "package.json":
                signals["stack"] = "JavaScript/TypeScript"
                pointers.append("package.json - scripts and dependencies")
            elif entry.name == "pyproject.toml":
                signals["stack"] = "Python"
                pointers.append("pyproject.toml - Python package metadata")
            elif entry.name == "AGENTS.md":
                signals["agents_guidance"] = "project AGENTS.md present"
                pointers.append("AGENTS.md - project agent guidance")
            elif entry.name == "CLAUDE.md":
                signals["claude_memory"] = "CLAUDE.md present"
                pointers.append("CLAUDE.md - Claude Code memory")
            elif entry.name.lower().startswith("readme"):
                pointers.append(f"{entry.name} - project overview")
            elif "prd" in entry.name.lower() or "spec" in entry.name.lower():
                pointers.append(f"{entry.name} - product or task requirements")
        if len(scanned) >= max_files:
            signals["scan_limit"] = f"stopped after {max_files} files"
            break

    return ProjectContext(
        str(root),
        True,
        f"allowlist root scan up to {max_files} files",
        scanned,
        skipped,
        dirs[:40],
        signals,
        pointers[:16],
        do_not_touch[:16],
        str(global_agents) if global_agents else None,
        summarize_agents(global_agents),
        str(project_agents) if project_agents.exists() else None,
        summarize_agents(project_agents if project_agents.exists() else None),
        agent_map,
        existing_context,
        git_state,
    )


def collect_skill_names(roots: Iterable[Path], limit: int = 80) -> list[str]:
    skills: list[str] = []
    seen: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        for skill_md in sorted(root.glob("*/SKILL.md")):
            if len(skills) >= limit:
                return skills
            name = skill_md.parent.name
            try:
                text = skill_md.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                text = ""
            match = re.search(r"(?m)^name:\s*['\"]?([^'\"\n]+)", text[:1000])
            if match:
                name = match.group(1).strip()
            if name and name not in seen:
                seen.add(name)
                skills.append(name)
    return skills
