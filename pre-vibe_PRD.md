# pre-vibe 产品价值评估报告

**项目名**：pre-vibe  
**定位建议**：面向 coding agent 的「首轮上下文工程 / prompt-to-spec compiler」  
**目标用户**：初次使用 Agent 的用户、junior builder、非工程背景 builder、PM/设计/运营转代码用户、团队内的 citizen developer  
**报告日期**：2026-06-05  
**结论等级**：建议进入 MVP，优先做轻量 CLI/Skill 版本，而不是一开始做完整自动拦截平台。

---

## 1. Executive Summary

pre-vibe 有明确开发和使用价值，但它的最佳定位不应是普通的 **prompt optimizer**，而应是：

> 在 coding agent 正式开始工作前，将用户模糊的一句话需求转译为可执行、可追踪、可复用的工程上下文包，并生成一份紧凑的首轮注入 prompt。

它解决的不是「模型不会写代码」，而是「用户不会给出足够好的工程任务上下文」。这类问题在 vibe coding 用户中非常常见，尤其是新手、junior builder、非工程背景用户和刚开始使用 Agent 的团队成员。

综合判断：

| 维度 | 评分 | 判断 |
|---|---:|---|
| 用户痛点强度 | 8/10 | 新手常常不知道如何描述需求、约束、验收条件和项目上下文。 |
| 使用频率 | 7/10 | 每个新项目、新 feature、新 bugfix session 都可能触发。 |
| 技术可行性 | 8/10 | 作为 Skill/CLI/插件可快速实现；真正的全自动拦截依赖平台能力。 |
| 差异化空间 | 7/10 | 需从「prompt 优化」升级为「spec compiler + context gate」。 |
| 商业化潜力 | 6.5/10 | C 端个人付费中等；B 端团队 onboarding、bootcamp、内部开发规范更有潜力。 |
| 平台风险 | 7/10 | Codex、Claude Code、Kiro、Cursor 等平台可能内建类似能力。 |
| 总体建议 | **Build MVP** | 先验证“减少修正轮次 / token 浪费 / 返工”的效果。 |

**核心建议**：做，但要缩小 MVP 范围。第一版不要追求“自动拦截所有新 session”，而是做一个显式触发的 `pre-vibe` Skill/CLI：输入原始想法和项目路径，输出 `PRE_VIBE_SPEC.md` 与 agent-specific injection prompt。

---

## 2. 问题定义：为什么新手 vibe coding 容易失败

很多初级用户在开启 Agent session 时，输入通常是：

> “帮我做一个 xxx 网站。”  
> “修一下这个 bug。”  
> “做一个像 Notion 一样的 app。”  
> “帮我把这个项目跑起来。”

这类输入缺少关键工程上下文：

1. **目标不清**：用户想要的是 demo、MVP、生产可用功能、修复 bug，还是学习解释？
2. **边界不清**：哪些功能必须做，哪些功能不做？
3. **项目状态不清**：已有代码、框架、环境、依赖、测试命令、部署目标是什么？
4. **验收标准缺失**：怎样才算完成？是否需要测试？是否要兼容移动端？是否要处理异常状态？
5. **非功能约束缺失**：性能、安全、隐私、权限、可维护性、部署成本等。
6. **Agent 工作方式缺失**：用户不知道该让 Agent 先读文件、先计划、先问问题，还是直接改代码。
7. **上下文污染**：用户在连续纠错中不断补充条件，导致 session 中出现过期假设、废弃方案、错误路径和重复 token。

这不是单纯的 prompt 写作问题，而是 **需求澄清 + 工程上下文建模 + Agent 工作协议设计** 的问题。

近期关于 novice vibe coding 的研究也指出，新手使用 AI coding agent 能快速原型和获得信心，但容易出现过早收敛、代码质量不稳定、工程实践参与不足等问题；研究者明确提出需要更好的脚手架和学习支持。[^novice-vibe]

---

## 3. 现有工具已经覆盖了什么

pre-vibe 不是从零开始创造一个不存在的范式，而是在几个已有趋势的交汇点上做产品化封装。

### 3.1 Codex / coding agent 最佳实践

OpenAI Codex 文档强调，高质量任务通常需要清楚给出目标、上下文、约束和完成标准；Plan mode 可以先读取文件、提出澄清问题并形成计划，之后再执行。Codex 也支持通过 `AGENTS.md` 向 agent 提供项目级说明。[^codex-best][^codex-agents]

这说明 pre-vibe 的方向是符合 agent 开发实践的：

- 先收集任务上下文；
- 再形成计划或 spec；
- 最后进入执行；
- 使用文件化约定减少反复解释。

### 3.2 Claude Code 的 memory / CLAUDE.md / clear context

Claude Code 文档强调，每个 session 会重新开始并在启动时加载 memory；`CLAUDE.md` 适合存放构建命令、测试命令、代码规范、架构说明和团队工作流，但文档也提醒 memory 不应膨胀，过长的说明会消耗上下文并降低遵循度。[^claude-memory][^claude-memory-setup]

Claude Code 最佳实践还强调：context 会快速填满，性能会随上下文变差；如果纠错超过两轮，应该考虑 `/clear` 并用更好的 prompt 重开。[^claude-best]

这与 pre-vibe 的“清理上下文后首轮注入”非常一致：pre-vibe 的价值不是把所有聊天历史塞给 agent，而是把有效信息压缩成一个干净的工程任务文件。

### 3.3 Skills / Plugins / Progressive Disclosure

OpenAI 和 Anthropic 都在推动 Skill 这种“可复用任务能力包”机制。Skills 通常由 `SKILL.md` 和可选 scripts、references、assets 组成，模型先看到 skill 的名称和描述，只有当 skill 被选中时才加载完整说明。[^openai-skills][^codex-skills][^agent-skills]

这对 pre-vibe 很重要：

- pre-vibe 可以作为 Skill 运行；
- Skill 本身不应携带大量固定知识；
- 应采用 progressive disclosure，只在需要时读取模板、项目扫描规则、agent adapter；
- 输出应落地为文件，而不是把所有内容常驻上下文。

### 3.4 Kiro / Spec-driven development

Kiro 的 spec workflow 将一个粗略想法转成 `requirements.md`、`design.md`、`tasks.md` 三类工程文件，并强调先把 vague request 转成结构化需求。[^kiro-specs]

这与 pre-vibe 的方向高度重合，也说明市场正在验证“spec-first coding agent workflow”。但 Kiro 更像一个 IDE/平台内建流程；pre-vibe 可以走更轻、更跨平台、更面向新手的路线。

---

## 4. 仍然存在的产品空白

虽然 Codex、Claude Code、Kiro、Cursor、GitHub Copilot 等工具已有 plan、memory、rules、skills、spec 等能力，但对新手来说，仍存在一个明显空白：

> 新手不知道什么时候该用这些能力，也不知道该如何组织首轮上下文。

现有工具的隐含前提是用户已经知道：

- 应该让 agent 先读哪些文件；
- 应该提供哪些业务约束；
- 应该怎样写 acceptance criteria；
- 应该怎样避免上下文污染；
- 应该把长期项目规则放进 `CLAUDE.md` / `AGENTS.md`，把单次任务信息放进 task spec；
- 应该怎样在不同 agent 之间迁移任务上下文。

但 pre-vibe 的目标用户恰恰不知道这些。

因此 pre-vibe 的真实机会不是“再做一个 Plan mode”，而是：

1. **把新手的一句话输入变成结构化工程任务**；
2. **把隐性工程判断显式化**；
3. **把 Agent 首轮上下文标准化为文件**；
4. **降低 session 中途反复补充、反复推翻、反复返工的概率**；
5. **让用户在使用过程中学习工程表达方式**。

---

## 5. 产品定位建议

### 5.1 不推荐的定位

不建议把 pre-vibe 定位为：

- “更好的 prompt optimizer”
- “自动帮你写完所有代码的 agent”
- “替代 senior engineer 的工具”
- “万能项目经理”
- “把用户所有想法一次性扩成超长 prompt 的工具”

这些定位会导致产品边界不清，也容易被平台内置功能替代。

### 5.2 推荐的定位

推荐定位为：

> **pre-vibe is a first-turn context compiler for coding agents.**  
> 它把 vague vibe coding prompt 转成可执行 spec，并生成适配目标 agent 的首轮注入上下文。

中文表达可以是：

- “vibe coding 的开场白编译器”
- “Agent 开工前的上下文闸门”
- “把一句话想法变成工程 spec 的 pre-flight 工具”
- “面向新手 builder 的 coding agent intake layer”

最推荐的 slogan：

> **Before you vibe, spec the vibe.**

---

## 6. 目标用户和使用场景

### 6.1 一级目标用户

| 用户 | 痛点 | pre-vibe 价值 |
|---|---|---|
| 初次使用 coding agent 的用户 | 不知道 agent 需要什么上下文 | 用问答和模板帮他补齐任务信息 |
| junior builder | 能描述想法，但缺工程拆解能力 | 转成 scope、requirements、tasks、验收标准 |
| 非工程背景创业者 / indie hacker | 会讲产品愿景，不会讲技术细节 | 把产品语言翻译成工程任务 |
| bootcamp / 学习者 | 容易复制粘贴代码但不理解工程流程 | 在使用中学习需求澄清和测试思维 |
| 团队内非专业开发者 | 会用 agent，但输出风格不一致 | 强制使用团队模板和标准 |

### 6.2 次级目标用户

| 用户 | 价值 |
|---|---|
| senior engineer | 个人使用价值较低，但可以用来标准化团队 prompt 和 onboarding。 |
| tech lead | 可以为团队沉淀 task spec 模板、验收标准、代码库扫描规则。 |
| AI coding 工具开发者 | 可以将 pre-vibe 作为 intake / onboarding / plan 前置层。 |

### 6.3 高频场景

1. 新项目初始化：从一句话产品想法生成 MVP spec。
2. 新 feature：从模糊需求生成 feature spec 和 implementation plan。
3. bugfix：从“这里坏了”生成复现步骤、可能原因、调查计划和验证标准。
4. refactor：把“优化一下代码”转成范围、风险、回归测试、禁止行为。
5. UI/UX 改动：把“做得好看点”转成页面状态、组件、交互、响应式标准。
6. 学习/解释模式：把“帮我做”转成“边做边解释，每步让我确认”。

---

## 7. 你提出的 workflow 评估

你当前设想的 workflow：

1. 用户给出一句话或模糊描述；
2. 触发 pre-vibe；
3. 自动拦截并整理 context；
4. brainstorm 式多轮提问；
5. 填入已有答案和 reference；
6. 使用 fetch 检索并摘要更多 reference；
7. 扫描项目文件夹、env、`CLAUDE.md`、`AGENTS.md`、memory、skills/plugins、工作 mode；
8. 生成 prompt spec suggestion；
9. 展示在 session window 并备份 md；
10. 用户补充或确认；
11. clear context 并首轮 prompt 注入；
12. pre-vibe 退出，只保留 md。

整体方向是对的，但建议做三处调整。

### 7.1 从“brainstorm 多轮提问”改成“有预算的澄清”

新手用户最怕被问太多。pre-vibe 应避免像需求访谈一样无限追问。

建议使用 **question budget**：

- Quick mode：最多 3 个问题；
- Standard mode：最多 8 个问题；
- Deep mode：最多 15 个问题；
- 如果用户不回答，系统用明确假设继续，并写入 `Assumptions / Unknowns`。

问题优先级应按影响排序：

1. 目标和完成标准；
2. 用户/使用场景；
3. 范围和非范围；
4. 技术栈/部署环境；
5. 数据、权限、隐私；
6. UI/UX 期望；
7. 测试与验证方式；
8. 时间、复杂度、风格偏好。

### 7.2 从“扩展 context”改成“压缩可执行 context”

pre-vibe 最大风险是把上下文越扩越大。它应该做的是：

- 补齐缺失信息；
- 去重；
- 标注假设；
- 明确风险；
- 把原始信息转成短而强的执行 prompt；
- 把长内容保存到文件，而不是全部注入 session。

推荐输出两层文件：

1. `PRE_VIBE_SPEC.md`：完整任务 spec，可稍长；
2. `PRE_VIBE_INJECTION.md`：真正首轮注入 agent 的紧凑 prompt，建议控制在 1,000–2,000 tokens 内。

### 7.3 从“扫描 env”改成“安全 allowlist 扫描”

不要默认扫描 `.env`、secret、token、私钥、数据库连接字符串。

默认可扫描：

- `README.md`
- `package.json` / `pnpm-lock.yaml` / `requirements.txt` / `pyproject.toml` / `Cargo.toml` 等依赖文件
- `AGENTS.md`
- `CLAUDE.md`
- `.claude/rules/`
- `docs/`
- `src/` 文件树摘要
- 测试目录结构
- 配置文件名和脚本命令

默认不可读取：

- `.env`
- `.env.*`
- private key
- credential files
- token cache
- local database dumps
- production logs with personal data

如果确实需要 env 信息，只读取变量名，不读取变量值，并要求用户确认。

---

## 8. 推荐产品形态

### 8.1 MVP 形态：Skill + CLI

第一版建议做两个入口：

```bash
pre-vibe "build a habit tracker app" --agent codex --project .
pre-vibe "fix the login bug" --agent claude-code --project .
```

以及 Skill 触发方式：

```text
Use pre-vibe to turn this idea into a clean coding-agent spec: ...
```

MVP 不要依赖“平台自动拦截所有新 session”，因为这通常需要宿主平台 API、扩展权限、session lifecycle hook 或 CLI wrapper 支持。显式触发更容易落地。

### 8.2 V1 形态：Agent adapters

为不同 agent 输出不同注入格式：

| Adapter | 输出重点 |
|---|---|
| Codex | `AGENTS.md` 检查、Plan mode 友好 prompt、`Goal / Context / Constraints / Done when`。 |
| Claude Code | `CLAUDE.md` / `.claude/rules` 检查、`/clear` 后注入 prompt、plan-before-editing 指令。 |
| Cursor / Copilot | 文件路径、编辑边界、测试命令、diff 审查指令。 |
| Kiro-like spec flow | `requirements.md`、`design.md`、`tasks.md` 三段式输出。 |

### 8.3 V2 形态：Workspace onboarding layer

团队版可以支持：

- 团队 spec 模板；
- 项目规则检查；
- 安全扫描策略；
- approved stack / forbidden stack；
- PRD-to-task 转换；
- 任务质量评分；
- 历史 session 复盘；
- prompt/spec 版本管理；
- 团队内成功案例模板库。

---

## 9. 核心功能设计

### 9.1 Intent Normalizer

将原始输入拆成：

- 用户真正想要的结果；
- 可能的产品类型；
- 是否已有代码库；
- 是否是新功能、bugfix、refactor、学习任务、部署任务；
- 缺失信息；
- 需要确认的高风险假设。

### 9.2 Context Scanner

读取项目结构并生成摘要：

```text
Project type: Next.js app
Package manager: pnpm
Key scripts: dev, build, test, lint
Existing agent files: CLAUDE.md present, AGENTS.md absent
Test framework: Vitest
Potential entry points: src/app, src/components, src/lib
Risk: .env exists but was not read
```

### 9.3 Clarification Engine

不是随便 brainstorm，而是按任务类型生成高价值问题。

示例：用户说“帮我做一个 AI 简历优化网站”。

pre-vibe 不应问 20 个泛泛问题，而应先问：

1. 这是 demo、MVP 还是生产可用产品？
2. 用户上传简历后，输出应是评分、改写建议、完整重写，还是岗位匹配？
3. 是否需要账号、支付、简历文件存储？
4. 目标技术栈和部署平台是什么？
5. 成功验收标准是什么？

### 9.4 Reference Fetcher

仅在用户需求依赖外部知识时启用：

- API 文档；
- 框架最新版本；
- 第三方服务限制；
- 竞品界面或流程；
- 合规或安全要求；
- 平台部署文档。

所有外部 reference 应写入来源、日期、摘要和使用范围，避免把不可靠信息混进 spec。

### 9.5 Spec Compiler

把原始需求、扫描结果、用户回答、reference 摘要编译成 `PRE_VIBE_SPEC.md`。

### 9.6 Injection Generator

生成最终给 coding agent 的首轮 prompt。

核心原则：

- 短；
- 明确；
- 可执行；
- 带文件路径；
- 带禁止事项；
- 带验收标准；
- 要求 agent 先计划再改代码；
- 要求 agent 在不确定时提出最小必要问题；
- 要求 agent 完成后说明修改文件、测试结果和后续风险。

### 9.7 Context Hygiene

pre-vibe 结束后：

- 不保留闲聊和 brainstorming 上下文；
- 保留 `PRE_VIBE_SPEC.md`；
- 把真正执行 prompt 作为新 session 的第一条消息；
- 必要时在 prompt 中要求 agent 读取 spec 文件，而不是复制整份 spec。

---

## 10. 推荐的 `PRE_VIBE_SPEC.md` 模板

```markdown
# PRE_VIBE_SPEC

## 0. Session Meta
- Created at:
- Target agent:
- Project root:
- Task type: new project | feature | bugfix | refactor | deploy | learning
- Work mode: quick | standard | deep
- Confidence score:

## 1. Raw User Input
> 原始输入，不改写。

## 2. Normalized Goal
用 3-6 句话说明真正要完成什么。

## 3. Background / User / Use Case
- Target user:
- Main scenario:
- Business/product goal:

## 4. Scope
### In Scope
- 必须完成的事项。

### Out of Scope
- 本轮明确不做的事项。

## 5. Requirements
### Functional Requirements
- FR-1:
- FR-2:

### Non-functional Requirements
- Performance:
- Security:
- Privacy:
- Accessibility:
- Maintainability:

## 6. Acceptance Criteria
- AC-1:
- AC-2:
- AC-3:

## 7. Project Context
### Repo Summary
- Framework:
- Language:
- Package manager:
- Key scripts:
- Test framework:

### Relevant Files / Directories
- `path/to/file` — why relevant

### Agent / Memory Files
- `AGENTS.md`:
- `CLAUDE.md`:
- `.claude/rules/`:

## 8. Constraints
- Technical constraints:
- Product constraints:
- Time constraints:
- Style constraints:

## 9. Assumptions and Unknowns
### Assumptions
- A-1:

### Unknowns
- U-1:

## 10. Implementation Plan Suggestion
1. Inspect relevant files.
2. Propose plan.
3. Implement minimal vertical slice.
4. Run tests/lint/build.
5. Report changes and risks.

## 11. Verification Plan
- Commands to run:
- Manual checks:
- Edge cases:

## 12. Risk Register
- Risk:
- Impact:
- Mitigation:

## 13. Final Injection Prompt
复制这里的 prompt 到目标 coding agent 的新 session。
```

---

## 11. Final Injection Prompt 模板

```markdown
You are working in this repository. First read `PRE_VIBE_SPEC.md`, then inspect only the files needed for this task.

Goal:
<normalized goal>

Important context:
- <project summary>
- <constraints>
- <assumptions>

Rules:
1. Do not start editing until you have proposed a short implementation plan.
2. Do not read secret files such as `.env` unless explicitly approved.
3. Keep the first implementation minimal and aligned with the acceptance criteria.
4. If a requirement is ambiguous, ask at most 3 high-impact questions; otherwise continue with stated assumptions.
5. After changes, run or explain the relevant verification commands.

Done when:
- <acceptance criterion 1>
- <acceptance criterion 2>
- <acceptance criterion 3>

Report back with:
- Files changed
- Key decisions
- Verification results
- Remaining risks or follow-up tasks
```

---

## 12. 竞争与替代方案分析

| 方案 | 已有能力 | pre-vibe 的机会 |
|---|---|---|
| Codex Plan mode | 先读文件、问问题、生成计划 | pre-vibe 可以在 Plan 之前生成标准 spec 和可复用上下文文件。 |
| `AGENTS.md` | 项目级 agent 说明 | pre-vibe 更偏单次任务 intake，不污染长期项目规则。 |
| Claude Code `/init` / `CLAUDE.md` | 生成和加载项目 memory | pre-vibe 可区分长期 memory 与本轮 task spec。 |
| Claude Code Skills | 复用任务流程 | pre-vibe 可以作为 Skill，也可以生成其他 Skill-friendly context。 |
| Kiro Specs | requirements/design/tasks | pre-vibe 可做更轻量、跨 agent、面向新手的前置层。 |
| Prompt optimizer | 改写 prompt | pre-vibe 不只改写 prompt，还扫描项目、澄清需求、生成验收标准。 |
| Senior engineer 手写 spec | 高质量但不可规模化 | pre-vibe 把 senior 的上下文工程习惯产品化给新手。 |

---

## 13. 风险与缓解策略

### 13.1 自动触发能力受限

**风险**：作为 Skill/plugin，pre-vibe 可能无法真正拦截所有新 session。很多平台的 Skill 触发是由模型判断或用户显式调用决定的。

**缓解**：MVP 用 CLI wrapper 或显式命令：

```bash
pre-vibe "..." --agent claude-code --project .
```

后续再做 IDE extension、shell alias、MCP server 或平台插件。

### 13.2 追问太多导致用户流失

**风险**：新手想快速开始，不想填长表单。

**缓解**：使用 Quick / Standard / Deep 三档模式，并提供“用默认假设继续”。

### 13.3 context 反而变大

**风险**：pre-vibe 可能把原本短 prompt 扩成超长 spec，导致 token 成本上升。

**缓解**：分离完整 spec 和注入 prompt。注入 prompt 必须短，完整内容留在文件中。

### 13.4 错误 reference 污染任务

**风险**：fetch 到过时 API、错误教程或不相关竞品信息。

**缓解**：reference 必须有来源、日期、摘要、置信度和使用范围。外部信息不能直接成为强约束，除非用户确认。

### 13.5 安全与隐私风险

**风险**：扫描项目时读取 `.env`、token、私钥、用户数据。

**缓解**：默认 denylist secret 文件；只读 allowlist；支持 dry-run 显示将读取哪些文件；输出前自动 redaction。

### 13.6 平台内建替代

**风险**：Codex、Claude Code、Kiro 等平台可能内建更强的 intake/spec 功能。

**缓解**：做跨平台、模板化、团队规范、评估指标和历史 spec 管理。不要只做单平台 UI 小功能。

---

## 14. 商业化判断

### 14.1 个人版

个人版适合：

- indie hacker；
- bootcamp 学生；
- junior developer；
- 非工程背景 builder；
- AI coding heavy user。

可能付费点：

- 高质量模板包；
- agent-specific adapters；
- 项目扫描；
- 一键生成 spec；
- 历史 spec 管理。

但 C 端单独付费意愿可能有限，因为很多用户会认为“我可以直接问 ChatGPT”。

### 14.2 团队版

团队版更有商业潜力：

- 团队统一 AI coding 开工流程；
- 新人 onboarding；
- 内部工具开发规范；
- 安全扫描策略；
- team memory / task spec 模板；
- 避免 junior 使用 agent 乱改代码；
- 形成可审计的 task spec 记录。

团队版可以按 seat、workspace 或 template pack 收费。

### 14.3 教育版

对 bootcamp、AI 编程课程、创业营也有价值：

- 教学生如何把想法变成需求；
- 教 acceptance criteria；
- 教测试和范围管理；
- 减少“AI 帮我写了但我不知道发生了什么”的问题。

---

## 15. 成功指标设计

MVP 应该用可测指标验证，而不是只看主观感觉。

### 15.1 核心指标

| 指标 | 目标 |
|---|---|
| 首次计划可接受率 | 使用 pre-vibe 后，agent 第一版 plan 被用户接受的比例提升。 |
| 修正轮次 | 从初始 prompt 到可执行方案的往返轮次下降。 |
| Token 消耗 | 到达“开始写代码”前的 token 降低或更可控。 |
| 任务完成率 | 相同任务下完成率提升。 |
| 测试通过率 | 生成代码通过 lint/test/build 的比例提升。 |
| 上下文污染率 | session 中过期假设、反复推翻方案、无关聊天减少。 |
| 用户信心 | 新手用户是否更清楚 agent 在做什么。 |

### 15.2 实验设计

做一个简单 A/B test：

- 20 个常见任务；
- 10–20 名新手用户；
- A 组直接把想法给 agent；
- B 组先经过 pre-vibe；
- 比较：完成时间、修正次数、token、代码质量、测试结果、用户满意度。

任务样例：

1. 做一个习惯追踪 app；
2. 给现有 Next.js 项目加登录；
3. 修复表单提交 bug；
4. 把页面改成响应式；
5. 接入 Stripe 测试支付；
6. 给 API 加权限检查；
7. 重构一个混乱组件；
8. 添加单元测试；
9. 部署到 Vercel；
10. 解释并清理旧代码。

---

## 16. MVP 范围建议

### 16.1 必做

1. 显式触发：`pre-vibe "task" --project . --agent claude-code`。
2. 项目 allowlist 扫描。
3. 任务类型识别。
4. 最多 8 个澄清问题。
5. 生成 `PRE_VIBE_SPEC.md`。
6. 生成 `PRE_VIBE_INJECTION.md`。
7. 支持 Codex 和 Claude Code 两个 adapter。
8. 支持 Quick / Standard / Deep 三档。
9. 不读取 secret 文件。
10. 提供 `--no-fetch`，避免不必要外部检索。

### 16.2 暂缓

1. 真正自动拦截所有新 session；
2. 完整 GUI；
3. 多 agent 编排；
4. 全自动代码执行；
5. 长期 memory 管理；
6. 团队权限系统；
7. marketplace plugin；
8. 完整 eval dashboard。

### 16.3 第一版文件结构

```text
pre-vibe/
  SKILL.md
  references/
    spec-template.md
    question-bank.md
    agent-adapters.md
    scan-policy.md
  scripts/
    scan_project.py
    redact.py
    generate_spec.py
  assets/
    examples/
      new-project.md
      feature.md
      bugfix.md
      refactor.md
```

如果按 Skill 标准设计，`SKILL.md` 应保持短小，只负责触发条件和流程导航；长模板、问题库、扫描策略应放到 references 中，避免常驻上下文。

---

## 17. 推荐路线图

### Phase 0：手动验证，1 周

- 不写完整工具；
- 用固定 Markdown 模板和人工流程跑 10 个真实任务；
- 验证用户是否愿意在 coding 前回答几个问题；
- 观察生成 spec 是否真的减少后续返工。

### Phase 1：MVP CLI + Skill，2–4 周

- CLI 读取项目结构；
- 生成 spec；
- 输出 agent-specific injection；
- 支持 Codex / Claude Code；
- 加 secret redaction；
- 收集指标。

### Phase 2：模板化与 adapter，4–8 周

- 新项目、feature、bugfix、refactor、deploy、learning 六类模板；
- 支持更多 agent；
- 支持团队模板；
- 支持历史 spec 目录。

### Phase 3：团队版，8–12 周

- workspace config；
- team policy pack；
- onboarding flow；
- spec review；
- task quality scoring；
- eval dashboard。

---

## 18. 最终判断

pre-vibe 值得做，尤其适合当下 coding agent 普及但用户工程素养参差不齐的阶段。

它的核心价值不是让 senior engineer 更强，而是让 beginner 不再用一句混乱 prompt 把 agent 带偏。对于 senior engineer，pre-vibe 的价值更多是团队流程标准化和新人 onboarding；对于 junior 和非工程用户，它可以直接提高 task framing、执行质量和学习效率。

最重要的是：

> pre-vibe 不应该追求“生成更多上下文”，而应该追求“生成更少但更正确、更稳定、更可执行的上下文”。

如果你能把它做成一个轻量、跨 agent、安全、可测量的首轮 context compiler，它有真实的产品机会。

建议下一步不是立即做复杂插件，而是先做一个可以跑真实任务的 MVP：

```bash
pre-vibe "<用户原始想法>" --project . --agent claude-code --mode standard
```

输出：

```text
PRE_VIBE_SPEC.md
PRE_VIBE_INJECTION.md
```

然后用 A/B test 证明：

- 修正轮次下降；
- token 浪费下降；
- agent 第一版计划质量上升；
- 代码通过测试概率上升；
- 新手用户更能理解项目执行路径。

如果这些指标成立，pre-vibe 就不只是一个 prompt 工具，而是 coding agent 工作流里的“开工前标准化层”。

---

## 19. 参考资料

[^codex-best]: OpenAI Developers, *Codex best practices*. Key points: task context, Plan mode, AGENTS.md, skills and clear task prompts. https://developers.openai.com/codex/learn/best-practices

[^codex-agents]: OpenAI Developers, *AGENTS.md*. Key points: Codex reads `AGENTS.md` before work and builds an instruction chain from global/project files. https://developers.openai.com/codex/guides/agents-md

[^codex-skills]: OpenAI Developers, *Codex Skills*. Key points: skills extend Codex with task-specific instructions, references, scripts and progressive disclosure. https://developers.openai.com/codex/skills

[^codex-plugins]: OpenAI Developers, *Codex Plugins*. Key points: plugins bundle skills, apps and MCP servers as installable distributions. https://developers.openai.com/codex/plugins

[^claude-memory]: Anthropic, *Claude Code memory*. Key points: sessions start fresh, `CLAUDE.md` and auto memory are loaded at start, concise instructions work better. https://code.claude.com/docs/en/memory

[^claude-memory-setup]: Anthropic, *Claude Code memory setup*. Key points: project memory should include build/test commands, coding standards, architecture notes and common workflows; long memory files consume context. https://code.claude.com/docs/en/memory

[^claude-best]: Anthropic, *Claude Code best practices*. Key points: context fills quickly, performance degrades, use `/clear` and stronger prompts when sessions become cluttered. https://code.claude.com/docs/en/best-practices

[^claude-workflows]: Anthropic, *Claude Code common workflows*. Key points: planning before editing, asking Claude to inspect files and propose plans before implementation. https://code.claude.com/docs/en/common-workflows

[^openai-skills]: OpenAI Developers, *Skills guide*. Key points: a skill is a versioned bundle with `SKILL.md`; name/description/path are exposed and full instructions load when invoked. https://developers.openai.com/api/docs/guides/tools-skills

[^agent-skills]: Agent Skills, *Open standard for AI agent skills*. Key points: skill folders can include `SKILL.md`, scripts, references and assets with progressive disclosure. https://agentskills.io/home

[^kiro-specs]: Kiro Docs, *Specs concepts*. Key points: specs bridge product requirements to technical implementation and generate requirements, design and tasks from rough ideas. https://kiro.dev/docs/specs/concepts/

[^novice-vibe]: *Vibe Coding with AI: Conversational Programming and Learning with an AI Coding Assistant among Novice Programmers*, arXiv preprint. Key points: novice vibe coding supports rapid prototyping but risks premature convergence, uneven code quality and weak engineering practice engagement. https://arxiv.org/abs/2510.12399

[^vibe-survey]: *Vibe Coding in Practice: A Survey of Insights, Realities, and Strategies*, arXiv preprint. Key point: successful vibe coding depends on systematic context engineering, established development environments and human-agent collaboration models. https://arxiv.org/abs/2601.18341

[^spec-kit-agents]: *Spec Kit Agents: Grounding Coding Agents in Large-Scale Repositories*, arXiv preprint. Key point: repository-scale coding agents can suffer from context blindness; context-grounding hooks can improve performance. https://arxiv.org/abs/2604.05278

[^agents-md-study]: *Agent-Native Software Engineering: Initial Evidence from AGENTS.md Practices*, arXiv preprint. Key point: repository-level agent instructions are associated with lower runtime and token consumption in studied projects. https://arxiv.org/abs/2509.14744


##20. 我补充的要点

1. 需要参考更多已有的开源项目（例如：https://github.com/topics/prompt-optimization 中最近更新和star数最多的项目）和其他 Agent Plan Mode 的设计标准。 的实现，尤其是OPENAI和ANTHROPIC的官方文档和cookbook中的最佳实践（信息差之一）
2. 关注使用场景的泛用性，pre-vibe 是一般事务性工作，研究工作和代码开发工作都可以使用的context优化工具，而不只是像superpowers一样专为代码开发设计，面向普通用户和对prompt engineering不太了解，甚至都不太了解正在使用的agent的相关功能的用户
3. 首选以 codex plugin 的技术标准和形式开发第一版MVP
4. 主要产品亮点是：摆脱单纯的 text2text 的 prompt optimizer形式，针对Agent workflow中的具体env/project细节，以及用户的个人需求，补充信息差（重要），生成类tutorial的suggestions spec和可直接注入执行的标准工程文本，同时要尽量压缩本工具的token消耗，不干扰正常工作流。
5. 中英双语，以用户界面语言设置和初始输入语言为准，用户可通过提示词/设置自主调整
6. 生成文本应该包括spec，suggested AGENTS.md 和 First standard prompt 三个部分

##21. 新的review
你的测试结果其实很正常：**pre-vibe 提升质量，但 token 不降反升，说明它现在更像“context expander”，还不是“context optimizer”。**

真正要优化的方向不是“把生成的 spec 写短一点”，而是把 pre-vibe 改成一个 **预算驱动的 context compiler**：先判断任务复杂度和不确定性，再决定要问多少、扫多少文件、fetch 多少 reference、注入多少内容。

## 一句话结论

pre-vibe 的 token 增加，大概率来自这几个地方：

1. 每次都走完整 discovery / brainstorm / scan / fetch / spec 流程。
2. 把“给人看的 spec”和“给 agent 执行的 injection prompt”混在一起注入。
3. 过度补充背景知识，把 reference summary、项目扫描结果、用户原话、推理过程都塞进首轮 prompt。
4. 没有区分日常事务、研究、coding 三类任务的上下文密度。
5. 没有做 context budget、去重、缓存、分层加载和按需召回。

所以优化重点应该是：

> **长期保存完整 spec，首轮只注入最小可执行上下文。**

也就是：
`用户模糊输入 → pre-vibe 生成完整 PRE_VIBE_SPEC.md → 压缩成 EXECUTION_BRIEF → 只注入 brief + 文件路径 + 执行规则`

而不是：
`用户模糊输入 → 生成很完整的 spec → 把完整 spec 全部喂给 agent`

---

# 1. 先给 pre-vibe 加一个 Token Budget Controller

你现在应该在 pre-vibe 开头就做任务分级，不要默认进入完整流程。

建议分成四档：

| 模式          | 适用任务                    | pre-vibe 行为        | 目标注入长度                    |
| ----------- | ----------------------- | ------------------ | ------------------------- |
| `micro`     | 日常事务、简单写作、小改动           | 不扫项目、不 fetch、不多轮追问 | 300-800 tokens            |
| `standard`  | 普通研究、简单功能开发             | 最多 3 个问题，轻量 scan   | 800-1800 tokens           |
| `deep`      | 多文件 coding、产品 spec、复杂研究 | 允许 scan/fetch/多轮澄清 | 1800-3500 tokens          |
| `architect` | 新项目、重构、系统设计             | 完整 spec-first 流程   | 3500-6000 tokens，但必须分阶段注入 |

关键是：**token budget 要成为硬约束，不是建议。**

可以在 plugin 里增加：

```yaml
context_budget:
  micro:
    max_questions: 0
    max_fetches: 0
    max_scanned_files: 0
    max_injection_tokens: 800

  standard:
    max_questions: 3
    max_fetches: 2
    max_scanned_files: 10
    max_injection_tokens: 1800

  deep:
    max_questions: 6
    max_fetches: 5
    max_scanned_files: 30
    max_injection_tokens: 3500

  architect:
    max_questions: 10
    max_fetches: 8
    max_scanned_files: 80
    max_injection_tokens: 6000
```

pre-vibe 的第一步不应该是“扩展上下文”，而应该是：

```text
Classify task:
- scenario: daily | research | coding
- complexity: micro | standard | deep | architect
- uncertainty: low | medium | high
- risk: low | medium | high
- context budget: ...
```

如果分类结果是 `micro`，pre-vibe 甚至应该几乎不出现，只做轻微 rewrite。

---

# 2. 把“完整 Spec”和“首轮注入 Prompt”彻底分离

这是最重要的优化。

你现在的 workflow 里有：

> 生成 prompt spec suggestion 文档，展示并备份 md 到项目文件夹，然后 clear context 并进行首轮 prompt 注入。

这里的问题是：**如果首轮注入还是把 spec 的大部分内容带进去，就没有省 token。**

应该改成两个文件：

```text
.pre-vibe/
  PRE_VIBE_SPEC.md          # 给人看、给后续查阅，完整
  EXECUTION_BRIEF.md        # 给 agent 首轮注入，极短
  CONTEXT_INDEX.md          # 可按需读取的引用索引
  DECISIONS.md              # 用户确认过的关键决定
```

然后首轮只注入 `EXECUTION_BRIEF.md` 的内容。

## 推荐的 EXECUTION_BRIEF 模板

```md
# Execution Brief

## Goal
{一句话目标}

## Current Task
{本轮只做什么}

## Hard Constraints
- {最多 3-7 条}

## Relevant Context
- Spec file: .pre-vibe/PRE_VIBE_SPEC.md
- Decision log: .pre-vibe/DECISIONS.md
- Read these only if needed: {路径列表}

## Done When
- {可验证验收标准}

## Operating Mode
Start with a short plan. Do not read unrelated files. Ask only blocking questions. Prefer smallest safe change.
```

这个 brief 应该控制在 **400-1200 tokens**。

完整 spec 只作为文件路径存在，不直接进入上下文。Agent 后续需要时再读。

---

# 3. 引入“Context Pyramid”：不要平铺上下文

pre-vibe 现在的问题可能是把所有 context 都平铺到了 prompt 里。应该改成金字塔结构：

```text
Level 0: Task intent
Level 1: Execution brief
Level 2: Decisions / constraints
Level 3: Relevant files index
Level 4: Full spec
Level 5: Raw references / scan logs / fetched docs
```

首轮注入只包含 Level 0-2，最多带一点 Level 3。

不要注入 Level 4-5。

也就是：

```text
注入：目标、约束、当前任务、验收标准、必要路径
不注入：完整 brainstorming、长 reference 摘要、所有项目结构、所有问题答案
```

一个很实用的规则：

> **任何不能直接影响下一步动作的内容，都不要进入首轮 prompt。**

---

# 4. 对三类场景使用不同策略

你已经测了日常事务、研究、coding，这很好。它们不能共用一个 pre-vibe 流程。

## A. 日常事务：pre-vibe 应该极轻

日常事务的目标通常不是“工程化”，而是“明确输出”。

优化策略：

```text
不要 scan
不要 fetch
不要生成完整 spec
不要多轮追问
只做 intent normalization + output contract
```

输出结构可以是：

```md
Goal:
Output:
Audience:
Tone:
Constraints:
Missing info:
Next action:
```

首轮注入 300-600 tokens 足够。

如果日常任务还跑完整 spec 流程，token 一定亏。

## B. 研究任务：用“检索计划”替代“检索摘要全注入”

研究场景最容易 token 爆炸，因为 fetch 出来的 reference summary 很长。

建议改成：

```text
不要把所有 fetch summary 注入
只注入 source map + research questions + evidence requirements
```

例如：

```md
Research Plan:
- Question 1: ...
- Question 2: ...

Source Map:
- source A: useful for market size
- source B: useful for competitor claims
- source C: useful for implementation examples

Use policy:
Only open/read sources when answering a specific section.
```

也就是说，pre-vibe 不应该替 agent 完成完整研究，只应该生成 **research scaffold**。

研究场景的 token 优化关键是：

> fetch 的结果默认进 `.pre-vibe/references/`，不要默认进 prompt。

## C. Coding：只注入 change set，不注入全项目理解

coding 场景最该节省 token，因为项目文件本来就在磁盘上。

不要把项目扫描摘要写成一大段塞给 agent。应该生成：

```md
Relevant Files:
- src/app/page.tsx — likely entry point
- src/lib/db.ts — database helper
- package.json — scripts/dependencies

Do Not Touch:
- migrations/
- generated/
- vendor/

First Step:
Read only package.json and src/app/page.tsx before editing.
```

首轮注入的重点不是“我已经理解整个项目”，而是：

> **我知道 agent 第一批应该读哪些文件，不应该读哪些文件。**

项目扫描的产物应该是 `CONTEXT_INDEX.md`，不是 prompt 正文。

---

# 5. 加一个“信息增益阈值”，避免无效追问

brainstorm 多轮提问很容易提升质量，但也很耗 token。

建议给每个问题打分：

```text
Question value = impact_on_execution × uncertainty_reduction × irreversibility_risk
```

只有高于阈值才问。

更简单的产品规则：

```text
Only ask if the answer would change:
1. architecture
2. data model
3. external dependency
4. user-facing behavior
5. acceptance criteria
6. irreversible operation
```

否则不要问，直接写入 Assumptions。

例如不要问：

```text
你希望这个工具更现代还是更简洁？
```

改成：

```text
Assumption: Use a minimal, maintainable implementation unless user specifies visual polish.
```

在 spec 里增加：

```md
## Assumptions
- A1: ...
- A2: ...

## Blocking Questions
- Q1: ...
```

首轮最多问 1-3 个 blocking questions。其他都变成 assumptions。

---

# 6. 做“Context Diff”，不要每轮重复注入

pre-vibe 的另一个 token 黑洞是重复。

如果用户补充信息后，每次都重新生成完整 spec 并注入，token 会持续增长。

应该维护：

```text
base_spec
new_user_input
diff
updated_decisions
new_execution_brief
```

后续只注入 diff：

```md
Context Update:
- Changed: target platform is now iOS first
- Added: must support offline mode
- Removed: web dashboard is no longer in scope

Continue using:
- .pre-vibe/PRE_VIBE_SPEC.md
- .pre-vibe/DECISIONS.md
```

不要重新注入完整上下文。

---

# 7. 引入“压缩等级”，让用户或系统选择

建议加三个 compression modes：

```yaml
compression:
  terse:
    style: bullets only
    max_tokens: 700
    no_rationale: true

  balanced:
    style: compact structured markdown
    max_tokens: 1500
    include_rationale: only_for_tradeoffs

  full:
    style: full spec
    max_tokens: 4000
    include_rationale: true
```

默认应该是 `balanced`，而不是 `full`。

日常事务默认 `terse`。
coding 默认 `balanced`。
复杂 architecture 才允许 `full`。

---

# 8. 给 pre-vibe 加“负向规则”：明确禁止做什么

你现在的工具可能太积极了。要加一些硬规则：

```md
Do not expand context unless it changes execution.
Do not include raw references in the injection prompt.
Do not include brainstorming history in the injection prompt.
Do not summarize the entire repository.
Do not ask non-blocking preference questions.
Do not include implementation tutorial content unless the user is learning.
Do not include both a full spec and an execution brief in the same injection.
Do not fetch external references for routine coding tasks unless dependency/API uncertainty is high.
Do not scan files outside likely task boundaries.
```

这些负向规则比“请尽量简洁”有效得多。

---

# 9. 把“质量提升”和“token 节省”拆成两个指标

你现在看到的是：质量提升，但 token 增加。

这说明 pre-vibe 已经证明了“上下文结构化有价值”，但还没证明“成本效率有价值”。

建议用下面这几个指标重新评估：

```text
Quality Lift:
- first-pass success rate
- number of correction turns
- number of bugs introduced
- user satisfaction

Token Cost:
- pre-vibe tokens
- first execution tokens
- follow-up correction tokens
- total session tokens

Efficiency:
- tokens per accepted outcome
- tokens per merged change
- correction turns avoided per 1k extra tokens
```

关键不是总 token 是否一定下降，而是：

> **单位成功结果的 token 是否下降。**

有些复杂任务，pre-vibe 前置多花 2k tokens，但减少后面 8 轮返工，整体是赚的。
但日常任务如果多花 1k tokens 只减少半轮返工，就是亏的。

---

# 10. 推荐你下一版 MVP 改成这个流程

```text
1. classify task
2. assign budget
3. normalize user intent
4. decide whether to ask, scan, fetch
5. generate full spec only if useful
6. generate tiny execution brief
7. save full artifacts to project
8. inject only execution brief
9. track token delta and outcome
```

更具体一点：

```text
User input
  ↓
Pre-vibe Router
  ↓
Scenario: daily / research / coding
Complexity: micro / standard / deep / architect
  ↓
Budget Policy
  ↓
Context Acquisition
  - questions only if blocking
  - scan only if coding/deep
  - fetch only if research/API uncertainty
  ↓
Artifact Generation
  - PRE_VIBE_SPEC.md
  - CONTEXT_INDEX.md
  - EXECUTION_BRIEF.md
  ↓
Injection
  - only EXECUTION_BRIEF.md
  - references by path
  ↓
Agent Work
```

---

# 11. 一个可以直接放进 plugin 的优化版核心指令

你可以把下面这段加入 pre-vibe 的主指令里：

```md
# Token Discipline

Pre-vibe is a context compiler, not a context expander.

Before generating any output, classify the request by scenario, complexity, uncertainty, and risk. Assign a context budget. The budget is a hard limit.

Generate durable project artifacts when useful, but never inject the full artifact by default. The session injection must be a compact Execution Brief containing only:
- goal
- current task
- hard constraints
- key assumptions
- relevant file/source pointers
- done-when criteria
- operating mode

Do not include brainstorming history, raw references, full project summaries, long rationale, or non-actionable background in the injection.

Ask only blocking questions. Convert non-blocking unknowns into explicit assumptions.

For coding tasks, prefer file pointers over file summaries. For research tasks, prefer source maps over long source summaries. For daily tasks, skip scan/fetch/spec unless the task is high-risk or ambiguous.

If the Execution Brief exceeds the budget, compress in this order:
1. remove rationale
2. remove examples
3. collapse background into assumptions
4. replace summaries with file/source pointers
5. narrow current task scope
```

---

# 12. 我建议你的下一轮实验设计

你可以做一个 A/B/C 测试：

## A: No pre-vibe

原始用户 prompt 直接给 agent。

## B: Current pre-vibe

你现在的完整流程。

## C: Budgeted pre-vibe

加入 router、budget、brief-only injection。

然后按场景分别测：

| 场景     | 主要看什么                                                 |
| ------ | ----------------------------------------------------- |
| 日常事务   | 总 token 是否下降                                          |
| 研究     | 引用质量 / 幻觉率 / source reuse                             |
| coding | first-pass success / bug 数 / 文件读取量 / correction turns |

预期结果应该是：

```text
日常事务：C 应该明显少于 B，接近 A，但质量略高于 A
研究任务：C 可能 token 不一定最低，但 source 更稳
coding 任务：C 应该比 B 少很多 token，同时保留大部分质量提升
```

---

# 13. 最关键的产品判断

pre-vibe 不应该追求：

```text
让每个任务都变得更完整
```

而应该追求：

```text
用最小必要上下文，让 agent 第一步不要走错
```

你现在的 MVP 已经证明了前半句：结构化上下文能提高执行质量。
下一步要证明的是后半句：**结构化上下文可以被压缩成最低成本的执行 brief。**

我的建议是把下一版定位从：

> prompt optimizer

进一步改成：

> budget-aware context compiler for agent sessions

产品机制上从：

> expand vague intent into full context

改成：

> compile vague intent into durable spec + minimal execution brief

这会更接近真正能规模化使用的形态。

