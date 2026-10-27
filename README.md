# cc-workflow

Claude Code 的项目级 agent 工作流框架。它把用户目标逐层转成系统需求、模块责任、公共契约、代码和运行证据；发现问题时回到有权修改该内容的层，修正后再继续原任务。

## 工作流

```text
用户目标 → Intent → Spec → Architecture → Module Design → Implementation → 真实用户路径验收
           ↕ 跨 Intent Reconcile        ↑ 依条目与契约追踪变更、反馈和返回位置
```

各层回答不同的问题：**Intent 定义用户要什么，Spec 定义系统必须保证什么，Architecture 决定谁负责，Module Design 定义模块怎样对外协作，Implementation 用代码和运行证据兑现契约。** `workflow` 负责恢复进度、选择当前可推进的工作，不替这些层作决定。下游发现问题先定位所属层；仅当目标或关键约束需要改变、或材料不足以确定产品选择时，才把选择交给用户。

框架只有一条执行逻辑：从仓库恢复当前目标及依据，沿稳定条目和真实消费者找到受影响的工作，选择当前能闭合的一项；若其前提未闭合，进入前提的权威层修复并保存返回位置。修复后重新读取产物与评审结果，再继续原任务。状态表示文档所处阶段，不能替代对当前版本的评审、代码测试或真实用户路径证据。无关模块按原有有效依据继续。

## 各流程负责什么

| Skill | 负责的问题与产物 | 边界和特点 |
|---|---|---|
| [`intent`](.claude/skills/intent/SKILL.md) | 用户要达成什么、从什么真实状态开始、按什么顺序操作、怎样知道成功？在 `INTENT.md` 保存目标、硬约束、已确认选择和未决产品选择。 | 用户目标的权威来源；不替 Spec 写系统行为，也不指定模块或 API。交给 Spec 的是条目 ID、用户路径和仍需用户决定的问题。 |
| [`intent-reconcile`](.claude/skills/intent-reconcile/SKILL.md) | 多个 Intent 是否等价、重叠、依赖或冲突？必要时协调共同目标、关系和约束。 | 只处理 Intent 之间的语义关系；不因为共用技术或数据源就合并，也不把系统需求写成用户决定。 |
| [`spec`](.claude/skills/spec/SKILL.md) | 系统在正常、边界和失败情况下必须表现成什么样？在 `SPEC.md` 写可追溯的 REQ/INV、验收条件和架构待决问题。 | 描述可观察的系统保证，不决定模块、接口字段、存储或算法；检查 Intent 覆盖与跨能力正确性。 |
| [`architecture`](.claude/skills/architecture/SKILL.md) | 哪个模块主责每项需求，谁提供公共能力，谁消费它，依赖和状态归谁？维护 `ARCHITECTURE.md` 基线。 | 确定模块边界、公共能力与契约的归属、跨模块不变量的集成负责人；不写具体 API 或内部算法。已有基线变化先做 `impact`。 |
| [`module-design`](.claude/skills/module-design/SKILL.md) | 一个已命名模块向消费者承诺什么、内部如何完成？产出该模块的 `DESIGN.md` 和必要的 `contracts/`。 | Provider 负责自己公共契约的输入、输出、状态、时序和失败语义；设计还要证明消费者需要的输入在对应步骤已经可得。不能自行改变模块归属。 |
| [`implementation`](.claude/skills/implementation/SKILL.md) | 当前设计和契约是否已由代码实现并验证？产出代码、测试及标明范围的运行证据。 | 实现内部细节，但不能在代码中暗改需求或公共契约。模块交接证明该模块的实际范围；完整用户目标仍需整条真实路径验收。 |
| [`workflow`](.claude/skills/workflow/SKILL.md) | 当前进度和证据是什么，下一项可闭合的工作在哪里？ | `status` 只读；`continue` 在已授权目标内选择工作、修复必要前提并返回原任务，不建立第二套需求或生命周期。 |

## 何时拆分

拆分看**哪种结果可以独立管理和验证**，不看文档长度、代码目录或技术栈。

| 对象 | 拆分条件 | 决定者 |
|---|---|---|
| Intent | 子目标有独立的用户价值，用户能单独排序、修改或验收；还有自己的关键选择，而且单独管理确有收益。目标只是变大或要写多个 Spec 时，修改原 Intent。 | `intent`；跨 Intent 的重叠与冲突由 `intent-reconcile` 协调。 |
| Spec | 系统行为有清楚边界，**每一侧都能分别描述和验收**。维护节奏不同、文档较长只能作辅助理由。已有 Spec 覆盖同一行为时优先修改。 | `spec`；一个 Intent 可以对应多个 Spec，多个 Intent 也可共用一个 Spec。 |
| 模块 | 责任、权威状态、公共能力和依赖能形成清楚的边界，并保持系统不变量。一个 Spec 不必对应一个模块，一个模块也可满足多个 Spec。 | `architecture` 指定模块和归属；`module-design` 只设计既定模块的契约与内部方案。 |
| 实现工作 | 按已确认的模块和契约组织代码与测试；可按无依赖的范围推进。 | `implementation`；不通过新建实现目录来重新定义模块。 |

例如，用户希望“导入交易记录，核对异常后生成月报”。这可以是**一个 Intent**，因为用户要的是一条完整结果。若“导入与校验”和“生成月报”各有明确行为边界和独立验收条件，可以形成**两个 Spec**。Architecture 再判断由哪些模块承担，并指定“月报只能使用已校验记录”的集成负责人；不能因为有两个 Spec 就机械地建两个模块。跨 Spec 不变量在一个 Spec 中定义稳定 ID，其他参与的 Spec 引用该 ID 并说明各自的责任。

## 交接和反馈怎样运行

正常交接沿着可追溯的条目推进：

```text
INT-001/G-01（用户结果）
  → SPEC-001/REQ-001（系统行为与验收）
  → Architecture（主责模块、Provider、Consumer、集成验证人）
  → MOD-xxx/DESIGN.md（Provider 契约与消费者前提）
  → 代码、测试、实际运行证据
```

**例一：契约错误，返回 Module Design。** 实现月报时发现校验模块的公共契约允许“尚未完成校验”的记录被读取；Spec 已明确要求只使用完成校验的记录。Implementation 记录失败输入、实际结果、对应 REQ 和调用方，交给该契约的 Provider Module Design 修正。随后只检查实际受影响的消费者、代码、测试与运行证据，再返回月报实现。无需把已明确的系统要求重新交给用户决定。

**例二：产品选择未定，返回 Intent。** Spec 发现“月报是否包含未成交订单”会改变用户看到的结果，现有 Intent 也没有答案。Spec 记录两个结果及影响，由 Intent 向用户澄清并保存决定；之后 Spec 更新对应 REQ，Architecture 和下游仅复核受影响的能力与契约。若用户此前已经明确选择，就按原决定修正规则，不重复提问。

每次反馈都标明**来源条目、观察到的问题、证据范围、应由哪层决定、受影响的路径和返回位置**。收到反馈、修改文字、评审通过、真实运行通过是不同的进度；下游必须读取当前产物与证据，不能仅凭 `archived`、`final` 或一次旧 PASS 推断问题已闭合。无关模块按仍有效的依据继续。

## 完成与验证

分别报告三类结论：文档和契约是否就绪、模块代码及其实际边界是否验证、用户从真实起点走完整条路径是否成功。模块可以在自身必需的公共与可运行集成边界通过后交接，同时记录尚待集成的步骤、负责人和下一项检查；**模块交接不等于用户目标完成**。模拟数据、组件测试和静态检查只证明它们实际覆盖的范围。真实路径未运行时，写明缺少的环境或输入及恢复位置。

跨层归属、授权与用户路径规则见 [`cross-layer-coordination.md`](.claude/references/cross-layer-coordination.md)；条目影响追踪见 [`change-impact.md`](.claude/references/change-impact.md)；评审和证据分级见 [`verification.md`](.claude/references/verification.md)。影响结论和恢复位置写入现有产物的 `# Resume Notes`，不维护第二份关系库。

## 在项目中使用

这些是项目级 `.claude/` 指令。只有业务项目实际加载的那份文件会影响 agent；更新本仓库不会自动更新已复制到其他项目的版本。部署时同步 `skills/`、`agents/`、`references/` 三个目录，并保留业务项目自己的改动。验证时比较两边对应文件，确认当前运行环境加载的是预期版本；仅看到本仓库提交成功不代表业务项目已采用新规则。

## 存储

默认产物位置如下；业务项目已有约定时沿用项目约定：

```text
docs/intents/INT-NNN/INTENT.md
docs/specs/SPEC-NNN/SPEC.md
docs/architecture/ARCHITECTURE.md
docs/modules/MOD-<slug>/DESIGN.md
docs/modules/MOD-<slug>/contracts/    # 仅在需要机器可读契约时使用
docs/modules/MOD-<slug>/impl/         # 或沿用项目现有代码布局
```

每个 Intent 一个自包含目录；`id` 是唯一权威，关系用 `parent` / `related` / `impact_scope` 表达，不嵌套。

## 审查与验证

各层 Skill 只规定本层产物与完成条件；共享判断集中在上述 references。
`tests/workflow/` 提供流程场景和辅助分析；上下文统计只能提示哪些重复内容
需要人工检查，不能单独证明规则有效或可删。

## 原则

各层只管自己 · 修改优先于新建 · 按责任边界拆分 · 可追溯但轻量 · 已授权纠错自动推进，改变已确认的产品含义或关键约束才询问。

详细见 [CLAUDE.md](./CLAUDE.md)。
