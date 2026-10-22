# UC001 提交/恢复等待取消与旧清理回执

状态：`ACCEPTED / IMPLEMENTED`，按用户持续授权自行接受。承接[真实UI并发](2026-10-16-real-ui-concurrency.md)，落实UC001 BR-CSE-005/008与Session v2现有取消/按代清理语义，不改变Auth/App/Gateway业务规则。

## 决定与范围

1. 邮箱COMPLETE/RECOVER等待时同样允许键盘返回设备入口；普通本机设备登录等待也提供明确取消。同步abort、隔离回调、清一次性状态并尽力取消当前intent，设备钥匙保留。重复提交仍互斥，不以禁用取消掩盖并发问题。
2. Auth可能已提交，取消不表示邮件/凭据/Auth Session撤回，也不保证通知送达。只有精确原票据cancel成功HTTP才主张BFF确认；原root或恢复后的当前root都须按真实票据取消，不能将旧票据误用于新root。失联时下次进入读取权威Session；不自动重试Complete或生成钥匙。
3. 真实UI验收在BFF完成EMAIL/DEVICE后的201响应处hold，验证提交等待取消后SIGNED_OUT/真实业务401，保留同一non-extractable钥匙并经显式设备登录恢复；另先真实EMAIL响应丢失，再于恢复DEVICE成功响应在途时取消，验证新恢复root的取消。保持产品Abort，不强求DevTools读取已取消或keepalive未消费的正文。
4. Developer公共header提供同源“返回开发者工作台”链接，以真实SPA导航返回Session入口，不增加注销/账号切换语义。旧SESSION_INVALID已发送按A代DELETE且服务端清理成功、回执仍hold时，另一标签页登录B；旧页面经该链接读取B，再进入私有页取得B查询结果。放行旧DELETE回执后，同一页面文档/QueryClient不得被旧回调注销、导航或清空；B真实业务仍成功，旧A不回填。

不为测试暴露产品QueryClient。真实DOM/网络与组件内存证据继续分层；header链接不是刷新整个文档，需验证文档标记不变、真实Session重读以及新B视图不发生额外清理/意外重读。测试控制仅本轮透明代理/固定fixture，不注入Cookie/JSON、不改服务时钟或编译相邻后端。

## 验证及完成边界

必要产品变更先取得失败回归；运行普通测试、strict typecheck、隐私门禁及全部真实镜像套件。focused只作诊断，不能替代无参数全量结果。记录latest digest和本轮资源清理。

本包不设计context 32次上限后的显式重建，也不宣称其它私有页/权限变化全矩阵完成，UC001/fencing继续IN_PROGRESS/OPEN。

## 实现中的回归证据

取消组件回归先取得4失败/27通过：普通设备缺少取消入口，邮箱COMPLETE/RECOVER的返回按钮禁用。按本包开放取消后UI31项通过，仍同步阻止重复提交；回归检查立即abort、不等cancel回执、恢复后的当前票据、迟到成功不触发旧onEstablished，以及设备钥匙不删除。Developer header键盘导航也先因缺少链接失败，新增同源Router Link后Developer52项通过；测试fixture的同一Session到期值改为一次性固定，避免每次模拟读取无意续期。

普通门禁当前289项Vitest、28项Node及全量strict typecheck通过（含新增命令输出3项回归）。生成输入漂移检查与fixture浏览器8通过/4项Admin范围跳过通过；真实镜像验收另行记录，不用组件回归替代。

首轮focused为4通过/1失败（exit1，约1.8分钟）：原私有视图两项及新增取消两项通过，旧清理回执case在90秒期限超时；finally继续使用已到期的Playwright request fixture又产生清理错误。此时尚不能区分产品交错失败或测试同步点问题；先补静态阶段定位和有界等待，不能把未知超时当作已证实身份漏洞，也不删目标断言。

再次focused在镜像inspect阶段因空输出JSON解析退出，尚未启动业务容器/浏览器。命令收集器原在child `exit`立即resolve，不能保证stdio已读完；改为`close`并新增退出后尾部stdout/stderr、UTF-8分片、显式allowFailure与spawn error回归。此为测试设施修正，不据此归因Gateway镜像或产品登录。

有界定位后focused为2通过/1失败：新case已在同一文档取得B摘要/空列表且放行旧204，停在`Response.finished()`。产品clear只消费`response.ok`而不读正文，不能用DevTools完成通知证明JS回调执行。本包接受仅在该测试页被动观察原生fetch：原参数/原Promise/原Response原样返回，不读body、凭据或Cookie，只记录精确DELETE路径的HTTP状态和次数。以原fetch成功204及后续真实浏览器任务屏障确认回调机会，再检查同页B、实际权威/B业务及无额外请求/导航；不暴露QueryClient、不注入响应，也不靠固定睡眠判成功。

修正观测后的private-view focused三项全通过（浏览器约19.2秒，完整命令exit0）；旧DELETE204已由原生fetch确认，同文档B空列表/权威/真实业务保留，无额外清理/导航/重读，随后显式UI刷新仍成功。没有为此修改产品Session回收逻辑。独立`edge:e2e`也通过本轮Gateway latest的九条Developer查询路由存在及BFF不可用时失败关闭。上述不代替无参数全量真实套件，最终结果另记。

## 最终联合验收

无参数`pnpm test:real` **19项全通过**（浏览器约5.2分钟，无重试/跳过，完整命令exit0）；包含原16项及新增提交等待取消、恢复新root取消、同页B建立后旧清理回执三项。前置strict real/privacy类型、合成隐私回归和production build通过。289项Vitest、28项Node、全量strict typecheck、生成漂移检查、fixture浏览器8通过/4项Admin范围跳过、`edge:e2e`及diff检查也通过。

本轮重新拉取三个backend `latest`，只在该轮固定image ID，没有编译相邻后端：

| 镜像 | 本轮digest |
| --- | --- |
| Gateway | `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9` |
| Auth | `sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3` |
| App | `sha256:6f20c469a0e9566e045a5966fd51d81ce0b1293c650e2b277fa62bc3b5a3579b` |
| Mongo 8.2.12 | `sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3` |
| Traefik | `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0` |

runner finally完成，复查无本轮容器、网络或BFF/测试子进程残留；`legacy`本地与远端仍为`e68851e343bd0e077e5ccd0b680fe6813216ced0`。未修改Auth/App/Gateway/API仓库，也未用报告隐私护栏隐藏失败状态。

本包只补上述交错，不覆盖context签发上限后的显式重建或全部UC002–005页面/权限变化矩阵；UC001仍IN_PROGRESS、fencing仍OPEN。
