---
name: pre-vibe
description: Use when a user wants to turn a vague request into a token-disciplined first-turn context package for an agent, including general work, research, and coding tasks. Produces a handbook spec, project AGENTS guidance, and a compact first prompt, then asks for approval to clear context and inject the prompt.
---

# pre-vibe

pre-vibe is an Agent first-turn context intake compiler. Use it before normal execution when the user wants cleaner context, better task framing, or a reusable prompt/spec package.

## Token Discipline

Pre-vibe is a context optimizer, not a context expander.

- Classify the request before expanding context.
- Assign a hard budget: `micro`, `standard`, `deep`, or `architect`.
- Ask only blocking questions.
- Prefer file/source pointers over long summaries.
- Never inject the full spec by default.
- Do not include brainstorming history, raw references, full repository summaries, or non-actionable background in the first prompt.

## Workflow

1. Identify the task scenario: `general`, `research`, `coding`, or `mixed`.
2. Assign budget and compression mode before reading context.
3. Read only the minimum safe context allowed by the budget.
3. Do not read secret files such as `.env`, private keys, token caches, local databases, or production logs.
4. Ask only high-impact clarification questions when the answer would materially change the output. Otherwise continue with explicit assumptions.
5. Generate exactly three project-facing Markdown outputs:
   - `PRE-VIBE-SPEC.MD` - handbook only, not injected into formal workflow.
   - `INIT-AGENTS.MD` - project-level AGENTS guidance based on global Codex AGENTS where available.
   - `FIRST-PROMPT.MD` - compact execution brief, the only default injected context.
6. Ask the user to review or edit the files.
7. Continue until the user explicitly approves the next step: run `/clear`, inject only `FIRST-PROMPT.MD`, and begin formal work.

## Scripted Path

When working in a local filesystem and file output is requested, prefer the bundled script:

```bash
python3 pre-vibe-plugin/scripts/pre_vibe.py --task "<raw task>" --project . --agent codex --mode auto --output-dir .
```

If the plugin is installed outside this repository, resolve the script path relative to the plugin root.

After the script runs, do not stop at file generation. Ask:

```text
我已生成 PRE-VIBE-SPEC.MD、INIT-AGENTS.MD、FIRST-PROMPT.MD。
是否批准我执行 /clear，并仅注入 FIRST-PROMPT.MD 作为正式 workflow 的初始上下文？
```

## References

Load only what is needed:

- `references/workflow.md` for the full intake flow.
- `references/scan-policy.md` for safe project scanning.
- `references/question-bank.md` for scenario-specific clarification questions.
- `references/templates.md` for output structure.
- `references/agent-adapters.md` for Codex, Claude Code, and generic agent prompts.
- `references/language-policy.md` for Chinese/English behavior.
- `references/token-budget.md` for budget and compression rules.
- `references/context-pyramid.md` for what may enter the first prompt.
