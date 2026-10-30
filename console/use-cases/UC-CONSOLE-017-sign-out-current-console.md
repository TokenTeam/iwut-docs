# UC-CONSOLE-017：显式退出当前 Console 会话

状态：`ACCEPTED`，2026-10-30，依据用户持续 goal 的自主设计、接受和实施授权登记。设计接受不表示 BFF、页面或真实镜像验收已经完成；实施状态见[退出工作包](../implements/2026-10-30-current-console-sign-out.md)。

## 目标与边界

已登录用户在 Developer Console 或 Admin Console 明确结束此工作台的当前会话。默认执行两件分别确认的事：由 BFF 对捕获的 Auth token 调用精确撤销，再按原 binding/generation 清理此 Console Authority。普通用户即可退出，不要求 Developer、Reviewer 或平台管理员资格。

本用例扩展 [UC001 明确排除的显式退出](UC-CONSOLE-001-establish-console-session.md)，不改变登录、取消登录和失效清理的既有含义。Auth 撤销权威为 [UC-AUTH-008](../../auth-center/use-cases/UC-AUTH-008-revoke-own-session.md)，载体与精确方法例外引用[设备认证与 Session 契约](../../platform/contracts/auth-device-session-v1.md)。本地清理继续遵守 [Console Session v2](../query-contracts/console-session-v2.md) 的按代隔离；新增退出编排不将既有 `DELETE /api/session` 重新解释为 Auth 撤销。

“退出此工作台”保留 IndexedDB 中的不可导出设备私钥、公开材料与 credentialId，用户以后可以明确选择设备或邮箱登录。它不是“从此浏览器移除账号”、撤销设备凭据、清除全部站点存储、撤销其它 Session、账号注销或退出 Developer。两个 Console 各自退出自己的 Auth Session 与 Authority，不调用另一端、不共用退出状态、不使用跨域 Cookie 清除。已通过在线检查的在途业务及已签发短期 JWS 不承诺中止。

## 用户入口与确认

- 两端全局账号入口提供“退出此工作台”；只在当前 Session 已确认时可用，不通过页面所在域名推断身份或角色。
- 短确认说明将结束当前工作台会话、清除当前私有页面与未保存填写、保留本机设备登录能力，另一工作台和其它会话不受本操作直接影响。已发出的业务命令结果仍需另行核对，退出不能被解释为取消其提交。
- 用户确认后捕获当前 Session 的公开 binding/generation，立即停止当前页面新增业务请求、卸载该代私有子树并清理对应 Query、表单、确认和一次性秘密。只保留退出目标与进度等最小非秘密状态；不等待撤销回执才遮蔽数据。
- 不自动设备登录、重放登录流程、bootstrap 新 context 或重新发送任何业务命令。操作期间重复点击不再发送；依赖失败时提供明确核对或重试入口。

## 专用 BFF 编排

新增精确入口 `POST /api/auth/logout`，正文严格为 `{contextBinding, generation}`，二者沿用 canonical Opaque32。拒绝额外字段、query、客户端 token、authId、Session ID、credentialId、上游地址或任意 method/path。使用当前 surface 的精确 Origin、same-origin Fetch Metadata、JSON、正文大小限制及 `no-store`，不引入通用 Auth 代理。

Edge 只为该 method/path 增加到所属 BFF 的精确入口，保留其它 `/api` 失败关闭。Auth 外呼通过 BFF 配置的 Gateway 内部地址执行已有 `auth.revoke-current-session`：

```text
DELETE /auth-center/v1/sessions/current
x-iwut-session: BFF 捕获的原 Auth token
无 query、无 JSON 正文
```

这是已有 DIRECT / preserve SESSION 路径，不经过 Console Cookie ForwardAuth，也不先用“当前 Auth Session 仍有效”的业务检查挡住幂等撤销。浏览器不获得 token，不发送 `x-iwut-session`。BFF 不透传浏览器 Cookie、Authorization 或自造身份头；外呼 `credentials: omit`、禁止重定向、固定超时，不转发上游 Set-Cookie 或任意诊断。不是 `RevokeOwnSessions`：后者禁止包含当前 Session，不得以遍历列表代替此精确命令。

处理顺序与结果如下：

1. 用当前 Cookie 读取 Authority。只有其公开 binding/generation 与请求完全相等，才可在本次 handler 私有闭包捕获对应 token；不能以客户端目标重新定位任意 Auth Session。读取失败关闭；若已经换到另一有效代则返回 `409 / CONSOLE_SESSION_CHANGED`，不撤销或清理新代。
2. 对捕获 token 发送一次正式 Auth 撤销。只有收到并严格验证正式 `SessionRevoked` 成功形状，才标记 `REVOCATION_CONFIRMED`；网络、超时、5xx、非契约状态或畸形成功均为 `UNCONFIRMED`，不能把 401 或无内容的任意 2xx 猜为成功。
3. 不论 Auth 撤销是否确认，都尝试以原 selector 和 generation 清理此 Console 的 Authority，且只删除请求已观察到的原 generation carrier。不能删除固定 context、另一代 carrier、另一端 Cookie 或任何设备存储。确认原代已经不再能通过 Authority 才标记 `CLEARED`；明确 CAS no-op 后的匹配读取也可证明原代已不存在，不能仅凭写请求已发送证明清理。
4. 清理确认后返回 `200` 且严格正文为 `{contextBinding, generation, console: "CLEARED", auth: "REVOCATION_CONFIRMED" | "UNCONFIRMED"}`。HTTP 200 只表示本地退出已确认，客户端必须读取 `auth`，不能统一显示远端撤销成功。
5. Authority 读取/清理仍未知时返回 `503 / CONSOLE_LOGOUT_UNCERTAIN`，不提供成功 Cookie 或成功文案。原代不存在且当前确为 SIGNED_OUT、又无法取得原 token 时，可按上述 `CLEARED / UNCONFIRMED` 返回：没有持久退出回执，不能凭已经清空 Authority 推断先前 Auth 调用成功。

handler 捕获后若另一标签页登录 B，后续 Auth 调用仍只针对 A token，按代清理仍只针对 A。B 的新 Session 或独立明确发起的登录不属于 A 的退出范围；不为追求“退出全部”而取消未知的新 flow。A 的迟到 carrier 不能使已清理的 A generation 恢复有效，旧回执也不能清除或改写 B。

## 未知结果与重入

收到 `CLEARED / REVOCATION_CONFIRMED`，显示当前工作台会话已退出，并提供用户明确选择的返回登录入口。收到 `CLEARED / UNCONFIRMED`，显示“已退出此工作台，服务端会话撤销尚未确认”；不假称设备已移除或其它会话已结束。

网络失败、响应丢失或 `CONSOLE_LOGOUT_UNCERTAIN` 后，保持该代私有页面关闭。仅明确读取 `/api/session` 核对当前 Authority：

- SIGNED_OUT 只证明当前 Console 无可用会话，不证明 Auth 撤销成功；按本地退出确认、Auth 未确认展示。
- 仍为原 binding/generation 时，说明退出尚未确认，允许用户明确重试同一目标的专用退出。每次 handler 最多一次上游撤销，Auth 自身的 token 定向幂等仍由 UC008 保证；无自动重试或后台重放。
- 已是 B 时，只接受新的会话观察并说明登录状态已变化，本次结果不作用于 B；若用户还要退出 B，必须重新确认 B 的当前会话。
- 读取失败则继续显示结果待核对，不把 5xx、431 或离线当作 SIGNED_OUT，也不通过清全部 Cookie、站点存储或私钥绕过。

本用例不持久化 token 副本、退出秘密队列或可取回 token 的浏览器句柄。Authority 已清理后若 Auth 回执缺失，就如实保留远端撤销未确认的结论，不借新 Session 去撤销旧目标、不复活旧 Authority。刷新可能丢失内存进度，只能重新观察当前事实，不能还原不存在的远端回执。

既有会话失效恢复的 `DELETE /api/session` 保留原语义和调用场景，不暗中增加上游撤销；新退出通过专用入口实现，避免旧迟到业务错误意外发起高一级副作用。

## 生命周期与验收

退出 UI 和回执均绑定发出时的 surface、binding、generation 与组件 lifetime。用户离开、旧组件卸载或新身份出现后，旧回调不得恢复私有内容、覆盖新的 Session Query、导航新身份到登录页或删除其缓存。原代本地遮蔽与清理不得跨代扩大；重新进入只读取当前 Session，不自动登录。

验收至少包含：

1. 两端普通用户在实际页面明确退出；正式 Auth 当前 token 后续在线检查失败，当前 Console 无可用 Authority，另一独立 Session 与另一端仍有效。
2. IndexedDB 设备钥匙保持且仍不可导出；退出后不自动签名或登录，用户另行明确设备登录可创建新代。
3. 上游幂等成功、已过期/已撤销 token 与无匹配记录的合法 token 按 UC008 处理；浏览器无 token、URL/正文/日志/存储无秘密。
4. Auth 503、断流、畸形成功和回执丢失分别保留未确认结论；本地清理可独立确认，Mongo 写未知不得冒称退出完成。
5. A 外呼等待期间 B 登录、A 回执迟到、A carrier 迟到、重复 A 请求和旧组件卸载均不影响 B；没有未带目标条件的清理。
6. Origin/Fetch Metadata/媒体类型/超大正文/额外字段/错误方法/path 拒绝；Edge 只新增精确 BFF route，不扩普通 Console surface 或 Gateway 凭据矩阵。

组件、BFF 合成外呼和真实 Mongo 交错证据分层记录；至少两端正式撤销与设备保留链通过真实 Auth/Gateway 才能称实际交付。当前设计无需新增 Auth RPC，但仍需实现专用 BFF、Edge、浏览器入口及上述验证；现有 clear 的测试不能直接替代。
