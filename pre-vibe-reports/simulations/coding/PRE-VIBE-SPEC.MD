# PRE-VIBE-SPEC.MD
> 路径指引：本文件是 handbook，建议保存在 `/Users/kimfischer99/Coding/Working Space/Project_13_05.06/pre-vibe-reports/simulations/coding/PRE-VIBE-SPEC.MD`。不要把本文件全文复制进正式 workflow；正式执行只注入 `FIRST-PROMPT.MD`。

## 0. 任务路由
- Scenario: coding
- Complexity: standard
- Compression: balanced
- Target agent: codex
- Budget: max_questions=3, max_scan=10, max_fetch=2, max_injection_tokens=1800
- Brief token estimate: 432
- Quality score: 5.8/10

## 1. 原始输入
> 根据当前项目 PRD，为 pre-vibe plugin 增加 token budget、精简 first prompt，并更新测试。

## 2. 标准化目标
把原始需求压缩成适合 agent 开始工作的最小必要上下文，场景为 coding。

## 3. 当前任务
先读取少量相关文件并提出计划，再执行最小安全改动。

## 4. Blocking Questions
- 本轮是否允许修改文件，还是只生成计划？
- 哪些验证命令或人工检查必须通过？
- 有没有明确禁止触碰的目录、数据或接口？

## 5. 假设
- 非阻塞未知项默认写入假设，不通过追问消耗上下文。
- 完整 spec 只作为 handbook，不进入正式执行上下文。
- 正式执行只注入 FIRST-PROMPT.MD 中的精简 brief。
- 默认不读取 secret 文件，不触碰生成物和依赖目录。

## 6. 硬约束
- 不要把 PRE-VIBE-SPEC.MD 全文复制进正式 workflow。
- 不要读取 `.env`、私钥、token、数据库 dump 或生产日志。
- 只问会改变执行路径的 blocking questions。
- 先读最少相关文件，再提出计划；不要总结整个仓库。

## 7. Context Index
- Project root: `/Users/kimfischer99/Coding/Working Space/Project_13_05.06`
- Relevant pointers:
- pre-vibe-plugin/ - likely relevant directory
- pre-vibe_PRD.md - product requirements
- README.md - project overview
- Do not touch:
- .git/
- Scanned files: pre-vibe_PRD.md, README.md
- Skipped secret-like files: None
- Signals: {"dir:pre-vibe-plugin": "present"}

## 8. 拓展搜索计划
- 只有 API/依赖版本不确定且会阻塞实现时才搜索。
- 优先官方文档；不要默认搜索普通教程。

## 9. 上下文补全
- 已参考全局 AGENTS: /Users/kimfischer99/.codex/AGENTS.md

## 10. 完成标准
- 目标、当前任务、硬约束、关键假设和完成标准清楚。
- 正式执行上下文不包含完整 spec 或长背景。
- 下一步操作需要用户批准 `/clear` 和注入 FIRST-PROMPT.MD。
- 包含少量相关文件指针、禁止触碰区域和验证建议。

## 11. Token Discipline Notes
- 把 handbook、项目规则和正式注入 prompt 分开。
- 用文件/source 指针替代长摘要。
- 如果 FIRST-PROMPT 超预算，先删 rationale 和例子。
- coding 任务首轮只告诉 agent 第一批该读哪些文件。

## 12. 预算警告
- None
