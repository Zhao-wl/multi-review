# Review Router

Router 在派遣前一次性解析目标、建立不可变 Review Packet、确定完整 reviewer 集合，并输出符合 contracts/route-decision.schema.json 的 Route Decision。路由完成前不启动任何 reviewer。

## 目标解析顺序

1. 使用用户明确附带或指定的 Spec、Plan、代码实现、Diff、分支或文件。
2. 用户未指定材料时，检查工作区 Diff。
3. 工作区没有可审查变更时，检查当前分支相对默认分支的变更。默认分支按顺序从本地 origin/HEAD、仓库配置、明确存在的 main 或 master 识别；无法可靠确定时询问用户。不能用同名 upstream 代替默认分支。
4. 目标仍不明确时先询问用户。无 Git 仓库时不能假设存在 Diff 或默认分支，必须询问目标。

## Review Packet

在派遣前固定以下全部字段；创建后视为不可变，各 reviewer 接收同一份原始 Packet：

- review_id：每次审查唯一；重试沿用同一值，包括执行重试与格式重排。
- artifact_type：spec、plan、implementation 或 mixed。
- risk：low、medium 或 high。
- targets：用户指定或按解析顺序确定的审查对象。
- changed_files：可核查的变更文件集合；不适用时为空数组并说明原因。
- requirements：适用的需求与来源。
- acceptance_criteria：适用的验收标准。
- test_evidence：用户提供或仓库中可核查的测试证据，不把未运行的测试写成已通过。
- constraints：只读、语言、平台、时间或其他明确限制。
- excluded_scope：明确不审查的范围。
- requested_reviewers：用户要求包含的 reviewer ID。
- excluded_reviewers：用户要求排除的 reviewer ID。
- evidence_rules：finding 必须定位 claim、location、impact 与可核查 evidence；事实、推断和未知项必须区分。

不得把任何 reviewer 的 findings 回填进 Review Packet，也不得在后续批次修改 Packet。

## 风险路由

完整读取 routing/default-routes.yaml，按 artifact_type 的有序角色列表选择角色，并结合 orchestration/risk-levels.md 取最高适用风险：

- low 自动选择 2 个，正常 Route Decision 必须恰好 2 个。
- medium 自动选择 4 个，正常 Route Decision 为 2–4 个；2–3 个只允许来自用户手动排除后的有效路由。
- high 自动选择最多 6 个，正常 Route Decision 为 2–6 个。

手动路由严格按以下顺序执行：

1. 先用 reviewers/index.json 验证 requested_reviewers 与 excluded_reviewers 的 ID。存在未知 ID 时停止并询问用户修正；requested_reviewers 与 excluded_reviewers 有交集时停止并询问用户。
2. 从 artifact_type 对应的默认有序路由移除 excluded_reviewers，再按自动默认数量选取，后续候选负责补位；不得因前部角色被排除而提前缩小自动集合。
3. requested reviewer 按用户给定顺序追加到自动集合，不占自动默认名额；与自动集合或自身重复的 ID 只保留首次出现。
4. 若最终数量超出当前风险上限，提高到能容纳该数量的最低风险。最终数量超过 6 时停止并询问用户缩减，不启动 reviewer。
5. 合法最终数量为 2–3 且低于最终风险的自动默认数量时，Route Decision 的 reason 必须明确记录“覆盖缩减”及 excluded_reviewers 排除项。
6. 最终集合少于两个 reviewer 时，应用下述确认与降级规则。

完成全部步骤后才一次性确定完整角色集合。不得自行移除角色或豁免风险。

如果用户排除后只剩少于两个 reviewer，先说明异构覆盖不足并等待用户确认。用户坚持并确认后，只能记录为“降级覆盖”，不得生成伪装为正常有效路由的 Route Decision；可以按确认集合派遣，但最终状态强制为 incomplete。

## 派遣与失败处理

为每个已选角色读取 reviewers/{reviewer_id}.md，使用平台原生能力启动真实独立子代理。每个子代理只接收不可变 Review Packet、自身角色说明和 contracts/finding.schema.json，不能读取其他 reviewer 的 findings。

平台并发槽位不足时可以分批，但完整角色集合不得改变，后一批不能收到前一批 findings。必选 reviewer 执行失败或超时最多重试一次；仍失败时记录限制，最终状态为 incomplete。无法启动真实独立子代理时停止，主代理不得模拟多个 reviewer。

## Route Decision 输出

在派遣前输出并冻结 artifact_type、risk、required_reviewers 与 reason。reason 必须用中文完整说明目标来源与默认分支识别来源、风险信号、排除项、自动集合及补位、requested 追加与去重、风险提升、最终角色顺序与数量、是否覆盖缩减或降级覆盖，以及是否需要分批；技术标识保持原文。

## 硬规则

- Review Packet 创建后不得因任何 reviewer 的输出而修改。
- 用户未指定材料且无 Git 仓库时，询问目标，不猜测。
- 无法可靠识别默认分支时询问用户，不能用同名 upstream 代替默认分支。
- requested_reviewers 与 excluded_reviewers 有交集时停止并询问用户。
- 最终数量超过 6 时停止并询问用户缩减，不启动 reviewer。
- 排除后少于两个 reviewer 时，必须说明异构覆盖不足并等待确认。
- 分批执行时，后续批次不能收到前一批 findings。
- 路由完成前不启动任何 reviewer。
