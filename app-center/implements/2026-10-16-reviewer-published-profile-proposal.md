# Reviewer 当前公开 Profile 投影设计草案

状态：`PROPOSED`。日期：2026-10-16。

本文是待用户审核的变更提案，不改变已接受的 UC、BR 或 API。接受后才更新权威正文、生成 brief 并实现。业务权威为 [UC031](../use-cases/UC-APP-031-query-application-profile-reviews.md)、[资料查询契约](../query-contracts/profile-management.md) 及 [UC016](../use-cases/UC-APP-016-decide-application-profile-revision-review.md)。

## 问题与建议

UC016 APPROVE 已要求 Reviewer 显式提供观察到的 currentPublishedProfileRevisionId，包括首次公开时的 NONE，并在最终事务中比较该指针。现有 UC031 审核详情只有待审快照，没有当前公开资料或指针；管理员查询要求当前 admin 权限，不能作为 Reviewer 的替代读取路径。决定响应中的指针是事后结果，也无法满足事前确认。

建议扩展 UC031 的现有详情，在同一个 MongoDB snapshot 返回当前公开指针及对应的最小资料内容，不增加独立查询入口或额外角色。队列不增加正文。

## 拟增加的响应

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

建议保留现有字段 1–6，在详情增加 message 字段 `current_published_profile = 7`。该 message 的 oneof 为 `google.protobuf.NullValue none = 1` 与 `PublishedProfileForReview published = 2`；published 内依次使用字段 1–4 表达上面的四项内容，description/icon 使用 optional string。最终 Proto 字段占用仍需共享 API owner 核对后落地。

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

## 接受后的实现范围与验收

接受后更新 UC031 审核详情、一致性和 BR-PRF-043/046 的适用范围、资料查询契约及相应 brief/spec。UC016 仅增加查询来源交叉引用，不改批准自动公开、指针 CAS 或拒绝语义。

App 实现范围为 Reviewer read model/port/usecase、Mongo snapshot 查询、API/transport 与编码验证；不复用当前 admin 的授权入口，不新增写模型、schema migration 或 Profile 策略版本。

验收至少覆盖：

1. 从未公开返回显式 none；存在公开资料时返回正确 ID 和批准内容，description/icon presence 不丢失。
2. 独立 Profile Reviewer 可读，只有 Version 权限者不能读；权限检查先于路径存在性，既有利益冲突提示及决定禁令继续成立。
3. 悬挂、跨应用、未批准、缺失批准事实和内容漂移均失败关闭；Catalog 不可见不等于 none。
4. 真实 MongoDB 读写竞争下，一个响应的 pointer 与内容始终配对；对合法待审记录提交过期指针被 CAS 拒绝，同一 Review 的双决定只有一个成功，不发生覆盖。不为测试绕过单一 working 修订约束。
5. HTTP JSON、原生 gRPC 和生成客户端区分 none/published/缺失/非法状态；最长合法内容完整返回，缓存头在成功和错误路径保持成立。
6. Console 首次公开、替换预览、409 重新确认和未知结果回读；拒绝请求继续省略 pointer。

## 审核点与后续顺序

请审核同一详情中增加 Reviewer 专用最小投影，以及 explicit none、损坏失败关闭和读后 CAS 的边界。用户接受后才修改权威来源和实现。

此草案与 [Version 正式检查定义](2026-10-16-version-review-check-definitions-proposal.md) 构成第 1 步。接受后先实现 App/API，再由 Gateway agent 为两个决定 RPC 增加精确 `ADMIN` surface，最后由 Console agent 接入决定并完成真实 Cookie/权限撤销/并发验收；不改变既有 API Session 接口已完成验收的结论。
