# UC002–005：真实管理权转让与私有读取回收

状态：`ACCEPTED / IN_PROGRESS`，2026-10-16，按用户持续授权自行决定。落实已接受只读用例，不增加业务写UI、Console写路由、Reviewer权限或UC006–007。

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
