# cc-workflow

Claude Code 的轻量级 agent 工作流框架。捕获用户意图、协调跨意图语义关系，通过反馈回路交给下游 Spec / Architecture / Module。

## 工作流

```text
User → Intent ──→ Reconcile (跨 Intent) ──→ Spec ──→ Architecture ──→ Module / Implementation
        ↑                    │
        └────── /intent feedback ←── 下游问题回流
```

Intent 层是用户目标的权威来源。下游发现问题通过 `/intent feedback` 回流，由 Intent skill 判定归属后改 Intent（需用户确认）或重定向。

## Skills

| Skill | 用途 |
|---|---|
| `intent` | 捕获、澄清、持久化、演化用户 Intent |
| `intent-reconcile` | 比较两个或多个 Intent，提出语义协调方案 |
| `spec` | 把澄清后的 Intent 转化为可验证、可追溯的系统需求 |
| `architecture` | 维护系统架构基线，划定模块边界、公共能力归属、依赖方向 |
| `module-design` | 在已确认的基线之上独立设计一个模块的公共契约与内部设计，并向 Implementation 交付可执行的设计结果 |
| `implementation` | 在已确认的 DESIGN.md 之上编写可运行代码、可执行测试与运行证据；对重要交付调用 Reviewer；对发现的上游错误跨层回溯修复 |
| `workflow` | 只读地从 Git、条目引用、契约和验证证据恢复项目进度：`/workflow status [ID]` |

完整的权限与跨 Skill 协调见各 Skill 与 `.claude/references/` 下的共享规则。
跨层语义变更使用 `.claude/references/change-impact.md`，按条目和实际消费者追踪；影响结论及恢复位置写回现有 `# Resume Notes`，不维护第二份关系库。

## 在项目中使用

这些是项目级 `.claude/` 指令。只有业务项目实际加载的那份文件会影响 agent；更新本仓库不会自动更新已复制到其他项目的版本。部署时同步 `skills/`、`agents/`、`references/` 三个目录，并保留业务项目自己的改动。验证时比较两边对应文件，确认当前运行环境加载的是预期版本；仅看到本仓库提交成功不代表业务项目已采用新规则。

## 存储

```text
docs/intents/INT-NNN/INTENT.md
```

每个 Intent 一个自包含目录。`id` 是唯一权威，关系用 `parent` / `related` / `impact_scope` 表达，不嵌套。

## 原则

各层只管自己 · 修改优先于新建 · boundary-driven 细化 · 可追溯但轻量 · 修改权威内容前必须用户确认。

详细见 [CLAUDE.md](./CLAUDE.md)。
