"""Safe project and local component scanning helpers."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable

from pv_models import ProjectContext


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
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        candidates.append(Path(codex_home) / "AGENTS.md")
    candidates.append(Path.home() / ".codex" / "AGENTS.md")
    for path in candidates:
        if path.exists():
            return path
    return None


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
