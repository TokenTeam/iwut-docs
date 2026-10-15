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
