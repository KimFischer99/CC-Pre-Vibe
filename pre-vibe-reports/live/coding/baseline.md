我没有修改文件。

**结论**
根据 PRD，MVP 应按“显式触发的 Codex plugin + Skill + 本地 CLI”搭建，不做自动拦截 session、不做 GUI、不做多 agent 编排。当前项目已经基本落在这个方向上：manifest、Skill、references、deterministic CLI、单元测试和 comparison runner 都存在。核心还差的是把 PRD 里的“更完整 spec 模板、真实 adapter 差异、dry-run / no-fetch / redaction、live A/B eval”补齐到可验证标准。

**建议架构**
1. Plugin 壳层  
   使用 `pre-vibe-plugin/.codex-plugin/plugin.json` 暴露 `skills` 路径和 marketplace metadata。当前 manifest 形态是合理的，见 [plugin.json](</Users/kimfischer99/Coding/Working Space/Project_13_05.06/pre-vibe-plugin/.codex-plugin/plugin.json:1>)。

2. Skill 入口  
   `SKILL.md` 只保留触发条件和流程导航，长内容放 `references/`，符合 progressive disclosure。当前结构已在 [pre-vibe-reports/architecture.md](</Users/kimfischer99/Coding/Working Space/Project_13_05.06/pre-vibe-reports/architecture.md:7>) 中定义。

3. CLI 核心流水线  
   `pre_vibe.py` 应保持无网络、无第三方依赖、可离线运行：
   - Intent normalizer：识别 `general/research/coding/mixed`
   - Context scanner：allowlist 扫描 + denylist 跳过 secret
   - Clarification engine：按 `quick/standard/deep` 控制问题预算
   - Spec compiler：生成 `PRE_VIBE_SPEC.md`
   - Agent guidance generator：生成 `SUGGESTED_AGENTS.md`
   - Injection generator：生成短首轮 prompt

   当前脚本已经有任务分类、语言识别、安全扫描和输出写入，见 [pre_vibe.py](</Users/kimfischer99/Coding/Working Space/Project_13_05.06/pre-vibe-plugin/scripts/pre_vibe.py:96>) 和 [pre_vibe.py](</Users/kimfischer99/Coding/Working Space/Project_13_05.06/pre-vibe-plugin/scripts/pre_vibe.py:469>)。

4. 输出文件  
   PRD 必做项要求 `PRE_VIBE_SPEC.md`、`PRE_VIBE_INJECTION.md`、Codex/Claude adapter、三档模式和不读 secret，见 [pre-vibe_PRD.md](</Users/kimfischer99/Coding/Working Space/Project_13_05.06/pre-vibe_PRD.md:694>)。当前实现输出的是：
   - `PRE_VIBE_SPEC.md`
   - `SUGGESTED_AGENTS.md`
   - `FIRST_STANDARD_PROMPT.md`
   - `pre_vibe_result.json`

   建议保留 `FIRST_STANDARD_PROMPT.md` 这个更清晰的命名，或增加 `PRE_VIBE_INJECTION.md` 作为别名以贴合 PRD。

**MVP 缺口优先级**
P0：
- 补齐 `PRE_VIBE_SPEC.md` 结构：Scope、Requirements、Acceptance Criteria、Risk Register、Verification Plan。
- Codex / Claude Code adapter 做出实际差异，而不是只记录 `agent` 字段。
- 增加 `--dry-run`，列出将扫描和跳过的文件。
- 增加 `--no-fetch` 参数；即使 MVP 不 fetch，也要让接口语义对齐 PRD。
- 测试 secret redaction，不只测试 `.env` 文件名跳过。

P1：
- 扫描 `docs/`、`.claude/rules/`、测试目录树摘要，但不读敏感内容。
- 增加 golden snapshot 测试，锁定中文/英文输出结构。
- 增加 task subtype：new project、feature、bugfix、refactor、deploy、learning。

P2：
- 可选 reference fetcher，必须带来源、日期、摘要、置信度和使用范围。
- 历史 spec 管理和团队模板。

**测试计划**
本地 deterministic gate：
```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s pre-vibe-plugin/tests
python3 pre-vibe-plugin/scripts/run_comparison_tests.py --project . --output pre-vibe-reports/comparison-report.md
```

需要覆盖：
- 分类测试：`general/research/coding/mixed`，中英文输入都要测。
- CLI 输出测试：确认 3 个 Markdown + JSON 都生成，标题和关键 section 存在。
- 安全扫描测试：`.env`、key、token、db、log 被跳过；allowlist 文件被扫描。
- 语言策略测试：中文输入输出中文，英文输入输出英文，`bilingual` 可强制。
- adapter 测试：Codex prompt 包含 plan-first、AGENTS.md、verification；Claude prompt 包含 clean context、CLAUDE.md/memory 区分。
- token 预算测试：first prompt 保持在目标阈值内，例如 1,000-2,000 tokens。
- snapshot 测试：防止模板结构被无意破坏。
- plugin 验证：manifest schema、relative skills path、安装后 skill 可发现。
- live A/B：按 PRD 的 20 个任务设计，比较首次 plan 接受率、修正轮次、token、完成率、测试通过率和用户信心，指标见 [pre-vibe_PRD.md](</Users/kimfischer99/Coding/Working Space/Project_13_05.06/pre-vibe_PRD.md:653>)。

**我做的验证**
我读了 PRD、架构文档、manifest、脚本、测试和现有报告。纯内存检查通过：当前任务被识别为 `coding`，语言为 `zh`，首轮 prompt 估算约 185 tokens。单元测试在当前只读沙箱里失败，是因为系统临时目录不可写，`tempfile.TemporaryDirectory()` 无法创建目录；这不是代码断言失败。现有 comparison report 显示三类场景 readiness 都高于 raw prompt，见 [comparison-report.md](</Users/kimfischer99/Coding/Working Space/Project_13_05.06/pre-vibe-reports/comparison-report.md:5>)。