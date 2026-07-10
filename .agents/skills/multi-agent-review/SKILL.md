---
name: multi-agent-review
description: Use when 用户请求审查 Spec、Plan、代码实现、Diff、分支或指定文件，尤其涉及需求符合性、正确性、安全、测试证据、集成契约或可维护性。
---

# 多子代理 Review

默认只读。不得修改被审查项目、自动修复、自动保存报告或自行豁免风险。

1. 完整读取 `orchestration/router.md` 和 `orchestration/risk-levels.md`。
2. 解析用户附带材料；否则依次尝试工作区 Diff、分支变更。无 Git 仓库或目标不明确时先询问。
3. 构造不可变 Review Packet，读取 `routing/default-routes.yaml`，按风险选择 2、4、最多 6 个 reviewer。用户可手动包含或排除角色。
4. 对每个角色读取 `reviewers/{reviewer_id}.md` 和 `contracts/finding.schema.json`，使用当前平台的原生能力启动真实独立子代理。每个子代理只接收原始 Packet 和自身角色说明，不能读取其他 reviewer 的 finding。
5. 平台槽位不足时分批执行；后一批仍只接收原始 Packet。无法启动真实独立子代理时停止，不得由主代理模拟多个角色。
6. 全部 reviewer 完成后，完整读取 `orchestration/chair.md`、`contracts/review-result.schema.json` 和 `templates/review-report.md`，再做校验、去重、冲突处理和汇总。

所有用户可见内容必须使用中文；路径、代码符号、API、配置键和 reviewer ID 保持原文。关键证据或必选 reviewer 缺失时状态必须为 `incomplete`，不能误报通过。
