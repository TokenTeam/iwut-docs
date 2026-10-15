# Console 登录流程 fencing 待决问题

状态：`OPEN`。记录日期：2026-10-16。

本文是 [UC-CONSOLE-001](../use-cases/UC-CONSOLE-001-establish-console-session.md) 的实现缺口与候选方案记录，不接受新架构，不修改 UC 的权威要求，也不把下列候选方案解释为当前部署约束。

## 原始要求与当前覆盖

[BR-CSE-005](../use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-005) 要求当前流程唯一，并规定开始新操作、切换方式、取消或离开登录上下文后，旧响应不能覆盖新状态或设置 Cookie。Complete 还必须绑定到 BFF 自身签发或记录的事务上下文。[BR-CSE-006](../use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-006) 定义 Begin 幂等恢复、显式重发与 Complete 结果未知恢复；UC 的“页面状态模型”还要求 flowId 与 operationId 共同约束结果消费。

当前加密 flow Cookie 已证明“Complete 的 operationId 属于曾由本 BFF 签发的 Begin”，但没有证明“这个 Begin 在 Complete 返回时仍是当前意图”。加密防篡改不提供撤销、消费或并发顺序。

调查基线是 Console `cf40408` 后的实现：

- `packages/bff-login/src/index.ts` 的两个 Begin handler 在上游调用返回后执行 `writeFlowCookie`；没有共享的当前 generation，也没有取消命令。
- 两个 Complete handler 在调用 Auth 前执行 `readFlowCookie` 并比较 kind/operationId；等待 Auth 返回后直接执行 `establishSession`。该函数写 Session Cookie 并删除 flow Cookie，期间不重新核对当前意图。
- `packages/bff-auth/src/index.ts` 的 `readSessionResult` 只校验加密封装、形状和到期时间。`consoleSessionForwardAuth` 将该结果恢复为上游 token；没有 generation 或撤销状态查询。
- `packages/console-auth-ui/src/index.tsx` 的设备与邮箱操作各有独立 pending；原实现不能协调两种方式并行，也没有在异步完成后统一核对当前 flowId。`packages/browser-auth/src/client.ts` 支持 AbortSignal，但调用方取消请求不会撤回已由 BFF/Auth 提交的结果。

上述事实说明 UC001 仍需增量实施；现有成功登录测试不能作为并发要求已经完成的证据。

同一个 flow Cookie 还限制结果未知恢复的组合：邮箱 Complete 未知后，新的设备 Begin 会把 flow kind/operationId 替换为 DEVICE；若设备探测未能建立 Session，此时直接重试仍有效的原邮箱 Complete 会被 BFF 的 EMAIL flow 校验拒绝。页面保留原操作不等于 BFF 仍允许消费它。后续架构必须明确区分当前用户意图和该意图下允许的恢复操作，验证“设备探测失败 → 原邮箱 Complete”的真实组合；不能仅分别 mock 两条恢复按钮就宣称 BR-CSE-006 闭环。

## 两类不同的竞争

第一类发生在 BFF 尚未决定写 Cookie 时：

1. Complete A 携带 flow A 的 Cookie 进入 BFF，通过初始校验，然后等待 Auth。
2. 新 Begin B 已返回，或页面已取消 A。
3. Auth 的 Complete A 返回成功；原 handler 仍写入 Session A，并删除可能已被 Begin B 更新的 flow Cookie。

另一个顺序是 Begin A 比 Begin B 更晚返回，A 的 flow Cookie 覆盖 B。浏览器忽略 A 的 JSON 不能阻止浏览器处理 A 的 `Set-Cookie`。

第二类发生在响应已经发出之后：

1. BFF 判断 A 当时有效，提交成功并发出含 `Set-Cookie` 的响应，但响应仍在网络中。
2. BFF 随后处理取消或 B，确认新的当前意图。
3. A 的响应最后到达浏览器；浏览器仍可能写入旧 Cookie。

服务器在发出 A 响应前做一次最终检查，只能处理第一类。它不能召回已经在途的响应，也不能要求浏览器按服务器提交顺序应用同名 Cookie。迟到的删除 Cookie 响应同样可能删除新 Cookie。

## AbortController 与页面序号的能力边界

统一 flowId、同步互斥、AbortController 和卸载时的回调隔离都应实现。它们能让旧结果不再触发 `onEstablished`、覆盖表单、清除新错误或推进新状态；还能减少用户发起的重复请求。

它们不能作为 BFF Cookie 的安全控制：取消 fetch 不代表请求未到达，不代表 Auth 未登记凭据或创建 Session，也不能保证响应头尚未被浏览器处理。页面离开时的取消通知也可能根本没有送达。

因此必须区分页面本地取消与 BFF 已确认的取消。若最终契约要求服务端撤销，生效顺序必须有可观察的服务器确认点；不能把本地点击或 AbortSignal 触发当作该确认点。页面恢复后还需读取当前 Session/flow 状态，不能仅凭旧页面回调判断身份。

## 候选 A：保留加密 Session，增加共享 fence

候选 A 保留 Cookie 内的加密上游 token，但新增服务端共享的 Console context、当前 flow generation 与有效 Session generation。具体存储产品和数据格式尚未决定。

必要条件包括：

- context 与 Developer/Admin surface 隔离；同一 context 的 Begin、显式重发、切换与取消有原子顺序。仅保存每个 operationId 的独立记录不足以判定哪个是当前意图。
- Complete 在调用 Auth 前原子取得当前操作的执行权，并在成功后以 compare-and-set 核对 generation。过时结果不能提交新的有效 Session；重复 Complete 的进行中、结果未知和已完成状态不能靠重放旧 token 伪造成功。
- Session 封装携带受认证的 context/generation。`/api/session`、BFF 自身的受保护调用与私有 ForwardAuth 全部检查同一共享 fence；只在 Complete 检查而继续无状态接受旧 Session，不能闭环。
- 取消、新意图及退出要定义是否失效已提交的 Session generation，以及确认后的行为；上游 Auth 的提交无法与该 fence 做一个本地原子事务。

此方案能保证失效的旧 Session Cookie 不再被 BFF/Gateway 链接受。它仍不能保证浏览器物理上不写入在途旧 Cookie。旧 Cookie 覆盖新 Cookie 后可能导致登录态被拒绝，需要重新设备登录；旧的删除响应也可能造成同样的可用性问题。

因此选择此方案必须先接受并记录对 BR 的精确定义：承诺“已失效 generation 不会恢复有效登录态”，还是继续要求“旧 Complete 响应绝不写 Cookie”。不能在代码中暗中用前者替换后者。

## 候选 B：稳定 context Cookie 与服务端 Session

候选 B 在登录前建立稳定、不可伪造的 HttpOnly context Cookie，服务端共享记录拥有当前 flow 与 Session。Begin、Complete、取消和切换均不重新设置或删除身份载体 Cookie；它们只原子改变该 context 的服务端状态。ForwardAuth 从当前记录恢复上游 token。

这样旧 Complete 响应没有 `Set-Cookie`，页面丢弃旧 JSON 后不再出现由该响应覆盖身份载体的竞争。它把 Cookie 生命周期与单次登录结果分离，但也将当前的无状态 Session 改为服务端 Session，新增共享存储的部署、容量和可用性要求。

必须先解决的边界包括：首次 context 初始化的多标签页并发、在途 bootstrap Cookie 响应、context 轮换与退出策略、当前 flow 的原子竞争规则、Session 到期、共享存储故障，以及如何让页面确认它正在操作当前 context。稳定 context 不能在每次 Begin 或取消时重新签发，否则同名 Cookie 的竞争仍会回来。即使采用本方案，BFF 也只能按收到并确认的命令排序，不能知道尚未送达的本地取消。

## 两种方案共同的跨副本与重启要求

进程内 Map、单个实例 mutex 或仅靠浏览器 Web Locks 都不能证明跨 BFF 副本成立。共享 fence 或服务端 Session 必须由全部副本读写，并以原子条件更新定义胜者；不能假定粘性路由始终成立。

重启后必须明确采用持久恢复，或统一失效并要求重新设备登录。不能让丢失的 fence 记录被解释成“允许接受仍未到期的旧加密 Session”。记录过期时间、TTL 清理和实际业务到期校验应独立：TTL 删除延迟不能延长有效期，过早删除也不能重新激活旧 generation。共享存储不可用时应失败关闭并表达依赖不可用，不能降级为跳过 fence。

Auth 已提交但 BFF fence 竞争失败或提交结果未知时，可能留下平台 Session。BFF 若已取得 token，可评估通过现有 `RevokeCurrentSession` 做受控清理；这不撤销已发生的凭据登记，也不能覆盖响应丢失、token 未取得或撤销失败的情况。恢复仍需保留原密钥并遵守 BR-CSE-006，不能以创建新密钥代替恢复。

## 本轮允许完成的增量与保留项

无需新增数据库依赖即可实施并验证：固定原邮箱、公钥、requestId 的 Begin 重试；冷却后使用新 requestId 与原密钥的显式重发；挑战到期控制；统一页面 flowId 与同步互斥；取消/切换/卸载后的回调隔离；结果未知时保留材料和按协议恢复。

这些增量不得被登记为 Cookie 竞争闭环，也不得因此把 UC001 整体标记完成。候选 A/B 均保持 `OPEN`，本记录不引入新数据库依赖。

架构选定后的验证至少应包括：真实浏览器延迟旧 Begin/Complete 响应头、取消与新登录交错、同 Cookie 的双标签页、两 BFF 副本交错处理、提交点重启、共享状态不可用，以及旧 generation Cookie 对 `/api/session` 和 ForwardAuth 的一致拒绝。测试应检查浏览器 Cookie 和实际受保护请求的身份结果；仅断言被 mock 的 `onEstablished` 没有调用，不能证明服务器与 Cookie 边界成立。
