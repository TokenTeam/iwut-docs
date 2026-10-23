# UC006–007：决定响应的跨Session隔离与等待清理边界

状态：`ACCEPTED / IN_PROGRESS`，2026-10-23，按用户持续授权自行接受。承接[Profile加载后关系变化](2026-10-23-profile-loaded-conflict-recovery.md)，补BR-CRV-003/004及UC007引用的决定Session边界，不以读取请求矩阵或组件mock代替真实决定验收，不扩大Developer写UI或新增退出/账号切换业务用例。

## 当前实现缺口与最小修复决定

静态检查发现`ReviewDecisionForm`独立保存决定ApiError并调用Session恢复，详情父页只消费query.error。决定得到SESSION_INVALID后，若按预期generation的DELETE回执仍在途，父页原snapshot和Query.data没有因此进入读取侧既有退场流程；仅禁用表单不足以证明已卸载私有内容。先新增两能力的合成延迟清理回归，必须先观察RED才能把此推断登记为已复现。

最小方案：仅将当前决定的精确Session错误转交其已捕获的详情Query实例，使它进入既有详情Session恢复路径；同时清该实例data。必须验证仍是同一缓存对象、query key属原Session且QueryClient当前Session仍匹配，不得按宽泛key覆盖新Query或新身份。错误严格限定HTTP401/SESSION_INVALID及HTTP409/CONSOLE_SESSION_CHANGED；其它403（包括利益冲突）、404、网络/5xx与协议错误仍保持原恢复语义，不能伪装成Session失效。

详情query error驱动原`useRecoverInvalidSession`：当前Session明确失效才发一次带原contextBinding/generation的DELETE；收到回执前隐藏原snapshot/理由/checks/预览并同步清捕获Query.data，不后台重发决定/读请求。迟到清理回执仍按当前Session保护，不能导航或清除新身份的同目标/其它能力内容。结果未知的同Review恢复要求不变；不能把本包局部内存证据称为全heap清理。

## 真实矩阵设计

原19项顺序保留，随后追加Version/Profile各旧401、旧DELETE204、旧成功200共6项，预期决定专项25项、默认全量113项，以实际终态为准。先401/204，最后才真实成功决定，复用原Version `resources[2].versions[2]`及第三份Profile C的正式PENDING，不创建新App/Profile/Review、改配额或seed决定终态。

复用原main BrowserContext/设备钥匙为A；另用原Version-only及Profile-only账号，各在同一context通过正式EMAIL生成独立non-extractable钥匙一次。B始终是另一能力Reviewer，进入其真实非空队列，不用旧目标为空推断隔离。三EMAIL（含原main）＋六例各A/B DEVICE共15次签发，保留32上限，不复制storageState/私钥。真实邮件冷却/DEVICE节流仅用于准备，429/未知不自动重放。

1. **迟到401**：A真实加载PENDING并预览REJECT；固定外部Auth Session失效fault后以独立同源读确认SESSION_INVALID。唯一决定POST的真实Gateway401被RESPONSE/HOLD；B登录后释放旧401，原页通过正式工作台入口进入B获权队列。旧错误不能导致DELETE B、恢复原snapshot/理由/结果，B权威Session/carrier及明确刷新保持。
2. **迟到204**：A加载同一PENDING目标并预览，正式失效fault后唯一决定POST实际401；生产恢复的旧generation DELETE实际提交204但回执HELD。此时旧私有详情必须已经卸载。B登录，原SPA通过工作台建立B非空队列后释放旧ACK；同document、URL、投影/asOf、B权威Session/carrier保持，无额外决定、Session读取/DELETE或导航。只被动计原生fetch状态，不读认证材料或旧未消费正文。
3. **迟到成功200**：A重新DEVICE并真实读原PENDING/重新确认REJECT，真实App已决定200后RESPONSE/HOLD；B登录，原SPA进入另一能力非空队列，在30秒deadline前释放原成功并确认传输完成。B页面不得出现旧结果、理由、snapshot或新自动读；只把原Review终态视为后端事实，不把B变成决定人。每例只一个明确POST、无自动重放，C/Version最后才被该项正式决定。

透明代理不生成业务JSON或授权成功；B页面需真实权限链和非空投影。Session失效控制仅固定原main账号、loopback bearer、精确POST/无query/application-json空对象，有界4次外部失效fault；不接收subject/Session/DB/URL，未知fault写失败关闭而不自动重放。此fault不冒称正式撤销/禁用UI或Auth命令证明，也不改原权限/资格事实。该控制及6项浏览器实现尚待后续交付，不因本次组件修复而标通过。

## 阶段与门禁

先交付精确Query失效helper、两能力组件与core先红后绿，统一测试/strict/固定pin生成检查；在真实矩阵接线完成后冻结产品/runtime/runner/spec，每轮pull published latest跑25项专项和默认全量113项。不能把仅新组件绿或原040冻结的19项当成改后生产UI已真实验收。中途提交明确为IN_PROGRESS，不push；不删除25条原Application缓存头断言、不编译相邻后端或以local-compat替代。

完整UC、不同修订指针UI并发可达性、策略/Scope/依赖故障、其它角色/生命周期及UC001/fencing继续开放。本矩阵仅列明六种决定交错，不等于任意提交点或所有Session组合完成。

## 第一阶段：已复现的等待清理缺口与局部修复

产品修订已本地提交`238bc070f2bf9fc75615592007568a98a44e2f16`。两cap组件新增6项首轮2失败/4通过：明确失败是在原generation DELETE已经发出、回执仍deferred时，Version/Profile旧snapshot和决定表单仍在；不是准备/定位器问题。其它4项新Session同目标/另一能力对旧ACK的保护原本即绿，保留作回归。接入修复后6/6全部通过。

核心新增16项先16失败/旧50通过，再66/66绿；之后额外在途读取测试先1失败/66通过，证明只setState清data仍会被忽略Abort的迟到读回填，补捕获对象级cancel后67/67绿。新增共17 core＋6组件，完整两文件156/156通过。仅对精确Session HTTP/reason设置捕获详情Query.error并同步清data，取消同对象在途读，不操作新Query/新generation；详情父页原恢复hook成为唯一清理者，等待中隐藏旧私有子树且禁用详情刷新。普通403利益冲突、能力撤销、其它错误与未知恢复的原断言未改。

最终源码下统一`pnpm test`926项Vitest＋183项Node、`pnpm typecheck`、官方同pin`pnpm generate:check`、`pnpm build`、`pnpm edge:e2e`均exit0。fixture浏览器10通过/6既有非目标skip（4.8秒），不是业务服务E2E，也不覆盖新六项真实交错。仓库独立性288文件与diff检查通过；本轮测试资源已清理，本地legacy仍`e68851e343bd0e077e5ccd0b680fe6813216ced0`，未push。

**未完成项不缩减**：本次尚未新增固定Auth失效fault或六项真实spec，未重跑改后19/107，更未运行计划25/113；前040轮次不能挪作新产品证据。下一阶段须接入上述已接受六项，在同一最终源码冻结后重新pull latest，完成25专项与113无参数全量，原25缓存头仍为失败门禁，不以本阶段组件绿宣布完成。

真实接线注意：首次外部失效前固定并正式读出C/Version目标，后续不调用依赖旧main Node Auth Session的准备观察（该账号旧Session会被fault失效）；不通过复制新浏览器token或暗中替换Node Session规避。原owner/governor及B两个单项Reviewer不作为失效目标，未知fault写不能重发。真实DOM/网络与组件Query对象证据继续分层。

## 第二阶段：固定控制与六项真实spec接线

Console已本地提交并冻结`badf1f559983ab9e0da893bed0a563364ef17f40`，产品修复仍为前238，新增固定失效控制/runner/六项serial spec，不增业务资源。控制新增12项Node先12 RED后12 GREEN：精确空JSON/媒体/16KiB、固定Mongo集合和活跃Session filter、ready、4次上限、并发拒绝不占次数、未知或零修改冻结、静态错误及外层bearer均覆盖；未知写不重放。ready仅证明本轮决定fixture已正式准备，原19项与恢复完成顺序仍由真实serial验收，控制不冒称治理业务授权。

统一926项Vitest＋195项Node、strict/官方同pin生成/Edge、Node语法/diff及独立性290文件通过。新增spec strict首轮暴露exactOptionalPropertyTypes的字段形状，已对齐真实driver返回；清理gate沿用既有精确method/path，另直接校验真实DELETE正文为原contextBinding/generation，不增加不存在的gate参数或伪造清理请求。旧401可能已触发产品正式Session重读/导航，工作台Link不强求重复GET；B非空队列仍经真实受Session绑定的API和独立权威Session/carrier验证。

旧200回执可能被产品post-response Session fence取消正文，不将取消当失败或强读未消费DevTools JSON；以真实上游200/完整传输及现有另一Reviewer context的实际终态/决定人读回分层证明。主context三EMAIL＋六例12DEVICE合计15签发，不因终态读回追加登录。旧401/204/200、B投影精确asOf、同document和无额外Session/业务/DELETE/导航均保留明确断言；原全部决定缓存头检查未改。

开始本冻结的published25项专项，每轮仍拉latest、轮内固定解析ID，运行期不改产品/runtime/runner/spec。真实专项与其后113项完整门禁均未达终态，不登记为通过、不push。
