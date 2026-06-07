# Pre-Vibe

Pre-Vibe is a Codex plugin for preparing a new session before real work begins. It turns a rough first message into project-specific starting context, guided questions, AGENTS.md-compatible guidance, and a compact execution prompt.

It is designed for new Codex users, junior builders, and early product sessions where the first request is short, vague, or missing execution detail. Pre-Vibe reads safe project context, checks Codex guidance, asks only blocking questions, writes starting documents, and hands Codex a concise first prompt after approval.

## Install

The easiest beginner path is to ask Codex:

```text
Help me install the Pre-Vibe plugin from KimFischer99/Pre-Vibe into Codex.
```

Codex can then run the install command for you and explain each step. If you already know how to run Codex plugin commands, use:

```bash
codex plugin marketplace add KimFischer99/Pre-Vibe --sparse .agents/plugins --sparse plugins/pre-vibe && codex plugin add pre-vibe@pre-vibe
```

After installation, start a new Codex thread, open **Plugins**, and enable **Pre-Vibe**.

## Quick Start

1. Open Codex in the project you want to prepare.
2. Enable **Pre-Vibe** from the plugin picker.
3. Type a rough request such as “Help me turn this idea into a build plan.”
4. Answer the native question dialogs when Codex opens them.
5. Review the generated starting documents.
6. Approve the handoff so Codex can continue from `FIRST_PROMPT.md`.

## What It Builds

Pre-Vibe writes task-specific Markdown in the active project:

- `PRE_VIBE_SPEC.md`: a beginner-friendly handbook with goals, scope, project language, evidence, acceptance criteria, risks, and next steps.
- `AGENTS.md`: created when the project has no root agent guidance.
- `PROJECT_AGENTS.md`: created as a reviewable proposal when a root `AGENTS.md` already exists.
- `FIRST_PROMPT.md`: a compact execution contract for Codex, fully rewritten on each handoff.
- `PROJECT_INDEX.md`: architect effort only; an index of project intent, resources, tools, files, environment, and purpose.

`PRE_VIBE_SPEC.md`, the agent guidance document, and `PROJECT_INDEX.md` stay independent. `FIRST_PROMPT.md` may reference the files Codex should use for the handoff.

## Effort Levels

Pre-Vibe can choose effort automatically, and users can adjust it through plugin settings tools.

- `mini`: small ordinary tasks; up to 3 blocking questions.
- `default`: normal research or coding tasks; up to 5 blocking questions.
- `architect`: new products, refactors, high-uncertainty work; up to 10 blocking questions and `PROJECT_INDEX.md`.

Settings available through the plugin:

- default effort: `auto`, `mini`, `default`, or `architect`
- session effort override
- architect-only project index toggle
- auto-upgrade behavior

## Workflow

Pre-Vibe follows a session-start workflow:

1. Detect existing Pre-Vibe documents, AGENTS.md files, and git state.
2. Build a safe project and Codex environment index.
3. Resolve effort level and document output plan.
4. Ask native UI questions for unresolved blocking decisions.
5. Capture local and online evidence for `PRE_VIBE_SPEC.md`.
6. Build customized starting documents.
7. Clear the working context and hand off through `FIRST_PROMPT.md`.

## Architecture

The plugin package lives in `plugins/pre-vibe/` and includes:

- `.codex-plugin/plugin.json`: plugin manifest
- `.mcp.json`: bundled stdio MCP server registration
- `skills/pre-vibe-workflow/SKILL.md`: plugin-scoped workflow guidance
- `scripts/mcp_server.py`: MCP tool surface
- `scripts/pv_*.py`: focused workflow modules for routing, scanning, questions, settings, artifacts, and compact output

The MCP server returns short user-visible status text and structured workflow data for Codex. The Python layer provides deterministic routing, validation, scanning, settings, and safe writing; Codex authors the final task-specific Markdown.

## Development Checks

```bash
python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/pre-vibe
python3 -m py_compile plugins/pre-vibe/scripts/*.py
codex review --uncommitted
```

## Safety

Pre-Vibe uses allowlist project scanning, skips secret-like files, keeps output paths inside the active project, and avoids silently overwriting existing root `AGENTS.md`.

## License

MIT
