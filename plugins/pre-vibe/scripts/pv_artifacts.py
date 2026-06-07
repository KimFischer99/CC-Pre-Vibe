"""Artifact validation and writing for Codex-authored starting documents."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ARTIFACT_FILENAMES = {
    "spec": "PRE_VIBE_SPEC.md",
    "agents": "PROJECT_AGENTS.md",
    "prompt": "FIRST_PROMPT.md",
}


def estimate_tokens(text: str) -> int:
    cjk_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    other_chars = max(len(text) - cjk_chars, 0)
    return max(1, int(cjk_chars / 1.7 + other_chars / 4))


def redact_secret_like(text: str) -> str:
    patterns = (
        r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*[^\s]+",
        r"(?i)(bearer)\s+[a-z0-9._~+/=-]{20,}",
        r"(?i)(jwt|cookie|session)\s*[:=]\s*[^\s]+",
        r"-----BEGIN [A-Z ]+PRIVATE KEY-----.*?-----END [A-Z ]+PRIVATE KEY-----",
    )
    redacted = text
    for pattern in patterns:
        redacted = re.sub(pattern, "[REDACTED]", redacted, flags=re.DOTALL)
    return redacted


def validate_artifact_contents(contents: dict[str, str]) -> None:
    for key, text in contents.items():
        if key in {"spec", "agents", "prompt"} and "INIT_AGENTS.md" in text:
            raise ValueError("artifact content must not reference the retired INIT_AGENTS.md filename")
    spec_text = contents.get("spec", "")
    agents_text = contents.get("agents", "")
    if re.search(r"(?i)(^|[/\\])PROJECT_AGENTS\.md\b|PROJECT_AGENTS\.md\b", spec_text):
        raise ValueError("PRE_VIBE_SPEC.md must not reference PROJECT_AGENTS.md")
    if re.search(r"(?i)(^|[/\\])PRE_VIBE_SPEC\.md\b|PRE_VIBE_SPEC\.md\b", agents_text):
        raise ValueError("PROJECT_AGENTS.md must not reference PRE_VIBE_SPEC.md")


def ensure_output_dir_inside_project(output_dir: Path, project_root: Path | None = None) -> Path:
    root = (project_root or Path.cwd()).expanduser().resolve()
    output = output_dir.expanduser()
    resolved_output = output.resolve() if output.is_absolute() else (root / output).resolve()
    if resolved_output != root and root not in resolved_output.parents:
        raise ValueError("output_dir must be inside the active project root")
    return resolved_output


def write_artifacts(
    output_dir: Path,
    contents: dict[str, str],
    status: dict[str, Any] | None = None,
    project_root: Path | None = None,
) -> dict[str, str]:
    if status is not None:
        raise ValueError("status is internal context and must not be written to disk")
    output_dir = ensure_output_dir_inside_project(output_dir, project_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}
    validate_artifact_contents(contents)
    for key, text in contents.items():
        if key not in ARTIFACT_FILENAMES:
            raise ValueError(f"unsupported artifact key: {key}")
        path = output_dir / ARTIFACT_FILENAMES[key]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(redact_secret_like(text).rstrip() + "\n", encoding="utf-8")
        written[key] = str(path.relative_to(output_dir))
    return written
