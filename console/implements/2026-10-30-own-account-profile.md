# 本人账号资料编辑接入

状态：`IMPLEMENTED / ORDINARY_VERIFIED / REAL_PARTIAL`，2026-10-30。依据持续goal授权实现[UC016](../use-cases/UC-CONSOLE-016-edit-own-account-profile.md)。Auth业务权威仍为[UC005](../../auth-center/use-cases/UC-AUTH-005-edit-own-user-profile.md)和[查询契约](../../auth-center/query-contracts/user-profile-editing.md)，不把应用公开资料编辑器改名充当本人资料。

## 自主实施决定

- 新增共享 `@iwut/console-profile-ui`，两端共用结构与字段输入，使用各自主题变量和Tailwind扫描入口。Developer与Admin各自持有QueryClient、Session及bound fetch；共享组件不合并登录态，也不依赖Developer/Reviewer/平台管理员资格。
- 使用 `/account/profile` 和全局账号入口。Developer在该全局页不展示应用侧栏或选中“应用”；不从账号页读取某个App的owner摘要。Admin不套两类审核或治理能力门禁。
- 本人快照、字段目录分开读取。保存为明确PATCH，仅提交正式set/remove与body expectedRevision；共享transport仅补充PATCH方法，不新增通用BFF代理或浏览器Session header。
- 客户端为无状态 `edit(baseline,set,remove)`：接收调用方已确认的正式完整快照，验证未涉及字段保持及no-op，不在client闭包另存个人资料或隐式要求先调用某个GET。回执本身是原子确认点的完整资料，不用后续无版本GET拼成“写入结果”。
- 完整支持六种正式类型，按目录生成输入，只有用户明确选为设置/删除的字段才进入命令。纯删除不读取或依赖schema；保留未知旧key原消息。未来目录类型只能只读，未来wire分支无法无损解析时失败关闭，不能默默删字段。
- 字符串保持空格、Unicode和前导零，集合以正式value集合提交而目录标签保留声明顺序；当前年级只从保存锚点和schema学年派生。重新设置不提交confirmedAt，不由客户端模拟学年推进或学校认证。
- 仅修订是并发下界。Auth明确不保证墙钟时间递增，因此changed回执不因updatedAt相等/回退而被误拒；no-op须保持原时间，重复相同grade按正式规则保留原确认时间。日期“今天”仅使用上海本地日历作预检，服务端仍最终判定。

## 私有读取与恢复

共享runtime绑定Session metadata与单个页面lifetime，不保存权限或个人资料快照。两读模型Query使用不同根与同一scope/页面ID；GET/ACK写回绑定精确Query对象及原data身份，缓存较新revision只提升下界。Schema采用之后也不能跳过Query对象保护。

正式 `(401, SESSION_INVALID)` 或 `(409, CONSOLE_SESSION_CHANGED)` 才触发宿主恢复；其它401/403只使本资料区域退场，5xx不能借相同reason清除整个登录态。恢复前立即abort并清空捕获旧Query.data、卸载表单，不等待注销回执；旧Session或已离页响应在正文解码前拒绝，不碰同key替换实例。

目录网络/格式/依赖失败不等于空目录，不阻止独立权威本人快照与纯删除；账号拒绝优先退场。命令未知、冲突或回执后基线变化时冻结写入，保留输入，明确读回本人资料与目录、对照并采用。即使目录仍失败，也可采用完整本人快照以进行纯删除；不重放未知命令。

## 当前证据

- 无状态API client33/33定向通过，API client strict通过。
- 六类型纯model87/87通过，含raw文本/false/0、日期与集合、未知key、学年、64删加64新值按最终态和容量。首轮3条参数展开测试构造错误修正记录由执行代理提供，未改变产品断言。
- runtime19/19通过，覆盖旧Session/离页正文不解码、Query/data身份、revision99挡旧ACK2、关闭只清捕获对象、目录503后纯remove和精确Session错误组合。随后增加正式Session拒绝的立即清理，待组件批次一并复验。
- 新workspace依赖仅复用现有固定版本；offline install已完成，未下载包、未改全局工具。没有build或改写正在运行真实回归的dist。

## 集中组件与普通门禁

共享包最终model87＋runtime19＋实际client组件11，共**117/117**通过。组件覆盖明确设置/删除与checkbox确认、零自动写、目录503纯删除、还原/离页、未知结果明确读取采用、ACK/读取后的精确Query/data保护，以及正式Session拒绝在等待宿主恢复前立即遮蔽/清旧Query。首轮UI的两项同一问题为本地ACK推进baseline后Query observer尚保留旧prop，错误被当作外部变化；已改为只对实际新prop作观察，保留owner保护。一次导航测试直接await被阻止Promise超时引发7项fixture级联，改实际Link点击后全场景通过，不把级联冒称7个产品漏洞。

双端路由/Session定向**182/182**通过，使用共享实际组件与客户端：普通USER不查询App/Reviewer/Gov，Developer账号页无侧栏，换代清两根和表单，旧响应不回填。能力拒绝不清本人资料，完整Session恢复则清对应scope。

根代理完整 `pnpm test` **exit0，1756项Vitest＋392项Node**；完整工作区strict与build **exit0**，新增包117项在最后scope提取后再次通过。完整root typecheck首轮另发现低层matcher从TSX入口引入造成real环境TS6142，已用纯 `@iwut/console-profile-ui/scope` 导出解决，不扩大real tsconfig来掩盖UI依赖。旧真实spec并行修订的4个未定义marker也已由其所有者修正，随后real types通过。

两端共用Tailwind源码扫描已加入；build仍保留大chunk体积提示，没有调高阈值隐藏。当前真实链只准备了独立测试目录及两条set/remove spec，未执行；测试目录覆盖五类型，不包含AcademicGrade或假学年，不冒充生产目录交付。

前一完整轮139312固定候选Console61dd9b3，不含UC016，已终态78通过/16失败/40未执行，详情见[集中门禁](2026-10-30-console-integration-gates.md)。它不能证明本包成功，也未被新普通绿结果替换。下一步接专用ordinary USER、固定测试目录及真实专项，同时有界诊断UC015和旧会话隔离试验；完整goal保持进行中。

本包产品与普通测试已本地提交 **`31d0e38`**（`:sparkles: feat: add shared account profile editing`），没有push，原legacy保持e68851e。真实spec、测试目录与runner接线将以独立候选记录，不能把尚未执行的准备计入成功证据。

## 首次真实诊断

真实接线冻结 `cbe165d`，轮次35230两端各一条set/remove专项：Admin普通USER通过，五类型设置、明确删除、未涉及字段保持、权威读回、原Session与零App请求均通过。Developer在直接访问 `/account/profile` 的匿名登录入口失败，未执行资料命令；已定位到产品边界只给返回首页链接，正在增加本页就地登录，不能借Admin成功声称双端都通过。完整结果、固定静态hash和清理见[集中门禁](2026-10-30-console-integration-gates.md#恢复后的四项诊断35230)。AcademicGrade不在本次真实覆盖中，五类型测试目录也不代表生产字段目录已交付。

就地登录修正已本地提交 `a9bee4b`：复用DeviceLoginPanel，只更新当前Session Query；账号页仍不挂载Rail、不跳应用首页，应用页面原登录边界不变。六文件集中组件79/79与Developer strict通过（本人资料Host8项），初次strict的新测试误传Testing Library不支持的exact选项已修正。UC016补充匿名直入语义，产品未改任何登录协议；真实双端复验仍待结果。
