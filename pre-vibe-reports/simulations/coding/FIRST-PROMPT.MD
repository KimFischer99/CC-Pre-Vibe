# FIRST-PROMPT.MD
> 注入路径指引：用户批准后执行 `/clear`，然后只把本文件作为新 session 的初始上下文注入。不要注入 `PRE-VIBE-SPEC.MD` 全文。

## Goal
把原始需求压缩成适合 agent 开始工作的最小必要上下文，场景为 coding。

## Current Task
先读取少量相关文件并提出计划，再执行最小安全改动。

## Hard Constraints
- 不要把 PRE-VIBE-SPEC.MD 全文复制进正式 workflow。
- 不要读取 `.env`、私钥、token、数据库 dump 或生产日志。
- 只问会改变执行路径的 blocking questions。
- 先读最少相关文件，再提出计划；不要总结整个仓库。

## Key Assumptions
- 非阻塞未知项默认写入假设，不通过追问消耗上下文。
- 完整 spec 只作为 handbook，不进入正式执行上下文。
- 正式执行只注入 FIRST-PROMPT.MD 中的精简 brief。
- 默认不读取 secret 文件，不触碰生成物和依赖目录。

## Relevant Context
- Handbook: `/Users/kimfischer99/Coding/Working Space/Project_13_05.06/pre-vibe-reports/simulations/coding/PRE-VIBE-SPEC.MD` (read only if needed)
- Suggested project AGENTS: `/Users/kimfischer99/Coding/Working Space/Project_13_05.06/pre-vibe-reports/simulations/coding/INIT-AGENTS.MD` (user may review/copy manually)
- pre-vibe-plugin/ - likely relevant directory
- pre-vibe_PRD.md - product requirements
- README.md - project overview

## Search Policy
- 只有 API/依赖版本不确定且会阻塞实现时才搜索。
- 优先官方文档；不要默认搜索普通教程。

## Done When
- 目标、当前任务、硬约束、关键假设和完成标准清楚。
- 正式执行上下文不包含完整 spec 或长背景。
- 下一步操作需要用户批准 `/clear` 和注入 FIRST-PROMPT.MD。
- 包含少量相关文件指针、禁止触碰区域和验证建议。

## Operating Mode
Start with a short plan. Do not read unrelated files. Ask only blocking questions. Prefer the smallest safe next action.
