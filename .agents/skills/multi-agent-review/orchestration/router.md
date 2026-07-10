# Review Router

Router 在派遣前一次性解析目标、建立不可变 Review Packet、确定完整 reviewer 集合，并输出符合 contracts/route-decision.schema.json 的 Route Decision。路由完成前不启动任何 reviewer。

## 目标解析顺序

1. 使用用户明确附带或指定的 Spec、Plan、代码实现、Diff、分支或文件。
2. 用户未指定材料时，检查工作区 Diff。
3. 工作区没有可审查变更时，检查当前分支相对其基线的变更。
4. 目标仍不明确时先询问用户。无 Git 仓库时不能假设存在 Diff 或分支基线，必须询问目标。

## Review Packet

在派遣前固定以下全部字段；创建后视为不可变，各 reviewer 接收同一份原始 Packet：

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

应用手动覆盖时，先加入 requested_reviewers，再应用 excluded_reviewers，去重后一次性确定完整角色集合。用户增加 reviewer 导致原风险范围不再合法时，提高到能容纳该数量的最低风险等级。不得自行移除角色或豁免风险。

如果用户排除后只剩少于两个 reviewer，先说明异构覆盖不足并等待用户确认。用户坚持并确认后，只能记录为“降级覆盖”，不得生成伪装为正常有效路由的 Route Decision；可以按确认集合派遣，但最终状态强制为 incomplete。

## 派遣与失败处理

为每个已选角色读取 reviewers/{reviewer_id}.md，使用平台原生能力启动真实独立子代理。每个子代理只接收不可变 Review Packet、自身角色说明和 contracts/finding.schema.json，不能读取其他 reviewer 的 findings。

平台并发槽位不足时可以分批，但完整角色集合不得改变，后一批不能收到前一批 findings。必选 reviewer 执行失败或超时最多重试一次；仍失败时记录限制，最终状态为 incomplete。无法启动真实独立子代理时停止，主代理不得模拟多个 reviewer。

## Route Decision 输出

在派遣前输出并冻结 artifact_type、risk、required_reviewers 与 reason。reason 必须用中文说明目标来源、风险信号、自动路由与手动覆盖，以及是否需要分批；技术标识保持原文。

## 硬规则

- Review Packet 创建后不得因任何 reviewer 的输出而修改。
- 用户未指定材料且无 Git 仓库时，询问目标，不猜测。
- 排除后少于两个 reviewer 时，必须说明异构覆盖不足并等待确认。
- 分批执行时，后续批次不能收到前一批 findings。
- 路由完成前不启动任何 reviewer。
