未能落盘修改：当前会话是只读沙箱，`pre-vibe-reports/live/research/pre-vibe-context` 检查为 `not_writable`，随后 `apply_patch` 被拒绝：writing is blocked by read-only sandbox。

**产物/修改文件**
- 未修改任何文件。
- 已准备的目标修改：
  - `PRE_VIBE_SPEC.md`：补全为 research spec，包含研究问题、范围、竞品地图、差异化假设、引用要求、验证计划。
  - `SUGGESTED_AGENTS.md`：仅保留长期规则，新增研究证据分层与引用规则。
  - `FIRST_STANDARD_PROMPT.md`：改为可直接开启新 session 的研究执行 prompt。

**关键决策**
- 不把 pre-vibe 定位成普通 prompt optimizer，而是定位为 `first-turn context compiler / prompt-to-spec compiler`。
- 研究对象优先覆盖：DSPy/GEPA、Promptfoo、PromptWizard、TextGrad、Arize Prompt Learning、LangChain Promptim、OpenPrompt。
- 差异化判断轴：现有工具多优化已有 prompt/pipeline 的输出质量；pre-vibe 应优化 coding agent 开工前的人类需求、项目上下文、验收标准和首轮注入 prompt。
- 无需提问，按 spec 假设继续。

**验证结果**
- 已读取：
  - `pre-vibe-reports/live/research/pre-vibe-context/PRE_VIBE_SPEC.md`
  - `SUGGESTED_AGENTS.md`
  - `FIRST_STANDARD_PROMPT.md`
  - `pre-vibe_PRD.md`
  - `README.md`
  - pre-vibe skill 模板与语言策略
- 已核对外部一手来源线索：
  - [DSPy](https://dspy.ai/)：optimizers improve programs against metrics，包含 GEPA/MIPROv2。
  - [Promptfoo docs](https://www.promptfoo.dev/docs/intro/) 与 [CLI optimize](https://www.promptfoo.dev/docs/usage/command-line/)：open-source eval/red-team 工具，并支持 `promptfoo optimize`。
  - [PromptWizard GitHub](https://github.com/microsoft/PromptWizard)：task-aware prompt optimization framework。
  - [TextGrad GitHub](https://github.com/zou-group/textgrad)：textual-gradient optimization framework。
  - [Arize Prompt Learning](https://arize.com/docs/ax/prompts/prompt-optimization/prompt-learning-sdk)：open-source SDK，依赖 dataset/feedback/evaluators。
  - [GEPA GitHub](https://github.com/CerebrasResearch/gepa)：reflective text evolution，推荐经 DSPy 使用。
  - [LangChain Promptim](https://www.langchain.com/blog/promptim)：experimental prompt optimization library，需要 prompt、dataset、evaluators。
  - [OpenPrompt GitHub](https://github.com/thunlp/OpenPrompt)：prompt-learning framework。

**剩余风险**
- 文件未能写入，完成标准中的“生成文件”在当前权限下未满足。
- GitHub stars、license、commit 活跃度、最新 release 仍需在可联网研究 session 中逐项记录访问日期。
- Benchmark/性能提升数字只能引用论文或官方实验，不能作为独立验证事实。