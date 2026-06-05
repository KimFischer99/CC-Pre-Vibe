# pre-vibe Workflow

pre-vibe keeps one product positioning across scenarios:

> Agent first-turn context engineering / context intake compiler.

General work, research work, and coding work are scenario templates, not separate product positions.

## Pipeline

1. Normalize the raw user task.
2. Classify scenario, complexity, uncertainty, and risk.
3. Assign hard token budget and compression mode.
4. Decide whether to ask, scan, or search.
5. Compile the handbook spec only when useful.
6. Generate project-level AGENTS guidance that does not conflict with global Codex AGENTS.
7. Generate a compact FIRST-PROMPT execution brief.
8. Ask the user to approve `/clear` and FIRST-PROMPT injection.

## Modes

- `micro`: no questions, no scan, no fetch, 300-800 token injection.
- `standard`: at most 3 questions, light scan, 800-1800 token injection.
- `deep`: at most 6 questions, broader scan, 1800-3500 token injection.
- `architect`: at most 10 questions, staged injection, 3500-6000 token injection.

When unanswered, continue with named assumptions.
