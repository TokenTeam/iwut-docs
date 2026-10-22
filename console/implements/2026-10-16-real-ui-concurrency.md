# UC001 真实 UI 迟到与私有视图隔离验收

状态：`ACCEPTED / IMPLEMENTED`，按用户持续授权自行接受。承接ADR005、Session v2接线契约和报告隐私护栏；不修改Auth/App/Gateway，不引入业务写操作。

## 范围与决定

1. 实际React邮箱Begin等待期间必须仍能由键盘取消/返回设备入口。取消立即隔离旧回调、清理一次性表单并中止本地请求，尽力发送原票据cancel；只有实际BFF确认才主张服务端取消。取消后的旧挑战不得推进新表单，新意图使用自己的root。取消不是Auth邮件撤回，不因邮件已发就声称未发送。
2. 用真实SMTP、真实双BFF和透明故障转发器安排旧Begin响应/外呼迟到。验证实际取消/重新开始，挑战、错误、按钮、Session及真实业务身份不受旧结果影响；不为测试关闭产品Abort，也不把浏览器中止后未消费旧响应夸大成React一定执行了旧回调。
3. 实际Developer私有页在同context另一标签页建立新代后，旧成功body或旧SESSION_INVALID不得被旧页面消费，更不能注销新代或回填旧私有DOM。透明代理只延迟原始响应，不伪造JSON/状态/身份；业务身份通过真实Gateway/App读取确认。登录仍由真实协议/本机non-extractable钥匙完成。
4. 私有Query严格按binding/generation分区，离开旧身份时取消并移除旧scope；旧异步回调不得清除新scope。以组件/QueryClient测试直接检查内存移除，以真实浏览器导航、渲染和网络重读验证不复用旧结果；不为观测缓存给产品暴露调试对象，不把间接DOM证据等同直接检查所有heap。

必要修复必须先补失败回归；认证材料不进入日志/报告，所有real spec使用共享隐私test。fixture仅准备读取数据，不代表业务写命令已验收。published latest每轮重新拉取并登记digest，所有故障控制仅本轮loopback/bearer设施，结束回收本轮资源。

业务迟到响应包含Gateway ForwardAuth产生的401，不能仅在App服务前拦截。测试设施因此在浏览器与真实Traefik之间增加仅本轮的透明HTTPS转发器：两段均真实TLS，上游显式校验本轮证书与固定SAN，不关闭验证；Host、状态、正文与Cookie不改写。故障只按固定proxy/method/path匹配一次；不加入产品路由/调试接口。另给私有视图准备两个专用注册账号和一条只读Application，并以固定专用账号的受控Auth Session撤销fixture产生真实SESSION_INVALID，不允许任意账号/数据库写入参数。

## 完成边界与门禁

实现上述交错后联合重跑所有既有真实测试，不删除或跳过旧用例以换取全绿；运行strict typecheck、普通回归、production build和隐私门禁。新增交错的实际观察和剩余未证项须分别记录。

本包不处理context 32次签发后的显式重建入口，不把局部交错覆盖当作UC001全部完成；UC001/fencing继续IN_PROGRESS/OPEN。

## 实现发现与证据边界

邮箱返回按钮原先对所有pending禁用，已有组件测试也以“等待期间不可取消”为预期。按BR-CSE-005/008修订该预期，先取得键盘取消回归失败，再允许BEGIN/RESEND期间返回，同步abort/隔离/清一次性状态并尽力取消原票据；COMPLETE/RECOVER等待期间的按钮互斥本包未改变。额外覆盖本地密钥准备尚未结束及重发等待时取消，设备钥匙不删除。

全部现有私有页面9类Query已经显式配置`gcTime: 0`并消费取消signal；不能把本次集中清理描述为此前正常页面默认保留五分钟或已发生身份泄漏。Provider新增按旧binding/generation统一取消和移除，是不完全依赖页面配置的安全加固，直接回归使用无observer的`setQueryData`/`fetchQuery`，另证明StrictMode重放仍可正常读取。只覆盖登记的9类root，不声称清空整个heap。

旧错误恢复在等待`cancelQueries`后已有最终代检查，原本能阻止旧authority读取覆盖新Session；本次在发起该读取前再检查一次，仅消除新代已胜出后的多余读取，不夸大为已复现的身份覆盖漏洞。

首轮完整镜像验收实际为13通过、2失败、1因serial前项失败未运行（exit1，约5.6分钟）：新增私有成功body交错及Begin取消case失败，不能将既有13项当作新增用例通过。只做已知spec路径的focused诊断时runner会明确标记非完整门禁；修正后仍必须无参数联合重跑全部。

报告隐私护栏只保留测试定义位置，导致上述失败缺少具体断言行。诊断修订仅允许从原stack提取精确匹配可信testInfo.file的有界正整数line/column；静态错误标识、错误数量/状态、无DOM/任意原文/cause的约束不变，无有效frame就退回定义位置。先用合成canary再次验证安全位置和全产物保密，再用于focused真实诊断，不靠恢复原错误文本或截图定位。

安全定位后的focused诊断再次2失败/1未运行，指出两处均失败于测试调用Playwright `response.json()`，不是UI断言：私有transport已正确取消过时代正文；keepalive cancel客户端仅消费`response.ok`，DevTools不保证保留其未读正文。修正的是测试观测假设，不改变产品fence/Abort，也不恢复正文消费。私有A的真实列表先在原UI读取，SESSION_INVALID先由同A代同路由的真实请求确认，再hold相应200/401刷新；新B后仅观察被放行的HTTP状态、DOM及真实B重读。cancel以精确入口成功HTTP及原票据为服务端确认，不索取不保证可见的keepalive正文。

修正观测后的focused为3项全通过（约16.2秒，完整命令退出0），仅证明新增spec，不代替最终完整16项验收。其前置同样重新拉取三个backend latest、生产构建、真实注册/SMTP及隐私回归，无后端源码或响应fixture替代。

## 2026-10-16 最终验证

无参数 `pnpm test:real` **16项全通过**（浏览器阶段约5.0分钟，无重试/跳过，完整命令退出0），包含全部原13项和新增3项；不是focused结果外推。前置strict real/privacy类型检查、合成隐私回归与production build均通过。

| 新增真实证据 | 实际观察 |
| --- | --- |
| Begin等待取消/新意图 | 原Auth已真实投递且200响应被hold；键盘返回使原请求中止，精确原票据cancel HTTP200确认；新邮箱/新root真实UI登录成功，旧操作不能推进表单或改变Session，原邮件不重复投递，本地两钥匙不可导出 |
| 旧成功与B交错 | 原A列表在实际UI可见，刷新200被hold；另一标签页真实设备登录B后放行，原A名称没有再次进入DOM；UI协调到B并从真实Gateway/App读取空列表，权威Session仍为B |
| 旧SESSION_INVALID与B交错 | 固定A外部失效fixture后，同A代同路由真实401/SESSION_INVALID确认，再hold UI刷新401；B登录后放行，旧页不发清理B的DELETE、不回填A，真实B列表和权威Session正常 |

所有轮次backend latest digest保持：Gateway `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9`、Auth `sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3`、App `sha256:6f20c469a0e9566e045a5966fd51d81ce0b1293c650e2b277fa62bc3b5a3579b`。每轮先拉取latest再固定本轮image ID，不读取/编译相邻后端源码，没有改三个后端。

其它门禁：285项Vitest（UI28、Developer51）、25项Node回归（HTTP(S)16/Mongo6/有界子进程3）、全量strict typecheck、fixture Playwright 8通过/4按Admin surface跳过、repository independence和diff检查通过。隐私合成子流程始终保留4失败/1通过、exit1，四处实际断言/API位置得到安全定位且stdout/stderr/全部临时产物无随机canary/ARIA YAML。71份brief与367行registry检查通过。本轮已拥有的容器、网络和服务子进程无遗留。

Console提交分离为：`498bcaf`（Begin等待取消）、`cdd1543`（统一私有scope清理）、`a58ed62`（安全失败位置）及`a79506b`（真实UI并发设施/验收）；legacy分支仍保持原`e68851e`，没有移动备份。

## 保留的下一步

UC001/fencing继续 `IN_PROGRESS / OPEN`。本包不覆盖Complete/Recover等待期间的显式UI取消；旧SESSION_INVALID已经发出DELETE、其回执仍在途时，新代在同一React QueryClient建立的实际UI回调交错仍须补（已有组件及协议证据不能替代）。context 32次签发上限后的显式重建仍需独立设计；其它私有页/权限变化全矩阵也没有因Application列表的两项交错而完成。
