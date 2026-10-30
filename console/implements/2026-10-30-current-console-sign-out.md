# 当前 Console 会话的显式退出设计

状态：`DESIGN_ACCEPTED / IMPLEMENTATION_PENDING`，2026-10-30。依据持续 goal 自主设计并接受 [UC017](../use-cases/UC-CONSOLE-017-sign-out-current-console.md)，本记录没有实现或执行验证，不借已有 Session 清理证据宣称 Auth 撤销已接入。

## 当前证据

- UC001 明确排除了显式退出，并要求另立用例引用 Auth UC008。当前两个 Shell 没有显式退出入口；两端 `session.ts` 的 `clearSession` 仅发送带 binding/generation 的 `DELETE /api/session`。
- `packages/bff-auth/src/authority.ts` 的 `clearResponse` 调用 `store.clearSession` 并删除该 generation 的已观察 carrier，没有向 Auth 外呼。`console-session-store` 的清理只按匹配 generation `$unset session`，刻意不清新 flow，也不修改另一代。
- 正式 `AuthenticationService.RevokeCurrentSession` 已由固定 API `6fea3db` 生成，HTTP 为 `DELETE /auth-center/v1/sessions/current`、无正文，token 只在专用 header。Gateway `9d6a27f` 的 `auth.revoke-current-session` 使用 DIRECT/preserve SESSION，不先在线验证 token 有效性，已有普通内部路径可供 BFF 精确调用。
- `RevokeOwnSessions` 是其它有效 Session 的明确集合回收，禁止包含当前 Session，不能用于实现本次退出。此前仅按名称查找而遗漏 `revoke-current-session` 的判断不作为设计依据。
- Edge 对 `/api/auth/*` 是精确 allowlist，未知 `/api` 拒绝。因此新增 BFF handler 还必须在共享 Edge renderer 明确增加 `POST /api/auth/logout`，不是只依赖已有前缀路由。

以上是源码与权威文档核对，不等于已验证发布镜像上的新退出流程。没有读取或保存运行中的 Session token、Cookie、钥匙或个人正文。

## 自主决定及取舍

### 默认精确撤销，同时分别陈述两个结果

选用专用 BFF `POST /api/auth/logout`：捕获当前 A token，单次调用 Auth UC008，再独立按 A generation 清理 Console Authority。相比只复用 clear，此流程真正尝试结束上游当前 token；相比清整个浏览器，它保留设备登录能力及另一端独立性。既有失效 clear 不增加 Auth 副作用，避免迟到业务拒绝升级为用户未选择的撤销。

Auth 回执确认和 Console 清理确认是两个事实。200 正文必须同时携带精确目标、`console: CLEARED` 与 `auth: REVOCATION_CONFIRMED | UNCONFIRMED`；只清理成功时使用明确部分成功文案。Auth 已撤销但本地写未知，或两者均未知，不能以成功状态结束等待，必须明确核对。

### 不额外持久化退出秘密队列

上游 token 仅在已存在的 Authority 密文和当前 handler 闭包内出现，不为退出再建可重放秘密副本。清理后若 Auth 回执未知，无法在后续请求重新取得旧 token：产品接受并明确告知“本地已退出、服务端撤销尚未确认”，不将这种有限能力包装成可无限恢复的全远端退出。

若浏览器收到未知而原 Authority 仍存在，用户可以明确重试同一目标；若已清理，只读核对即可，不重建旧代、不拿新 token 代替旧 token。响应丢失后即使状态恰为 SIGNED_OUT，也没有证据补造 Auth 成功回执。此取舍避免为了退出引入第二套 token 生命周期、后台重试和秘密清理义务。

### 精确目标优先于全局清退

命令绑定当前 surface、binding、generation，而不接受客户端指定的 Auth Session ID。BFF 捕获 token 后即使 B 登录，A 的撤销与 CAS 清理仍只针对 A；旧回执不把 B 导航回入口或清新缓存。别的明确登录 flow 不在本命令范围，不能借退出旧代取消较新的登录意图。

确认后立即卸载 A 私有子树、清对应内存和一次性秘密；服务端清理未知时仍不能宣称已退出。保留设备私钥不代表自动登录授权，退出后等待用户新的明确选择。过期/失效会话仍由原恢复机制处理，不让缺少有效本地 target 的请求随意撤销其它目标。

## 有限实施清单

1. 在共享 BFF 模块实现严格的退出请求/结果、固定 Auth 撤销适配器与按代清理；双 BFF 只安装同一精确流程，禁止透传任意 URL/header/body。
2. 共享 Edge renderer 添加且仅添加 `POST /api/auth/logout`；失败关闭、Cookie 剥离和原普通路由矩阵不变。
3. 双端全局账号入口、短确认与退出结果/核对组件；复用现有 Session scope 清理，原代安全退场优先，禁止自动登录和全存储删除。
4. client/组件覆盖结果区分、未知核对、禁止自动重试和新代保护；真实 Mongo/双 handler 覆盖 clear 写未知与新登录交错；真实两端页面完成 Auth 撤销、另一端保持及原钥匙明确重新登录。
5. 记录实际候选、镜像、结果和清理；集中必要检查，不在每个小改动后运行完整真实套件。

不新增 Auth/Gateway 业务接口，不要求新增 Console direct surface，也不修改 Auth UC008 的幂等规则。部署仍须具有既有内部 `auth.revoke-current-session` 路径；若目标镜像缺路由或正式 ProtoJSON/错误行为不符，则据实登记外部阻塞，不能回退为仅 clear 却报告完全退出。Cookie header 431/33+ carrier 的传输边界仍独立，不因新按钮而宣称已修复。

## 当前完成边界

本轮仅创建 UC017 与本设计记录，未修改 Console 产品代码、registry 或入口索引，未构建、未运行测试、未发送外部协调消息。功能状态保持 `IMPLEMENTATION_PENDING`。
