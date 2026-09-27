# UC-APP-019：为 Auth 解析 OAuth 应用授权上下文

状态：`PROPOSED`

## 目标与范围

向授权 Auth 服务提供 client 配置、secret 验证和特定用户当前可用的应用授权快照，让 Auth 不依赖客户端上报的 scopes/批准状态。只读提供方，不签用户 token。

## 输入与输出

三个精确内部方法、权限和字段见 [App 提供方契约](../../platform/contracts/app-oauth-client-v1.md)。clientId 为必填；上下文输入 authId 仅来自受信 Auth 调用者，不公开给普通用户查询。

## 主流程

1. 验证服务 JWS、audience 和方法级 permission；未知服务/方法拒绝。
2. 配置读取返回元数据；secret 验证只比较当前 revision 的摘要，不返回可重建 secret 的数据。
3. 上下文解析在同一 Mongo snapshot 读取 client、Application、exact-major TEST Publication、批准 Version/Review 和当前 ACTIVE Tester。
4. 返回当前批准 scopes、资格版本、最小展示资料与短时快照期限；任何缺失/不一致失败关闭。

## 业务规则

<a id="br-oac-006"></a>
### BR-OAC-006：内部查询与最小披露

只允许显式配置的 Auth service principal，按 [App 提供方契约](../../platform/contracts/app-oauth-client-v1.md) 分离读取/验证/解析权限；不是所有内网调用都可信。输入不能替换批准 scopes 或 version，输出不含 secret/摘要、学生资料或用户邮箱。

GetClientConfiguration 可以返回 DISABLED 元数据供 Auth 解释，但不能据此通过授权；VerifyClientSecret 和 ResolveAuthorizationContext 对禁用配置不成功。

<a id="br-oac-007"></a>
### BR-OAC-007：TEST 资格与批准范围

首版复用 UC-APP-012 的 exact-major TEST 发布及 ACTIVE Tester 资格，不新增管理员自动运行特权。必须存在该 client 的 applicationId/rpcApiMajor 对应 testVersionId，Version 属于该应用且 APPROVED，与批准 Review snapshot 一致；不可回退 draft、其他 major 或任意历史已批准版本。

本查询返回该批准版本 requiredScopes/optionalScopes，不重新定义 Catalog；Auth 再查当前权威目录。宿主 capabilities 的完整匹配仍由 UC-APP-012 执行，这里只给 OAuth 授权提供运行资格事实。

<a id="br-oac-008"></a>
### BR-OAC-008：一致快照与资格版本

所有资格事实和 scope 集合来自单个 Mongo snapshot，不拼接不同事务的记录。返回 configRevision、publicationRevision、versionId、testerMembershipId 和 adminAuthId，绑定算法与期限见 [App 提供方契约](../../platform/contracts/app-oauth-client-v1.md)。移除后重新加入的 Tester 必须有新的 membership episode，不能使旧 token 恢复。

发布/管理员/配置变化不通过缓存旧查询继续成功。查询不写 Auth 数据、不回调 Auth 形成循环；当前 Developer 状态由 Auth 自己确认。Auth 必须识别快照仅代表读取时点，App 不承诺在响应后冻结发布。

<a id="br-oac-009"></a>
### BR-OAC-009：展示来源与失败关闭

consent 展示只能读取当前已公开 ApplicationProfile 的投影；未有公开资料时返回技术名称和明确的无公开资料标记，不能把未经审核的 DRAFT 展示为官方批准内容。不返回应用控制的 HTML，门户必须安全渲染文本。

未知 client、无 TEST 发布、非 Tester、批准事实不一致不产生授权上下文；依赖故障不能返回空 scopes 冒充可登录的成功。错误分类见共享契约，Auth 不能用缓存或前端值兜底。

## 验收场景

- 服务凭据逐方法授权、错误 audience/USER token/公网访问拒绝。
- 当前 Tester 正常解析；移除后重加返回新资格版本，旧 token 绑定不再匹配。
- TEST 槽切换、major 不同、跨应用 Version、批准 snapshot 不一致拒绝或返回新的明确快照。
- secret 轮换与 Verify/Resolve 交错，不能拼接旧验证结论与新配置；响应无 secret。
- 无公开资料时只给技术 fallback；存储故障不能成功输出空范围。

## 依赖与实现边界

依赖 UC-APP-018、既有版本审核/TEST 发布/Tester 与公开资料读取。STABLE/灰度的公开运行资格尚无 UC，是未来扩展依赖，不阻碍本 TEST 纵切片设计。Auth Catalog 的生产来源仍需实现，不能把 App 测试 fixture 作为权威。
