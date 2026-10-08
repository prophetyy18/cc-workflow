# Agent 工作流

本仓库记录如何在 Claude Code 中使用 agent 工作流。

## 子代理

- `Explore`：只读检索
- `Plan`：实现前的方案设计
- `general-purpose`：多步骤任务
- 自定义：放在 `.claude/agents/*.md`

## 模式

**并行审查。** 一个维度一个子代理（正确性 / 性能 / 安全），对抗式验证每条 finding，只修复已确认的。

**扇出研究。** 同一问题派给 N 个独立子代理，再汇总。

**配置优于 prompt。** 重复检查放进 `.claude/settings.json`，不放进对话。

**验证后再修复。** 每条 finding 先对抗式验证，再动代码。

## 规则

- 一个子代理一个上下文。
- `.claude/` 进版本控制。
- 不可逆或对外动作先确认。
- 长等待用 `ScheduleWakeup`，别轮询。
