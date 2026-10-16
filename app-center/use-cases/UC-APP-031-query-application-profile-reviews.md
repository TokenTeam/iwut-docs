# UC-APP-031：查询 ApplicationProfileRevision 审核队列与审核详情

状态：`ACCEPTED`

## 目标与范围

> 具备 `app.profile.review` 的 Reviewer 查询待处理公开资料审核队列，并读取一次资料审核的不可变详情。

本用例将 [资料管理与审核查询契约](../query-contracts/profile-management.md) 中的 Reviewer 查询交付为正式 API。管理员 ProfileRevision 列表/详情仍是独立管理查询范围；本用例不实现分配、锁单、SLA、通知、申诉或恢复被拒绝修订。

## 身份与精确权限

两个查询只接受可信 USER 身份和 `app.profile.review`。`app.version.review`、Application 管理员或 Developer 资格都不隐式授予权限。权限检查先于对象查找。

缺少身份返回 `ReviewerIdentityRequired`；缺少精确权限返回 `ApplicationProfileReviewPermissionRequired`。

## 待处理队列

```text
ListPendingApplicationProfileReviewsQuery {
  applicationId?
  pageSize: 1..100 = 20
  pageToken?
}
```

队列只包含 `ApplicationProfileReview.status=PENDING` 且所属 Application `lifecycleStatus=ACTIVE` 的记录。`SUSPENDED` 不阻止审核；`CLOSING/CLOSED` 按 UC027 排除。

按 `(submittedAt ASC, profileReviewId ASC)` 稳定 keyset 分页。队列项包含 Application ID/name、ProfileRevision ID/sequence/displayName、ProfileReview ID/attempt、submittedAt，以及查询时计算的：

```text
decisionEligibility {
  eligible
  conflicts: CURRENT_ADMIN | REVISION_CREATOR | REVIEW_SUBMITTER []
}
```

冲突项不从队列隐藏。eligibility 是界面提示，UC016 的决定事务仍重新计算。

## 审核详情

详情路径中的 `applicationId/profileRevisionId/profileReviewId` 必须匹配。结果包含：

```text
ApplicationProfileReviewDetail {
  application { applicationId, name, adminId, lifecycleStatus, platformAvailabilityStatus }
  profileRevision { profileRevisionId, sequence, reviewStatus, revision, createdBy }
  review {
    profileReviewId, attempt, status, sourceRevision,
    snapshot { displayName, description, icon },
    submittedBy, submittedAt, decision?
  }
  currentPolicy { version, requiredCheckIds }
  currentPublishedProfile { oneof state { none | published { profileRevisionId, displayName, description?, icon? } } }
  decisionEligibility
  asOf
}
```

内容必须取不可变 Review snapshot。终态 Review 可按 ID 读取。当前 policy 第一版为 `app-profile-review-v1` 及其固定检查项，但查询结果不替代 UC016 在写入时对 expected policy 和 confirmed checks 的复查。

## 一致性与错误

单页和详情在 MongoDB majority snapshot 中构造。Application、ProfileRevision、Review 的引用、sourceRevision 或 snapshot 不一致时返回 `ApplicationProfileReviewStateInconsistent` / INTERNAL；不能省略坏项或回退到当前 ProfileRevision 内容。

不存在或路径不匹配返回 `ApplicationProfileReviewNotFound`。合法空队列成功返回空页。pageSize/pageToken 非法返回 INVALID_ARGUMENT。响应使用 `private, no-store`。

## 当前公开资料投影

```text
ApplicationProfileReviewDetail {
  ...既有字段
  currentPublishedProfile {
    oneof state {
      none: explicit null marker
      published {
        profileRevisionId
        displayName
        description?  // 缺省保持缺省
        icon?         // 普通文本；缺省保持缺省
      }
    }
  }
}
```

保留现有字段 1–6，在详情增加 message 字段 `current_published_profile = 7`。该 message 的 oneof 为 `google.protobuf.NullValue none = 1` 与 `PublishedProfileForReview published = 2`；published 内依次使用字段 1–4 表达上面的四项内容，description/icon 使用 optional string。字段编号在共享 API 生成检查中核对。

HTTP JSON 示例：

```json
{ "currentPublishedProfile": { "none": null } }
```

```json
{
  "currentPublishedProfile": {
    "published": {
      "profileRevisionId": "01995000-0000-7000-8000-000000000002",
      "displayName": "示例应用",
      "description": "当前公开说明"
    }
  }
}
```

服务成功返回时必须存在 currentPublishedProfile 且恰有一个 state。缺字段、空对象、未知 state 或非法 ID 都是客户端不可用于批准的响应；不能解释为 NONE。首次公开只由服务端确认的 none 表示。

不返回当前公开修订的 creator、submitter、审核人、完整 Review、其他历史修订或管理字段。icon 保持现有不透明纯文本契约，不当作 URL 自动加载。待审内容仍取 `review.snapshot`，并与 currentPublishedProfile 分开展示；当前资料不替换待审快照。

## 授权与一致性

沿用 UC031：可信 USER 身份、精确 `app.profile.review`，先检查权限，再查对象；Version Reviewer、Developer 或当前 admin 都不隐式取得此读取权。详情路径三元组不匹配继续 NOT_FOUND。

在原有详情 snapshot 内读取 ApplicationProfile、其当前公开修订及批准 Review，并验证：

1. ApplicationProfile 属于同一 Application；公开指针为空才返回 none。
2. 非空指针是合法 ProfileRevision ID，指向同 Application 的 APPROVED 修订；其批准 Review 与修订、内容和既有批准不变量一致。
3. published 内容来自被该批准事实确认的不可变资料，不能回退到 working 修订、最新创建修订或待审 snapshot。

ApplicationProfile 缺失、非空指针悬挂、跨 Application 引用、非 APPROVED 状态或批准内容不一致，均使整次详情返回既有 `ApplicationProfileReviewStateInconsistent` / INTERNAL；数据库不可用按既有基础设施错误映射，不能伪装成 none 或返回部分详情。

当前公开在此表示 ApplicationProfile 的公开指针，不要求 Stable 槽位或普通 Catalog 当前可见。SUSPENDED、归档或没有 Stable 不将非空指针转换为 none；CLOSING/CLOSED 的终态详情仍按现有审计读取规则返回事实，不因此授予决定权。

同一响应的 application、待审 Review、currentPolicy、当前公开投影、eligibility 和 asOf 必须来自同一 snapshot。该结果仅是读取时观察；不锁定任务，也不授权后续写入。

## 决定与并发

Console 批准确认页展示“当前公开资料”和“本次拟公开资料”。none 显示“首次公开”，published 显示替换对象 ID 和内容；用户明确确认后，才把本次观察的 pointer 带入现有命令：

| 观察到的状态 | UC016 APPROVE 请求 |
| --- | --- |
| `none: null` | 显式 `expectedCurrentPublishedProfileRevisionId: null` |
| `published.profileRevisionId = X` | `expectedCurrentPublishedProfileRevisionId: X` |
| 缺失、解析失败或未知状态 | 阻止批准，重新读取；不得猜测 null |

继续提交本次观察的 expectedProfileRevisionRevision 与 expectedPolicyVersion。REJECT 仍省略 expectedCurrentPublishedProfileRevisionId，不检查或改变公开指针。UC016 的写规则、错误和事务边界不改变。

APPROVE 提供的指针与最终事务中的当前指针不同时，由现有指针 CAS 返回 `ApplicationProfilePublicationConflict`（HTTP 409 / gRPC ABORTED）。Console 重新读取并让 Reviewer 重新确认；不替换成最新指针后自动重发。同一 Review 已被其他 Reviewer 决定时，继续返回既有 already-decided 等错误，不强行将所有竞争映射为指针冲突。未知提交结果沿用决定结果回读流程，不假定失败并自动重复执行。

## 大小、缓存和兼容

资料沿用现有界限：displayName 80、description 1000、icon 512 个 Unicode scalar values。单个新增内容投影即使使用 JSON Unicode 转义也应小于 32 KiB；实际编码测试同时覆盖 JSON 与 protobuf。该数值是新增投影的验证界限，不新设更宽的输入界限或放宽 transport 配置；详情整体仍受现有 transport 上限约束，不截断正文或返回只有 pointer 的“成功”。

这里不把 UC039 管理查询的 2 MiB 预算误写成 UC031 已有业务规则。实现若发现合法整体响应可能超过现有 transport 上限，应在编码验证阶段提出具体 gap，再审核预算变更。

成功与错误响应沿用 private, no-store，经 Gateway/BFF 后也必须成立。新增投影只存在于受 Reviewer 精确授权保护的详情，不扩展到公共 Catalog。

共享 API 先生成类型，Console agent 先升级严格解码和 oneof 校验：允许旧服务缺少该字段时继续只读，批准必须等待完整合法投影。随后协调 App 服务启用输出及 Console 页面刷新；现有旧 JSON decoder 不接受未知字段，需要明确切换窗口。不能把接口加字段当成旧页面天然兼容，也不通过全局忽略未知字段掩盖非法状态。


## 最小查询模型与索引

复用或补齐 `(status, submittedAt, profileReviewId)` 索引。read port 独立于决定 repository；队列通过批量 lookup 读取 Application 和 ProfileRevision，禁止 N+1。

## API 草图

```text
rpc ListPendingApplicationProfileReviews(...)
  POST /v1/reviews/application-profiles:search body=query

rpc GetApplicationProfileReview(...)
  GET /v1/applications/{application_id}/profile-revisions/{profile_revision_id}/reviews/{profile_review_id}
```

## 验收场景

1. 只有精确 `app.profile.review` 可读取；Version Reviewer 单独权限不足。
2. PENDING+ACTIVE 入队；CLOSING/CLOSED 排除；SUSPENDED 保留。
3. applicationId filter、升序 keyset、tie-break 与 token 绑定稳定。
4. 当前管理员、revision creator、submitter 冲突被完整提示而不隐藏队列项。
5. 详情返回 immutable snapshot 与当前固定 policy/checks。
6. 终态 Review 可查询但不进入 pending 队列。
7. 路径不匹配统一 NOT_FOUND；无权限先失败。
8. sourceRevision/snapshot/引用损坏返回 INTERNAL，不产生部分结果。
9. HTTP 与原生 gRPC 一致，真实 MongoDB 验证索引与 snapshot 行为。

## 实现依赖与交付边界

ProfileRevision、ProfileReview、固定 policy 和决定流程均已交付。当前公开投影扩展仅需读取既有数据，不新增写模型或 migration。现有查询契约提供读取语义；本工作包新增 API、read port/usecase、Mongo query、必要索引、transport/wiring 和验收，不改变 UC013–016 写模型。

## 业务规则

<a id="br-prf-041"></a>
### BR-PRF-041：Profile Reviewer 查询精确授权

资料审核队列与详情只接受具备 `app.profile.review` 的可信 Reviewer，权限检查先于对象查找。

<a id="br-prf-042"></a>
### BR-PRF-042：待处理资料队列资格

队列只包含 PENDING 且 Application 生命周期 ACTIVE 的资料 Review；SUSPENDED 保留，CLOSING/CLOSED 排除。

<a id="br-prf-043"></a>
### BR-PRF-043：资料审核快照权威

待审内容来自提交时不可变 snapshot，不能用当前 ProfileRevision 替换。详情另返回当前公开指针对应的批准资料，必须独立标识，不能覆盖待审内容。

<a id="br-prf-044"></a>
### BR-PRF-044：利益冲突提示不替代决定检查

查询计算的 eligibility 只用于 Reviewer 界面；UC016 在决定事务中重新计算全部冲突和前置条件。

<a id="br-prf-045"></a>
### BR-PRF-045：稳定资料队列分页

队列按 `(submittedAt, profileReviewId)` 升序 keyset 分页，token 绑定 Reviewer 与 filter。

<a id="br-prf-046"></a>
### BR-PRF-046：资料审核查询失败关闭

引用、sourceRevision、snapshot 或当前公开资料/批准事实损坏导致整次查询 INTERNAL；不能跳项、降级、伪造 NONE 或返回部分详情。

## 变更记录

- 2026-10-16：用户接受 Reviewer 当前公开资料最小投影，沿用精确权限和 UC016 指针 CAS。
- 2026-10-07：将既有 PROPOSED Reviewer 查询语义收敛为正式工作包，设计进入 `ACCEPTED`。
