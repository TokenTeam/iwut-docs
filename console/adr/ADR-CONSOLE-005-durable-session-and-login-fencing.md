# ADR-CONSOLE-005：持久 Session 与登录流程 fencing

状态：`ACCEPTED`（2026-10-16；用户持续授权下自行决定）。实现按工作包分阶段，接受不表示现有运行链路已经切换。

## 背景

[登录 flow fencing 缺口](../query-contracts/login-flow-fencing.md) 证明，仅加密 Cookie、页面 AbortController 或响应发出前的最终检查，不能解决跨请求、跨副本及已发出响应的顺序问题。单个 flow Cookie 也不能同时保留邮箱恢复与设备探测操作。另一个入口是旧业务响应触发的无版本 Session clear：它可能注销另一个标签页刚建立的新 Session。

## 决定与不变边界

保留 ADR-CONSOLE-004 的共享 Traefik、双独立 BFF、私有 ForwardAuth 与 Gateway 不解析 Cookie 的边界。BFF 改用自己拥有的 Mongo 数据库保存当前 Console context、登录意图与认证 Session；不读写 Auth/App 数据库，不把它们的 Mongo schema 当作产品 API。Developer/Admin 使用隔离 collection/命名空间、密钥和 Cookie 名，部署账号只有自身库权限。

全部副本连接同一 replica set。安全状态不缓存在进程内，不采用 sticky session 或 Map 降级。每个 context 的当前状态保存在一个文档内，用 revision compare-and-set 做原子转换；持久写使用 majority+journal，权威读取使用 primary+linearizable 并设置有界超时。过期条件在 Mongo 服务端时钟的读写谓词检查，TTL index 只回收空间。Mongo 故障、记录缺失、未知 schema 和解密失败都不能退回旧无状态 Cookie。

这是为了在确认新意图或取消后，所有副本对同一文档观察一致的当前代；不能只用“多数读取大概足够新”支撑并发保证。[Mongo 对单文档 real-time order 的说明](https://www.mongodb.com/docs/manual/core/read-isolation-consistency-recency/#real-time-order) 是本存储选择的依据。代价是每次 Session/ForwardAuth 增加有界数据库读取，部署可用性与延迟受它影响；不缓存是当前正确性选择，今后优化需另证不破坏 fence。

## 两种 Cookie，不使用预登录身份提升

1. 匿名 context Cookie：固定 surface 名称，随机 256-bit opaque 值，HttpOnly/Secure/SameSite=Strict/Path=/、无 Domain。数据库仅保存其带命名空间的摘要；它用于定位流程，**单独永不认证、永不返回身份或上游 token**。
2. 认证 carrier：每次真实 Auth 成功后，BFF 生成独立随机 generation 和 256-bit secret；Cookie 名包含该 generation，值是 opaque secret。数据库只保存 secret 摘要，并把它与当前 context/generation/加密 Session 绑定。其期限不晚于 Auth Session 和 context 的较早到期时间。

读取只检查服务端当前 generation 指定的精确 Cookie 名和值。不能遍历 Cookie 后选择“第一个”“最新的”或任何仍能解密的旧 Session；context 与 carrier 不能跨 context/surface 混用。预登录 context 即使被攻击者预先知道，也不会获知后来新生成的认证 carrier。此处采用不同的登录前/后凭据，遵循 [OWASP 关于登录后更换 Session ID 及多 Cookie 关系校验的要求](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html#renew-the-session-id-after-any-privilege-level-change)，不是把已知匿名 Cookie 直接提升为认证 bearer。

旧 Complete 若已发出响应，其旧 carrier 可以物理到达浏览器，但名字不同，不会覆盖当前载体；共享状态也不再接受它。旧取消/clear 响应不删除统一身份 Cookie，只删除请求已观察到的、精确的旧 carrier 名；不得发送会清除未来新一代的同名 Cookie。退出及 SESSION_INVALID 清理必须携带预期 public generation，以 CAS 失效对应 Session；不匹配时不得注销当前新代。

安全承诺是：旧结果不能替换、恢复或清除当前有效身份。HTTP 已发出的响应头无法召回，不能继续把“任何迟到响应在物理上绝不会写入任何 Cookie”当作可实现的不变量。BR-CSE-005 同步澄清这个确认点，而不是降低身份隔离要求。

## Bootstrap 与命令确认点

创建 context 是独立、同源、无 Auth 副作用的 bootstrap；只接受 BFF 自己创建且仍有效的记录，不接管客户端指定的新 ID。浏览器在获得 Cookie 后再次确认 public context binding，再开始登录意图。所有后续命令绑定该 binding、预期 revision、BFF 已登记的 root flow ID；Cookie 被另一个 bootstrap 响应替换时必须报 context changed 并停止，不自动迁移 operation 或身份。

初始双标签页可能同时发出无 Cookie bootstrap。确认不能召回另一个在途 bootstrap；迟到的新匿名 context 可能令页面失败关闭并要求重新确认，这是已接受的可用性边界，不得错误展示旧/其它身份。页面 Web Locks 可减少这种情况，但不是服务端安全证明。

开始/替换意图、重发、切换、取消都比较预期 revision；先成功提交的命令拥有该代。BFF 在外呼 Auth 前原子登记执行 claim，返回结果时再比较 root/operation/claim。取消只在 BFF 的 CAS 确认后成为服务端事实；本地取消立即丢弃页面回调并尽力发命令，离线或通知未送达不能声称服务器已撤销。未获确认时下次进入必须读取权威 Session/flow。

## 结果未知与恢复子操作

邮箱意图保留当前 email operation；设备探测是该意图下的有界恢复子操作，不覆盖原邮箱 operation。两条路径任一成功只能提交一代 Session，并终止兄弟执行 claim。探测失败后，仍有效的原邮箱 Complete 可以显式重试；不自动发送验证码、生成新设备或恢复旧 Auth token。

不得把过期执行 lease 解释为“上游未提交”。设备/邮箱 Complete 外呼后失联、BFF 重启或写入超时都可能已经提交；保留 root 与稳定 claim/commit ID，进入结果未知恢复。邮箱 Begin 可按原 requestId 恢复幂等结果。Mongo 写入超时后读回确认当前代；读回仍未知时不发成功 Cookie，不立即撤销上游 token（可能撤销已经持久提交的 Session），也不自动重放 Complete。重启不能重新激活旧 claim。

原始 Auth token 仅存于按 surface/context/generation 认证加密的 envelope，不存明文；数据库没有验证码、proof 或设备私钥。Browser Session 摘要可增加 public generation/context binding，但仍不含 Auth Session ID、token、角色和邮箱。旧 API 的 SESSION_INVALID 必须针对发出请求时捕获的 generation 处理，不能读取回调发生时的新代后将其清掉。

## 资源与部署约束

context/flow/session 有绝对期限，不由 TTL 删除时间延长；读取旧载体不续期。每 context 同时只有一个 root、一个邮箱操作与一个设备恢复操作，不保存无限历史。Cookie 总头长、carrier 数量、context 创建与每 context 签发次数必须有硬上限和同源错误表达；清理只能删除观察到的旧载体，不使用 wildcard。初始 context 期限上限 24 小时，root 上限 10 分钟，最多 32 次认证签发；到达上限需显式失效并 bootstrap 新 context，不能静默绕过 fence。实际 Auth expiresAt 可以更早。

生产接线前必须给 bootstrap 增加部署侧有界限流；数据库凭据、TLS、超时和 key rotation 都是启动必需配置，不提供无状态默认回退。独立数据库可复用现有 Mongo 集群基础设施，但不复用后端业务库或权限。切换期间旧无状态 Cookie 统一视为无效，设备密钥保留并允许用户重新登录；不双读旧格式，以免绕过共享 fence。

## 分阶段实施与门禁

第一阶段交付单文档 Mongo 状态核心及真实 replica-set 并发/重启/到期/失败关闭验证，不改变产品请求路径。第二阶段一起接入 BFF、Browser flow DTO、条件 Session clear 与 Edge exact routes；中间代码不能启用半套新协议。第三阶段用真实 HTTPS 浏览器延迟响应头，验证双标签页、两 BFF 副本、新/旧 Complete、取消/清理、bootstrap 交错、恢复子操作、数据库故障与重启；只有到此才关闭 fencing 缺口。

Mongo 存储测试不证明 Cookie 行为，组件测试不证明服务端提交，成功登录不证明故障恢复。UC001 和跨副本缺口在最终联合门禁通过前保持 IN_PROGRESS/OPEN。
