# Reviewer 多子代理技能设计

## 1. 背景与目标

本项目需要提供一套项目级 Review 技能，由多个性格、职责和检查盲点不同的子代理独立审查同一份材料，再由主代理完成路由、去重、冲突处理和中文汇总。

首版目标：

- 同时支持 Codex、Cursor 和 Claude Code。
- 默认通过单一 Review 入口自动路由，也允许用户手动指定或排除 reviewer。
- 支持 Spec、Plan、Implementation 和混合材料。
- 默认只读，不修改被审查项目，不自动保存报告。
- 低、中、高风险分别启动 2、4、最多 6 个 reviewer；平台并发不足时分批执行。
- 所有用户可见输出和最终报告使用中文。
- 每个 reviewer 使用独立上下文，不能读取其他 reviewer 的 findings。

非目标：

- 首版不包含 Unity、Web、Backend、CLI、CI 等领域插件 reviewer。
- 不自动修复 finding，不自动提交代码，不自动授予风险豁免。
- 不依赖多数投票判断 finding 真伪。
- 不固定具体模型名称。
- 不在主代理中模拟多个 reviewer 人格来代替真实子代理。

## 2. 核心决策

采用“共享内核 + 三端薄适配层”。技能稳定 ID 使用 `multi-agent-review`，避免与 Cursor 内置 `/review` 重名：

- `.agents/skills/multi-agent-review/` 保存唯一共享内核。
- Codex 和 Cursor 直接使用共享技能入口。
- Claude Code 通过 `.claude/skills/multi-agent-review/SKILL.md` 薄入口加载共享内核。
- 三个平台分别保留原生子代理定义，但原生定义只负责元数据、只读边界和共享角色文件定位。
- 不使用符号链接，避免 Windows、Git 和不同客户端之间的兼容问题。

该方案避免把编排、角色、Schema、路由和报告模板混在单一文件中，同时避免三套完整规则长期漂移。

## 3. 目录结构

```text
.agents/
└── skills/
    └── multi-agent-review/
        ├── SKILL.md
        ├── agents/
        │   └── openai.yaml
        ├── orchestration/
        │   ├── router.md
        │   ├── chair.md
        │   └── risk-levels.md
        ├── reviewers/
        │   ├── requirement-integrity.md
        │   ├── acceptance-criteria.md
        │   ├── plan-feasibility.md
        │   ├── spec-compliance.md
        │   ├── correctness-auditor.md
        │   ├── security-abuse.md
        │   ├── test-skeptic.md
        │   ├── integration-contract.md
        │   └── maintainability-pragmatist.md
        ├── routing/
        │   └── default-routes.yaml
        ├── contracts/
        │   ├── route-decision.schema.json
        │   ├── finding.schema.json
        │   └── review-result.schema.json
        └── templates/
            └── review-report.md

.codex/
└── agents/
    └── 每个 reviewer 一个 TOML 文件

.cursor/
└── agents/
    └── 每个 reviewer 一个 Markdown 文件

.claude/
├── skills/
│   └── multi-agent-review/
│       └── SKILL.md
└── agents/
    └── 每个 reviewer 一个 Markdown 文件

tests/
└── review-skill/
    ├── scenarios/
    ├── fixtures/
    └── expected/
```

生产技能、平台适配和测试材料互相隔离。测试场景不会进入正常 Review 上下文。

`agents/openai.yaml` 只保存 Codex UI 展示信息和包含 `$multi-agent-review` 的默认提示，不承载审查流程。

## 4. 角色模型

| Reviewer ID | 中文性格 | 阶段 | 核心职责 | 明确排除 |
|---|---|---|---|---|
| `requirement-integrity` | 追问型需求编辑 | Spec、Plan、Mixed | 目标、用户、范围、非目标、术语、隐藏前提 | 不评代码风格 |
| `acceptance-criteria` | 可证伪的验收官 | Spec、Plan | 可观察、可测试、可判定的验收条件 | 不设计具体实现 |
| `plan-feasibility` | 务实的落地工程师 | Spec、Plan | 依赖、顺序、迁移、回滚、验证点 | 不重写整个方案 |
| `spec-compliance` | 逐条核对的审计员 | Implementation | Spec、实现、测试的追溯矩阵 | 不自行改变需求 |
| `correctness-auditor` | 严谨的逻辑检查者 | Implementation | 条件、状态、异常、并发、幂等、生命周期 | 不提交纯风格意见 |
| `security-abuse` | 攻击者思维的风险猎手 | 全阶段 | 认证、授权、输入、敏感数据、滥用路径 | 不泛化为普通代码审查 |
| `test-skeptic` | 不轻信测试的证据怀疑者 | Spec、Plan、Implementation、Mixed | 弱断言、过度 Mock、回归缺口、测试与 AC 对应关系 | 不把“有测试”视为通过 |
| `integration-contract` | 边界守门人 | 全阶段 | API、Schema、事件、配置、版本兼容、调用链 | 不深入无关内部实现 |
| `maintainability-pragmatist` | 务实维护者 | Implementation、Refactor | 重复规则、复杂度、职责边界、可测试性 | 不要求理想化重构 |

角色性格用于形成不同的认知关注点，不用于戏剧化角色扮演。所有 reviewer 遵守同一份证据契约和中文输出契约。

Router 和 Chair 由主代理承担，不额外占用子代理并发额度。Reviewer 子代理不得再次派遣修复代理。

## 5. 输入解析与 Review Packet

无参数调用按以下顺序解析目标：

1. 用户附带或明确引用的 Spec、Plan、文件。
2. 当前工作区未提交 Diff。
3. 当前分支相对默认分支的变更。
4. 无法确定或当前目录不是 Git 仓库时，询问用户。

默认分支按顺序从本地 `origin/HEAD`、仓库配置、明确存在的 `main` 或 `master` 识别。无法可靠确定时询问用户；不能把当前分支的同名 upstream 当作默认分支。

支持的意图包括：审查指定 Spec、Plan、Diff、分支、文件路径，以及手动包含或排除 reviewer。具体语法不绑定任何平台的专有命令解析器。

主代理在派遣前构造不可变 Packet：

```yaml
review_id: string
artifact_type: spec | plan | implementation | mixed
risk: low | medium | high
targets: []
changed_files: []
requirements: []
acceptance_criteria: []
test_evidence: []
constraints: []
excluded_scope: []
requested_reviewers: []
excluded_reviewers: []
evidence_rules: strict
```

`review_id` 每次审查唯一；同一次审查的执行重试与格式重排沿用同一值。

每个 reviewer 收到同一份基础 Packet，再附加且仅附加自己的角色说明。任何 reviewer 都不能读取其他 reviewer 的 finding。

## 6. 路由与并发

| 风险 | 默认 reviewer 数量 | 典型情况 |
|---|---:|---|
| 低 | 2 | 文档、注释、小配置、局部低风险修改 |
| 中 | 4 | 普通业务逻辑、多文件重构、测试或接口调整 |
| 高 | 最多 6 | 权限、支付、迁移、存档、CI/CD、外部集成、发布和关键性能路径 |

典型路由：

- Spec：`requirement-integrity`、`acceptance-criteria`；按风险增加 `plan-feasibility`、`security-abuse`、`integration-contract`、`test-skeptic`。
- Plan：`plan-feasibility`、`acceptance-criteria`；按风险增加 `requirement-integrity`、`integration-contract`、`security-abuse`、`test-skeptic`。
- Implementation：`correctness-auditor`、`spec-compliance`；按风险增加 `test-skeptic`、`integration-contract`、`security-abuse`、`maintainability-pragmatist`。
- Mixed：优先覆盖 Spec Compliance、Correctness、Security、Test、Integration，再根据材料补 Requirement 或 Plan Reviewer。

表中的 2、4、最多 6 是自动路由的默认 reviewer 数量，不是用户手动排除后的精确数量。Route Decision 使用 Draft 2020-12 条件约束表达合法范围：`low` 的 `required_reviewers` 精确为 2，`medium` 为 2–4，`high` 为 2–6。

Router 必须在派遣前一次确定完整 reviewer 集合。平台并发槽位不足时分批运行；后一批仍然只接收原始 Packet，不能接收前一批 findings。主代理等待全部 reviewer 完成后才开始 Chair 汇总。

手动路由使用唯一算法：

1. 先验证 `requested_reviewers` 与 `excluded_reviewers` 的 ID；两者有交集时停止并询问用户。
2. 从 artifact 默认有序路由移除 `excluded_reviewers`，再按自动默认数量选取，后续候选负责补位。
3. `requested_reviewers` 按用户给定顺序追加到自动集合，不占自动默认名额，并按首次出现去重。
4. 最终数量超出当前风险上限时，提高到能容纳的最低风险；超过 6 时停止并询问用户缩减，不启动 reviewer。
5. 合法最终数量为 2–3 且低于最终风险的自动默认数量时，Route Decision 的 `reason` 必须明确记录“覆盖缩减”及排除项。
6. 少于两个 reviewer 时不能生成有效 Route Decision，必须提示异构覆盖不足并等待用户确认；确认后应补足到至少两个 reviewer。用户坚持以少于两个 reviewer 继续时属于降级覆盖，不能伪装为正常有效路由，最终状态必须标记为 `incomplete`。

Route Decision 的 `reason` 完整记录目标与默认分支来源、风险信号、排除项、自动集合及补位、requested 追加与去重、风险提升、最终角色顺序与数量、覆盖缩减或降级覆盖，以及批次安排。

## 7. Finding 与汇总契约

每条有效 Finding 必须满足：

```yaml
id: F-001
reviewer: security-abuse
severity: blocking | advisory | question
category: authorization
location: src/api/projects.ts:84
claim: 导出接口缺少对象级授权
evidence: 处理器只检查登录状态，没有检查项目成员关系
impact: 用户可能导出其他项目的数据
recommendation: 导出前检查成员关系并增加回归测试
confidence: low | medium | high
```

严重度语义：

- `blocking`：直接证据证明违反需求、引入缺陷或存在不可接受风险。
- `advisory`：有证据支持、可执行，但不阻止当前验收。
- `question`：材料不足或存在歧义，需要用户或作者补充信息。

以上英文值仅用于 Schema 和跨平台路由。中文报告分别显示为“阻塞问题”“建议问题”“待确认问题”，不直接展示英文严重度。

关键问题不能仅凭怀疑标为 `blocking`。

`Review Result.reviewer_results` 的每一项都是关闭对象，不接受未声明字段，并且必须包含：

```yaml
reviewer: requirement-integrity  # 9 个稳定 reviewer ID 之一
agent_id: string                 # 实际子代理标识
status: completed | failed | invalid
finding_ids: []                  # 唯一的 F-001 形式 Finding ID
limitations: []                  # 字符串数组
```

Chair 的处理规则：

- 先校验 Finding Schema 和证据完整性。
- 按主张、位置和影响合并重复问题，同时保留多个证据来源。
- Reviewer 冲突标记为 `needs_human_decision`，不投票。
- 没有可核查证据的意见降为 `question` 或丢弃。
- 单个高置信度 blocking finding 不因其他 reviewer 沉默而消失。

最终状态限定为：

- `pass`
- `needs_changes`
- `needs_human_decision`
- `incomplete`

`incomplete` 表示关键材料、证据或必选 reviewer 结果不足，不能误报为通过。

以上状态同样是内部稳定值。中文报告分别显示为“通过”“需要修改”“需要人工决策”“审查不完整”。

## 8. 中文输出契约

所有用户可见内容必须使用中文，包括：

- Reviewer findings。
- Router 的派遣说明。
- Chair 的汇总、失败提示和限制说明。
- 最终报告的标题、严重度说明、检查范围和后续操作。

文件路径、代码符号、API 名称、配置键和稳定 reviewer ID 保持原文。子代理若返回英文内容，Chair 必须转换为中文后再呈现，同时保留原始技术标识。

最终报告包含：

1. 审查结论。
2. 阻塞问题。
3. 建议问题。
4. 待确认问题。
5. 需求追溯矩阵。
6. Reviewer 覆盖情况。
7. Reviewer 冲突。
8. 用户明确批准的豁免。
9. 必需后续操作。
10. 审查限制。

默认只在对话中输出。用户明确要求保存时才写入指定位置。

## 9. 失败处理

| 失败情况 | 处理 |
|---|---|
| 未找到审查目标 | 询问用户，不启动 reviewer |
| 当前目录不是 Git 仓库 | 支持指定文件或粘贴材料；不自动审查 Diff |
| Reviewer 启动失败 | 使用相同 Packet 重试一次，仍失败则记录角色缺失 |
| Reviewer 超时 | 保留其他结果；必选角色超时则状态为 `incomplete` |
| 输出不符合 Schema | 要求原 reviewer 仅修正格式一次，不重新审查 |
| Finding 缺少证据 | 降为 `question`；关键证据缺失时状态为 `incomplete` |
| 无读取权限 | 不绕过沙箱，报告无法覆盖的范围 |
| 平台未启用真实多代理 | 停止审查，不由主代理模拟多个角色 |
| 并发槽位不足 | 分批执行，保持输入隔离 |
| 用户中途取消 | 停止剩余代理，不输出伪完整结论 |

主代理不能冒充失败 reviewer 补写结论。

## 10. 三端适配

### Codex

- 技能入口：`.agents/skills/multi-agent-review/SKILL.md`。
- 子代理定义：`.codex/agents/*.toml`。
- 子代理使用只读沙箱，通过 `developer_instructions` 加载对应角色文件与 Finding 契约。
- 不固定模型，继承当前会话配置。

### Cursor

- 技能入口：`.agents/skills/multi-agent-review/SKILL.md`。
- 子代理定义：`.cursor/agents/*.md`。
- 适配文件仅包含平台元数据、只读工具边界和共享角色位置。
- 使用继承模型，不绑定具体模型名称。

### Claude Code

- 薄技能入口：`.claude/skills/multi-agent-review/SKILL.md`。
- 子代理定义：`.claude/agents/*.md`。
- 子代理只使用 Read、Glob、Grep 等只读能力，并加载单个对应角色文件。
- 不向一个子代理预载全部 reviewer 内容。

任一平台不能提供真实独立子代理上下文时，明确报告不支持本次多代理审查，不降级为主代理角色扮演。

## 11. 测试策略

技能开发遵循 RED、GREEN、REFACTOR。

### RED：无技能基线

使用固定场景观察无技能代理的自然失败：模糊需求、缺失验收标准、迁移无回滚、边界条件错误、弱断言、对象级授权缺失、Schema 兼容破坏、重复业务规则、英文或无证据 finding。

基线结果保存在 `tests/review-skill/`，不进入生产技能上下文。

### GREEN：最小技能

静态验证：

- Skill Frontmatter 合法。
- 9 个角色 ID 唯一。
- 三端适配文件与共享角色一一对应。
- 路由表引用均有效。
- JSON Schema 可解析，示例可通过验证。
- 中文报告模板包含全部必需章节。
- 子代理未获得写入能力。

行为验证：

- 风险路由数量符合 2、4、最多 6。
- 至少启动两个真实独立子代理。
- Reviewer 只收到原始 Packet 和自身角色说明。
- Findings 满足结构和证据要求。
- 最终报告全部使用中文。
- 高置信 blocking finding 不会被投票覆盖。
- 失败或证据不足不会输出虚假 `pass`。
- 默认运行不修改项目。

### REFACTOR：压力和异常

- 面对“快速看一下，不用证据”的压力仍坚持证据契约。
- 正确处理排除关键 reviewer、超时、非法 JSON、重复 finding 和 reviewer 冲突。
- 英文 finding 转换成中文且不翻译技术标识。
- 并发不足时分批执行且不发生 finding 污染。

### 三端验收

- 所有平台适配文件执行静态校验。
- 当前环境已安装的平台分别运行真实冒烟测试。
- 未安装或无法启动的平台只能标记为“静态兼容，尚未实机验证”。
- 每个平台至少验证一次自动路由和一次手动指定 reviewer。
- 测试产物不写入被审查的示例项目。

## 12. 官方能力依据

- [Codex Skills](https://learn.chatgpt.com/docs/customization/overview#skills)
- [Codex Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Cursor Skills](https://cursor.com/docs/skills)
- [Cursor Subagents](https://cursor.com/docs/subagents)
- [Claude Code Skills](https://code.claude.com/docs/en/slash-commands)
- [Claude Code Subagents](https://code.claude.com/docs/en/sub-agents)

## 13. 验收结论

设计完成后的实现必须满足：三端结构兼容；当前环境可用的平台能够启动真实独立 reviewer；默认只读；动态风险路由有效；异常情况下不误报通过；所有最终报告均为中文。
