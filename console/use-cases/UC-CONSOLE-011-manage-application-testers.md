# UC-CONSOLE-011：管理应用测试邀请与成员

状态：`ACCEPTED`，2026-10-30。依据用户持续 goal 的自主设计和接受授权登记。先在 P0 产品冻结期间完成设计；待 P0 静态产物固定、前端集成工作包明确解除冻结后开始实施。设计接受不表示客户端、页面或真实链路已经完整验收；实现证据分别登记。

## 用户目标与权威边界

当前应用管理员在“测试配置”页创建或轮换测试加入链接、撤销指定链接、移除指定测试成员，并理解三个动作各自的结果和恢复方式。

后端权威分别为 App [UC008 创建/轮换链接](../../app-center/use-cases/UC-APP-008-create-or-rotate-tester-join-link.md)、[UC010 移除成员](../../app-center/use-cases/UC-APP-010-remove-application-tester.md)、[UC011 撤销链接](../../app-center/use-cases/UC-APP-011-revoke-tester-join-link.md)、[UC037 管理查询](../../app-center/use-cases/UC-APP-037-query-application-tester-management.md)及 [Tester 加入 URL v1 契约](../../platform/contracts/tester-join-url-v1.md)。本 UC 只定义 Console 流程，不复制资格、容量、事务或审计规则。

测试资格与邀请属于整个 Application，不属于某个运行版本或协议 major。测试发布仍在 UC008 版本与发布工作台，管理查询与分页继续遵循 Console UC005。

## 页面职责与独立动作

沿用 `/applications/:applicationId/testers`，保留容量/当前链接概览、成员列表、链接记录三个独立读取区域及各自 asOf。成员默认 ACTIVE；链接保留现有 ACTIVE/REVOKED/ALL 筛选与显式分页，不引入用户资料搜索或批量导出。

| 动作 | 入口与确认目标 | 独立结果 |
| --- | --- | --- |
| 创建或轮换邀请链接 | 概览中的明确操作；绑定打开确认时的 applicationId 与已读 activeJoinLinkId；无有效链接与轮换现有链接分别表达 | 新 ACTIVE 链接及仅一次返回的 joinUrl；不新增/移除成员 |
| 撤销邀请链接 | 当前链接或某条已读链接记录；绑定 applicationId + joinLinkId | 目标链接终态，不隐式创建替代链接，不移除已有成员 |
| 移除测试成员 | 已读 ACTIVE 成员行；绑定 applicationId + membershipId，以及用于确认展示的该行身份 | 只结束该 membership episode；不撤销链接，不变更 Auth 账号或版本发布 |

短确认可以使用浮窗；一份确认只执行一个上述命令，不组合“移除并撤销”或“撤销并重建”。大量规则/成员编排仍在整页，不扩成多层大型浮窗。打开、关闭、切换目标不发送命令。提交前再次核对当前页面目标仍与捕获值一致，陈旧概览不得悄悄换成“当前任意链接”。

创建使用“预期没有有效链接”；轮换绑定已读的精确 activeJoinLinkId。请求不由用户手填并发标识，也不把旧列表第一页当作当前 active 链接。移除按 membershipId 定位，绝不按 testerAuthId 批量移除或误操作重新加入的新 episode。

移除前如已知仍有有效链接，说明“对方仍可通过有效加入链接再次加入”。移除不是黑名单；成员重新加入和链接是否有效仍由后端判定。撤销只阻止该链接的后续加入，当前成员可以继续具有测试资格。提示不要求用户另行同意一个隐藏的第二命令。

## 一次性邀请链接

只有完整、目标匹配的创建/轮换成功回执可以展示 joinUrl。客户端依据 URL v1 契约核对 URL、精确 joinLinkId 与凭证格式，不执行 DNS/HTTP 请求，也不要求部署前缀对应一个可打开的页面；默认 mock 前缀是合法后端输出。

joinUrl 仅保存在当前应用、当前 Session、当前展示组件的内存中：

- 作为可选择的只读文本展示，由用户明确点击复制；复制失败时保留明确提示，不假称已复制。
- 不自动复制、打开、跳转、加载预览、请求图片、发送邮件或生成第三方二维码；本增量不实现加入/扫码落地页。
- 不把 URL 写入浏览器地址、history、localStorage、sessionStorage、IndexedDB、Query/Mutation 缓存、日志、trace 或错误对象；不将复制动作绑定到导航链接。
- 明确提示只披露一次；关闭披露区、切换应用/会话、离页或访问被拒绝时立即清除。已复制到系统剪贴板的内容由用户持有，界面不承诺能够撤回剪贴板。
- 概览和历史页只显示安全元数据，不从 joinLinkId、hash、部署前缀或缓存拼回旧 joinUrl。遗失后必须以新一次明确轮换取得新凭证，不能自动轮换或假装“重新显示”。

创建回执中的 joinUrl 与管理读模型分开保管；后续读回失败不会把 joinUrl 塞进 Query。若 Session/权限已经变化，迟到成功不能重新披露旧身份下的凭证。

## 命令状态、失败与读回

确认绑定当前 Session、应用、目标与页面 lifetime；用同步提交锁防重复点击。状态区分可确认、发送中、明确成功、明确拒绝、结果未知、读回中与等待重新确认。写请求不自动重放；主动离页也不采用卸载时补发。

成功回执应验证目标、终态及必要结果形状，再重新读取三个管理区域。不得把命令 resource 强塞进 UC037 的 Managed read model，或把三个响应的 asOf 说成同一事务；也不得用 `removed/revoked=false` 假称本次首次执行了状态迁移。

冲突、5xx、网络中断、畸形成功或未知结果暂停写入，保留安全的操作目标说明。恢复仅执行现有三类只读 RPC：概览是 GET，成员/链接列表是 POST `:search`，它们虽有 POST 方法仍是查询，不能发明三条 GET 列表接口。失败后提供明确“重新读取当前测试配置”，不自动重发原创建、轮换、撤销或移除。

读回后由用户核对当前事实并明确开启新基线。创建/轮换结果未知且未取得凭证时，即使概览出现 ACTIVE 链接也不显示伪造 URL，不宣称原命令一定成功；需要新凭证时必须明确确认当前链接的新轮换。列表某页缺少目标不等于该目标已经移除/撤销，不自动遍历所有页证明结果，也不把第一页拼成完整历史。前端说明“当前已加载记录”与可确认的事实，提供显式分页/筛选核对，不能凭缺席发出补偿写入。

发送中/结果待核对时离页提示；Session 失效或应用访问被拒绝时立即退场并清除私有成员、表单、确认及一次性 URL，不让离页提示阻止安全退场。5xx 不自动清登录 Cookie，也不把暂时读取失败当成永久失权。

## 私有消费与缓存边界

沿用 generation-bound Session、`createBoundPrivateFetch` 和应用级 PrivateReadAttempt。请求 signal 从页面生命周期传递；旧 Session、旧应用或旧 lifetime 的响应不能更新当前 UI、发起新查询/命令、导航或显示一次性材料。

写前/读回前捕获相关 Query 实例；回填、退场和清理只作用于仍是同一实例的对象。不能在异步完成后用宽泛 key 重新枚举并覆盖/清理同 key 的新实例。成员与链接列表仍保留各自分页和过滤上下文；明确从头重读可以产生新 generation，但不是重新获得写授权的证明。

## 接入、实施切片与验收

Gateway `9d6a27f` 已为三条既有命令开放 DEVELOPER surface，Admin 不开放；固定 API 为 `6fea3db899d3d096d4d3dfc59b2c85432a4b9eb6`。这不表示页面、镜像部署和完整业务实链已交付。

建议下一实施切片：

1. 新增只含三命令的 `createTesterCommandClient`，复用同源 transport 和已生成 schema；不修改现有读取客户端的职责。创建/轮换使用 `CreateOrRotateTesterJoinLinkCommandSchema` 的 optional presence，不手写空字符串冒充无 active link。两条 DELETE 无业务 body，不套用版本 If-Match/revision。
2. `TesterCommandPanel` 持有捕获的 intent、确认状态、锁与读回恢复；`OneTimeTesterJoinLink` 单独持有/清除 joinUrl 和显式复制状态。`OverviewRegion` 增加创建/轮换入口，成员行增加移除入口，链接行增加撤销入口；三个区域由现有父页协调读回，不复制整个页面或另建测试版本导航。
3. 暴露精确 intent：`{ kind: "create-or-rotate", applicationId, expectedActiveJoinLinkId?: string }`、`{ kind: "revoke", applicationId, joinLinkId }`、`{ kind: "remove", applicationId, membershipId }`。展示身份不能替代目标 ID，未知结果不能复用旧 intent 无声重发。
4. 验证客户端 exact body/path、目标匹配回执和一次性 URL 格式；组件覆盖三个独立动作、轮换冲突、旧 episode、新目标/Session/Query 实例隔离、Clipboard 失败、关闭/离页清除，以及未知仅读回不重放；真实隔离链通过后再登记已交付。

现有官方生成输入已包含 `tester_join_link.proto`、`tester_membership.proto` 与 `tester_management.proto`，无需为本切片升级 API pin 或手工生成第二套业务类型。具体 schema/type 与组件接口建议由本工作包交接报告列出；新增业务授权和入场规则仍引用后端权威。
