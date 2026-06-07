---
name: "pre-vibe-workflow"
description: "Internal orchestration guidance for the Pre-Vibe Codex plugin when it is enabled. Use only to coordinate Pre-Vibe MCP tools, native question UI, starting-document rules, AGENTS.md compatibility, and first-prompt handoff inside the plugin workflow."
---

# Pre-Vibe Workflow

This skill is bundled with the Pre-Vibe plugin as workflow guidance for Codex. Users enable Pre-Vibe from the Codex plugin picker and describe their rough task naturally.

## Operating Rules

1. Start with `prepare_project_start`.
2. If the structured result contains a native question request, call `open_question_dialog`; do not print backend fields or blocking questions as ordinary chat.
3. If existing Pre-Vibe documents are detected, ask whether to reuse/update, regenerate, or compare before writing.
4. Use project files, AGENTS guidance, and safe environment evidence before asking the user for facts already available locally.
5. Every blocking question must include why it matters and the recommended answer.
6. Keep `PRE_VIBE_SPEC.md`, `AGENTS.md` or `PROJECT_AGENTS.md`, and `PROJECT_INDEX.md` independent from each other; `FIRST_PROMPT.md` may reference the files needed for handoff.
7. Treat online references as evidence for `PRE_VIBE_SPEC.md`; keep `FIRST_PROMPT.md` compact.

## Document Contract

- `PRE_VIBE_SPEC.md`: beginner-friendly project handbook with Project Language and Evidence.
- `AGENTS.md`: created only when the project has no root `AGENTS.md`.
- `PROJECT_AGENTS.md`: proposal when a root `AGENTS.md` already exists.
- `FIRST_PROMPT.md`: rewritten fully on each Pre-Vibe handoff as the execution contract.
- `PROJECT_INDEX.md`: architect effort only; indexes project intent, resources, tools, files, environment, and purpose for Codex.

## Intensity

Use the configured effort level first, then session override, then auto detection. The user may change effort through Pre-Vibe settings tools without using command-style prompts.
