# App Center 统一语言

状态：`PROPOSED`

本文件记录当前用例及已经明确的下一步设计方向中出现的词。

## Application

由开发者在 App Center 中创建的一条应用记录。

当前只包含 id、name、adminId 和 createdAt。它不表示公开目录资料、OAuth client、可发布版本、审核对象或运行中的服务。

## Application ID

系统生成、全局唯一且创建后不可改变的 UUIDv7。

调用方不能从其格式推断 owner、名称、创建时间或其他业务信息。

## Developer

发起新建应用用例的参与者。

所有师生都可以申请成为 Developer。师生身份由客户端与用户中心共同进行弱验证；由于没有官方合作和服务端官方验证界面，这个结果不被视为强身份凭证。

Developer 资格由 Auth 独立保存，状态为 `PENDING/APPROVED/REJECTED/SUSPENDED`。只有 `APPROVED` 可以创建应用。

客户端在发起申请时完成弱师生验证，平台后续自行联系确认。不向 App Center 传递或保存学生证明材料；Auth 只保存资格结果及必要的操作审计信息。

## authId

Auth Center 分配的用户身份 ID。App Center 不负责生成或解释它。

## adminId

Application 当前管理员的 authId。创建时等于调用者 authId，不属于 CreateApplication 请求正文。

adminId 不是永久绑定创建者的字段：学生毕业后可以通过未来的管理员转让用例把应用交给新的维护者。

## name

开发者为应用填写的技术名称。长度为 1–50，只允许英文字母、数字、`-`、`_`；保留输入大小写供管理界面和开发者识别，但同一 adminId 下按 ASCII lowercase 结果唯一。它不是面向普通用户的 displayName。

## description

面向用户公开的应用简介。它不属于 Application 或 CreateApplicationCommand，由 ApplicationProfileRevision 保存；当前是遵循 [BR-PRF-004](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-004) 的可空纯文本。

## ApplicationProfileRevision

某个 Application 的一版完整公开目录资料。它与 ApplicationVersion 分离，以便资料修改、审核和发布不制造虚假的运行版本。

UC-APP-013 已建立包含 displayName、可空 description 和可空 icon 的 DRAFT，并分配独立 UUIDv7、应用内 sequence、乐观并发 revision 与创建/修改审计；UC-APP-014 建立其完整替换编辑语义；UC-APP-015 建立提交审核与 SUBMITTED 状态；UC-APP-016 建立 APPROVED/REJECTED 决定、批准后自动公开和 REJECTED 终态。icon 当前只是不透明字符串，未来受控资产能力需要显式扩展和迁移。

## Application Profile Icon

ApplicationProfileRevision 中可空的不透明字符串。它遵守 [BR-PRF-005](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-005) 的长度与字符规则，但 App Center 不解释它是 URL、资产 ID 或其他引用，也不读取它指向的内容。

## Profile Sequence

系统在单个 Application 内为 ApplicationProfileRevision 分配的单调递增整数，从 1 开始。它只用于稳定排序和审计，不是资料修订身份，也不同于乐观并发 revision；规则见 [BR-PRF-001](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-001)。

## DRAFT ApplicationProfileRevision

尚未提交审核、不会进入普通用户目录的完整资料草稿。根据 [BR-PRF-006](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-006)，一个 Application 同时至多拥有一份 DRAFT 或 SUBMITTED 工作修订；当前管理员依据 [BR-PRF-009](use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-009) 和 [BR-PRF-011](use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-011) 进行带乐观并发控制的完整替换。

## SUBMITTED ApplicationProfileRevision

已经形成不可变 ApplicationProfileReview snapshot、正在等待 Reviewer 决定的资料修订。它不能继续以草稿更新，不会仅因提交而改变当前公开资料，并继续占用唯一工作修订位，因此不能并行创建下一份 DRAFT；规则见 [BR-PRF-006](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-006)、[BR-PRF-016](use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-016) 与 [BR-PRF-022](use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-022)。

## ApplicationProfileReview

某个 ApplicationProfileRevision 的一次独立审核 attempt。它保存不可变 displayName/description/icon snapshot、sourceRevision、提交审计和一次性 decision。

## ApplicationProfileReview Decision

具有 `app.profile.review` 权限且无利益冲突的 Reviewer，依据版本化 ProfileReviewPolicy 对 PENDING ProfileReview 写入的一次性 `APPROVED` 或 `REJECTED` 结论。批准会自动把该 Revision 设为当前公开资料；拒绝不改变原公开资料。

## APPROVED ApplicationProfileRevision

已经通过资料审核的完整资料修订。批准 decision 与 `currentPublishedProfileRevisionId` 替换在同一业务操作中完成；它不会创建 stable、grey 或 test 发布槽位。

## REJECTED ApplicationProfileRevision

资料审核被拒绝的修订。它是终态，不直接编辑也不恢复为 DRAFT。网页端可以用其内容预填创建表单，再调用普通创建用例生成拥有新身份的 DRAFT；权威规则见 [BR-PRF-031](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-031)。

## Current Published Profile Revision

`ApplicationProfile.currentPublishedProfileRevisionId` 指向普通用户当前可见的已批准资料。它由资料批准自动替换，不是管理员手动操作的第四种发布槽位；首版不提供选择旧 Revision 或回滚公开资料。

## ApplicationVersion

某个 Application 的一次可审核、可发布的网页版本。它拥有独立 UUIDv7 ID、应用内 sequence、开发者版本标签、入口 URL、RPC 兼容声明、scopes 和审核生命周期。

ApplicationVersion 由独立用例创建，不再把临时 version 字符串存入 Application。版本内容、审核记录和 stable/grey/test 发布槽位是不同概念。

## Version Sequence

系统在单个 Application 内分配的单调递增整数，从 1 开始。它用于稳定排序和审计，不是版本身份，也不参与 RPC 或 SemVer 兼容判断。

## Version Label

开发者为 ApplicationVersion 填写的人类可读版本标签，例如 `v1.0.0`。它是 1–50 个 Unicode code point 的纯字符串，同一 Application 下大小写敏感地唯一，不解析为 SemVer。

## RPC API Range

ApplicationVersion 声明的 Expo Host RPC major 兼容区间，使用 `[min, maxExclusive)` 表达。上下界都必须明确，不能默认兼容尚未发布的未来 major。

它不同于 Expo 客户端 build version，也不同于学生应用自己的 Version Label。

## Required Capability

除了 RPC major 外，网页版本要求宿主明确提供的能力名，例如 `camera.read.v1`。没有额外要求时保存空数组。

## Required Scope / Optional Scope

ApplicationVersion 希望通过 Auth 取得的用户数据权限。Required Scope 是正常工作所必需的权限；Optional Scope 可以由用户拒绝而不阻断基本功能。二者不得重复或交叉。

## DRAFT ApplicationVersion

刚创建、尚未提交审核的版本。当前管理员可以用完整替换操作修改其可编辑内容；每次实际修改都需要匹配 revision。DRAFT 不会进入普通用户目录，也不能成为 stable 或 grey 版本。

## SUBMITTED ApplicationVersion

已经形成 ApplicationReview 快照、正在等待 reviewer 决定的版本。SUBMITTED 不能继续编辑，也不等于 APPROVED 或已发布。

## ApplicationReview

某个 ApplicationVersion 的一次审核 attempt。它保存提交时的受审核字段快照、源 Version revision、提交者、提交时间和审核工作流状态。

snapshot 创建后不可修改；同一 Version 被拒绝后若再次提交，会创建新的 ApplicationReview，而不是覆盖旧记录。

## Reviewer

由 Auth 授予专用审核权限的平台审核人员。运行版本审核使用 `app.version.review`，公开资料审核使用独立的 `app.profile.review`；两者不互相隐式授权。Reviewer 不等于 Developer，也不等于拥有所有能力的通用管理员。

Reviewer 不能审核自己创建、提交或当前管理的应用版本或公开资料。

## ApplicationReview Decision

Reviewer 对 PENDING ApplicationReview 作出的一次性 `APPROVED` 或 `REJECTED` 结论。Decision 保存审核策略版本、明确确认的检查项、审核人、审核时间，以及可选的批准备注或必需的拒绝理由。

Decision 写入后不可修改；纠错、撤销或重新审核必须产生新的显式行为和审计事实。

## APPROVED ApplicationVersion

对应审核快照已经被 reviewer 接受的 Version。APPROVED 只获得进入后续发布流程的资格，不等于已经进入 test、grey、stable 或普通用户目录。

## REJECTED ApplicationVersion

最近一次审核被拒绝的 Version。拒绝决定保留原因；它不能直接编辑，必须先由当前管理员针对最新 rejected review 显式恢复为 DRAFT。

## Draft Restoration

当前管理员处理一次 REJECTED ApplicationReview、使对应 ApplicationVersion 回到 DRAFT 的显式行为。它记录 restoredBy、restoredAt 和恢复后的 Version revision，但不修改原 decision 或 snapshot。ApplicationProfileReview 不使用 Draft Restoration。

一个 rejected review 只能恢复一次。新的审核 attempt 若再次被拒绝，会拥有自己的 Draft Restoration。

## ApplicationPublication

某个 Application 在一个明确 rpcApiMajor 下的当前发布槽位状态。它与 ApplicationVersion 的审核生命周期分离，并拥有自己的 revision 和修改审计。

当前已定义 Test、Grey 与 Stable 槽位。全部槽位共享 revision 和追加式审计。

## Grey Rollout

UC-APP-021 定义的 exact-major 灰度运行配置，包含 rolloutId、目标 ApplicationVersion、万分比 exposureBasisPoints 和只在服务端保存的 cohortSeed。它必须依附 Stable 基线，只对可信已登录 authId 做确定性分桶；连续 rollout 内比例调整和 Version 替换不改变 cohort，Clear 后重新建立会产生新 cohort。

Grey Rollout 不是 Version 审核状态、Tester 资格或客户端 Filter。

## Test Slot

ApplicationPublication 指向一个兼容且 APPROVED ApplicationVersion 的测试发布槽位。它表示面向开发者社群中普通用户的小范围受控分发，要求应用已有当前已批准公开资料；它可以在 tester 为零时存在，但不会仅因存在就向普通用户公开。

Version 进入或离开 Test Slot 不改变它的 reviewStatus，也不会停用 Version。

开发版 iWUT Client 直接打开任意 URL 是客户端开发预览能力，不属于 Test Slot，不创建 Publication，也不提供 OAuth 运行资格。

## Application Tester

拥有某个 Application 测试访问资格的 Auth 用户。Tester Membership 属于整个 Application，不绑定 rpcApiMajor、ApplicationVersion 或具体 test 槽位。

当前 admin 不会自动成为 Tester。更换 test 槽位不会使既有 Tester 失效；运行时仍使用客户端实际 rpcApiVersion 和 capabilities 解析兼容版本。

Tester 不要求 Developer 资格。用户通过有效 Tester Join Link 自助加入；同一 `(applicationId, authId)` 同时最多有一个 ACTIVE Membership episode。被移除后不存在黑名单，持有效链接且容量允许时可以再次加入。

## Tester Join Link

允许已登录用户在后续用例中自行加入 Application Tester 列表的匿名凭证，不指定目标 authId，也不等于一条 Tester Membership。

每个 Application 同时最多有一个 ACTIVE Tester Join Link。App Center 只保存 secret 哈希和链接生命周期；二维码只是 joinUrl 的展示形式。轮换会以 `ROTATED` 原子撤销旧链接并创建新链接；显式撤销使用 `MANUAL` 且不创建替代链接。两种撤销都不会新增或移除 Tester。

## Tester Membership Episode

一个 authId 在某个 Application 中从加入到被移除的一段 Tester 资格。每次重新加入创建新的 membershipId，不恢复过去的 REMOVED episode。

每个 Application 最多有 100 个 ACTIVE Tester。重复使用有效链接加入时返回既有 ACTIVE Membership，不重复占用容量。

当前管理员按 membershipId 移除 Tester 时，episode 进入 REMOVED 终态并释放一个名额。移除不撤销加入链接、不建立黑名单；若链接仍有效，该用户可以创建新的 Membership episode。

## Test Launch Resolution

App Center 为已认证 Tester 执行的只读授权查询。它使用 Application 级 ACTIVE Membership、宿主实际 RPC API major、host capabilities 和对应 ApplicationPublication，解析唯一的 test ApplicationVersion。

解析不代表 App Center 实现客户端、WebView 或 RPC bridge，也不会回退到其他 RPC major、grey 或 stable。

## Test Launch Descriptor

Test Launch Resolution 的一次性查询结果，包含 test Version 的 launchUrl、版本身份、RPC range、requiredCapabilities、scopes 和所使用的 publicationRevision。

Descriptor 不持久化为新实体，不是长期 session 或 Auth token；客户端如何启动页面、执行 consent 和提供 RPC 能力属于相邻边界。

## ApplicationPublicationHistory

每次 Publication 槽位真实变化时追加的不可变审计记录，包含前后 Version、结果 revision、操作者、时间以及发布复检依据。

History 不替代当前 ApplicationPublication，也不要求使用 event sourcing 重建当前状态。

## Review Attempt

ApplicationReview 在单个 versionId 下从 1 开始递增的序号，用于区分同一 Version 的多次提交。reviewId 才是审核记录的稳定身份。

## Revision

ApplicationVersion 的乐观并发版本号。创建 DRAFT 时为 1；客户端执行内容修改或生命周期迁移时必须提交读取到的 revision，成功产生变化后原子递增。

revision 不是 Version Sequence，也不是 Version Label。它用于检测同一 ApplicationVersion 上的并发修改和状态竞争。

## updatedBy / updatedAt

ApplicationVersion 最近一次实际内容或生命周期修改的 authId 和系统时间。创建时分别等于 createdBy 和 createdAt；无内容变化的更新不会改写它们。

## createdAt

Application 或 ApplicationVersion 创建成功的系统时间，用于后续审计。由 App Center 时钟产生，创建后不可修改。

## Application Creation Quota

某个 adminId 最多可以拥有多少个计入配额的 Application。初始上限暂定为 10，未来可以根据其已上线应用数量提升。

## ApplicationAdminTransfer

把 Application 管理权从当前 admin 转给指定新 admin 的申请。原 admin 发起，新 admin 接受后，Application.adminId 才发生改变。

Application 只保存当前 adminId；申请状态、双方身份和审计时间保存在独立转让记录中。
