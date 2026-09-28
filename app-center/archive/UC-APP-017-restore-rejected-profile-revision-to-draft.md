# UC-APP-017：将被拒绝的应用公开资料修订恢复为草稿

状态：`SUPERSEDED`

> 归档重建说明：原始 UC 正文未进入 Git 历史。本文依据注册表中的 retired 记录、UC-APP-013 与 UC-APP-016 的现行规则重建历史意图和否决结果，不代表找回的原始措辞，也不是实现依据。

## 历史意图

该提案计划为管理员提供服务端命令，把 `REJECTED` 的 ApplicationProfileRevision 恢复为可编辑的 `DRAFT`，使管理员能够修改被拒绝的公开资料并再次提交审核。

预期行为与 [UC-APP-006](../use-cases/UC-APP-006-restore-rejected-version-to-draft.md) 的 ApplicationVersion 恢复流程相似：保留原审核决定和理由，同时让原修订重新进入可编辑状态。原计划分配的 `BR-PRF-033`–`BR-PRF-040` 没有留下可验证的正文，因此不在本文重建具体命令、字段、错误、并发语义或验收条件。

## 否决决定

本提案在进入实现前被否决，未生成 implementation brief，也没有服务端或 API 实现。

公开资料修订采用不可变历史：Reviewer 作出拒绝决定后，ApplicationProfileReview 和 ApplicationProfileRevision 同时进入 `REJECTED` 终态。恢复原修订会让一个已经由确定 snapshot 审核并形成终态决定的身份重新承载后续内容，增加审核历史、修订身份和工作指针的解释成本。

产品需要的是“以被拒绝内容为起点继续编辑”，不要求服务端复活同一个 ProfileRevision。该体验可以由读取既有内容、前端预填和普通新建命令完成，同时保持旧内容、snapshot、decision、reason 与审计事实不变。

## 生效的替代方案

现行流程由以下权威规则共同定义：

1. 前端通过管理员查询读取被拒绝修订的 `displayName`、`description` 和 `icon`，用于预填创建表单。
2. 前端调用 [UC-APP-013](../use-cases/UC-APP-013-create-application-profile-revision.md#网页端重新编辑被拒绝资料) 的普通创建命令。
3. App Center 把请求视为全新创建，分配新的 `profileRevisionId`、`sequence` 和创建审计；请求不携带源 Revision ID，服务端不保存复制关系。
4. [UC-APP-016 / BR-PRF-031](../use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-031) 保证原 `REJECTED` Revision、Review snapshot 和拒绝决定保持终态且不可改写。

因此，现行生命周期是：

```text
旧 ProfileRevision: SUBMITTED -> REJECTED（终态）
                                 |
                                 | 前端读取并预填
                                 v
新 ProfileRevision:             DRAFT -> SUBMITTED -> APPROVED | REJECTED
```

## 与 ApplicationVersion 恢复的差异

ApplicationVersion 的 [UC-APP-006](../use-cases/UC-APP-006-restore-rejected-version-to-draft.md) 明确允许对同一个 Version 执行受控的 `REJECTED -> DRAFT`，并在原 Review 上记录一次性恢复审计。ApplicationProfileRevision 选择不同模型：每次重新编辑都创建新的修订身份，旧修订保持不可变。

两者的差异是各自生命周期的显式产品决定，不能据 UC-APP-006 推导出 ProfileRevision 也支持恢复。

## 编号与历史规则

`UC-APP-017` 已被分配，不得重新用于其他行为。本文不恢复 `BR-PRF-033`–`BR-PRF-040`：这些编号没有可核验的权威标题或正文，继续作为 retired 编号保留。

未来如果产品重新引入服务端恢复或复制能力，应使用新的 UC 和 BR 编号，并重新设计权限、终态语义、审计、OCC、工作指针及并发约束；不得把本文重新改为活跃实现依据。
