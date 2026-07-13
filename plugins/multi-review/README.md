# Multi Review

`multi-review` 是一个结构化多角色审查插件。它针对 Spec、Plan、代码实现、Diff 与分支变更，按风险选择相互隔离的只读 reviewer，并以统一的 Review Packet、Schema 与汇总规则生成中文审查结论。

插件包含需求、验收、可行性、符合性、正确性、安全、测试、集成和可维护性等审查角色。审查流程只输出证据化结果，不自动修改被审查项目。

## 安装

```text
claude plugin marketplace add Zhao-wl/multi-review
claude plugin install multi-review@multi-review

codex plugin marketplace add Zhao-wl/multi-review
codex plugin add multi-review@multi-review
```
