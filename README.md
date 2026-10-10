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

完整的权限与跨 Skill 协调见各 Skill 与 `.claude/references/` 下的共享规则。

## 存储

```text
docs/intents/INT-NNN/INTENT.md
```

每个 Intent 一个自包含目录。`id` 是唯一权威，关系用 `parent` / `related` / `impact_scope` 表达，不嵌套。

## 原则

各层只管自己 · 修改优先于新建 · boundary-driven 细化 · 可追溯但轻量 · 修改权威内容前必须用户确认。

详细见 [CLAUDE.md](./CLAUDE.md)。
