# Context Pyramid

Only Level 0-2 belongs in the first prompt.

- Level 0: task intent
- Level 1: execution brief
- Level 2: decisions and hard constraints
- Level 3: relevant file/source pointers
- Level 4: full spec handbook
- Level 5: raw references, scan logs, fetched documents

Rules:

- Do not inject Level 4-5 by default.
- For coding, prefer file pointers over repository summaries.
- For research, prefer source maps over long source summaries.
- For daily/general tasks, skip scan/fetch/spec unless high-risk.
