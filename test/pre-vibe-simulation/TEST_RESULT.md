# pre-vibe v0.4 模拟测试报告

## 场景

测试在独立目录 `test/pre-vibe-simulation/` 中运行，不在插件包内部。模拟用户通过 slash prompt 启动：

```text
/prompts:pre-vibe "请把 test/pre-vibe-simulation/feature-brief.md 整理成一个可执行的小功能：添加状态字段、验收清单和维护者备注，别改其他文件。"
```

父进程执行 `run_simulation.py`，worker 子进程完成 pre-vibe 路由、三份文档生成和正式任务编辑。

## 结果

| 检查项 | 结果 |
|---|---|
| 项目执行索引在提问前完成 | 通过 |
| Codex 组件索引存在 | 通过 |
| 桌面逆向失败提示词会进入 native UI 问题状态 | 通过 |
| SPEC 和 PROJECT_AGENTS 无互相文件名引用 | 通过 |
| 未生成 INTAKE.md 或同类草稿 | 通过 |
| 正式任务完成 | 通过 |

生成文件：

- `generated/PRE_VIBE_SPEC.md`
- `generated/PROJECT_AGENTS.md`
- `generated/FIRST_PROMPT.md`
- `feature-brief.md`

本地运行还会生成 `generated/.pre-vibe/status.json`、`simulation-result.json` 和 `child-process.log`。这些文件包含运行快照或本机路径，只作为本次验证证据保留在工作区，不纳入提交。

正式任务已把 `feature-brief.md` 更新为包含状态、验收清单和维护者备注。

## Token 估算

本测试使用插件内 `estimate_tokens()` 的近似估算，不是 Codex 服务器真实计费数据。

| 阶段 | 估算 token |
|---|---:|
| slash prompt 输入 | 37 |
| pre-vibe decision JSON | 1089 |
| 三份生成文档 | 776 |
| formal first prompt | 241 |
| formal 读写目标文档上下文 | 238 |
| 合计 | 2381 |

## 关键观察

- default 档位没有阻塞问题时直接进入 `READY_TO_COMPILE`，但不是跳过 intake：结果中先出现 `project_execution_index`，再出现 `codex_component_index`。
- 控制样例 `我要逆向桌面上的这个东西，要用上pre-vibe` 进入 `NEEDS_USER_INPUT`，问题包含 `requires_native_ui=true`，不会再直接生成无用文档。
- 生成文档围绕用户指定的 `feature-brief.md`，不是插件组件模板说明。
