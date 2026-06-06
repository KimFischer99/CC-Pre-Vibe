# pre-vibe v0.4 架构报告

## 目标

pre-vibe 是原生 Codex Plugin 工作流，不是单一 skill，也不是 Python 文本模板生成器。它的目标是在新 session 开始时，把用户短小、模糊、混乱或高风险的初始需求整理成可执行上下文：先索引项目和 Codex 环境，再通过原生提问 UI 澄清阻塞问题，最后生成定制化文档并只注入紧凑的 first prompt。

本版实现版本：`0.4.0+codex.20260606200430`。

## 关键决策

| 要求 | v0.4 实现 |
|---|---|
| 只参考 spec-kit / agents.md 的文档规划，不借鉴形式 | SPEC 采用需求、用户场景、验收、边界、成功标准等规划思想；AGENTS 采用“给 agent 的 README”思想；运行形态仍是 Codex Plugin。 |
| 绝对不是单一 skill | 保留 `.codex-plugin/plugin.json`、MCP companion、workflow skill、slash prompt source、命令源文件和部署脚本。 |
| 必须 slash 启动 | 新增 `prompts/pre-vibe.md`、`commands/pre-vibe.md`，并用 `install_slash_prompt.py` 安装到 `~/.codex/prompts/pre-vibe.md`。当前 Codex 官方文档公开保证 custom prompt slash 入口；非交互 CLI 无法证明 App/CLI 候选窗是否裸显示 `/pre-vibe`，但已提供命名为 `pre-vibe` 的 command source。 |
| 询问前必须扫描 | `route_intake()` 默认执行项目执行索引和 Codex 组件索引；状态判断先检查 context evidence，再允许 `NEEDS_USER_INPUT`。 |
| 使用原生提问 UI | `BlockingQuestion` 输出 `header`、`options`、`requires_native_ui=true`；workflow 指令禁止把阻塞问题直接写到普通聊天。若当前 surface 没有 native question/user-input UI，必须停在该状态。 |
| 三档强度 | `mini/default/architect` 的问题上限为 `3/5/10`；三档都做项目和组件索引，只调整扫描深度、fetch 深度和文档详略。 |
| 文档必须定制 | `write_artifacts()` 只负责写入 LLM 已生成内容，不生成正文；规则要求基于用户输入、项目证据、环境证据和用户答案写作。 |
| 文件名调整 | `INIT_AGENTS.md` 已替换为 `PROJECT_AGENTS.md`。 |
| SPEC / PROJECT_AGENTS 不互相引用 | 写入时强制校验：SPEC 不得包含 `PROJECT_AGENTS.md`，PROJECT_AGENTS 不得包含 `PRE_VIBE_SPEC.md`，任一最终文档不得引用旧 `INIT_AGENTS.md`。 |
| AGENTS 不冲突 | PROJECT_AGENTS 必须参考全局 AGENTS，且不得削弱或冲突。 |

## 工作流

```text
slash or natural trigger
  -> INTAKE_STARTED
  -> NEEDS_CONTEXT
       - safe project execution index
       - Codex component/plugin/skill/slash prompt index
       - optional source map / fetch
  -> NEEDS_USER_INPUT
       - only if blocking answers remain
       - native question/user-input UI only
  -> READY_TO_COMPILE
       - write PRE_VIBE_SPEC.md
       - write PROJECT_AGENTS.md
       - write FIRST_PROMPT.md
  -> AWAITING_APPROVAL
  -> READY_TO_INJECT
       - pre-vibe clears context
       - inject FIRST_PROMPT.md only
  -> DONE
```

## 核心实现

- `scripts/pre_vibe.py`
  - `route_intake()`：分类任务、选择强度、强制索引、生成状态和问题。
  - `safe_walk()`：allowlist 项目扫描，跳过 secrets、依赖、构建产物。
  - `inspect_codex_environment()`：扫描全局 AGENTS、plugin cache、enabled plugins、marketplace plugins、skills、slash prompt files。
  - `component_suggestions_for()`：基于任务和已安装组件生成组件使用建议或缺口建议。
  - `write_artifacts()`：只写入已生成内容，并执行文件名/交叉引用校验。
- `scripts/mcp_server.py`
  - 暴露 `classify_intake`、`scan_project_safe`、`inspect_codex_environment`、`write_pre_vibe_artifacts`。
  - `classify_intake.scan` 默认 `true`，防止再次出现“无搜索、无扫描、直接生成模板”的路径。
- `prompts/pre-vibe.md`
  - Codex custom prompt command source。
  - 安装后位于 `~/.codex/prompts/pre-vibe.md`。
- `commands/pre-vibe.md`
  - 为支持插件命令文件发现的 Codex 版本保留同源命令入口。

## 文档生成规则

`PRE_VIBE_SPEC.md` 面向用户和初级 builder。它应写成项目 handbook，包含原始需求、标准化目标、用户场景、范围、需求、验收标准、项目证据、组件建议、风险、建议和下一步。它可以解释为什么这么做，但不能提到 agent 指导文件的文件名或路径。

`PROJECT_AGENTS.md` 面向 Codex。它只保留项目执行规则、命令、目录边界、安全约束、验证方式、全局 AGENTS 继承和冲突规则。它不能包含教程式解释，也不能提到 handbook 文件名或路径。

`FIRST_PROMPT.md` 是唯一默认注入内容。它可以引用必要的生成文件和项目文件，但必须压缩成目标、当前任务、硬约束、关键假设、相关上下文、完成标准和操作模式。

## 部署证据

- 源包 validator 通过：`pre-vibe-plugin`
- 部署目录 validator 通过：`/Users/kimfischer99/plugins/pre-vibe`
- installed cache validator 通过：`~/.codex/plugins/cache/personal/pre-vibe/0.4.0+codex.20260606200430`
- `codex plugin list --marketplace personal` 显示 installed/enabled 版本 `0.4.0+codex.20260606200430`
- slash prompt 已安装：`~/.codex/prompts/pre-vibe.md`

## 边界

官方 Codex 手册目前明确公开的 slash 扩展是 custom prompt command，示例调用形式为 `/prompts:name`。插件文档公开列出的 bundle 能力是 skills、apps、MCP servers；本地 validator 也不接受 manifest 级 `commands` 字段。因此 v0.4 已实现可分发的插件包和 slash prompt source，但裸 `/pre-vibe` 是否直接出现在候选窗，需要在 Codex App/CLI 交互 UI 里最终确认。
