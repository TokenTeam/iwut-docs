# App Center 开放问题

以下问题不阻塞当前文档设计；其中标在具体用例“实现前需要确认”部分的项目，会阻塞对应设计进入 `ACCEPTED`，或阻塞实现进入其声明的下一状态。

## 身份

- developerStatus 被暂停后，已有应用是否继续可用，还是只禁止创建和管理？
- `app.version.review` 权限由谁申请、授予、暂停和撤销？当前只确认 Auth 是权限事实来源。
- 是否需要双人批准、按 scope/风险等级分配 reviewer，或在高风险应用上升级审核？当前 UC-APP-005 只要求一名无利益冲突的 reviewer。

## 字段

- 外部自托管 URL 的内容可以在不改 URL 的情况下变化；审核如何描述和限制这一弱保证？
- requiredCapabilities 的正式命名规范是什么，是否需要由某个上下文维护 catalog？
- Scope 被 Auth 删除、deprecated 或 retired 时，已批准版本和已授权 token 分别如何处理？当前 DRAFT 可以保留，但 UC-APP-004 会阻止仍申请该 scope 的版本提交审核；开发者需要先从草稿中移除它。
- 当前 icon 只是可空不透明字符串。若未来升级为受控图标资产，由 App Center 还是 Resource Hub 保存、如何保证内容版本稳定，以及怎样迁移既有字符串？

## 用例行为

- 配额初始值是否确认为 10？本文根据“初始是是个”暂按“十个”处理。
- 哪些 Application 计入配额：全部、未删除，还是未归档？当前只有创建用例，暂按全部创建记录计数。
- 上线应用数量如何提升配额：固定公式、人工审核还是二者结合？
- CreateApplication 是否需要幂等键？当前名称唯一规则已能阻止同名重复创建，暂不增加幂等键。
- reviewer decision 当前写入后不可修改。资料审核不建立系统内申诉渠道，开发者需要直接联系平台；若未来确有纠错需求，应设计独立、可审计行为，不原地改写 decision。
- test 槽位清空是普通管理员行为，还是在存在活跃 tester 时需要额外确认？
- Application 管理员日常可恢复归档应如何影响 Catalog、配额和 owner 义务？平台紧急暂停/恢复已经与它分离并由 UC-APP-028 提案定义。
- AI DRAFT 审核未来读取哪些内容、如何标识模型与策略版本、结论是建议还是门禁，以及怎样进入生命周期？当前不实现，也不增加 AI 状态或自动迁移。

## UC-APP-027 已关闭的接受依赖

- [UC-AUTH-026](../auth-center/use-cases/UC-AUTH-026-apply-application-closure.md) 已把 application closure tombstone 纳入 authorize、code exchange、token/refresh、UserInfo 和在线 delegation 的最终检查边界，并与 [Application Closure v1](../platform/contracts/application-closure-v1.md) 对齐。
- [Application 关闭近期认证证明 v1](../platform/contracts/application-close-reauth-proof-v1.md) 已固定当前 Session 所属同一登记设备的新 challenge/signature、`purpose=app.close`、applicationId、sub、jti、auth_time 和 5 分钟上限；普通 USER JWS `iat` 明确不能替代。

## 旧实现（已确认，不再开放）

- 旧实现已雪藏；当前实现是 App Center 首个正式版本，不作为独立第二代 module。
- 服务从未上线，因此不迁移旧 application 数据，也不维护旧 API 兼容；旧代码只作为需求参考。

## 已确认的相邻边界

- UC-APP-005 的真实 reviewer 身份/permission transport 等待 Auth Center 重新设计；核心实现不猜测 token KV、claim 或 header 形状。
- UC-APP-005 的 VersionReviewPolicy 首版由 App Center 本地拥有；仍需发布第一版
  正式检查项和内容政策，并实现不可变的历史版本 repository。
- reviewer 打开自托管页面的 iframe/隔离浏览环境属于前端与安全运行环境，不属于 UC-APP-005 后端核心。
- UC-APP-005 批准时发现当前 admin 或 submittedBy 已暂停，由注入的 System Auth ID 将 PENDING Review 与 SUBMITTED Version 原子迁移为 REJECTED。

在对应新用例出现前，不为了回答这些问题提前扩充领域模型。

## 已确认的后续设计方向

- Test-only Application 进入独立的“我参与的测试”入口，不因 Tester 资格混入普通公开目录。
- Stable 可以直接选择任意当前合格的 APPROVED Version，不强制要求它先进入 Test 或 Grey；回退是重新设置历史合格 Version。
- 管理员日常停止某个渠道使用 clear；平台紧急处置使用 [UC-APP-028](use-cases/UC-APP-028-suspend-and-restore-application.md) 的 Application 级 suspension，不销毁原槽位配置。
- [UC-APP-026](use-cases/UC-APP-026-transfer-application-administration.md) 已提出普通管理员转让的完整规则：原管理员发起、目标显式接受，接受时原子移动配额；目标容量不足或存在同名应用时拒绝。平台强制转让、争议仲裁和紧急接管明确后置为独立治理用例。
- [UC-APP-027](use-cases/UC-APP-027-close-application.md) 已确定不可逆关闭语义：CLOSING 立即停止本地运行与管理、释放配额和 owner 义务，保留历史与技术名称；Auth application tombstone 持久收敛后进入 CLOSED。归档、临时停用和平台 suspension 仍是不同的可恢复能力。
- [UC-APP-028](use-cases/UC-APP-028-suspend-and-restore-application.md) 已形成平台 suspension/restore 提案：两项精确权限独立授予，平台可用状态与关闭正交，暂停保留配置和 owner 义务，统一阻止 Catalog、启动、Tester Join 与 OAuth 在线 provider，恢复后重新执行当前资格。管理员日常归档仍另立用例。
- [UC-APP-021](use-cases/UC-APP-021-manage-grey-rollout.md) 已接受 Grey 首版只面向已登录用户、要求 Stable 基线、使用万分比和 per-rollout CSPRNG seed 的 HMAC 确定性分桶。
- Filter 使用独立 ApplicationFilterRevision 方向，避免把规则塞进 Application 或强制与 Profile 同步修订；规则语言和审核策略仍待定义。
