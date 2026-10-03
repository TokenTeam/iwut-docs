# App Center 开放问题

以下问题不阻塞当前文档设计；其中标在具体用例“实现前需要确认”部分的项目，会阻塞对应设计进入 `ACCEPTED`，或阻塞实现进入其声明的下一状态。

## 身份

- developerStatus 被暂停后，已有应用是否继续可用，还是只禁止创建和管理？
- `app.version.review` 权限由谁申请、授予、暂停和撤销？当前只确认 Auth 是权限事实来源。
- 是否需要双人批准、按 scope/风险等级分配 reviewer，或在高风险应用上升级审核？当前 UC-APP-005 只要求一名无利益冲突的 reviewer。
- 管理员转让由原 admin 发起、新 admin 接受；是否允许平台 reviewer 强制取消或介入争议？
- 管理员转让后，原 admin 与新 admin 的配额占用如何变化？当前建议在接受时检查新 admin 配额并转移一个占用。
- 若新 admin 已有大小写等价的同名应用，转让是直接拒绝，还是允许同时改名？当前建议拒绝并要求先改名。

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
- Application 级禁用应如何区分 admin 与 SysAdmin 权限，如何影响 Catalog、运行解析和现有 Publication，并允许怎样的重新启用？紧急隐藏公开资料归于此能力，不增加 ProfileRevision REVOKED 状态。
- AI DRAFT 审核未来读取哪些内容、如何标识模型与策略版本、结论是建议还是门禁，以及怎样进入生命周期？当前不实现，也不增加 AI 状态或自动迁移。

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
- 管理员日常停止某个渠道使用 clear；平台紧急处置使用后续 Application 级 suspension/disable，不销毁原槽位配置。
- Grey 首版只面向已登录用户做确定性分桶，并且必须存在 Stable 基线；具体哈希输入、seed 与比例语义由 Grey UC 定义。
- Filter 使用独立 ApplicationFilterRevision 方向，避免把规则塞进 Application 或强制与 Profile 同步修订；规则语言和审核策略仍待定义。
