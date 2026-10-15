# UC002–005：真实管理权转让与私有读取回收

状态：`ACCEPTED / IN_PROGRESS`（前端已实现，真实镜像响应头门禁未通过），2026-10-16，按用户持续授权自行决定。落实已接受只读用例，不增加业务写UI、Console写路由、Reviewer权限或UC006–007。

## 已证问题与决定

新增组件回归已复现：Application详情先成功，同Session刷新404后统一错误出现，但旧详情仍在DOM和Query data；现有gcTime:0不解决仍挂载observer的错误保留。其它Version/Profile读取及Tester兄弟请求继续补回归，不把静态相似代码当已执行证据。

采用[本次私有读取边界](../query-contracts/private-read-boundary.md)：Session错误走既有路径；其它明确401/403/404终止当前页面attempt、先遮蔽/卸载，再取消并清精确旧Query，旧成功不能回填。明确重读/重新进入才创建新attempt。子资源404不永久否定整个Application；关联缓存可保守丢弃，Session不注销。网络/5xx可保留当前上下文已读快照但必须标旧asOf；从头重置分页与同key刷新分开表达。

## 真实镜像矩阵

1. 隔离账号A/B通过真实注册、设备证明、Developer申请和Create建立Application；不把普通注册或Developer资格当Reviewer授权。Node仅在本轮内存保留各自测试私钥/Session，不从浏览器提取钥匙/上游token，不签假USER身份，不返回材料给control/fixture/日志。
2. Application必须真实Create以建立正式creation quota；仅Version/Profile/Tester附属读取模型由validator约束的受控seed准备，不冒称其创建/审核/加入命令已验收。随后通过真实归档命令建立ARCHIVED状态，默认管理列表仍可见。
3. B在转让前对相同深链接统一不可访问但Session仍有效。A在Application、Version列表/详情、Profile列表/详情、Tester实际页面先取得成功投影；通过真实A发起/B接受转让（非数据库改adminId），A各页随后明确404必须移除旧内容/计数/指针/分页，Session binding/generation保持且无DELETE。
4. Tester一路真实成功先在途，转让后另一路确认404：三区域隐藏并取消旧请求，丢弃迟到结果；Abort可能使代理gate直接DROPPED，不能强求消费被取消正文或伪装请求已交给React。忽略Abort的Promise由组件测试补直接Query证据。
5. B接任后从真实页面读取保留历史。真实转让应撤销ACTIVE邀请链接（ADMIN_TRANSFER），但保留ACTIVE Membership；不seed回ACTIVE以迎合旧断言。A默认列表实际重读不再包含该App，B仍能读ARCHIVED；no-store响应与Session仍有效分别验证。

测试准备命令走本轮Gateway内部端口和真实Auth/App，扩充固定API `a5d504c058c62cd91be451074d21608d69789918`生成输入，不改输入版本或手写第二套业务DTO。Node setup bundle独立临时目录，不作为静态资源发布；只开启本轮Developer申请/恢复ready开关。loopback随机bearer control仅接受精确固定fixture的转让动作和空body，不接受任意账号、ID、URL、token、数据库参数。

## 门禁与非目标

先红再实现，普通测试、strict类型、生成漂移、fixture浏览器、Edge、报告隐私及无参数全量真实镜像套件均需通过；focused只诊断。每轮拉取backend latest，轮内固定并记录digest，不编译相邻后端。记录失败、资源清理、代码与docs提交，legacy不变。

本包不关闭UC001/fencing或UC002–005完整矩阵；资格下降、独立Reviewer/运维、CLOSING/CLOSED、四状态/多页历史/413和Cookie硬上限可用性继续分包。新增读取边界不是后台推送撤权：在获得明确新拒绝前，只能呈现已标时间的上次读取，不承诺客户端获知未送达的权限变化。

## 实施中证据与当前镜像缺口

先红后绿的组件回归已经执行：第一条Application详情404用例复现旧DOM/Query残留，随后四页面组44项中12失败（6个明确拒绝、6个临时错误旧asOf提示）。最终扩至四组57项全部通过，另11项核心边界回归覆盖忽略Abort的旧Promise、精确Query实例清理、其它App/Session保留、focus/reconnect不解锁、显式重读重置本地页、子404返回概览及多页各自asOf；Developer全部93项通过。strict类型、生成漂移、fixture浏览器8通过/4个Admin非目标skip，以及Edge接线检查均通过。此前一次并发开发期间的类型检查曾失败（测试unknown类型及realdriver间接引入TSX），已分别修正，并把attempt/context/client封装拆为纯TS模块后正常命令通过；不靠给real测试打开JSX绕过。

首次focused真实镜像运行成功完成注册、真实Developer申请、DEVICE证明、Create、附属seed与真实Archive；B转让前实际Application深链接返回404，但缺少约定的`Cache-Control: private, no-store`（连no-store也不存在），故新断言失败，尚未执行转让矩阵。不删除该断言、不把fetch的request cache选项当response no-store证明，也不在Console增加正文代理或重复Gateway业务路由来掩盖后端缺口。后续将no-store保留为soft失败断言以在同轮收集剩余真实矩阵，套件仍必须exit1，不能把其余交互执行完算门禁通过；需要App对应错误路径修复并发布新镜像后再通过无参数全量门禁。

本轮镜像输入（每轮均重新pull latest，轮内固定）：App `sha256:6f20c469a0e9566e045a5966fd51d81ce0b1293c650e2b277fa62bc3b5a3579b`，Auth `sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3`，Gateway `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9`；基础Mongo `sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3`、Traefik `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0`。未编译后端或修改其工作区。

第二次focused通过B六种深链接实际404及统一不可访问UI，原B Session仍有效；除保留的no-store失败外，还遇到测试自身的归档文本定位歧义（筛选控件与列表徽标同文），已将断言收窄至“我的Application”列表，不改变产品行为或取消归档断言。生产读取边界与组件回归已单独本地提交`68f5101`；普通全仓366项Vitest及28项Node测试通过，但不以此关闭真实门禁。

第三次focused实际完成A先成功的六页面、真实发起/接受转让、A各页404后全部私有内容退出、Tester旧200在途被取消、A显式新attempt仍404、A/B默认列表反转且B可见归档、B六页面历史成功读取及ACTIVE Membership保留；A/B Session摘要保持且无DELETE的前置检查通过。持续捕获到Application详情404缺no-store三次（B接任前、A失权后、A显式重读），其它已观察读取未报此缺口。该轮仍失败：除3条保留的响应头断言外，最后“链接状态”选择器使用exact文本，与含内嵌option文本的label不匹配；已按既有真实spec采用同一label的非exact定位，未删除邀请链接ADMIN_TRANSFER历史断言。正在执行修正后的无参数22项真实套件，不把focused的部分执行写成完整通过。

无参数全量终态：22项中21通过、1失败，8.2分钟、exit1。旧21项全部通过，包括双surface context32、双副本重启、Mongo故障/提交回执丢失、旧私有业务/Session错误/清理回执、真实UI Begin/Complete/Recover未知结果和等待取消。新增转让用例失败包含3条明确no-store断言，另有一处测试自身strict定位：同一joinLinkId同时出现在Membership来源和链接历史；已限定至“邀请链接记录”列表。该轮已实际验证ACTIVE链接被真实转让撤销、revocationReason为ADMIN_TRANSFER、旧MANUAL撤销历史仍在；最后DOM与最终Session断言要以修正后的focused诊断为准。对应固定API生成/真实准备与spec为本地提交`5e0a76e`，定位修正另行提交。该全量轮的容器和网络已检查无残留；完整门禁没有通过，不能用下一次focused替代。

最终focused诊断终态：新spec完整执行23.0秒，1失败、exit1，错误清单仅3条Application详情404缺no-store；没有其它断言失败。真实转让与六页回收、Tester在途200退场、B接任后的六页历史、ARCHIVED默认可见、原ACTIVE链接真实撤销/ADMIN_TRANSFER和保留MANUAL历史、ACTIVE Membership保留，以及最后双方Session完全不变/无DELETE均已执行通过。当前代码strict real types与diff检查通过；仍需App发布修复后重新pull latest并运行无参数完整套件，本包不得标IMPLEMENTED，也不关闭上层UC/fencing。

已向用户请求授权通知App agent修复并发布镜像，未自行修改/编译App源码或跨chat派单，未推送本轮未过完整门禁的Console提交。legacy保留`e68851e343bd0e077e5ccd0b680fe6813216ced0`，已检查本地与远程一致；测试临时容器/网络清理后再交接。当前是明确的外部镜像契约缺口，不以反复运行相同镜像或删除响应头断言解决。

后续[资料分页与预算错误](2026-10-16-profile-pagination-and-budget.md)增量后的无参数完整门禁已执行完25项：24通过/1失败（8.4分钟），转让用例完整执行至最终双方Session不变/无DELETE，唯一错误清单为上述3条Application详情404缺no-store；测试定位问题已不再出现。用户通知Gateway CI完成后重新pull Gateway/App latest，digest仍与本页记录相同，缺口未解除。本包继续IN_PROGRESS，不将独立资料矩阵通过视为本包已完成。

随后[Tester分页与正文断流](2026-10-16-tester-pagination-and-privacy.md)增量后的无参数完整门禁终态为29项中28通过/1失败（8.6分钟），转让用例仍仅上述3条no-store断言失败；全部其余场景通过，未删断言或借其它包关闭本包。实际Auth/App/Gateway latest digest未变，本包仍等待App发布对应错误响应头修复。完整轮次容器和网络已核对清理，无后端源码修改或编译。

[Version分页与正式错误码恢复](2026-10-16-version-pagination-and-recovery.md)增量后再次无参数执行完整门禁33项：32通过/1失败，8.9分钟、exit1；新增Version4项及全部其它场景通过，转让用例完整执行至双方最终Session不变/无DELETE，错误清单仍只有上述3条Application管理详情404 no-store断言。三个业务latest digest未变化，仍不删断言、不推送或关闭本包；本轮容器/网络已核对清理，等待App对应修复发布。

[保留生命周期读取矩阵](2026-10-16-retained-lifecycle-read-matrix.md)增量后的无参数完整门禁终态为36项中35通过/1失败（9.9分钟），新增三阶段及原其它场景全部通过，转让用例仍仅同3条404 no-store断言失败。实际密码限流按header等待后完成同一注册，没有调高Auth限额或改变业务响应；digest未变，资源清理/本地保存，外部App修复依赖仍未解除。
