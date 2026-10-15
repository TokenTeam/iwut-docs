# UC005：真实 Tester 分页、容量与最小披露

状态：`ACCEPTED / IN_PROGRESS`，2026-10-16，按用户持续授权自行设计并接受。落实[UC-CONSOLE-005](../use-cases/UC-CONSOLE-005-query-application-tester-management.md)及[UC-APP-037](../../app-center/use-cases/UC-APP-037-query-application-tester-management.md)，不新增管理写UI、REMOVED Membership入口、用户资料聚合或Reviewer权限。

## 决定

用专用真实注册账号、Developer申请及DEVICE证明，正式Create两个Application。主App准备25个ACTIVE Membership和同一Tester早先REMOVED episode，以及26条合法链接元数据（1 ACTIVE、25 REVOKED）；另一App为空态和同管理员跨App token对照。附属读取fixture仍经过现有Mongo validator/index，不修改ownership/quota/认证安全状态。等时间排序键使用不同规范小写UUIDv7，验证真实keyset而非只比较行数。历史fixture只证明读取，不冒称真实加入/轮换/移除命令已交付。

三个区域分别读取、分页和刷新。概览容量25与成员首批20不一致是合法跨投影，不从当前页计算人数；旧REMOVED episode不进入固定ACTIVE列表，成员可以引用已REVOKED链接。链接ACTIVE/REVOKED/ALL切换只重置链接页，成员页和概览不随之重置；全部刷新则分别回到三个首批，不假称原子snapshot。

局部网络失败复用已有透明TLS代理：两个POST列表分别在真实App已完成200后断开回执，校验代理upstreamStatus及实际React旧asOf提示、兄弟区域保留和显式刷新恢复。不生成500/伪响应，也不把网络故障视为Session失效；三RPC的5xx分支仍由组件测试独立证明，不混称本轮真实500。

传输决定修订（同日接受）：一次DROP不保证浏览器fetch失败。首次新增真实场景在旧asOf提示处失败；随后独立原生Chromium+真实HTTP代理最小诊断得到POST实际发出2次、第一次gate DROPPED而fetch最终200，证实浏览器连接重试，不应修改产品刷新逻辑或放宽页面oracle。测试代理允许仅RESPONSE/DROP使用可选`dropCount` 1..3（默认1），每次都完整取得真实上游响应才断开，耗尽计数后不再干预；受控场景最多3次，分别记录bounded upstream statuses/count并最终核对JS错误与页面。它不是任意持续阻断、不伪造响应/身份、不关闭浏览器网络或产品自动刷新；旧one-shot协议保持原样。若浏览器仍恢复成功，测试须如实失败，不能把gate计数当UI失败证据。

Node闭包可通过正式精确DELETE撤销本包预登记ACTIVE链接，响应按固定API生成DTO验证，不发回浏览器或日志。固定loopback control只接受空JSON、固定动作，无ID/URL/正文参数；撤销后概览无当前链接但ACTIVE成员与容量保留。没有一次性join secret创建或恢复请求，不实现产品写入口。

## 错误与隐私

补齐成功响应解码分型：Tester三RPC的成功形状/fromJson错误统一为无正文、无cause的`ApiResponseError`，fetch TypeError仍是网络故障。已有region结果替换用于明确400/协议错误退场；不能让其被误判为网络而保留旧投影。明确错误不会因focus/reconnect自动重试，只有显式重读；只影响该区域，不清Session、其它区域或整App。后续503不能复活此前已退场内容，健康网络/5xx保留原asOf。401/403/404与Session错误继续沿用已接受私有读取边界。

真实响应检查private/no-store与白名单字段，不出现joinUrl/secret/tokenHash或隐藏createdBy/revokedBy/removedBy，不补查Auth资料。浏览器仅渲染opaque不可点击ID，无复制/导出/写按钮；分页token只驻留请求/内存，不进入前端路由、存储、日志或失败报告。真实同源协议探针验证跨查询种类、filter、App和篡改token的正式400；不称这些探针为产品会主动发送的请求。

## 验证与边界

先执行组件/API红回归，再实现分型及独立恢复；直接Query.state.data与真实DOM/网络证据分层，不宣称检查整个heap。focused仅诊断；完整门禁继续用无参数`pnpm test:real`拉取已发布Auth/App/Gateway latest并固定轮内digest。不得编译相邻后端或为通过测试放宽validator/响应头断言。

既有[Application详情404缺no-store](2026-10-16-management-access-loss.md)仍保留；本包不关闭完整门禁、UC001/fencing或UC002–005全部生命周期/资格矩阵，不以独立测试通过代替上层完成。

## 实施证据

API三RPC成功形状/fromJson回归先红，细分6个错误输入后全部绿；组件最初6红（三区协议错误无明确文案、三区400在focus/reconnect自动重试）。实现后Tester组件34项、API全包43项、Developer全包124项通过；新增13项区域测试保留兄弟Query实例/data、原Session及无DELETE，验证协议错误退场、随后503不复活、明确200恢复，同时健康和真实网络TypeError/503仍可自动foreground读取、旧asOf不变。fixture Session expiry固定并每次返回新Response，避免把fixture变化或body复用当产品错误。产品与API已本地提交`b9b3761`。

普通全仓410项Vitest/28项Node、strict类型通过；首次生成漂移因GitHub固定API取数60秒低速超时失败，原命令重试通过，不换输入或使用相邻源码。仍固定API `a5d504c058c62cd91be451074d21608d69789918`，新增tester_join_link descriptor仅供测试Node精确DELETE解析，不暴露产品写client。fixture浏览器8通过/4个Admin非目标skip。

首轮focused真实3项全部通过（11.2秒）：正式Create与validator/index seed成功；成员20+5、REVOKED20+5、ALL20+6的同时间ID排序、区域分页独立、键盘筛选/翻页/全部刷新、旧REMOVED排除及真实空态全部通过。六类真实token负例400/private/no-store通过；正式精确DELETE成功，刷新后当前链接为空、容量25和ACTIVE成员保留、原链接MANUAL历史可读、Session摘要保持且无DELETE /api/session。随后增加局部回执丢失的真实网络场景，仍须focused及无参数全量完成，不能沿用这三项通过代替新增场景证据。

有界代理新增5项Node先红后绿，原16项保留，共21项HTTP(S)回归通过；普通Node合计33项通过。两次DROP真实诊断仍在提示处失败，随后无正文/无Query访问的被动fetch元数据明确观测：仅一次JS fetch、两次真实200被丢弃、最终fetch仍成功，三次上游POST不是React自动刷新。最小HTTP/TLS/复用TLS实验只重试一次，不能据此声称TLS必然重试两次；仅按当前真实拓扑证据使用既定上限3，不扩成持续阻断。被动wrapper原参数/Promise/Response原样返回，输出仅静态布尔，不读取认证或业务正文；后续必须同时验证JS TypeError与DOM，不能只验证代理。

### 传输方案最终修订（ACCEPTED，同日）

三次DROP的真实诊断仍是一次JS fetch最终成功、4次上游；不能把有界DROP当必然网络故障，也不能继续增加次数凑失败。上述重复DROP实现未提交，撤回该扩展及其专属测试，保留原one-shot HOLD/DROP和已有证据。公开TCP RST的独立TLS最小诊断同样可能重试，不据此改成RST方案。

实际验收改用单次`RESPONSE/TRUNCATE`：代理先完整取得真实上游响应（仍受256KiB上限），然后原样转发真实status/headers及正文第一个原字节，write flush callback后断开，既不更改Content-Length/Transfer-Encoding也不补完正文。只允许非空且长度至少2的真实响应；其它形状失败关闭。记录upstreamStatus及bodyTruncated布尔，不记录正文/headers或凭证。它是传输中断而非伪造JSON/错误响应，浏览器fetch已得到真实200，但正文读取应TypeError；旧one-shot inspect/cleanup不变，必须由Node、原生浏览器和真实React分别验证。

成功HTTP正文读取的真实TypeError继续归网络故障，不转换成`null`/畸形成功而丢旧数据。完整传输但JSON语法错误仍归协议错误；已收到非成功HTTP的401/403/404即使错误正文读取失败，也保留明确status的既有ApiError边界，不降为可保留旧数据的网络错误。此澄清在共享fetch transport实施，并补成功断流/完整坏JSON/非成功断流回归。Tester真实旧asOf和显式恢复目标不变，不改变产品自动重试或引入正文代理。

最终实现：runtime新增25项先6红/19绿后全绿（原7项保留，共32项）；API全包68项、Developer124项通过。共享transport修复本地提交`d954441`。TRUNCATE新4项先红后绿、原16项保留，HTTP(S)共20项；原生TLS独立诊断严格证明单次真实POST、fetch200、正文TypeError及bodyTruncated。此前重复DROP的5项测试已撤回，不混入最终计数。

最终focused真实4项全部通过（15.3秒）：前述分页/空态/token/最小披露矩阵继续通过；成员与链接两次分别用独立原生协议探针证明真实200正文断流TypeError，再用实际React刷新取得原asOf旧快照提示、兄弟区域保留、显式正常读取恢复。精确真实撤销仍成功且25 ACTIVE保留、Session完全不变。没有fetch wrapper/产品Query hook、伪响应或提高重复次数。fixture/runner/spec及正常固定API生成描述符提交`4749a32`；普通全仓435项Vitest/32项Node、严格类型已通过。生成漂移收尾又遇同一GitHub低速超时，正用原命令重试；无参数29项完整真实门禁已启动，完成前不得把focused当全量通过。
