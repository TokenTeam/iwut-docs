# UC001/006/007：Admin 私有视图真实跨会话隔离

状态：`ACCEPTED / IN_PROGRESS`，2026-10-16。按用户持续授权自行决定并接受。本包补真实网络与生产React证据，不缩减完整审核决定、结果未知恢复或其它UC范围。

## 依据与未决项

沿用[UC006 BR-CRV-004](../use-cases/UC-CONSOLE-006-review-application-versions.md#br-crv-004)、[UC007](../use-cases/UC-CONSOLE-007-review-application-profiles.md)、[UC001](../use-cases/UC-CONSOLE-001-establish-console-session.md)及[读取恢复增量](2026-10-16-admin-read-recovery-and-late-responses.md)的Session generation与私有响应边界。已有组件Query回收不能代替真实Cookie/网络/DOM验证，Developer已有交错也不能自动证明Admin四个读取入口。

API输入固定pin不变；不修改后端源码、业务规则、治理/决定surface，不推测策略定义。App错误响应头、开发fixture首轮两项未定因异常、任意33+迟到carrier上限及完整决定依赖继续OPEN。新测试不放宽旧门禁、不补代理头。

## 功能与验收决定

1. 在隔离真实Auth中正式注册两个新的普通账号，分别只授`app.version.review`和`app.profile.review`。复用本轮G的正式治理接口，查询当前revision后CAS grant，未知回执只读确认一次，不重放。两者不Apply、不Create、不拥有审核资源、不成为平台管理员。原A/G/R/T、reviewOwner和V/P权限相位不变。
2. 两个新账号在同一Admin BrowserContext各自经真实EMAIL建立一把不可导出的本地设备钥匙；后续交错只用DEVICE显式切换。两个初始EMAIL加12例各A/B两次DEVICE最多26次签发，保持在既有32次上限内，不篡改计数/复制私钥/storageState。两个新邮箱加入正式冷却预算，DEVICE准备采用2100ms最小间隔；若仍返回429则该例失败，不自动重试。时间只用于尊重真实预算，不作为正确性oracle，不重放未知提交。
3. 覆盖Version/Profile的queue/detail四个旧入口，各有旧成功200、旧SESSION_INVALID401、旧DELETE204回执三种交错，共12例。旧角色仅拥有对应capability，新角色只拥有另一capability，使旧材料与新可见内容明确不同。新身份仍通过真实链路读取自己获权的队列，而非伪造空页或借无权限治理者替代。
4. 旧200或401先由透明TLS gate取得真实上游响应并暂缓，另一标签页建立新Session后释放。产品必须重新确认权威Session；旧成功不能交付到新身份的私有DOM，旧401不能清新Session/载体。若产品取消使正文不可读，不把DevTools读取失败当缺陷或声称JS已消费旧body；实际上游status、独立旧Session拒绝与实际DOM/后续授权读取分层证明。
5. 队列可用“从头刷新”让旧投影先退场；详情使用实际初始深链接读取控制迟到正文，不把同页刷新本应保留的健康快照误判为越权。页面获知新Session之前，不声称它能即时感知另一标签页的Cookie变化；在产品完成权威协调后验证新身份视图。
6. 旧清理回执交错必须先确认真实旧代DELETE已返回204但回执在途，再建立B。原页面通过生产header Router Link重新读取Session、经真实入口读取B获权队列；随后释放旧204，验证同一document标记、路由、B投影/时间/权威Session不变，无额外业务读取、Session清理或旧导航。仅被动观察原生fetch状态/次数，原参数、Promise与Response不变，不读凭据/body或暴露QueryClient。
7. 固定loopback随机bearer控制只对两个新subject各自设置本轮Auth `auth_sessions.revokedAt`，仅空JSON、无query、固定命令，不接受AuthId、SessionId、数据库、URL或Mongo命令。它是外部失效测试fault，不是正式Session撤销、账号禁用或治理UI交付证据。另提供固定只读role观察，返回最小权限/revision，不返回Session/私钥。
8. 成功私有查询保留private/no-store检查；失效与清理按现有正式协议验证status/reason/no-store。设备、安全摘要、Cookie只检查属性/代绑定，不输出值。所有real spec使用隐私test fixture。仅被动DOM布尔观察，不宣称浏览器全heap清理；精确Query内存边界仍由组件证明。

## 运行与交付边界

新spec复用既有审核readseed，无新增审核命令或数据事实。每例明确建立A、完成各自gate释放/页面清理，不以serial跳过余下矩阵掩盖失败；现有真实配置单worker、零重试保证共享context有序。准备器和控制边界先做Node合成负例，未知授权写不能自动重试。

实现后运行普通测试、strict、同pin生成漂移、build、fixture浏览器、Edge；随后从新拉取latest的空隔离环境运行专项及无参数完整门禁。运行时源码冻结，不重启仍存活的轮次；终态核验并清理本轮资源。若真实证据发现前端隔离缺口，先复现再在上述语义范围内最小修复；不得关闭正式Session防线或取消机制来迎合测试。

## 实现与前置证据

Console实现冻结为`4290e3c`。准备器/固定控制边界新增13项合成负例先因缺失实现全部失败，再全部通过；统一回归为690项Vitest＋102项Node通过，strict、固定API生成漂移、build通过。fixture浏览器10通过/6非目标skip，Edge真实Traefik路由隔离与fail-closed通过。上述合成/fixture证据不代替正式Auth grant或真实跨Session矩阵，也不关闭原fixture偶发异常的未定因记录。

真实运行从本轮重新pull的latest开始，实际image ID和专项/无参数终态待记录。不得登记本包、UC001/fencing或完整审核UC完成。提交仅本地；legacy本地及本次远程只读核验仍为`e68851e343bd0e077e5ccd0b680fe6813216ced0`。

### 首轮准备失败与身份边界修订

轮次`iwut-console-real-57321`在新增准备器处终态exit1，浏览器12项尚未开始，不能记作通过或12项失败。错误为静态`Admin view fixture unavailable`；终态后容器/网络为空。新准备器错误复用了App资源UUIDv7校验；Auth Session的authId是opaque string，既有bootstrap也未作UUIDv7假设。将合成actor/固定控制输入改成非UUID的安全Auth标识后，原13项中8项稳定失败；修订为测试实例的路径安全字母数字/下划线/连字符约束，保留固定subject、精确相等和Mongo JSON编码，不改变产品AuthId语义。补充空值/路径/query/引号/换行/超长/重复目标负例后14项通过、real strict通过，冻结`8233ef1`后重新拉取latest执行专项。没有自动重放未知grant或失效写，不把准备器错误归于后端或生产Session隔离。

### 修订后真实专项

轮次`iwut-console-real-62095`终态exit0，12项全部通过（1.1分钟浏览器执行、无skip/retry）。两能力的queue/detail四入口均收齐旧200、SESSION_INVALID401及旧清理204交错；B经真实生产React读取另一项获权非空队列，旧投影未回填、无旧401清新代，四个旧204场景保持同document/B路由/投影/精确asOf且无额外自动读取/清理/导航。正式权限/revision、两把non-extractable钥匙与carrier属性保持。准备阶段真实密码429只按既有registration规则等待；DEVICE未重放、未触发额外签发。

本轮五镜像均重新pull，ID与首轮及此前基线一致：Auth `sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3`；App `sha256:6f20c469a0e9566e045a5966fd51d81ce0b1293c650e2b277fa62bc3b5a3579b`；Gateway `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9`；Mongo `sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3`；Traefik `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0`。终态后本轮容器/网络为空；修订后的统一690项Vitest＋103项Node通过。专项不替代无参数63项门禁；该全量已按同冻结源码、新拉latest启动，待终态。

### 最终无参数完整门禁

冻结源码仍为`8233ef1`，轮次`iwut-console-real-69416`无参数执行`pnpm test:real`，终态exit1：63项中59通过、4失败（浏览器12.9分钟），无skip/未运行项。新增12项真实Admin跨Session矩阵在完整轮次再次全部通过；原审核读取/断流恢复、双origin32次签发、双副本/持久提交回执、Developer迟到响应、生命周期、资格下降恢复、Tester及原React登录恢复均已执行。

全部81条失败均落于原缓存响应头soft断言，没有额外功能/协议/Session硬断言失败：

| 失败矩阵 | 精确断言来源 | 数量 |
| --- | --- | --- |
| Admin精确权限/游标/路由 | `admin-review.real.spec.ts:433`，28个Reviewer查询400/403/404分别缺private/no-store | 56 |
| 管理权转让 | `management-transfer.real.spec.ts:257`，三个Application GET404缺no-store | 3 |
| owned-list游标 | `owned-application-pagination.real.spec.ts:200/201/220/221`，五个List400分别缺private/no-store | 10 |
| 资格与角色 | `qualification-read-matrix.real.spec.ts:368`，六个Application GET404分别缺private/no-store | 12 |

这些soft断言用于收齐后续真实功能证据，仍令四项和完整门禁失败；没有删除断言、代理补头、修改后端或编译相邻源码。每轮重新pull latest，最终五个image ID与上节完全一致，因此不能把Gateway CI完成表述成App错误头已修复。最终本轮容器/网络为空，本地与远程legacy再核验均未变，提交仅本地、未push。

本包的测试设施及所列跨Session场景已交付，整体状态仍`IN_PROGRESS`。App错误头需新镜像后再次跑完整门禁；原fixture偶发详情异常因果、任意33+迟到carrier容量、完整UC001及审核决定依赖继续OPEN。外部Session fault不是正式撤销命令证据，读取seed不是提交/决定命令证据；不能将本次两单项Reviewer代表所有角色/页面/生命周期交错，也不声称浏览器全heap验收。
