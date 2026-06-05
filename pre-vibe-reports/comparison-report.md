# pre-vibe Comparison Test Report

Deterministic offline comparison of raw task prompts versus pre-vibe generated context packages.

| Scenario | Raw tokens | FIRST-PROMPT tokens | Full artifact tokens | Raw readiness | pre-vibe readiness | Landing effect |
|---|---:|---:|---:|---:|---:|---|
| general | 12 | 382 | 1184 | 0 | 22 | higher readiness |
| research | 17 | 452 | 1334 | 2 | 24 | higher readiness |
| coding | 15 | 446 | 1327 | 2 | 24 | higher readiness |

## Interpretation

- Raw token cost is lower because no context engineering is performed.
- pre-vibe stores all three artifacts on disk, but the formal injection is the budgeted FIRST-PROMPT only.
- Landing effect is measured by a local readiness rubric: goal, assumptions, acceptance criteria, risks, verification, and scenario terms.
- A live model A/B/C test is still required before claiming real-world task completion improvements.
