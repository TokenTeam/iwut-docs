# Console Session v2：BFF / Browser 接线契约

状态：`ACCEPTED`，2026-10-16 按用户持续授权自行决定。实现 ADR-CONSOLE-005，不改变 Auth 协议或 Gateway 凭据矩阵；未完成联合验收前不关闭 UC001。

## 公共值与载体

`Opaque32` 是 32 随机字节的 canonical Base64url（43 字符），不是用户身份。public binding、flow ID、attempt ID 和 Session generation 均不携带 secret；私钥、Auth token、carrier secret 不进入 JSON。浏览器只在内存保存流程票据，不持久化它们。

```text
ContextSnapshot { contextBinding: Opaque32, revision: safe nonnegative integer }
FlowTicket       { contextBinding: Opaque32, revision, flowId: Opaque32 }
SessionSummary   { state: ESTABLISHED, authId, credentialId,
                   expiresAtUnixMs, contextBinding: Opaque32, generation: Opaque32 }
```

两 surface 分别使用 `__Host-iwut-{developer|admin}-context` 与 `__Host-iwut-{developer|admin}-session-{generation}`；匿名 context 与 carrier 均为随机 opaque secret，Mongo 只保存带 surface/purpose 的 SHA256 摘要。所有 Cookie 保持 Secure/HttpOnly/Strict/Path=/。旧固定名称 Session/flow Cookie 永不参与 v2 认证。

每个请求最多 8192 字节 Cookie header、最多 32 个该 surface 的 carrier；重复 context 或重复当前 carrier 拒绝，不按 Cookie 顺序选择身份。旧载体可忽略但不认证；清理只删除请求中观察到的精确旧名，永不删除当前新代或 context。AEAD envelope 使用 `v1.`+canonical packed nonce/tag/ciphertext，以 surface、context hash、用途和 generation/flow+slot+attempt 作为 AAD；不能跨记录搬用。

## 同源命令

除 GET capabilities/session 外，以下入口都要求精确 Origin + same-origin Fetch Metadata、JSON、大小上限和 no-store。context/flow 命令无上游 Auth 副作用；所有 Begin/Complete 仍以 credentials omit 经 Gateway 内部入口匿名调用 Auth。

| Method/path | JSON body | 结果 |
| --- | --- | --- |
| POST `/api/auth/context` | `{}` | 有有效 context 则返回 snapshot；否则创建新匿名 context 并设置其 Cookie。先消耗 surface 共享 bootstrap 配额。 |
| POST `/api/auth/context/confirm` | `{contextBinding}` | Cookie 与 binding 一致时返回 snapshot；不设置 Cookie。 |
| POST `/api/auth/flows` | `{contextBinding, revision, flowId}` | flowId 由浏览器提前随机生成并由 BFF 原子登记；比较旧 revision 后返回新 FlowTicket。同一 flowId 的原创建重试可读回已经登记的那一代，不覆盖别的意图。 |
| POST `/api/auth/flows/cancel` | `{flow: FlowTicket}` | 原子取消 OPEN flow；若同 flow 刚 FINISHED 且仅 revision+1，原子取消并失效其刚提交的 Session。新 flow/新 Session 不受旧取消影响。 |
| POST `/api/auth/flows/recover` | `{flow: FlowTicket, flowId: Opaque32}` | 原 root 仍 OPEN 则返回原票据，设备探测作为 DEVICE 子操作；若该 root 已 FINISHED，则登记恢复 root（不返回旧 token/carrier）。新 flowId 提前保留以恢复该登记的未知结果。其它意图已取代时拒绝。 |
| POST `/api/auth/{device|email}-login/begin` | `{flow: FlowTicket, ...原 Begin 字段}` | 挑战字段保持原协议；不设置 Cookie。 |
| POST `/api/auth/{device|email}-login/complete` | `{flow: FlowTicket, operationId, proof, code?}` | 真实 Auth 成功且当前 claim 提交成功后签发新代 carrier，返回六字段 SessionSummary。 |
| GET `/api/session` | 无 | 只有 context+当前 carrier 双重校验后返回 SessionSummary，否则 SIGNED_OUT。依赖不可用返回503，不转换成已登录或确定无效。 |
| DELETE `/api/session` | `{contextBinding, generation}` | 只失效该 generation，并只删除请求已观察到的对应载体；不匹配返回204 no-op。没有版本条件的 clear 拒绝。 |

同一 Cookie 的跨标签页竞争由 Mongo 原子 revision 决定。`CONSOLE_CONTEXT_CHANGED`、`LOGIN_FLOW_INVALID` 返回409，客户端停止旧流程，不自动采纳其它标签页的操作。`LOGIN_RESULT_UNCERTAIN` / `LOGIN_REQUEST_IN_PROGRESS` 返回409及合法等待秒数，不伪造成功。Mongo/加密/意外外呼错误返回不含材料的503。BEGIN/COMPLETE 本轮一次性执行 claim 的截止为60秒，长于40秒 Gateway 外呼预算与存储余量；过期只进入未知恢复，不证明上游未提交。

## 幂等、参数绑定与恢复

创建本地密钥后，PreparedEmailLogin 持有共享的纯公共 intent 状态（context bootstrap、预先生成 flowId、已确认 ticket）；任何网络结果未知都保留同一 localId/requestId 和已确认公共状态。Bootstrap 没有 Auth 副作用；在它得到确认前不发送 Begin。原 flow 创建响应丢失时用原 flowId/revision 确认，不重新生成密钥。

Begin 规范输入生成稳定 request hash，绑定 slot。相同邮箱 requestId/public key/email 重试只能返回原挑战或按 Auth 原幂等请求恢复；不匹配拒绝。执行中的 Begin claim 不被另一副本覆盖。外呼明确返回错误后标记 BEGIN_UNKNOWN；重试显式获取新执行 claim。BFF 重启留下的 BEGINNING 只有截止后才允许恢复，同参数邮箱 Begin 仍使用原 requestId。device Begin 不假定 Auth 幂等，旧执行结果不能提交到新 attempt。

Complete 在外呼前原子 claim；明确4xx验证码/认证失败可回到 READY，已完成/5xx/网络中断进入 UNCERTAIN。仍在 IN_FLIGHT 的执行不被抢占，只有截止后先显式登记未知，再由用户选择原 Complete 重试或设备探测；从不自动重试。每次结果提交比较 root revision、slot、operationId 与 claim，任何一个不匹配都不签发有效载体。

DEVICE 探测保留 EMAIL 操作。设备失败后能重试有效原邮箱 Complete；新的设备探测仅替换已结束/未知且非活动的 DEVICE slot。两子操作成功只能提交一个 Session，并清除兄弟 operation 的一次性状态。若原 Complete 已持久提交但浏览器未获得 carrier，恢复登记新 root，重新证明设备后签发全新载体，不索回旧 token；原邮箱操作此时已经结束，页面清理旧验证码并仅允许同密钥重发。

显式重发使用原 localId、新 requestId 与新 flowId，比较旧 ticket 的 revision；在新 root 得到确认前不发送新 Auth Begin。取消/卸载会中止本地请求并尽力发送带原票据的 cancel；未得到 BFF 确认时不能声称服务端撤销。取消确认后，已在途的旧 carrier 即使到达也不再有效。

Mongo 提交响应丢失时仅用本次已知 generation/commit ID 读回当前状态；读回不确定不发成功 Cookie、不擅自撤销 token。后续独立请求不复发旧 carrier secret。任何新成功都生成新的 generation/secret，不复用匿名凭据。

## 私有业务响应与旧错误回收

Gateway 现有 Console ForwardAuth allowlist 没有 public generation 请求头。本轮不越权修改 Gateway，也不把 tracing ID 或业务 query 参数借作认证载体。Developer 私有 API transport 在发出请求时捕获页面的 Session generation/binding，并在消费成功或失败响应前额外读取 `/api/session`：不相同或无法确认时不把业务 body/error 交给该页面，报告会话变化/依赖故障并重新协调身份。响应仍由 Gateway 直达浏览器，不经过 BFF body proxy。

这个校验依赖当前 generation 永不复用、权威读取不接受旧载体；它防止旧页面使用另一标签页新身份的响应。代价是每次私有 RPC 增加一次轻量 BFF 查询；未来若改为 Edge 按请求 generation fencing，必须由 Gateway 自己的 UC/发布交付，不能提前在浏览器发送一个实际不被转发的 header 后宣称受保护。

Session clear 捕获发出业务请求时的 generation，不从错误回调发生时的新状态取代它。异步清理完成后仍重新比较本地当前 generation，不能清空另一个新登录的私有 cache 或覆盖其摘要。私有视图按 binding/generation 重挂载，旧请求/缓存/表单不跨代复用；401/SESSION_INVALID 与会话变化都立即遮蔽原私有数据，网络5xx不误称认证失败。

## 资源与验证

bootstrap 采用 Mongo 内共享、失败关闭的 surface 级硬配额（初始120次/分钟），不依赖进程 Map 或不可信 X-Forwarded-For；只对需要创建 context 的调用消耗。部署可叠加可信 client IP 的 Edge 限流，不能绕过共享硬上限。每 context 最多32次签发，期限与 root/operation 仍服从 ADR005。连接串和密钥启动时显式配置；两个 BFF 独立数据库，Mongo 初始化失败不启动 Web listener。

验证需包括：真实 Mongo 的两 BFF handler 交错、缓存 Begin 参数绑定、EMAIL/DEVICE 恢复组合、取消已提交但迟到的 Complete、Session clear 与新代竞争、AEAD AAD 绑定、Cookie 上限、bootstrap配额、重启与依赖中断；现有真实镜像 HTTPS 浏览器主链必须继续通过。完整延迟响应/双标签页故障矩阵另行登记，不以 handler 单测替代。
