**结论**

`pre-vibe` 不应该把自己定位成又一个 “prompt optimizer”。这个赛道已经被 DSPy、GEPA、PromptWizard、TextGrad、promptfoo、Langfuse/Phoenix 等项目覆盖得很密。`pre-vibe` 更应该差异化为：

**Agent first-turn context compiler：在执行前，把模糊需求、项目上下文、约束、验收标准和首轮提示词编译成可交接的任务包。**

也就是优化的不是“某个 prompt 的分数”，而是“第一次把任务交给 agent 时的信息质量”。

**理由**

1. 开源 prompt optimization 已经很拥挤。DSPy 明确以 metric、训练样本、optimizer 来调优 prompt、few-shot 示例甚至权重，包含 MIPROv2、GEPA、SIMBA 等优化器。来源：DSPy docs。  
   https://github.com/stanfordnlp/dspy/blob/main/docs/docs/learn/optimization/optimizers.md

2. PromptWizard、TextGrad、promptolution 等都在做自动搜索、反馈、反思、离散优化或统一优化框架。PromptWizard 让 LLM 生成、批评、细化 prompts 和 examples；TextGrad 用文本反馈做类似自动微分；promptolution 目标是统一多个离散 prompt optimizer 并输出框架无关 prompt。  
   https://github.com/microsoft/PromptWizard  
   https://arxiv.org/abs/2406.07496  
   https://aclanthology.org/2026.eacl-demo.21/

3. 工程化侧也已有强玩家。promptfoo 做 eval、red teaming、CI/CD、模型对比；Langfuse 做 prompt 存储、版本、部署标签；Phoenix 做 tracing、eval、实验。`pre-vibe` 如果去做这些，会很容易变成低配版。  
   https://github.com/promptfoo/promptfoo  
   https://langfuse.com/docs/prompt-management/overview  
   https://arize.com/phoenix/

4. 现有优化器通常假设你已经有 prompt、样本、metric 或运行轨迹。`pre-vibe` 的机会在更上游：用户只有一句模糊需求时，先生成 `PRE_VIBE_SPEC.md`、`SUGGESTED_AGENTS.md`、`FIRST_STANDARD_PROMPT.md`，把任务边界、上下文、风险、验收标准梳理好。这是 prompt optimization 工具通常不解决的问题。

**建议**

1. 产品定位改成一句话：  
   **“Before the first agent run, compile the context.”**  
   中文可以是：**“让 AI Agent 第一次接手任务时就拿到完整任务包。”**

2. 不要主打“自动提升 prompt 准确率”。主打这些差异点：  
   `需求澄清`、`上下文扫描`、`验收标准生成`、`风险识别`、`AGENTS.md 建议`、`首轮执行 prompt 编译`、`隐私安全扫描策略`。

3. 和优化器做集成，而不是竞争。`pre-vibe` 可以输出：
   - 给 `promptfoo` 的初始 eval cases
   - 给 DSPy/GEPA 的 task description、metric 草案
   - 给 Langfuse/Phoenix 的 prompt metadata、实验说明
   - 给 coding agent 的首轮标准 prompt

4. 增加一个核心卖点：**context provenance**。标明每条要求来自用户原话、项目文件、推断还是假设。这样比普通 prompt 改写工具更可信。

5. 做几个模板场景作为入口：  
   `coding task intake`、`research brief`、`PRD to agent prompt`、`bug report to fix prompt`、`repo onboarding prompt`。这些比泛泛的“优化 prompt”更容易被用户理解和复用。

简短判断：`pre-vibe` 的差异化不是“把 prompt 调到更高分”，而是“在任何优化或执行开始前，把任务变成 agent 可执行、可验证、可复用的上下文包”。