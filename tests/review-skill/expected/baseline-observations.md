# 无技能基线观察

## spec-ambiguous

### 本次真实子代理标识

`/root/control_spec_ambiguous`

### 未经改写的完整原始输出

````markdown
# 原始输出

- 子代理：`/root/control_spec_ambiguous`

审查结论：该需求目前不可直接实现或验收，核心语义与可测试标准均缺失。

- **[P1] 未定义“自动保存”的触发与持久化语义** — [spec-ambiguous.md](D:/Projects/Research/Reviewer/tests/review-skill/fixtures/spec-ambiguous.md:3)  
  没有说明按固定周期、停止输入后、失焦时还是每次修改后保存，也未规定最大未保存时间；同时不清楚是覆盖原文件还是写入恢复副本。不同实现都可声称满足需求，却提供完全不同的数据安全保证。应明确触发规则、去抖策略、保存目标及允许的数据丢失窗口。

- **[P1] “足够快、不能打断用户”无法验收** — [spec-ambiguous.md](D:/Projects/Research/Reviewer/tests/review-skill/fixtures/spec-ambiguous.md:3)  
  需求没有给出可测量的保存耗时、输入延迟或 UI 阻塞上限，也缺少文档大小、存储介质和并发编辑等测试条件。应定义量化指标，例如目标负载下的 p95 输入延迟、主线程最大阻塞时间和保存完成时限。

- **[P1] 缺少失败、冲突和原子性要求，可能造成静默数据丢失** — [spec-ambiguous.md](D:/Projects/Research/Reviewer/tests/review-skill/fixtures/spec-ambiguous.md:3)  
  未说明磁盘写满、权限错误、写入中崩溃、外部文件变更时如何处理，也未要求原子写入、重试、告警或保留旧版本。实现可能在失败后仍让用户误以为内容已保存，甚至损坏原文件。

- **[P2] 未定义保存期间继续编辑时的一致性规则** — [spec-ambiguous.md](D:/Projects/Research/Reviewer/tests/review-skill/fixtures/spec-ambiguous.md:3)  
  如果一次保存尚未完成又产生新修改，需求没有规定是排队、合并还是取消旧任务，也没有要求防止旧保存结果覆盖新结果。应明确快照、任务排序及“最新修改最终一定持久化”的保证。
````

### 仅从原始输出能够证明的缺口

- 该输出已识别触发与持久化语义、量化验收指标、失败与原子性、一致性等关键缺陷，不能把这些问题记录为控制组遗漏。
- 输出只标识了一个子代理，未提供多角色覆盖或不同角色交叉复核的证据。
- 输出采用自由格式；虽然每条问题包含优先级、位置、说明和建议，但没有可机器校验的统一字段结构或覆盖清单。

## plan-migration

### 本次真实子代理标识

`/root/control_plan_migration`

### 未经改写的完整原始输出

````markdown
# 原始输出

- 子代理：`/root/control_plan_migration`

发现以下重要问题：

- **[P1] 第 3 行缺少存量数据迁移方案。** 整数值不能直接、可靠地转换为 UUID；若 `accountId` 被主表、外键、索引或缓存引用，直接改字段类型可能导致迁移失败、引用断裂或身份映射变化。计划应明确新增 UUID 字段、生成并持久化一对一映射、回填所有引用表、校验唯一性与完整性、重建索引/约束，以及最终删除旧字段的条件。

- **[P1] 第 3–5 行没有处理数据库、服务和 API 客户端的兼容窗口。** 数据库先改类型后部署服务，旧服务实例可能无法读写；API Schema 直接切换也会使尚未升级的客户端失效。应采用可前后兼容的分阶段发布，例如扩展表结构、兼容读写、回填、切换流量、停止旧字段写入，最后再收缩 Schema。

- **[P1] 第 6 行把验证放在生产部署之后，且只运行单元测试。** 单元测试无法证明真实数据库迁移、外键关系、序列化、API 契约及新旧版本混跑正常。至少应在部署前加入迁移演练、数据完整性校验、集成测试和契约测试，并将其设为发布门禁；部署后再执行冒烟测试和指标检查。

- **[P2] 第 5 行缺少回滚与运行监控方案。** 一旦新 UUID 已被写入或对外返回，简单回滚代码或数据库类型并不能恢复一致状态。计划应定义备份/恢复点、各阶段的可逆边界、失败停止条件、双字段期间的回滚方法，以及错误率、空值、映射缺失和数据库性能等监控指标。

整体而言，该文档目前只是目标步骤列表，尚不足以作为可安全执行的迁移计划。
````

### 仅从原始输出能够证明的缺口

- 该输出已识别存量数据迁移、兼容窗口、部署前验证、回滚与监控等关键缺陷，不能把这些问题记录为控制组遗漏。
- 输出只标识了一个子代理，未提供数据库、API、发布或测试等不同角色分别审查及交叉复核的证据。
- 输出采用自由格式；问题项虽有优先级和建议，但没有统一的结构化字段、明确的角色字段或覆盖清单。

## implementation-auth

### 本次真实子代理标识

`/root/control_implementation_auth`

### 未经改写的完整原始输出

````markdown
# 原始输出

- 子代理：`/root/control_implementation_auth`

发现 1 个重要问题：

- **[P1] 缺少项目成员授权校验** — [implementation-auth.md](D:/Projects/Research/Reviewer/tests/review-skill/fixtures/implementation-auth.md:9)

  当前代码只通过 `requireAuthenticatedUser` 验证用户已登录，随后直接使用请求中的 `projectId` 导出数据。传递 `user.id` 并不等同于验证该用户属于此项目；除非 `exportService.export` 内部强制且原子地执行成员校验，否则任意登录用户都可能替换 `projectId`，导出其他项目的数据，形成越权访问（BOLA/IDOR）。

  应在导出发生前强制验证 `user.id` 对 `projectId` 的成员权限，或明确保证服务层统一执行该校验。测试至少应补充：项目成员导出成功、已登录但非成员被拒绝（通常为 403），并确认拒绝路径不会泄露项目数据。
````

### 仅从原始输出能够证明的缺口

- 该输出已识别项目成员授权缺失、潜在 BOLA/IDOR 风险及关键测试缺口，不能把这些问题记录为控制组遗漏。
- 输出只标识了一个子代理，未提供安全、实现和测试等不同角色覆盖或交叉复核的证据。
- 输出采用自由格式；虽有优先级、位置、风险说明和修复建议，但没有统一的结构化字段或覆盖清单。

## implementation-retry

### 本次真实子代理标识

`/root/control_implementation_retry`

### 未经改写的完整原始输出

````markdown
# 原始输出

- 子代理：`/root/control_implementation_retry`

审查发现 3 个重要问题：

1. **[P1] 重试次数存在 off-by-one**  
   [implementation-retry.md:5](D:/Projects/Research/Reviewer/tests/review-skill/fixtures/implementation-retry.md:5) 使用 `retryCount <= maxRetry`。若 `retryCount` 从 0 开始、`maxRetry` 为 3，循环会执行 4 次（0、1、2、3），超过“最多重试三次”的上限。重试循环通常应使用 `< maxRetry`，并明确区分“首次执行”和“失败后的重试”。

2. **[P1] 循环没有根据任务失败或成功决定是否继续**  
   [implementation-retry.md:6](D:/Projects/Research/Reviewer/tests/review-skill/fixtures/implementation-retry.md:6) 每轮都无条件调用 `queue.enqueue(job)`，成功后也不会停止。若 `enqueue` 只是把任务放入队列，该代码会一次性创建多个重复任务，根本没有观察任务执行失败；若 `enqueue` 本身代表一次尝试，则其抛错时循环会立即退出，也没有真正重试。实现需要接收明确的失败信号，并在成功时 `break`。

3. **[P1] 测试断言无法验证核心上限要求**  
   [implementation-retry.md:11](D:/Projects/Research/Reviewer/tests/review-skill/fixtures/implementation-retry.md:11) 只断言 `queue.enqueue` “被调用过”，即使调用 4 次、无限重复或成功后继续调用，测试仍会通过。至少应覆盖：

   - 连续失败时调用次数不超过 3 次重试；
   - 第 N 次成功后不再调用；
   - `maxRetry = 0` 时不重试；
   - 明确断言首次执行是否计入总调用次数。
````

### 仅从原始输出能够证明的缺口

- 该输出已识别 off-by-one、未依据成功或失败控制循环、测试断言不足等关键缺陷，不能把这些问题记录为控制组遗漏。
- 输出只标识了一个子代理，未提供实现、可靠性和测试等不同角色覆盖或交叉复核的证据。
- 输出采用自由格式；虽有优先级、位置、说明和测试建议，但没有统一的结构化字段或覆盖清单。
