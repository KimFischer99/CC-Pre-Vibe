我先读取了指定的 [PRE_VIBE_SPEC.md](</Users/kimfischer99/Coding/Working Space/Project_13_05.06/pre-vibe-reports/live/coding/pre-vibe-context/PRE_VIBE_SPEC.md>)，再只检查了 PRD、README、架构说明、插件 manifest、核心脚本和测试。当前沙箱是只读，`pre-vibe-reports/live/coding/pre-vibe-context` 显示 `not-writable`，所以我无法直接改写文件；下面是应写入三份产物的最终内容摘要和执行结论。

**产物状态**
- 现有文件：`PRE_VIBE_SPEC.md`、`SUGGESTED_AGENTS.md`、`FIRST_STANDARD_PROMPT.md` 已存在。
- 未修改文件：只读沙箱阻止写入；我没有改动工作区。
- 当前 `PRE_VIBE_SPEC.md` 偏通用 intake，不足以表达本轮“根据 PRD 评估 Codex plugin MVP 架构与测试计划”的完整结论。

**关键决策**
- MVP 形态：Codex plugin + Skill + CLI，不做自动拦截所有新 session。
- 核心模块：Intent Normalizer、Safe Context Scanner、Question Budget、Spec Compiler、Agent Adapter、Output Writer。
- 输出文件：`PRE_VIBE_SPEC.md` 放完整任务上下文；`SUGGESTED_AGENTS.md` 只放长期规则；`FIRST_STANDARD_PROMPT.md` 保持短 prompt，指向 spec。
- 安全策略：默认 allowlist 扫描，跳过 `.env`、私钥、token、credential、db dump、生产日志；需要 env 时只读变量名且需用户确认。

**建议写入内容**
`SUGGESTED_AGENTS.md` 现有内容已经符合“只包含长期规则建议”，可保留。

`FIRST_STANDARD_PROMPT.md` 现有内容也可保留，已经能作为新 session 第一条消息使用。

`PRE_VIBE_SPEC.md` 建议补充这些核心段落：
```markdown
## MVP Architecture
pre-vibe MVP should be implemented as an explicit Codex plugin workflow, not a platform-level session interceptor.

Package shape:
- `.codex-plugin/plugin.json` exposes `skills/`.
- `skills/pre-vibe/SKILL.md` stays short and delegates long guidance to references.
- `scripts/pre_vibe.py` provides deterministic CLI generation.
- `tests/test_pre_vibe.py` covers classification, output generation, and secret skipping.

Runtime flow:
1. User explicitly invokes pre-vibe.
2. Skill identifies scenario: general, research, coding, or mixed.
3. CLI scans safe project context with allowlist and secret denylist.
4. Compiler generates questions, assumptions, acceptance criteria, scan summary, and verification plan.
5. Writer emits `PRE_VIBE_SPEC.md`, `SUGGESTED_AGENTS.md`, `FIRST_STANDARD_PROMPT.md`, and optional JSON metadata.

## MVP Scope
In scope:
- Codex plugin manifest.
- One reusable pre-vibe skill.
- Offline deterministic CLI.
- Safe project scanning.
- Agent-specific first prompt for Codex.
- Unit tests and offline comparison runner.

Out of scope:
- Automatic interception of every new agent session.
- External reference fetching by default.
- Editing `AGENTS.md` automatically.
- Reading secrets, production logs, databases, or token caches.
- Live Codex A/B execution unless explicitly approved.

## Test Plan
Unit:
- classify coding/general/research/mixed tasks.
- generate all required output files.
- skip secret-like files.
- preserve Chinese language behavior.
- keep `SUGGESTED_AGENTS.md` durable-only.
- keep first prompt compact and execution-ready.

Integration:
- run CLI against this repo with coding scenario.
- verify emitted files include scan summary, assumptions, acceptance criteria, and verification plan.
- validate plugin manifest.
- run offline comparison tests.

Manual/live:
- start fresh Codex sessions with baseline prompt vs pre-vibe prompt.
- compare clarification turns, plan quality, task completion, token usage, and safety behavior.
```

**安全扫描摘要**
- 已读取：`pre-vibe_PRD.md`、`README.md`、`pre-vibe-reports/architecture.md`、`pre-vibe-plugin/.codex-plugin/plugin.json`、`pre-vibe-plugin/scripts/pre_vibe.py`、`pre-vibe-plugin/tests/test_pre_vibe.py`、相关输出文件。
- 未读取：`.env`、私钥、token、数据库 dump、生产日志。
- 相关文件线索：插件已在 `pre-vibe-plugin` 成型；报告已有 [architecture-and-test-report.md](</Users/kimfischer99/Coding/Working Space/Project_13_05.06/pre-vibe-reports/architecture-and-test-report.md>)。

**验证结果**
- `python3 -m unittest discover -s pre-vibe-plugin/tests` 启动成功但失败：当前环境无可用临时目录，`tempfile.TemporaryDirectory()` 报 `No usable temporary directory found`。
- `python3 pre-vibe-plugin/scripts/run_comparison_tests.py --project . --output /tmp/pre-vibe-comparison-check.md` 同样因临时目录不可写失败。
- `git status --short` 可运行，但出现 `/tmp` cache 写入受限警告；工作区已有大量新增文件和 `pre-vibe-reports/live/` 未跟踪文件。

**剩余风险**
- 本轮无法直接落盘更新三份 md 文件。
- 现有测试失败来自只读/无 temp 环境，不能证明代码逻辑失败。
- live A/B 仍需真实 Codex token 和明确授权后再跑。