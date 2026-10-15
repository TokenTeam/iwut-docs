# UC-CONSOLE-005：只读查询 Application Tester 管理

状态：`ACCEPTED`

接受日期：2026-10-16

## 用户目标与范围

当前管理员查看 Tester 容量、ACTIVE Membership episode、当前加入链接状态与已有链接历史。后端规则引用 [UC-APP-037](../../app-center/use-cases/UC-APP-037-query-application-tester-management.md) BR-TST-037–043；共用前端 BR-CMG-001–004。

首版以 ACTIVE 管理为主，不提供 REMOVED/ALL Membership 历史入口；这些分页仍保留后端能力。只读页面不提供创建/轮换/撤销邀请、移除 Tester、复制或恢复 secret。本人参与查询/退出的 UC038/040 仍属于暂缓的客户端入口，不由管理员页面替代。

## 页面与流程

1. 从 Application 管理概览进入 Tester 页；`GetApplicationTesterManagement` 使用 `GET /app-center/v1/applications/{application_id}/tester-management` 读取容量及当前链接概览。
2. `ListApplicationTesterMemberships` 使用 `POST /app-center/v1/applications/{application_id}/tester-memberships:search`，正文直接是 `MembershipQuery`，固定显式 `MEMBERSHIP_STATUS_ACTIVE` filter，不使用 `{ query: ... }` wrapper 或 URL query。显示允许披露的 episode 标识、testerAuthId、加入时间与来源链接标识，不把 opaque ID 当邮箱或姓名；不调用 Auth 查询用户资料。
3. `ListApplicationTesterJoinLinks` 使用 `POST /app-center/v1/applications/{application_id}/tester-join-links:search`，正文直接是 `JoinLinkQuery`，首屏和重置筛选必须显式发送 `JOIN_LINK_STATUS_ACTIVE`，因为后端 unspecified 默认是 ALL；可切换 REVOKED/ALL 查看链接状态/时间及契约允许字段。不存在当前 ACTIVE link 使用明确空态；无可恢复 URL/secret 时不出现复制邀请入口。
4. overview、Membership 页和链接页分别有自己的 asOf、loading/error/empty 和刷新；读取来自不同请求时不声称它们是同一快照。提供刷新整个管理页，但不把组合请求当原子读取。
5. ACTIVE/REMOVED episode、链接撤销/替换与当前容量是不同事实。链接撤销不表示已有 Tester 自动退出，count 不由浏览器累计列表行计算。

## 前端业务规则

<a id="br-cmg-009"></a>
### BR-CMG-009：Tester 管理事实不扩张到用户资料或凭证

只展示 UC037 允许投影，不补查用户身份、历史操作人、joinUrl、secret 或 hash，不把 joinLinkId 拼成可用加入 URL。testerAuthId、joinLinkId、joinedViaJoinLinkId、replacedByJoinLinkId 均为不可点击的 opaque 文本，不生成链接、复制/导出便捷入口，也不进入日志或遥测。只读界面不提供会产生一次性 secret 的操作，且不以管理员身份推导本人 Tester 资格。

<a id="br-cmg-010"></a>
### BR-CMG-010：概览与两类列表独立恢复

每个查询独立维护 token、filter 和 asOf。Membership token 与 JoinLink token 永不混用；切换 JoinLink filter 清空该列表 items/token，失败时不能把旧 filter 数据标成新 filter。网络/5xx 且身份、Application、filter 未变化时可保留当前会话内该区域先前成功数据，并显著标为上次读取及其 asOf，不能把故障区域当空或实时数据。任一 RPC 返回统一不可访问 404、身份错误或 `SESSION_INVALID` 时，立即取消迟到请求并清空 overview 与两类列表的全部私有数据。400 坏 token 只重置对应列表并提供从首批刷新；整页刷新分别从三个区域首批读取，不宣称原子 snapshot。Membership 默认 ACTIVE 的选择不改变后端历史规则；不按前端列表长度重算容量。

## 依赖与验收

需要三个 UC037 RPC 的固定 API 客户端、Gateway DEVELOPER surface、真实 Auth/App；不增加后端详情 RPC 或用户资料聚合 BFF。

1. 无成员、无当前链接、ACTIVE 链接、撤销/替换历史均可读，首版没有 REMOVED Membership 入口和任何写按钮。
2. 同用户旧 REMOVED/新 ACTIVE 只按后端 ACTIVE 页呈现，链接撤销仍可有 ACTIVE 成员；不错误显示“已全部退出”。
3. 转让后旧管理员统一隐藏；资格下降管理员仍可读；其他用户和本人 Tester 不获管理视图。
4. 分页种类错用、过滤变化、局部失败/全部刷新与并发更新有验证；容量和成员列表不假装同一个快照。
5. 完整真实链路、私有 no-store、日志/存储无 token/私有正文及键盘可访问性通过；客户端宿主 runtime 不被假造。

## 首个实现决定

本 UC 自 2026-10-16 起接受，并按以下边界启动首个实现工作包：

- 继续使用固定统一 API 输入 `a5d504c058c62cd91be451074d21608d69789918`，生成 `app_center/v1/tester_management` 类型并实现三个严格同源 client；GET 禁止 query/body，两个 POST 正文直接是各自 Query ProtoJSON 且禁止 URL query。
- Developer Console 使用 `/applications/{applicationId}/testers`。overview、ACTIVE Membership 和 JoinLink 列表是三个独立 Query 区域；Membership 首版不提供 REMOVED/ALL 入口，JoinLink 筛选使用 URL search `links=ACTIVE|REVOKED|ALL` 并始终显式发送完整 ProtoJSON enum。
- 两类列表分别维护仅内存显式页状态和 token 栈，query key 绑定 authId、applicationId、查询种类、filter 和 token；切换身份、Application 或 filter 先以首批状态发请求，不能发出旧上下文 token。
- 只呈现 capacity、activeJoinLink、Membership 与 JoinLink 白名单元数据；所有身份和关系 ID 都是不可点击的 opaque 文本。创建/轮换/撤销链接、移除 Tester、复制/恢复/导出 secret 或 URL、Auth 用户补查和本人 Tester 入口均不在本包范围。
- 组件/浏览器 fixture、Gateway `latest` 三路由测试与真实 Auth/App 协议链分开登记；最终仍需真实浏览器联合验收。
