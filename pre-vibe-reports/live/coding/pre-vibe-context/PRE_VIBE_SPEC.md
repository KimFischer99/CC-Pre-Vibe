# PRE_VIBE_SPEC

## 0. 会话信息
- Target agent: codex
- Scenario: coding
- Mode: standard
- Language: zh
- Estimated first prompt tokens: 189

## 1. 原始输入
> 根据当前项目 PRD，评估如何搭建 pre-vibe Codex plugin MVP，并给出架构和测试计划。

## 2. 标准化目标
将原始需求整理为适合 agent 开始工作的上下文包，并按 coding 场景补齐目标、边界、假设、验收标准和首轮执行提示。

## 3. 建议先确认的问题
- 这是 demo、MVP、生产改动、bugfix、refactor 还是学习任务？
- 本轮必须完成什么，明确不做什么？
- 哪些命令或人工检查能证明完成？
- 哪些文件、API、页面或用户流程最相关？
- agent 应避免触碰什么？

## 4. 验收标准
- 生成完整 PRE_VIBE_SPEC.md。
- 生成只包含长期规则建议的 SUGGESTED_AGENTS.md。
- 生成可直接作为新 session 第一条消息的 FIRST_STANDARD_PROMPT.md。
- 列出安全扫描摘要、相关文件线索和验证命令。

## 5. 上下文扫描摘要
- Project root: `/Users/kimfischer99/Coding/Working Space/Project_13_05.06`
- Scanned files: pre-vibe_PRD.md, README.md
- Key directories: docs, plugins, reports
- Secret-like files skipped: None
- Signals: {"dir:docs": "present"}

## 6. 教程式建议
- 把一次性任务需求和长期项目规则分开，避免污染 AGENTS.md。
- 把不确定信息显式写成假设，agent 执行后才容易审查。
- 先定义验收标准，再让 agent 计划和执行。
- 代码任务要给出验证命令和禁止触碰区域，减少返工。

## 7. 假设和未知项
- 用户希望先澄清任务并压缩上下文，而不是立即让 agent 执行。
- 缺失信息会被写入假设和未知项，而不是隐藏在 prompt 中。
- 首轮 prompt 应尽量短，并引用完整 spec 文件。
- 默认不读取 secret 文件，不自动修改长期 agent 规则。

## 8. 风险
- The generated outputs are an intake artifact, not proof that execution is complete.
- External facts should be verified with primary or official sources when the task depends on current information.
- Durable guidance should be reviewed before being copied into `AGENTS.md`.

## 9. 验证计划
- Review `PRE_VIBE_SPEC.md` for missing constraints.
- Review `SUGGESTED_AGENTS.md` before adopting durable rules.
- Start a clean agent session with `FIRST_STANDARD_PROMPT.md`.
