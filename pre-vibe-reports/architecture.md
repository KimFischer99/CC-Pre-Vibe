# pre-vibe v0.1.1 Architecture

## Positioning

pre-vibe is a token-disciplined first-turn context intake compiler for agent workflows. General work, research, and coding are three task-intake strategies under the same product positioning, not separate product positions.

The v0.1.1 shift is from context expansion to context optimization:

```text
vague user input
  -> budgeted intake package
  -> handbook + project guidance on disk
  -> compact FIRST-PROMPT injection only after user approval
```

## Package Shape

The public plugin source is isolated from reports:

```text
pre-vibe-plugin/
  .codex-plugin/plugin.json
  README.md
  LICENSE
  skills/pre-vibe/SKILL.md
  skills/pre-vibe/references/
  scripts/pre_vibe.py
  scripts/run_comparison_tests.py
  scripts/run_live_codex_ab.py
  scripts/simulate_coding_workflow.py
  tests/test_pre_vibe.py

pre-vibe-reports/
  architecture.md
  reference-analysis.md
  comparison-report.md
  coding-workflow-simulation.md
```

## Runtime Flow

1. Classify the task as `general`, `research`, `coding`, or `mixed`.
2. Choose a hard budget: `micro`, `standard`, `deep`, or `architect`.
3. Scan only the safe project context permitted by that budget.
4. Convert non-blocking unknowns into assumptions; ask only blocking questions.
5. Generate exactly three uppercase Markdown files:
   - `PRE-VIBE-SPEC.MD`: handbook only, not default injected context.
   - `INIT-AGENTS.MD`: project AGENTS guidance derived with awareness of global Codex `AGENTS.md`.
   - `FIRST-PROMPT.MD`: compact execution brief and the only default injected context.
6. Ask the user to review/edit the first two files.
7. Continue until the user approves `/clear` and injection of only `FIRST-PROMPT.MD`.

## Token Budget Model

| Mode | Use Case | Context Policy | Injection Budget |
|---|---|---|---:|
| `micro` | daily/general tasks | no scan, no fetch, no questions | 800 |
| `standard` | ordinary research/coding | light scan, max 3 questions | 1800 |
| `deep` | multi-file coding/spec work | broader scan, max 6 questions | 3500 |
| `architect` | new project/refactor/system design | staged workflow | 6000 |

Compression is separately controlled as `terse`, `balanced`, or `full`, with `auto` mapped from the budget.

## Safety Model

The scanner skips secret-like files by default: `.env`, private keys, token/credential paths, local databases, dumps, and logs. It records skipped file names in the handbook so the user can see that relevant but sensitive context was intentionally excluded.

`INIT-AGENTS.MD` never replaces global Codex instructions. It summarizes global `AGENTS.md` when available, adds project-level durable guidance, and includes a conflict policy that keeps global/personal rules higher priority.

## Evaluation Model

v0.1.1 uses three lightweight checks:

- unit tests for classification, output naming, secret skipping, micro-budget behavior, and global AGENTS awareness;
- deterministic offline comparison for token estimates and readiness score;
- offline coding workflow simulation for the generate-review-approve-clear-inject-start sequence.

Live Codex A/B testing remains available, but it is deliberately separate because it consumes real model tokens and should use `final-answer-only` benchmark mode.
