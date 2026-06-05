# INIT-AGENTS.MD
> 替换路径指引：人工确认后，可复制本文件内容到项目级 `/Users/kimfischer99/Coding/Working Space/Project_13_05.06/AGENTS.md`。不要覆盖 Codex 全局 AGENTS；本文件只补充项目级规则。

## 全局 AGENTS 摘要
- Source: `/Users/kimfischer99/.codex/AGENTS.md`
- 全局 AGENTS.md 不存在或没有可摘要的规则。

## 现有项目 AGENTS 摘要
- Source: `not found`
- No existing project AGENTS.md found.

## Conflict Policy
- Global/personal Codex instructions remain higher priority than this generated project guidance.
- Do not add rules that contradict security, sandbox, approval, or tool-use instructions.
- Keep one-off task details in `PRE-VIBE-SPEC.MD`, not in project-level AGENTS.

## Durable Project Guidance
- 正式执行前先给出短计划。
- 不要默认读取 secret 文件、生产日志、数据库 dump 或 token cache。
- pre-vibe 只注入 `FIRST-PROMPT.MD`，不要注入 `PRE-VIBE-SPEC.MD` 全文。
- 遇到非阻塞未知项，用假设继续；只问 blocking questions。
- 完成后报告修改/产物、验证结果、剩余风险。
