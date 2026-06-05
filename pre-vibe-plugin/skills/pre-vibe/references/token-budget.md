# Token Budget

Budgets are hard limits.

| Mode | Behavior | Injection Target |
|---|---|---|
| `micro` | no scan, no fetch, no questions | 300-800 tokens |
| `standard` | max 3 questions, light scan | 800-1800 tokens |
| `deep` | max 6 questions, broader scan | 1800-3500 tokens |
| `architect` | max 10 questions, staged injection | 3500-6000 tokens |

Compression order:

1. remove rationale
2. remove examples
3. collapse background into assumptions
4. replace summaries with file/source pointers
5. narrow current task scope

Default mapping:

- general/daily -> `micro + terse`
- research -> `standard + balanced`
- coding -> `standard/deep + balanced`
- new project/refactor/system design -> `architect + staged`
