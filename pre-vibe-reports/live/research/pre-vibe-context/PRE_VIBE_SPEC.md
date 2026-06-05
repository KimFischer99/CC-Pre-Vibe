# PRE_VIBE_SPEC

## 0. 会话信息
- Target agent: codex
- Scenario: research
- Mode: standard
- Language: zh
- Estimated first prompt tokens: 186

## 1. 原始输入
> 调研 prompt optimization 开源项目，判断 pre-vibe 应该如何差异化。

## 2. 标准化目标
将原始需求整理为适合 agent 开始工作的上下文包，并按 research 场景补齐目标、边界、假设、验收标准和首轮执行提示。

## 3. 建议先确认的问题
- 这项研究要支持什么决策？
- 哪些来源类型可以接受或必须排除？
- 证据需要多新？是否必须引用官方或一手来源？
- 输出应偏广度、深度，还是明确推荐？

## 4. 验收标准
- 生成完整 PRE_VIBE_SPEC.md。
- 生成只包含长期规则建议的 SUGGESTED_AGENTS.md。
- 生成可直接作为新 session 第一条消息的 FIRST_STANDARD_PROMPT.md。
- 列出需要外部来源验证的信息差和引用要求。

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
- 研究任务要先定义可接受来源，否则 agent 容易混入弱来源。

## 7. 假设和未知项
- 用户希望先澄清任务并压缩上下文，而不是立即让 agent 执行。
- 缺失信息会被写入假设和未知项，而不是隐藏在 prompt 中。
- 首轮 prompt 应尽量短，并引用完整 spec 文件。

## 8. 风险
- The generated outputs are an intake artifact, not proof that execution is complete.
- External facts should be verified with primary or official sources when the task depends on current information.
- Durable guidance should be reviewed before being copied into `AGENTS.md`.

## 9. 验证计划
- Review `PRE_VIBE_SPEC.md` for missing constraints.
- Review `SUGGESTED_AGENTS.md` before adopting durable rules.
- Start a clean agent session with `FIRST_STANDARD_PROMPT.md`.
