你正在一个新 agent session 中工作。请先读取 `PRE_VIBE_SPEC.md`，再只检查完成任务所必需的上下文。

目标：
根据当前项目 PRD，评估如何搭建 pre-vibe Codex plugin MVP，并给出架构和测试计划。

场景：coding
目标 agent：codex

规则：
1. 开始执行前先给出简短计划。
2. 不要默认读取 secret 文件，例如 `.env`、私钥、token、数据库 dump 或生产日志。
3. 如果需求仍有高影响歧义，最多问 3 个问题；否则使用 spec 中的假设继续。
4. 保持实现或交付物贴合验收标准，不扩大范围。

完成标准：
- 生成完整 PRE_VIBE_SPEC.md。
- 生成只包含长期规则建议的 SUGGESTED_AGENTS.md。
- 生成可直接作为新 session 第一条消息的 FIRST_STANDARD_PROMPT.md。
- 列出安全扫描摘要、相关文件线索和验证命令。

最后请报告：产物/修改文件、关键决策、验证结果、剩余风险。
