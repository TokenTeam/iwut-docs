# ApplicationVersion 设计方向

状态：`PROPOSED`。本文只确定边界和后续用例顺序，不替代每个用例的详细设计。

## 结论

版本应从 Application 中立即移出，不保留临时字符串字段。服务没有上线和迁移负担，因此最干净的模型是：

```text
Application
  当前应用身份、技术名称 name、adminId

ApplicationProfileRevision
  一版需要审核和发布的公开目录资料

ApplicationVersion
  一次网页版本的运行内容、权限要求和 RPC 兼容声明

ApplicationReview
  每次提交的不可变内容快照与审核工作流

ApplicationPublication
  stable / grey / test 当前指向哪些已存在版本

ApplicationPublicationHistory
  发布、灰度、稳定和回滚的审计快照
```

旧代码和旧蓝图中值得保留的是“版本独立存在、系统分配内部顺序、按 RPC 合约选择版本”。需要改变的是把 `TEST/GREY/STABLE` 当作 Version.status，以及同时在 Application 保存发布指针。

## 三种版本不要混合

- `clientBuildVersion`：Expo/原生客户端构建版本。
- `rpcApiVersion`：宿主向网页提供的 RPC 合约版本。
- `versionLabel`：学生应用自己的版本标签，例如 `v1.0.0`。

ApplicationVersion 声明 `rpcApiRange + requiredCapabilities`，不使用抽象 platform/target。versionLabel 用于人类识别，不作为排序、发布或兼容判断的依据。

建议由系统分配应用内单调递增的 `sequence` 用于顺序，再用 UUIDv7 `versionId` 作为稳定身份。versionLabel 是大小写敏感、不解析的 1–50 code point 字符串，不强制 SemVer。

## 推荐的版本生命周期

```text
DRAFT
  → SUBMITTED
      → APPROVED
      → REJECTED → DRAFT → 修改或直接再次 SUBMITTED

APPROVED → REVOKED
```

- 只有 DRAFT 可以编辑；REJECTED 必须通过 UC-APP-006 显式恢复为 DRAFT。
- SUBMITTED 对应一次不可变审核快照。
- REJECTED 经明确恢复后可以修改或直接再次提交；每次重新提交都创建新的 ApplicationReview attempt。
- APPROVED 后 URL、scopes、RPC range、capabilities 等受审核字段不可原地修改；改变它们要创建新版本。
- `TEST/GREY/STABLE` 不是生命周期状态，而是 ApplicationPublication 中的槽位引用。

## 已选择的起点

第一个版本用例已经具体化为 [UC-APP-002：创建应用版本](../use-cases/UC-APP-002-create-application-version.md)。它创建只包含运行和授权必要信息的 DRAFT ApplicationVersion：

- 独立 versionId 与应用内 sequence。
- 不透明 versionLabel。
- launchUrl。
- RPC API major range 与 requiredCapabilities。
- requiredScopes 与 optionalScopes。
- DRAFT 状态、createdBy、createdAt，以及为草稿编辑初始化的 revision、updatedBy 和 updatedAt。

第二个版本用例已经具体化为 [UC-APP-003：更新草稿应用版本](../use-cases/UC-APP-003-update-draft-application-version.md)。它采用 PUT 式完整替换和 expectedRevision 乐观并发控制，只修改 DRAFT，不保存每次草稿内容的完整历史。

第三个版本用例已经具体化为 [UC-APP-004：提交应用版本审核](../use-cases/UC-APP-004-submit-application-version-review.md)。它创建独立的 ApplicationReview snapshot，并把 Version 从 DRAFT 原子迁移为 SUBMITTED。提交时重新验证 scopes 和公网 HTTPS URL；快照冻结登记信息，但不声称冻结自托管网页内容。

第四个版本用例已经具体化为 [UC-APP-005：审核应用版本](../use-cases/UC-APP-005-decide-application-version-review.md)。它使用专用 reviewer 权限、利益冲突规则和版本化审核策略，对 PENDING Review 写入一次性决定，并原子同步 Version 状态。APPROVED 仍不会自动发布。

第五个版本用例已经具体化为 [UC-APP-006：恢复被拒绝版本](../use-cases/UC-APP-006-restore-rejected-version-to-draft.md)。它针对最新 REJECTED Review 写入一次性 draftRestoration，并把 Version 显式恢复为 DRAFT；原拒绝 decision 不改变。

第六个版本用例已经具体化为 [UC-APP-007：设置 test 发布槽位](../use-cases/UC-APP-007-place-approved-version-in-test-slot.md)。它由当前管理员把 APPROVED Version 放入单个 rpcApiMajor 的 test 槽位，使用 Publication revision 和追加式 History，不改变 Version 状态。分区理由见 [ADR-002](../adr/ADR-002-partition-publication-by-rpc-api-major.md)。

第七个后续用例已经具体化为 [UC-APP-008：创建或轮换 Tester 加入链接](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md)。Tester 资格与加入凭证属于整个 Application，不绑定 rpcApiMajor；每个 Application 同时只有一个有效链接，二维码只是一次返回 joinUrl 的展示形式，轮换不创建 Tester Membership。

第八个后续用例已经具体化为 [UC-APP-009：通过有效链接加入 Application Tester 列表](../use-cases/UC-APP-009-join-application-as-tester.md)。任意已登录用户都可自助加入，不要求 Developer 资格；Membership 使用 episode 模型、ACTIVE 唯一约束和原子容量上限，被移除后仍可通过有效链接重新加入。

第九个后续用例已经具体化为 [UC-APP-010：管理员移除 Application Tester](../use-cases/UC-APP-010-remove-application-tester.md)。当前管理员按 membershipId 幂等结束 ACTIVE episode 并原子释放一个名额；移除不撤销加入链接或建立黑名单，存在有效链接时界面只显示重新加入警告。

第十个后续用例已经具体化为 [UC-APP-011：管理员显式撤销 Tester 加入链接](../use-cases/UC-APP-011-revoke-tester-join-link.md)。当前管理员按 joinLinkId 幂等写入 REVOKED/MANUAL，立即阻止后续加入但不创建替代链接、不移除现有 Tester。

第十一个后续用例已经具体化为 [UC-APP-012：为 Tester 解析 Application 的 test 启动目标](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md)。这是 App Center 的只读授权查询，不是客户端实现：它根据 ACTIVE Membership、exact RPC major Publication 和 capabilities 返回 TestLaunchDescriptor，不回退其他 major 或发布槽位。

releaseNotes 和其他版本展示资料暂不进入当前版本模型。[UC-APP-013](../use-cases/UC-APP-013-create-application-profile-revision.md) 已建立独立的 `ApplicationProfileRevision` 草稿及 displayName、description、icon 约束，其中 icon 是可空不透明字符串；[UC-APP-014](../use-cases/UC-APP-014-update-draft-application-profile-revision.md) 已建立完整替换编辑与乐观并发语义，[UC-APP-015](../use-cases/UC-APP-015-submit-application-profile-revision-review.md) 已建立独立审核快照与 `DRAFT -> SUBMITTED`，[UC-APP-016](../use-cases/UC-APP-016-decide-application-profile-revision-review.md) 已建立批准/拒绝、批准后自动公开和 REJECTED 终态。SUBMITTED 期间不创建并行 DRAFT；网页端可以用被拒绝内容预填 UC-APP-013 的新建表单，服务端不提供恢复或复制接口。

## 对旧蓝图的修正意见

旧蓝图把 displayName、description、icon、label、color 全部放入 ApplicationVersion，这能形成审核快照，但会把“目录资料变化”强迫成“运行版本变化”。当前更合适的默认边界是：

- Application.name 是大小写不敏感唯一的技术名称，不承担公开展示名称职责。
- ApplicationVersion 只保存与一次运行版本相关的 URL、RPC、capabilities 和 scopes；releaseNotes 等字段等对应用例出现时再加入。
- displayName、description、icon 等公开目录资料属于独立的 `ApplicationProfileRevision`。
- 应用资料修改审核资料 revision，而不是修改 Application 或伪造一个新的运行版本。

## 发布模型

ApplicationPublication 独立保存 `testVersionId/greyVersionId/stableVersionId`。如果多个 RPC major 长期共存，则一条 Publication 对应 `(applicationId, rpcApiMajor)`；如果客户端始终强制升级，也仍建议保留独立 Publication，只是不急着按 major 拆多条。

基本不变量：

- stable/grey 只能引用同一 Application 的 APPROVED 版本。
- 引用版本的 RPC range 必须覆盖 Publication.rpcApiMajor。
- 灰度比例和 rollout seed 属于 Publication，不属于 Version。
- 每次槽位变化写 PublicationHistory，回滚是恢复历史指针，而不是修改旧 Version。

## 推荐的后续用例顺序

1. 开发者创建 DRAFT ApplicationVersion（UC-APP-002）。
2. 开发者编辑 DRAFT（UC-APP-003）。
3. 开发者提交审核，建立 ApplicationReview attempt（UC-APP-004）。
4. reviewer 批准或拒绝（UC-APP-005）。
5. 当前管理员处理拒绝并恢复 DRAFT（UC-APP-006；拒绝分支）。
6. 将 APPROVED version 放入 test 槽位（UC-APP-007）。
7. 创建或轮换 Application 级 Tester 加入链接（UC-APP-008）。
8. 用户通过有效链接加入 Tester 列表（UC-APP-009）。
9. 管理员移除 Tester（UC-APP-010）。
10. 管理员独立撤销加入链接（UC-APP-011）。
11. App Center 为 Tester 解析 test 启动目标（UC-APP-012）。
12. 开始 grey rollout 并逐步提高比例。
13. 提升为 stable，并通过 PublicationHistory 回滚。

每一步都可以反过来更新前一步的模型，不需要现在一次性实现整套发布平台。

## 一个必须正视的弱保证

学生自托管的网页即使 URL 不变，内容也可能在审核后被替换。因此数据库中的“APPROVED 且不可修改”只能锁定登记信息，不能证明远端内容不可变。

后续必须在产品语义中选择：要求版本化不可变 URL、记录可验证构建摘要、使用平台托管制品，或明确采用“抽查与持续监控”的弱审核。当前不为这个问题预设虚假的强保证。
