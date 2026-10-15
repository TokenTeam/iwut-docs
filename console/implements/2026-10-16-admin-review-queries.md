# UC006–007：Admin 审核查询首阶段

状态：`ACCEPTED / IN_PROGRESS`，2026-10-16。按用户持续授权自行接受完整[UC006](../use-cases/UC-CONSOLE-006-review-application-versions.md)与[UC007](../use-cases/UC-CONSOLE-007-review-application-profiles.md)，先交付队列/详情，不缩减批准、拒绝、并发决定与结果未知恢复的最终范围。

## 权威与当前依赖

查询权限、队列资格、不可变snapshot、分页及一致性分别由[App UC030](../../app-center/use-cases/UC-APP-030-query-application-version-reviews.md)、[UC031](../../app-center/use-cases/UC-APP-031-query-application-profile-reviews.md)拥有。完整决定的缺口继续由[Version决定准备](../query-contracts/version-review-decision-readiness.md)及UC007依赖表跟踪：Version完整正式检查定义未核验，两个决定尚无ADMIN surface，Profile APPROVE缺Reviewer可读的当前公开指针/对照内容。不得复制后端规则、发明政策解释或借管理查询越权补齐。

固定API仍为`a5d504c058c62cd91be451074d21608d69789918`，只增加审核查询及其依赖Proto生成输入。Gateway工作区四个查询已有ADMIN声明，但不是镜像验收；本包须重新pull已发布latest验证实际四路由及混合认证链，不能根据相邻源码宣称运行时可用。

## 本阶段功能决定

- Admin会话入口面向获授权的审核人员/平台管理人员，不要求Reviewer先成为Developer或平台管理员。页面入口不是授权投影，每次请求继续由真实Session→USER身份链检查精确权限。
- 两个独立入口`/reviews/versions`、`/reviews/profiles`；详情路径分别为`/reviews/versions/{applicationId}/{versionId}/{reviewId}`、`/reviews/profiles/{applicationId}/{profileRevisionId}/{profileReviewId}`。三元ID逐项校验；不补查Developer管理面或Auth个人资料。
- 队列固定pageSize20，使用显式上一页/下一页替换整页而非累计跨时点拼接。applicationId可选精确筛选，仅合法UUID进入请求/URL；筛选、刷新、Session和能力attempt变化均回第一页。token仅存Query内存，不进入URL或持久存储；前页token栈不代表冻结快照，每页显示原asOf。
- 两类队列保留全部冲突项及正式原因；Profile队列没有submittedBy，不能为了统一表格补查或推断。空队列、权限不足、资源不存在与请求失败分开表达。
- 详情审核材料只能来自review.snapshot；当前Application/Version/ProfileRevision上下文、source revision、attempt、提交事实、当前policy/required IDs、eligibility/asOf、终态decision和Version draftRestoration分别表达。大整数精确保留。历史终态不能被当前DRAFT/ACTIVE policy覆盖成待处理。
- launchUrl、OAuth回调、description、icon和reason均为惰性纯文本，不外链、不嵌图、不预取。Profile null、空字符串和空白原文分别保留；google.protobuf.Value严格接受契约规定的形状，不把任意JSON当安全详情。
- 本阶段没有批准/拒绝表单、决定请求、写按钮或政策ID猜译。PENDING明确说明“审核决定尚未接入”；无冲突不表达为“已获批准资格”。未知policy可原样读取版本和ID，但不能因此开放决定。终态如实显示已有结果，不提供第二Publish或资料恢复。

## 私有读取与失效决定

Admin Version和Profile为两个独立capability，不复用Developer按App清理的scope。Query包含Admin Session binding/generation、capability attempt和filter/三元目标；不持久化私有响应。Session明确失效沿用按代清理，仅影响Admin，不清Developer Cookie或设备。

精确权限不足403先遮蔽并回收当前Session的该capability队列和详情；另一审核能力保留。迟到成功不能写回已退场attempt。只在用户明确重新读取/重新进入时创建新attempt，不建永久黑名单或自动循环；恢复后的旧权限错误不能清新attempt。详情404只退场该三元目标，不能伪称整项权限被撤销。Session类错误先按已有会话恢复分类；其它明确401/403亦失败关闭，但不清有效Session。

400或完整畸形成功是当前Query协议退场：清除捕获Query实例的数据，后续503不复活旧内容。网络、成功正文断流、5xx保留同上下文已核验数据与其原asOf并标旧快照；没有旧数据则只显示失败，不伪造空页。变换filter/目标/Session后不借用旧上下文数据。生产页面键盘可访问，错误/拒绝有明确状态和焦点恢复，不把原始服务错误正文渲染/记录。

## 分层验收与边界

先实现并测试生成client、严格投影、两类页面与能力隔离；组件用typed fixture，不记为真实业务交付。Edge检查必须增加四条ADMIN查询，验证未获得Developer同源surface、缺Cookie/伪造header/认证上游不可用失败关闭，不能误落静态fallback。

真实浏览器使用已发布Auth/App/Gateway latest与隔离Mongo。正式注册、bootstrap与grant建立真实角色，不seed Auth权限。读取fixture可以准备PENDING/终态/冲突/分页事实，但须校验validator/引用/当前与snapshot分离，不能当Submit/Decide命令证据。真实授权至少覆盖双Reviewer、单项权限交叉、无权限平台治理者/Developer、revoke后新请求拒绝、regrant后明确恢复及Session保持；测试过程的治理命令不是生产UI。

首阶段实现及专项通过不能关闭完整UC006/007或原App错误头门禁。验证仍包含普通测试、strict、固定生成漂移、生产build、fixture浏览器、Edge和真实镜像；最终完整门禁继续无参数运行，不能删旧缺头断言。需要新的后端权威决定时只记录最小缺口，不自行改后端或跨chat要求其他agent实施。

## 实施记录

本次先接受设计并开放上述读取实现。实际代码、红绿证据、镜像digest、真实结果与清理将在完成后追加；当前不登记任何新增功能为已实现。
