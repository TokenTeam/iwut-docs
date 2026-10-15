# UC005：真实 Tester 分页、容量与最小披露

状态：`ACCEPTED / IN_PROGRESS`，2026-10-16，按用户持续授权自行设计并接受。落实[UC-CONSOLE-005](../use-cases/UC-CONSOLE-005-query-application-tester-management.md)及[UC-APP-037](../../app-center/use-cases/UC-APP-037-query-application-tester-management.md)，不新增管理写UI、REMOVED Membership入口、用户资料聚合或Reviewer权限。

## 决定

用专用真实注册账号、Developer申请及DEVICE证明，正式Create两个Application。主App准备25个ACTIVE Membership和同一Tester早先REMOVED episode，以及26条合法链接元数据（1 ACTIVE、25 REVOKED）；另一App为空态和同管理员跨App token对照。附属读取fixture仍经过现有Mongo validator/index，不修改ownership/quota/认证安全状态。等时间排序键使用不同规范小写UUIDv7，验证真实keyset而非只比较行数。历史fixture只证明读取，不冒称真实加入/轮换/移除命令已交付。

三个区域分别读取、分页和刷新。概览容量25与成员首批20不一致是合法跨投影，不从当前页计算人数；旧REMOVED episode不进入固定ACTIVE列表，成员可以引用已REVOKED链接。链接ACTIVE/REVOKED/ALL切换只重置链接页，成员页和概览不随之重置；全部刷新则分别回到三个首批，不假称原子snapshot。

Node闭包可通过正式精确DELETE撤销本包预登记ACTIVE链接，响应按固定API生成DTO验证，不发回浏览器或日志。固定loopback control只接受空JSON、固定动作，无ID/URL/正文参数；撤销后概览无当前链接但ACTIVE成员与容量保留。没有一次性join secret创建或恢复请求，不实现产品写入口。

## 错误与隐私

补齐成功响应解码分型：Tester三RPC的成功形状/fromJson错误统一为无正文、无cause的`ApiResponseError`，fetch TypeError仍是网络故障。已有region结果替换用于明确400/协议错误退场；不能让其被误判为网络而保留旧投影。明确错误不会因focus/reconnect自动重试，只有显式重读；只影响该区域，不清Session、其它区域或整App。后续503不能复活此前已退场内容，健康网络/5xx保留原asOf。401/403/404与Session错误继续沿用已接受私有读取边界。

真实响应检查private/no-store与白名单字段，不出现joinUrl/secret/tokenHash或隐藏createdBy/revokedBy/removedBy，不补查Auth资料。浏览器仅渲染opaque不可点击ID，无复制/导出/写按钮；分页token只驻留请求/内存，不进入前端路由、存储、日志或失败报告。真实同源协议探针验证跨查询种类、filter、App和篡改token的正式400；不称这些探针为产品会主动发送的请求。

## 验证与边界

先执行组件/API红回归，再实现分型及独立恢复；直接Query.state.data与真实DOM/网络证据分层，不宣称检查整个heap。focused仅诊断；完整门禁继续用无参数`pnpm test:real`拉取已发布Auth/App/Gateway latest并固定轮内digest。不得编译相邻后端或为通过测试放宽validator/响应头断言。

既有[Application详情404缺no-store](2026-10-16-management-access-loss.md)仍保留；本包不关闭完整门禁、UC001/fencing或UC002–005全部生命周期/资格矩阵，不以独立测试通过代替上层完成。
