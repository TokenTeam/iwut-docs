# UC-CONSOLE-012：管理应用 OAuth 客户端

状态：`ACCEPTED`，2026-10-30。依据用户持续 goal 对前端功能设计、自行接受与实施的授权接受本有界用例。

## 用户目标与权威边界

当前应用管理员在“接入配置”独立管理 TEST、GREY、STABLE 三个渠道的 Public PKCE 与 Confidential 客户端，登记身份、查看元数据、启停和轮换服务端 secret。版本回调与权限声明继续在版本工作页编辑；本页不创建 consent、token 或运行资格，不把客户端身份同某个版本或 RPC major 绑定。

业务规则引用 App [UC018](../../app-center/use-cases/UC-APP-018-manage-oauth-client.md)、[UC020](../../app-center/use-cases/UC-APP-020-manage-stable-publication-slot.md)、[UC021](../../app-center/use-cases/UC-APP-021-manage-grey-rollout.md)及 [OAuth client 契约](../../platform/contracts/app-oauth-client-v1.md)。本用例只拥有浏览器流程、数据消费与秘密披露，不重定义服务端资格、唯一性、epoch、secret 或发布门禁。

## 页面结构与主流程

1. 保留应用级 `/applications/:applicationId/integration` 页面，以明确渠道选择展示两种客户端。切换渠道不会修改后端，也不从应用摘要猜测完整配置。
2. 进入渠道后使用专用 `GetApplicationOAuthRegistration` 读取权威 registration。只有正式 `404 + ERROR_REASON_OAUTH_REGISTRATION_NOT_FOUND` 表示当前渠道尚未登记；该返回在后端 App 管理员栅栏之后产生，可作为初次登记的明确空态。其他 404/403、畸形成功或 Session 拒绝不能吞为不存在。
3. 已有 Confidential identity 后，单独读取 `GetOAuthClientCredentialMetadata`。普通读取不返回、缓存或恢复 secret。
4. 缺少的 type 提供登记操作；已有 type 提供启用/停用。Confidential 另提供明确的 secret 轮换。每个命令在短确认区域内说明渠道、类型、目标身份和影响，再由用户单次确认发送。
5. 首次登记省略 expected registration revision；补登记、状态变更使用本次专用读取的 registration revision，轮换使用独立 credential revision。前端保留精确 bigint，不让用户填写，不在正常交互中显示技术修订。
6. 确认绑定打开操作时的目标及基线；读取或版本变化使原确认失效。命令成功后以专用 GET 核对当前元数据，不用 ACK 冒充之后的读模型；确认后的修订下界跨重读保留。

## 一次秘密披露

- PUBLIC 不生成 secret。CONFIDENTIAL 登记或轮换仅在完整、目标一致的成功回执并通过当前 Session/页面代际检查后披露一次。
- secret 只保留在独立命令组件的当前内存状态，不进入 Query/Mutation cache、localStorage、IndexedDB、路由、日志、错误文本或可持久化表单。只有用户明确点击复制才写剪贴板，不自动复制、打开或执行任何 URL。
- 披露区同时说明它用于可信服务端，不能嵌入浏览器网页、安装包或版本运行配置。提供立即隐藏入口；关闭操作、离页、换应用/渠道/Session、访问拒绝时移除披露。隐藏后不从元数据恢复。
- 写入结果未知或成功回执丢失时不推测、恢复或再次显示旧 secret；只允许读取 registration/credential 元数据。用户核对后若需要新秘密，必须重新明确发起一次轮换，不能重放原命令。

## 并发、失败与私有数据

- 所有请求复用当前 Console Session 的绑定 fetch 和私有页面 attempt；相同 route 不绕过 Gateway，最终授权由 App/Auth 执行。
- 写入串行且禁止重复点击；冲突、明确拒绝、5xx/断流/畸形 ACK 均不自动重试。未知和冲突暂停进一步写入，提供明确只读核对；核对不证明原未知请求一定成功。
- 正常读取的网络/5xx 可以保留本渠道上次元数据并标明读取失败，禁止用失败数据发新命令。协议错误/明确拒绝遮蔽相应内容；失权清理当前 App 私有范围，Session 错误走既有恢复。
- 更新缓存只允许操作发出时捕获、仍为同一个实例的私有 Query；迟到 ACK/GET 不能覆盖新会话、另一应用、另一渠道或同 key 的新读取 attempt。
- 在途或未知结果离页提示不阻止安全退场。secret 不能靠离页保存、后台重试或 Mutation 持久化保留。

## 依赖与验收

API 固定 `6fea3db899d3d096d4d3dfc59b2c85432a4b9eb6` 的现有 OAuth client 生成类型；Gateway `9d6a27f` 已为五个管理 RPC 开放 DEVELOPER。此依赖检查不等于前端真实写链已验收。

验收包括三渠道隔离、两类型登记、精确空态与其他 404 不降级、专用读取基线、独立 registration/credential OCC、状态 no-op、一次秘密与显式复制/隐藏、未知写只读核对、旧 Query 实例保护、迟到/换代/失权清理。组件和客户端合成测试独立登记；真实登记、状态变化和轮换仍需正式镜像联调证据。
