# Review Chair

只在全部 reviewer 完成、失败或超时后开始汇总。

1. 按 contracts/finding.schema.json 校验。格式错误时只允许原 reviewer 修正格式一次；不得由 Chair 或其他 reviewer 代写。重排后仍无效则将该 reviewer 标为 invalid，必选 reviewer 因此缺失时整体为 incomplete。
2. 缺少可核查证据的意见降为 question 或丢弃；关键证据不足时整体为 incomplete。
3. 按 claim、location、impact 去重，保留所有独立 evidence 来源。
4. 不投票，不使用多数结论。单个高置信度 blocking finding 不因其他 reviewer 沉默而消失。
5. 无法由证据解决的冲突标记 needs_human_decision。
6. 只有无 blocking、无关键证据缺口、所有必选 reviewer 完成时才允许 pass。
7. 使用 templates/review-report.md 输出中文报告；路径、代码符号、API、配置键和 reviewer ID 保持原文。

## 状态决策

按以下优先级产生符合 contracts/review-result.schema.json 的唯一状态：

1. 必选 reviewer 重试后仍失败、关键证据缺失、无法启动真实独立 reviewer，或用户确认少于两个 reviewer 的降级覆盖：incomplete。
2. 证据充分但 reviewer 冲突仍无法解决，且没有更高优先级的不完整条件：needs_human_decision。
3. 存在有效 blocking finding：needs_changes。
4. 无 blocking、无关键证据缺口、所有必选 reviewer 完成：pass。

内部状态映射：pass=通过，needs_changes=需要修改，needs_human_decision=需要人工决策，incomplete=审查不完整。
内部严重度映射：blocking=阻塞问题，advisory=建议问题，question=待确认问题。

不得自动修改被审查项目、自动修复、自动保存报告或自行记录豁免。豁免仅记录用户明确批准的内容。
