# pre-vibe v0.1.1 Architecture and Test Report

## Summary

v0.1.1 implements the PRD section 21 correction: pre-vibe is now a context optimizer with hard token budgets, not a default context expander.

The plugin now produces:

- `PRE-VIBE-SPEC.MD`: human-editable handbook, not injected by default.
- `INIT-AGENTS.MD`: project-level AGENTS proposal that accounts for global Codex `AGENTS.md`.
- `FIRST-PROMPT.MD`: compact execution brief, the only default injected context.

## Implemented Changes

| Area | v0.1.1 Behavior |
|---|---|
| Task intake | Routes `general`, `research`, `coding`, and `mixed` tasks. |
| Budget control | Adds `micro`, `standard`, `deep`, and `architect` hard budgets. |
| Compression | Adds `terse`, `balanced`, `full`, and `auto`. |
| Context policy | Uses file/source pointers instead of long summaries. |
| Workflow handoff | Asks for review, `/clear` approval, and FIRST-PROMPT-only injection. |
| AGENTS handling | Reads global Codex `AGENTS.md` where available and writes conflict-safe project guidance. |
| Benchmarking | Adds `final-answer-only` benchmark mode and a single coding workflow simulator. |

## Test Commands

```bash
python3 -m unittest discover -s pre-vibe-plugin/tests
python3 -m compileall pre-vibe-plugin/scripts pre-vibe-plugin/tests
python3 /Users/kimfischer99/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py pre-vibe-plugin
python3 pre-vibe-plugin/scripts/run_comparison_tests.py --project . --output pre-vibe-reports/comparison-report.md
python3 pre-vibe-plugin/scripts/simulate_coding_workflow.py --project . --output-dir pre-vibe-reports/simulations/coding --report pre-vibe-reports/coding-workflow-simulation.md
```

Deployment checks are recorded in `plugin-review.md` after the package is copied to the personal plugin source and reinstalled.

## Offline Comparison

The deterministic comparison now measures the full artifact package on disk separately from the injected `FIRST-PROMPT.MD`. The expected interpretation is:

- raw prompts remain cheapest before execution;
- pre-vibe improves readiness by adding assumptions, constraints, acceptance criteria, and file/source pointers;
- only `FIRST-PROMPT.MD` should be counted as default formal-workflow injection.

See `comparison-report.md` for current numbers.

## Coding Workflow Simulation

The single coding scenario simulation verifies the requested workflow state machine:

```text
generate -> review -> approve_clear -> inject -> start_work
```

The simulation checks:

- all three uppercase files exist;
- `PRE-VIBE-SPEC.MD` is treated as handbook;
- `/clear` approval appears in the prompt and handoff;
- `FIRST-PROMPT.MD` stays under budget;
- `INIT-AGENTS.MD` includes global AGENTS awareness.

See `coding-workflow-simulation.md` for current numbers.

## Remaining Limits

- External reference fetching is represented as a source-map/search-plan workflow, not live fetching inside the generator.
- Hooks are not added in v0.1.1 because the required handoff can be completed through skill/script interaction and explicit user approval.
- Live A/B/C evaluation is still needed before claiming reduced total tokens per successful outcome.
