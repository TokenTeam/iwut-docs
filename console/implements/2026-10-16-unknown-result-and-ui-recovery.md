# UC001 未知结果与真实 UI 恢复验收

状态：`ACCEPTED / IN_PROGRESS`，按用户持续授权自行接受。承接[真实 Session fencing 验收](2026-10-16-real-session-fencing.md)的未完成项，不放宽 ADR005/UC001 完成条件。

## 范围与决定

1. 使用真实 React 邮箱入口和键盘恢复按钮，验证真实 SMTP 已投递但 Begin 响应丢失时，显式重试保留原 requestId/邮箱/公钥、仅一把设备钥匙且不重复投递；另验证旧 Begin 迟到不能推进已取消的页面。
2. 真实 EMAIL Complete 未到 Auth 而结果未知，随后 DEVICE 探测确实失败，再以原 EMAIL operation/code/密钥成功完成；不把“Auth其实已经提交，DEVICE成功”代替该分支。
3. 为两个 production BFF 的 Mongo 连接增加仅本轮测试拥有的透明 TCP 代理。在 BSON OP_MSG 中只识别本 surface context collection 的 Session 提交命令，原样转发真实写入，按真实 responseTo 丢掉其执行后的回执；不得伪造数据库成功或修改数据。分别验证读回可用和读回也不可达两个分支。代理只记录阶段/计数，不输出 BSON 文档、context hash、密文或 token。
4. Mongo 故障控制仅 loopback、随机 bearer，参数不能选择任意目标、命令或数据库；只控制本轮固定目的地址和库的代理。丢回执后可按显式模式继续放行读回，或在有界窗口拒绝两副本的 Console Mongo 通信，之后由测试显式恢复。依赖未知时无成功Cookie、不擅自撤销Auth token，恢复必须重新证明设备并签发新代。

测试不得更改 Auth/App 业务库安全状态、导入私钥、注入 Session Cookie、修改时钟/lease、自动重试 Complete 或将 fixture 响应冒充真实协议。必要的 Console 修复须按现有权威契约解释原因、补回归并记录；需要新语义时先记录修订。

本包不宣称全部私有 DOM/cache 迟到矩阵、context 32次上限恢复入口或其它 UC 已完成。所有外部服务继续从 published latest 拉取，不读取相邻源码。

## 实现中发现与修正

实际 UI 的 Begin handler 原先仅将网络异常类识别为结果未知，对 HTTP502/503 显示依赖不可用的通用错误，虽然仍保留原 requestId/密钥，却没有明确未知发送结果。新增两项 UI 回归均先复现失败。按既有 BR-CSE-006/Session v2 契约，5xx不能证明邮件没有发出，因此将该 handler 的5xx同样归入未知提示、保留原请求及显式重试；不把其它4xx泛化为未知，也不自动重发或重置设备材料。后续用真实SMTP/响应丢失验收验证，不用这两项mock回归代替。

生成漂移检查的原Git fetch实际存活十余分钟仍无结果，而独立有界HTTPS/HTTP1只读查询能确认远程HEAD为固定API commit。取消该轮已核对PID的fetch后，原检查明确失败并执行自身临时目录清理，未把观测超时冒充完成。为后续CI设置验证子命令120秒期限及本次Git fetch的60秒低速保护（仅该命令，不改全局Git配置），补真实子进程成功/失败/期限回归；固定远程、commit、Proto清单和逐字节漂移要求不变，不引入本地源或静默fallback。此保护不声称已经定位原网络挂起根因。

## 2026-10-16 验证结果

`pnpm test:real` 最终 **13项全通过**（约4.8分钟，无自动重试/跳过），包含原9项与本轮新增4项；production Browser/BFF与Auth/App/Gateway latest联合执行。解析出的backend镜像digest仍与[接线记录](2026-10-16-session-v2-wiring.md)一致。

| 本轮新增真实证据 | 结果 |
| --- | --- |
| 实际UI Begin响应丢失 | SMTP已投递，BFF响应被真实转发器断开；页面显示未知并聚焦alert，键盘显式确认原请求；requestId/邮箱/公钥未变、本机仅1把non-extractable钥匙、邮件sequence不增加，原验证码最终登录成功 |
| 实际UI EMAIL未知→两次DEVICE失败→原EMAIL成功 | EMAIL外呼尚未到Auth时终止两BFF；设备Begin按防枚举契约返回正常挑战，两次真实Complete均401 AUTHENTICATION_FAILED；原EMAIL/code/key仍保留，过早重试409并由真实UI禁用倒计时，期限到达后显式完成原operation，未自动重放/重发/换钥匙 |
| Mongo真实写入回执丢失、读回可用 | 原始Session写入真实完成，回执的generation/commitId匹配本次候选才被丢弃；BFF读回确定后201，只签发1个新carrier并精确清旧名，权威Session与真实App读取成功 |
| Mongo真实写入回执丢失、读回不可达 | 断开该surface两副本全部Console池连接并拒重连；Complete实际503、无Set-Cookie，Session503而非假SIGNED_OUT；恢复通信后旧载体不能认证未交付的新代，同一intent/key显式恢复新root/新载体后真实业务读取成功 |

首轮为12通过/1失败：测试误以为未知设备会在Begin返回404。依据UC-AUTH-007 BR-LGN-002与错误表修正为普通挑战200、Complete统一401，严格保留两次失败和原EMAIL成功的目标后重跑通过；不是后端缺陷，也没有为绿测试绕过认证失败。

其它门禁：全量Vitest（UI26项）、22项Node传输/子进程测试、strict typecheck（含所有real spec）、fixture Playwright 8通过/4按Admin surface跳过、production build、repository independence与diff检查通过。有界重跑 `generate:check` 已确认固定输入无漂移，前一轮被取消的无界fetch仍登记为失败，不追记为通过。临时服务与故障代理均已退出，Docker本轮容器/网络无遗留。

## 仍未完成

本包及UC001继续 `IN_PROGRESS`，fencing缺口保持OPEN：迟到Begin的实际取消/替换交错尚未补齐；实际私有DOM/Query cache、旧SESSION_INVALID迟到回收矩阵仍待实现与验证；context 32次签发上限后的显式重建交互仍须独立设计。不以以上13项替代这些要求。
