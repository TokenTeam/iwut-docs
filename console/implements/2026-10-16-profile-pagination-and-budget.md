# UC004：真实资料分页、历史与预算错误

状态：`ACCEPTED / IN_PROGRESS`，2026-10-16，按用户持续授权自行设计并接受。实施已接受的UC-CONSOLE-004 / BR-CMG-007–008及UC002私有读取规则；不是新的资料写功能或Reviewer授权。

## 决定与边界

补齐真实浏览器的资料四状态、列表keyset、独立审核历史keyset、页外权威指针、原文表达和正式413预算错误矩阵。前一[管理权失效工作包](2026-10-16-management-access-loss.md)仍因App详情404缺no-store未过完整门禁；保留该失败，不以本包替代或关闭它。没有跨chat派单授权时不通知后端agent，不改/编译相邻后端源码。

同一Application的DRAFT/SUBMITTED共用正式working唯一索引，不能为测试绕过。专用账号经真实注册、Developer申请和DEVICE证明，通过正式Create建立两个Application。主App准备25条资料读取fixture：seq25 DRAFT为working，seq1..12 APPROVED（published=seq1），seq13..24 REJECTED；另一App准备SUBMITTED/PENDING并作为同一管理员的跨App ID隔离对照。全部附属fixture须经过现有Mongo validator/index，不修改ownership/quota或安全状态。

同步澄清UC004验收措辞：工作/公开指针只能使用权威UC039允许的组合，不把原“同或不同”误读为可将同一ID同时当成功的working/published。无后端规则变更。

seq24准备25条attempt升序REJECTED历史；这只验证兼容遗留读取投影，不宣称当前资料命令可以重试同一修订25次（正式UC039限制继续有效）。decision reason仍服从非空/非首尾空白等正式约束，不能用非法reason测试空字符串；null/空串/空白与惰性URL用允许这些表达的原文字段验证。页级working/published指针独立于当前页或filter；latestReview不从当前历史页推导。

列表token和review token只来自真实响应，保持不透明；在内存中比较/重放用于协议负例时不输出token，不进入URL路由、日志、诊断或持久化。真实同源客户端查询携带API契约要求的query参数，不与前端页面URL混淆。跨App、跨查询种类/筛选的token错用通过真实读请求验证正式400及no-store，不能合成错误正文。前端自身不会主动错用token；组件测试覆盖对应坏token的显式从头恢复。

## 非权限错误的投影

网络/5xx仅在相同读取上下文保留旧快照并标原asOf，沿用[私有读取边界](../query-contracts/private-read-boundary.md)。400坏token、413预算错误或畸形成功不是授权下降，不清Session/设备，也不触发整App权限黑名单；但本次查询失败时不能继续把旧正文、指针、latestReview或reviews呈现为本次成功结果。旧已读数据若仍被TanStack保留在挂载Query内，也不得出现在失败页面；可按当前Query精确回收，不影响其它资源或新attempt。413不得截断/跳过条目、自动翻页或重试同一超预算响应。

同key后台刷新失败与显式从头刷新分别验收：前者以组件Query refetch直接证明显示边界，不能冒称其为真实点击；后者在真实页面用正式413响应验证旧内容退出。不会为触发同key错误暴露产品QueryClient或伪造document visibility。

补充执行决定见[私有读取边界](../query-contracts/private-read-boundary.md)：失败先遮蔽，再按捕获的当前Query实例清除retained data，防止后续5xx把先前退场的内容复活；明确错误不因focus/reconnect自动重试。Profile成功解码错误与fetch网络TypeError分型，协议错误不附带原正文/cause。保留网络/5xx真实旧快照对照，不用关闭所有自动刷新来缩小语义。

## 真实镜像矩阵

1. 专用账号使用真实浏览器邮箱登录；仅测试driver准备凭据，被测页面为生产React，不拦截/合成业务响应。两个真实Create App下读取上述四状态，确认没有资料写/审核操作。
2. 主列表实际20+5分页，前/后页互换、不重复/不漏，筛选重置到首批；公开指针seq1初始在页外，筛选REJECTED时work/pub均在filter外仍忠实表达。默认页和筛选页各自显示真实asOf。
3. seq24详情真实20+5审核历史，latestReview始终为attempt25，历史翻页用新的完整详情；前后页不拼成一个snapshot。原文中的null/空串/空白、HTML/URL惰性文本保持区别，不生成img/link或外部探测。
4. 使用同一管理员另一App的profileId对照统一404；实际Session保持，无DELETE。不把同一管理员同时管理两个App解释为资源ID可跨App读取。
5. 固定loopback control仅接受空JSON和预登记fixture，令seq24的合法REJECTED旧原文超过2 MiB。超长值在mongosh内部按固定常量构建，受validator且远低于Mongo16 MiB单文档上限；不接受任意ID/文本/DB参数，不给浏览器返回原文。正式服务对该详情以及以其为首条的REJECTED列表返回413；前端明确预算错误且无旧内容/指针/历史，不截断为200，不清会话，不自动重试。

Node setup bundle仅在临时setup目录，凭据/Session只在闭包；沿用固定API `a5d504c058c62cd91be451074d21608d69789918`、真实latest镜像、报告隐私fixture和隔离资源清理。不得通过临时后端源码编译或修改镜像令测试通过。

## 验证和非目标

新增组件分支先红再实现；普通测试、严格类型、生成漂移、fixture浏览器/Edge及真实镜像执行分层记录。focused仅诊断，完整门禁仍需无参数全量；已知App404响应头失败不删除、不记绿。本包不关闭UC001/fencing或全部UC002–005，不实现UC006–007、资格/生命周期写UI或任何资料业务写命令。

## 实施与已执行证据

组件先红后绿：Profile list/detail×400/413四个新回归先在“旧原样名称仍在DOM”失败，原93个Developer用例通过；API三种成功校验/解码异常仍为TypeError或原始parser Error的回归先失败。实现后分别扩展至6个页面错误链用例与12项精确投影核心测试：先遮蔽再只清当前Query.state.data，保留错误但不自动重试，保护新同key实例/新成功及兄弟Query，后续同Query503不复活旧投影，明确新200可恢复；健康/网络/503保留自动focus刷新和原asOf。

Profile解码/形状断言现在统一为专门`ApiResponseError / MALFORMED_SUCCESS_RESPONSE`，无原正文、parser消息或cause；实际fetch TypeError与HTTP413 status/reason原样透传。API34项、Developer111项以及普通全仓388项Vitest/28项Node通过，严格类型通过。一次并行开发期的测试fixture每次Session读取都生成变化的expiry、以及尚未观察503就查重名恢复按钮造成假失败，已固定该轮expiry并等待同一Query实际503/DOM状态；没有放宽Session不变或旧正文退出的oracles。

首次focused真实镜像3项全部通过（16.7秒）：两个App通过真实Create建立；26条资料/49条审核由当前validator/index接受；四状态、列表20+5、审核历史20+5、latestReview25独立、页外/筛选外指针、同管理员跨App ID404、五种token绑定负例真实400、null/空串/空白/HTML/icon URL惰性原文均通过。最后固定事务扩展正文与25 snapshots后，正式列表/详情均真实413且`private, no-store`，原内容/指针/历史退出、Session摘要保持且无DELETE；没有截断200或未授权外链请求。

同key错误回收的直接Query证据只指公共Query.state.data，不宣称清除整个JS heap或Query内部所有历史引用；真实413的页面证据是明确从头刷新，不把组件invalidate模型称为真实后台UI refetch。负面token探针也不称为产品会主动发送非法token。

固定API仍为`a5d504c058c62cd91be451074d21608d69789918`。本轮backend latest分别为Auth `sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3`、App `sha256:6f20c469a0e9566e045a5966fd51d81ce0b1293c650e2b277fa62bc3b5a3579b`、Gateway `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9`；Mongo `sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3`、Traefik `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0`。无后端编译或工作区修改。

生成漂移检查首次因GitHub固定API取数低速超时失败，原命令重试后通过，没有改源版本、使用相邻路径或删除检查。fixture浏览器8通过/4个Admin非目标skip，Edge接线通过。产品/API回收逻辑单独本地提交`a8b098a`，真实准备与新增spec提交`eb163e6`。

无参数完整真实套件终态为25项中24通过、1失败，8.4分钟、exit1。新增3项资料场景全部通过；原真实登录/双surface context上限/双副本/Mongo/迟到回执与真实UI恢复场景均通过。管理权转让用例完整执行至历史和最终双方Session断言，唯一失败清单仍是3条Application详情404缺no-store（B接任前、A失权后、A显式重读），没有删除断言或把失败记绿。本包维持IN_PROGRESS，不关闭完整联合门禁或上层UC。

收到用户Gateway CI完成通知后再次pull已发布Gateway/App latest，实际digest均与本轮相同；未编译后端、未重复跑相同输入来代替修复。已按精确轮次`iwut-console-real-695461`核对退出后的容器（含已停止）及网络均无残留；不推送未过完整门禁的Console提交，legacy保持不变。

收尾复跑普通388项Vitest/28项Node和严格类型通过，docs 71份brief及367行registry（8 retired）检查通过。Edge默认38080端口首次被Docker报告占用而退出125；使用脚本既有`E2E_TRAEFIK_WEB_PORT=38081`重新执行后，配置工具、所需9条Developer读路由和失败关闭检查全部通过，无产品/断言修改，失败轮容器亦无残留。这是独立于真实门禁no-store失败的本机端口冲突，不将首次命令改记成功。
