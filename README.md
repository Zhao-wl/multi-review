# Multi Review

`multi-review` 是一个面向 Claude Code 与 Codex 的结构化多角色审查插件。

它根据 Spec、Plan、代码实现、Diff 或分支变更的材料类型与风险等级，选择多个相互隔离的只读 reviewer 进行审查。每个 reviewer 基于同一份不可变 Review Packet 返回可校验的结构化结果；主流程在所有 reviewer 完成后去重、处理冲突并输出中文审查结论。

插件覆盖需求完整性、验收标准、计划可行性、需求符合性、正确性、安全与滥用、测试证据、集成契约和可维护性等审查维度。它不会自动修改被审查项目，也不会以单个 reviewer 的结论替代其他审查视角。

## 安装

### Claude Code

```text
claude plugin marketplace add Zhao-wl/multi-review
claude plugin install multi-review@multi-review
```

### Codex

```text
codex plugin marketplace add Zhao-wl/multi-review
codex plugin add multi-review@multi-review
```
