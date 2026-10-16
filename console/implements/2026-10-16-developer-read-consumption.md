# UC001–005：Developer 私有读取消费边界

状态：`ACCEPTED / IN_PROGRESS`，2026-10-16。按用户持续授权自行决定并接受；本包落实既有只读页面，不添加业务写UI或改变后端授权。

## 当前证据与依据

依据[私有读取失效边界](../query-contracts/private-read-boundary.md)、[UC002 BR-CMG-002/004](../use-cases/UC-CONSOLE-002-query-owned-applications.md#前端业务规则)及UC003–005。Console `78c86b1` 的Developer attempt仅检查布尔active，close后activate可让旧异步工作再次有效；生成client包装没有把单请求signal交给消费边界。Application/Version/Profile投影只列举400/413/协议错误，未知错误或其它明确4xx仍可保留旧Query data却没有网络/5xx旧快照提示。Tester会替换未知错误区域，但focus/reconnect仍可能自动重试。Admin此前修订不自动证明Developer符合相同要求。

## 接受的实现决定

1. 每次读取捕获attempt lifetime；close使该lifetime永久失效，后续activate仅激活新lifetime，不复活旧工作。读取开始、成功返回和处理拒绝前都检查当次AbortSignal及当前attempt/lifetime；底层忽略Abort也不能交付旧正文，取消后的401/403/404不能变成新授权观察或清新Query。九个生成只读方法保持签名/序列化，包装转交原options.signal，不补认证头或BFF代理。
2. 消费边界同时确认QueryClient中的当前Session public binding/generation与捕获sessionKey相符。已知换代、SIGNED_OUT或Session投影缺失时失败关闭，不依赖React卸载时序，不把依赖故障当退出。Session远端在线确认继续由既有bound fetch拥有；本地消费检查不是授权缓存。
3. 旧快照仅允许真实TypeError、DOMException AbortError或ApiError HTTP500–599。其它非nullish错误（含未分类Error、未知thrown值及其它明确4xx）先遮蔽并精确清理对应Query data，保留当前错误、不删除被观察的Query或自动重试。没有错误的健康投影不受影响；不把未知错误猜成权限或网络错误。Session/权限错误仍由既有专门边界先处理，投影退场不触发新的Session清理。
4. Application/Version/Profile沿用精确Query实例＋error对象＋errorUpdatedAt的清理检查；旧回调不能清同key替换对象、新成功或新错误。已经因拒绝退场的数据，后续5xx/网络错误不能复活；仅新成功恢复。多页保留原每批asOf，不拼接新旧筛选；不重置正式token协议。
5. Tester三个region保持独立：未知错误退场仅作用当前region；focus/reconnect仅对健康或允许保留的临时错误自动重读。其它region、Session和正式容量独立，整页明确权限拒绝优先。AbortError采用与其它私有读取相同的临时错误分类；已取消attempt即使被region包装也不能交付私有数据。
6. 整App/Session回收除取消/移出cache，还清捕获旧Query对象中的data；只操作捕获实例，不能清替换对象。不是对浏览器全heap、DevTools、历史截屏的保证，不记录私有正文、凭据或token。

## 验收与交付边界

先写红测试：close/activate迟到成功和拒绝、请求级Abort（开始前/在途/成功/拒绝）、九方法原signal/参数传递、Session换代、精确旧对象清理。页面层覆盖三类投影及Tester三个region的未知错误/其它4xx立即退场、后续503不复活、focus/reconnect不自动重试、明确新成功恢复，以及健康网络/5xx/Abort原快照及时间保留。正常StrictMode异步成功不能因开发effect重放永久卡住；保留忽略Abort的底层测试，不关闭产品取消来取绿。

运行统一普通测试、strict、固定API生成漂移、build、fixture浏览器及Edge，冻结运行时源码后重新pull Auth/App/Gateway latest，跑无参数完整真实门禁。组件精确Query证据与真实网络/DOM证据分开登记，原63项不能冒充所有Developer页面的跨Session完整矩阵。

本包不解决App错误响应头、审核决定surface/政策定义/Profile公开指针、任意33+迟到carrier容量或原fixture偶发异常因果；不修改/编译后端源码，不删断言、不补代理响应头，不扩大已接受写权限。完整UC001–007及原门禁保持开放，提交仅本地、未通过完整门禁不push。

## 实现与前置验证

实现已落地：核心保留首次active以适配原挂载，close递增lifetime，旧请求必须同时通过signal/lifetime/当前Session检查；九方法保持原参数/this/序列化。三投影统一共享错误分类；Tester同时检查Query.error和保留包装data.error，明确拒绝后即使显式重试503也不恢复自动读取，只有新成功替换拒绝包装。捕获旧Query对象data同步清空，同key新对象及其它Session/App不受影响。

红绿证据分别为：核心前置57项中45失败/12通过，修订及真实生成方法集成扩展后66项通过；三投影前置120项中34失败/86通过，临时错误交叉扩展后128项通过；Tester前置55项中15失败，修订后55通过。新28项未mock生成client的createRoot StrictMode测试覆盖七页面、Session/DTO各0或15ms异步组合，九RPC真实本地序列化/解码/边界均运行并通过，只是合成wire证据，不当后端或原偶发异常已修复证据。

统一回归837项Vitest＋103项Node全部通过（Developer302项），strict通过。固定API远程拉取首轮60秒低速超时，第二次相同pin生成漂移检查成功，未改为读取相邻源码或绕过检查；随后build通过（保留大chunk警告），Edge路由隔离/fail-closed通过。

fixture首轮9通过/1失败/6非目标skip：Tester页初始`opaque-tester-auth-id`未出现，未取得当时DOM/错误类型因果证据。未改原spec或产品，再独立Tester repeat10为10通过，完整repeat3为30通过/18非目标skip；因此记录为偶发异常OPEN，不猜测StrictMode/HMR或负载原因，不声明已修。原Admin偶发记录也继续OPEN。

运行时已冻结，本地与远程legacy均仍为`e68851e343bd0e077e5ccd0b680fe6813216ced0`。接着按新拉latest执行无参数63项真实门禁，实际image ID及终态待记录；不把组件红绿或fixture重复通过当完整门禁完成。
