<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-029 --spec tools/brief-specs/UC-AUTH-029.json -->
# Brief — UC-AUTH-029：管理下一次学年更新时间

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-029` 管理下一次学年更新时间 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-UPF-019`–`BR-UPF-023`（5 条） |
| 外部引用 BR | `BR-UPF-018`（来自 `UC-AUTH-005`） |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-center-api-routing.md`、`platform/contracts/trusted-identity-v1.md` |

## 遇到 brief 未覆盖的问题

本 brief 刻意不覆盖全部设计。按以下顺序处理，**不要自行发明业务行为**：

1. 先在 §未纳入本 brief 的源小节 找标题，命中则按锚点查阅对应源文件。
2. 仍无法确定，或发现两条权威规则冲突：**停止受影响的实现**，产出一条结构化 gap：

   ```text
   blocked: true
   authority: <BR-*/UC-*/ADR-* 的权威位置>
   conflict: <一句话描述歧义或冲突>
   options: <可选方案>
   suggested: <建议方案>
   ```

3. gap 由设计任务（读全量概述文档的那个角色）解决并更新权威正文后，重新生成本 brief，再继续实现。

## 用例正文

### 目标与范围

平台管理员在 Auth Center 中读取和修改“下一次 currentAcademicYear 增加一的时间”。读取返回当前学年和严格晚于读取时刻的下一次更新时间；例如服务端时间为 `2026-10-10` 且尚未有管理员修改时，缺省下一次更新时间为 `2027-09-01T00:00:00+08:00`。

管理员设置的是包含年份的完整未来 Instant，而不是不带年份的月/日规则。例如在 2026-10-10 可以把下一次更新时间设置为 2027-02-20；不能设置为 2026-10-10 当时或更早。到达该时间时 currentAcademicYear 增加一，其后更新时间按上一次更新时间在 `Asia/Shanghai` 公历中逐次 `+1 year`。

本用例拟替代 `AUTH_ACADEMIC_CALENDAR_FILE` 和任意开始/结束区间文件，使 UC005 的编辑 schema、ACADEMIC_GRADE 锚点及 UC028 的 UserInfo 年级投影读取同一 Auth 运行时设置。它不修改用户已确认的 profile、不批量迁移年级锚点，也不把学年更新时间解释为学校对个人学籍的验证。

首版不开放时区、直接设置 currentAcademicYear、按学院/培养阶段分别配置、临时停用、一次排队多个未来时间或直接编辑 MongoDB。字段目录在线管理、ApplicationUserStorage 和学校教务日历同步仍是独立能力。

本设计已经用户审核接受。UC005/028、资料查询契约和共享路由契约同步改用本时间表；由脚本生成实施 brief 后开始 API 与 Auth 实现。

### 参与者与依赖

- **操作人**：ACTIVE USER，持有 audience=`iwut-auth-center` 的有效可信 USER JWS，并在 Auth 当前权威记录中满足 UC021 的完整平台管理员资格。每次读取和写入都在线复核账号状态、账号版本和完整管理员集合。
- **Auth Center**：唯一保存学年时间表锚点、revision 和不可变管理审计；UC005/028 只消费其权威结果，不再各自加载文件。
- **普通用户与第三方应用**：不能调用管理 API。普通用户只通过资料 schema 观察当前 academicYear；第三方只在得到对应 scope 后观察派生的当前年级代码。

依赖 [UC021](../use-cases/UC-AUTH-021-manage-platform-administrators.md) 的平台管理员资格、[UC010](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md) 的 Auth audience 身份，以及 [UC005/BR-UPF-018](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-018) 和 [UC028](../use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md) 的年级消费语义。

本用例复用“完整平台管理员资格在线复核”作为管理授权，不新增 `auth.*.manage` 权限、不扩充 UC021 四项固定 bundle，也不把设置管理能力投影到 App audience、OAuth scope 或 consent。若未来需要把配置管理员从平台管理员中拆分，另立 UC 调整授权模型。

### 输入与输出

```text
GetAcademicYearSchedule {}

UpdateNextAcademicYearRollover {
  nextRolloverAt: Instant    // 必填；包含年份，严格晚于提交检查时刻
  expectedRevision: Int64    // 必填，正数
  reason: String             // 去除两端空白后 1..1024 UTF-8 bytes
}

AcademicYearSchedule {
  currentAcademicYear: Int32
  nextRolloverAt: Instant    // 严格晚于本次读取使用的 observedAt
  observedAt: Instant
  revision: Int64
  updatedAt: Instant
  updatedByAuthId: AuthId?   // 缺省基线为空
}
```

所有 Instant 使用标准 UTC 线格式；年度递推时先转换到 `Asia/Shanghai`，增加一个公历年并保留当地月、日和时分秒，再转换为 Instant。官方客户端可以只让管理员选择日期并提交当日上海时区 00:00，但服务端契约保存完整 Instant，不擅自截断时间。

缺省基线的 revision 为正数，规则等价于每年 9 月 1 日 00:00（Asia/Shanghai）更新。管理员第一次修改也必须使用 Get 观察到的 expectedRevision，不能用“记录不存在”绕过并发控制。

### API 契约

独立 package `auth_center.v1.academic_year_policy`，service `AcademicYearPolicyService`：

| 方法 | Auth HTTP 路径 | 成功响应 |
| --- | --- | --- |
| `GetAcademicYearSchedule` | `GET /v1/academic-year-policy/schedule` | 200，当前学年与下一次更新时间 |
| `UpdateNextAcademicYearRollover` | `PUT /v1/academic-year-policy/schedule/next-rollover` | 200，提交后的完整时间表 |

PUT 正文只提交 nextRolloverAt、expectedRevision 和 reason；GET 无正文、无 query。两种方法同时提供 HTTP/JSON 与原生 gRPC，并以精确 full method 加入鉴权表。Gateway 使用 SESSION 路由换取 audience=`iwut-auth-center` 的 USER JWS；Auth 不接受 OAuth access token、App audience JWS、service JWS、直接 Session 或请求正文自报 actor。

响应使用 `Cache-Control: no-store`。拒绝未知/重复字段、null、非法 Timestamp、query 和超过 16 KiB 的请求。管理入口使用独立的默认关闭开关和有界读写限额；入口关闭不影响系统内部按缺省或已保存时间表计算学年。

### 主流程

#### 查询

1. 验证可信身份和精确方法，在线复核操作人当前为完整平台管理员。
2. 捕获一次服务端 observedAt，在同一一致性边界读取并验证权威时间表。
3. 从已保存锚点向后推算已经发生的年度更新次数，得到 currentAcademicYear 和严格晚于 observedAt 的 nextRolloverAt。
4. 返回当前投影、observedAt、revision 和最后一次人工更新时间；查询不写回“推进后的下一次时间”，也不增加 revision。

#### 修改

1. 验证身份、nextRolloverAt、reason、expectedRevision 和入口限额，并在线复核完整平台管理员资格。
2. 在 Auth 事务中捕获提交检查时刻，解析现有时间表在该时刻的 currentAcademicYear 和下一次更新时间。
3. 要求输入 nextRolloverAt 严格晚于该检查时刻，并保证它及按规则计算的后续时间可以由契约 Timestamp 表达；等于或早于当前时间均拒绝。
4. 比较 expectedRevision。若输入恰好等于当前投影的下一次更新时间，作为 no-op 返回；stale revision 仍先返回冲突。
5. 真实变化保留当前 currentAcademicYear，把输入时间保存为“使学年增加到 currentAcademicYear + 1”的新锚点，并从它重新开始逐年递推；严格增加一次 revision。
6. 时间表、revision 和 append-only 审计在同一事务提交，返回以同一提交检查时刻投影的完整结果。

### 错误语义与运行约束

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| 缺少或无效可信用户身份 | `USER_IDENTITY_REQUIRED` / `INVALID_USER_IDENTITY` | 401 / UNAUTHENTICATED |
| 操作人不是当前完整平台管理员 | `ACADEMIC_YEAR_POLICY_FORBIDDEN` | 403 / PERMISSION_DENIED |
| Timestamp、revision、reason 或请求形状非法 | `INVALID_ACADEMIC_YEAR_POLICY_REQUEST` | 400 / INVALID_ARGUMENT |
| nextRolloverAt 等于或早于提交检查时刻 | `ACADEMIC_YEAR_ROLLOVER_NOT_FUTURE` | 409 / FAILED_PRECONDITION |
| expectedRevision 过期 | `ACADEMIC_YEAR_POLICY_CONFLICT` | 409 / ABORTED |
| revision 或学年/时间计算范围耗尽 | `ACADEMIC_YEAR_POLICY_REVISION_EXHAUSTED` / `ACADEMIC_YEAR_RANGE_EXHAUSTED` | 409 / FAILED_PRECONDITION |
| 管理入口限额 | `ACADEMIC_YEAR_POLICY_RATE_LIMITED` | 429 / RESOURCE_EXHAUSTED |
| 设置损坏、存储/审计失败或提交结果未知 | `ACADEMIC_YEAR_POLICY_UNAVAILABLE` | 503 / UNAVAILABLE |

入口使用独立 `AUTH_ACADEMIC_YEAR_POLICY_ENDPOINTS_ENABLED`，缺省 false；启用要求用户端点、身份签发和平台管理员能力可用。读写分别按已认证 actorAuthId 有界计数，建议缺省每分钟读 60、写 10；最终常量在接受后的 brief 固定。内部资料消费不受管理入口开关和管理限流影响。

### 验收场景

1. 全新数据库无需 calendar 文件即得到 9 月 1 日基线；2026-08-31 23:59:59 与 2026-09-01 00:00（Asia/Shanghai）跨越正确 academicYear，2026-10-10 的下一次更新时间为 2027-09-01。
2. 设置带年份的未来 Instant 后，当前学年不立即变化，到点只增加一；下一次时间为上次时间的上海本地公历 `+1 year`。
3. 等于/早于事务检查时刻、非法 Timestamp、无法表示下一年度和客户端试图提交 currentAcademicYear 均拒绝。
4. `2028-02-29` 后为 `2029-03-01`，以后保持 3 月 1 日；跨多个年度停机仍一次读取出正确当前学年和下一时间。
5. 到点前重新设置替换未来序列；与旧边界并发时按最终事务时间决定旧边界是否已经计入，不丢增量也不双增。
6. 完整平台管理员可 Get/Update；部分 bundle、旧 JWS、DISABLED/CLOSED、Reviewer/Developer/App 运维人员、SYSTEM/service/OAuth 身份全部拒绝。
7. stale revision、并发写、相同下一时间 no-op、revision/范围耗尽、事务重试和提交未知语义确定。
8. 设置与审计原子提交；失败注入不产生无审计设置或重复事件；自动跨年不生成虚假的管理员审计。
9. 多实例同时观察相同 currentAcademicYear/nextRolloverAt；不依赖本地文件、cron、进程重启或读时写回。
10. UC005 schema、年级 set 和 UC028 UserInfo 在同一观察时间得到一致 currentAcademicYear；用户锚点不批量改写，finalYear 封顶和不跨阶段规则保持。
11. 不需要年级的 profile/UserInfo 路径不因设置故障失败；需要年级时设置损坏、数据库故障或范围溢出整次失败关闭。
12. 实施后即使外部环境残留 `AUTH_ACADEMIC_CALENDAR_FILE` 也正常启动且完全忽略；缺省和管理员修改只来自 Mongo 权威时间表。

### 实现依赖与交付边界

实施需新增独立 API Proto、Domain/Port/UseCase、Mongo 时间表与审计 repository、严格 HTTP/gRPC transport、管理员在线 gate、默认关闭入口及真实副本集并发/故障测试。现有 profile 与 OAuth 服务的静态 `*AcademicCalendar` 依赖改为按请求读取的 schedule provider；部署和 README 删除文件说明。

UC005 BR-UPF-018 的“版本控制部署输入”和非目标、UC028 的依赖/故障描述、资料查询契约、设计说明、实现记录及部署配置随本次接受同步修订。使用 `tools/gen_brief.py` 生成 brief 后开始实现；设计接受不代表部署入口已经启用。

## 业务规则（UC-AUTH-029 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-029-manage-academic-year-rollover.md#br-upf-019 -->
### BR-UPF-019：权威时间表与九月一日缺省

Auth 只保存一条权威年度时间表锚点：锚点 Instant 到达时生效的 academicYear，以及配置 revision/更新时间。对任意读取时刻，服务端按 [BR-UPF-021](../use-cases/UC-AUTH-029-manage-academic-year-rollover.md#br-upf-021) 推算已经到达的边界数量、当前学年和下一边界；不需要为每年生成或保存区间。

系统初始化时幂等 provision 一条确定基线，使其语义等价于每年 `09-01 00:00:00 Asia/Shanghai` 增加学年：9 月 1 日边界到达后 currentAcademicYear 为该公历年，边界之前为前一公历年。全新系统在 2026-10-10 读取时得到 currentAcademicYear=2026、nextRolloverAt=`2027-09-01T00:00:00+08:00`。多实例并发只能形成一份相同基线。

缺少部署文件不再是错误，也不会关闭 ACADEMIC_GRADE。已 provision 的设置若缺字段、BSON 类型非法、revision 非正、锚点 academicYear/Instant 不可解释或后续计算溢出，则失败关闭，不能静默重置为缺省。

<!-- 权威位置: use-cases/UC-AUTH-029-manage-academic-year-rollover.md#br-upf-020 -->
### BR-UPF-020：完整平台管理员在线授权

Get 与 Update 都要求当前 ACTIVE USER 的 Auth audience JWS 满足 UC021 管理身份要求，并在权威数据库在线复核完整管理员集合、accountRevision 和 permissionRevision。仅持有 Reviewer、Developer、App 运维权限、Application 管理权、SYSTEM/service identity 或历史管理员 JWS 均不能管理设置。

本能力不增加第五项平台管理员权限，也不把 `auth.platform-admin.manage` 拆成可单独授予的“日历管理员”资格。这里授权的是 UC021 定义的完整平台管理员身份；时间表本身不进入用户 permissions、OAuth Scope Catalog、第三方 token 或 UserInfo。

<!-- 权威位置: use-cases/UC-AUTH-029-manage-academic-year-rollover.md#br-upf-021 -->
### BR-UPF-021：未来锚点与逐年推进

Update 输入的是下一次更新时间本身，必须包含年份并严格晚于最终事务检查使用的服务端时间。设置 2027-02-20 表示到该 Instant 时 currentAcademicYear 才增加一；设置动作本身不改变当前学年。管理员可以把更新安排到明天或多年以后，相应地提前或冻结下一次学年推进，系统不另猜测其意图。

每个实际到达的边界只使 currentAcademicYear 增加一。下一边界取上一个边界在 `Asia/Shanghai` 当地时间的公历 `+1 year`，不是固定秒数或 365 天。若一次边界是闰年 2 月 29 日，下一非闰年的边界规范化为 3 月 1 日，保留当地时分秒；之后从 3 月 1 日继续逐年增加，不在后续闰年自动回到 2 月 29 日。例如 `2028-02-29 00:00+08:00` 后依次为 `2029-03-01 00:00+08:00`、`2030-03-01 00:00+08:00`。

服务停机、没有用户请求或跨过多个边界不丢失推进：读取根据锚点和 observedAt 直接得到累计次数，不能依赖 cron 每年写数据库。实现应使用有界的公历年差计算与至多常数次校正，不能按停机年数无界循环。自动跨年不会增加配置 revision、updatedAt 或管理审计。

待下一边界到达前，管理员可以使用当前 revision 再次设置另一个未来 Instant；新设置替换整条未来递推序列，但保留设置时已经生效的 currentAcademicYear。设置与旧边界竞争时，以事务内最终检查时刻为顺序：旧边界已经到达则先计入当前学年，再以输入建立下一锚点；尚未到达则由新锚点替换。

<!-- 权威位置: use-cases/UC-AUTH-029-manage-academic-year-rollover.md#br-upf-022 -->
### BR-UPF-022：乐观并发与不可变审计

配置使用单一正数 revision。真实变更在事务内比较 expectedRevision 并严格增加一次；并发 Update 至多一个使用同一旧 revision 成功。输入恰好等于当前投影 nextRolloverAt 时，在 revision 匹配和未来时间校验后作为 no-op 返回，不增加 revision 或审计；stale revision 一律冲突。

每次真实变更写一条不可变审计，包含 eventId、可信 actorAuthId、reason、before/after nextRolloverAt、设置时 currentAcademicYear、before/after revision、occurredAt 和新的锚点 academicYear；不记录用户 profile、学生关联、OAuth token 或第三方读取内容。时间表与审计同事务提交，审计失败全部回滚；事务重试复用 eventId，提交结果未知返回不可用，客户端先 Get 再决定是否重试。

系统首次 provision 的 9 月 1 日基线以 `source=SYSTEM_DEFAULT` 标记，不伪装成人工管理员变更。基线一经建立，数据库记录被删除或损坏不得在普通读写路径静默重建；恢复需要受控运维和审计。

<!-- 权威位置: use-cases/UC-AUTH-029-manage-academic-year-rollover.md#br-upf-023 -->
### BR-UPF-023：消费一致性与文件配置退役

UC005 的 schema/current academicYear、ACADEMIC_GRADE set 锚定和 UC028 的 UserInfo 派生读取同一 Mongo 权威时间表，并使用各请求捕获的一次服务端时间。涉及 profile 写入时，时间表读取、账号复核和 profile CAS 位于兼容的一致性/事务边界；涉及 UserInfo 时，时间表与当前 profile、token/grant 生命周期事实保持既有一致检查点。不得由两个进程各自缓存文件产生不同学年，也不得在依赖读取失败时降级为 9 月 1 日或旧缓存。

实施本 UC 后，代码和部署文档移除 `AUTH_ACADEMIC_CALENDAR_FILE`、区间 JSON 及 `configs/academic-calendar.example.json` 的权威作用。系统尚未部署，不设计旧文件在线迁移或双读优先级；进程不再读取该变量。外部环境中即使残留同名变量，也不作为启动错误，只是没有任何效果。测试 fixture 可以构造时间表对象，但不能成为生产配置旁路。

Profile 不含 ACADEMIC_GRADE 或 UserInfo 没有相应有效 scope 时，业务请求仍不必读取时间表；管理 API 和初始化 schema 独立存在。需要当前学年的请求遇到设置损坏、数据库故障或时间计算溢出时失败关闭，不返回部分资料或猜测学年。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-AUTH-005`

<!-- 权威位置: use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-018 -->
### BR-UPF-018：当前就读年级的锚定与阶段内推进

用户设置 `education.current_grade` 时提交 stage、year、finalYear 和从当前编辑 schema 观察到的 academicYear；必须满足 `1 <= year <= finalYear`。stage 只允许 `UNDERGRADUATE`、`MASTER`、`DOCTORAL`。academicYear 不是用户可自由选择的资料：Auth 按服务端当前时间从 [UC029/BR-UPF-019](../use-cases/UC-AUTH-029-manage-academic-year-rollover.md#br-upf-019) 的权威时间表取得当前学年，请求值必须与之相等；不匹配按学年冲突拒绝并要求刷新。服务端在原子提交时写 confirmedAt。

对当前学年 C 和已保存锚点 A，当前有效年级序号为 `min(year + (C - A), finalYear)`。C 小于 A、差值溢出、stage/数值非法、confirmedAt 缺失或权威时间表不能解释当前服务端时间均失败关闭。时间推进只改变派生读结果，不批量改写 profile，不增加 profile revision，也不伪造一次新的用户确认。

推算只在原 stage 内递增并在 finalYear 封顶：本科最后一年不会自动变为硕士一年，硕士也不会自动进入博士或“已毕业”。跨阶段、休学、留级、延期或学制变化只能由用户明确重新设置；新设置以当时当前学年建立新锚点。客户端可在学年切换后提示确认，但不得代替用户静默提交。

学年时间表由 Auth 按 [UC029](../use-cases/UC-AUTH-029-manage-academic-year-rollover.md) 持有：缺省逐年 9 月 1 日，平台管理员只能设置带年份且晚于当前时间的下一次更新时间；到点后学年增加一，并从该时间按上海本地公历逐年推进。时间表修改不改写 profile 或既有年级锚点，也不是学校对个人学籍的认证来源。GetOwnProfile 返回保存的锚点值；当前 schema 返回同一次服务端观察时刻的 currentAcademicYear，官方客户端与 UC028 使用本规则计算同一有效年级。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-center-api-routing.md`：Auth Center API 路由与 HTTP 映射

#### 路由边界

2026-10-12 下表仅已交付基线。密码管理/恢复、默认密码登录已展开 UC033/034 DRAFT 和 auth-password-v1 草案，未注册真实入口；旧 REGISTER/BIND/凭据撤销、注销 Prepare/app.close Complete 须同步密码与防旁路门禁，新修订未实施，不提前启用或登记虚构公网清单。

与 [App API 路由](../../platform/contracts/app-center-api-routing.md) 一致，Proto 只声明服务内部 `/v1/...` 路径。
Gateway 公共入口前缀为 `/auth-center`，在转发前剥离；原生 gRPC full method 不加前缀。
UC004–009 的 HTTP 绑定由 Auth 后端实现。Gateway 的路由与认证编排按
[UC-GW-001](../../gateway/use-cases/UC-GW-001-authenticate-and-forward.md) 独立交付。

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/device-logins` | AuthenticationService/BeginDeviceLogin | DIRECT | 200 |
| POST | `/v1/device-logins/{operation_id}/completion` | AuthenticationService/CompleteDeviceLogin | DIRECT | 201 |
| DELETE | `/v1/sessions/current` | AuthenticationService/RevokeCurrentSession | DIRECT | 200 |
| DELETE | `/v1/users/me/credentials/{credential_id}` | AuthenticationService/RevokeOwnCredential | DIRECT | 200 |
| GET | `/v1/users/me/profile` | UserProfileService/GetOwnProfile | SESSION | 200 |
| PATCH | `/v1/users/me/profile` | UserProfileService/EditOwnProfile | SESSION | 200 |
| GET | `/v1/user-profile-schema` | UserProfileService/GetProfileEditingSchema | SESSION | 200 |
| PUT | `/v1/users/{subject_auth_id}/reviewer-permission` | ReviewerPermissionService/ManageReviewerPermission | SESSION | 200 |
| GET | `/v1/users/{subject_auth_id}/reviewer-permission` | ReviewerPermissionService/GetReviewerPermission | SESSION | 200 |
| PUT | `/v1/users/{subject_auth_id}/application-review-permissions/{permission}` | ReviewerPermissionService/ManageApplicationReviewPermission | SESSION | 200 |
| GET | `/v1/users/{subject_auth_id}/application-review-permissions` | ReviewerPermissionService/GetApplicationReviewPermissions | SESSION | 200 |
| PUT | `/v1/users/{subject_auth_id}/application-operation-permissions/{permission}` | ApplicationOperationsPermissionService/ManageApplicationOperationsPermission | SESSION | 200 |
| GET | `/v1/users/{subject_auth_id}/application-operation-permissions` | ApplicationOperationsPermissionService/GetApplicationOperationsPermissions | SESSION | 200 |
| GET | `/v1/academic-year-policy/schedule` | AcademicYearPolicyService/GetAcademicYearSchedule | SESSION | 200 |
| PUT | `/v1/academic-year-policy/schedule/next-rollover` | AcademicYearPolicyService/UpdateNextAcademicYearRollover | SESSION | 200 |
| DELETE | `/v1/users/me/application-user-storage/{application_id}` | ApplicationUserStorageService/ClearOwnApplicationUserStorage | SESSION | 200 |

原 `/v1/registrations` 和 completion 路径不注册，旧 BeginUserRegistration/CompleteUserRegistration RPC 返回 UNIMPLEMENTED；不重定向、不代为发起注册，也不因启用用户入口恢复旧方法。

UC011 是唯一注册入口，三个 DIRECT 路由的字段及 Session 例外见[邮箱协议 v2](../../platform/contracts/auth-email-binding-v2.md)：

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/email-bindings` | EmailBindingService/BeginSetEmail | DIRECT | 200 |
| POST | `/v1/email-bindings/{operation_id}/completion` | EmailBindingService/CompleteSetEmail | DIRECT | 200 |
| GET | `/v1/users/me/email-binding` | EmailBindingService/GetOwnEmailBinding | DIRECT | 200 |

EmailBindingService package 为 `auth_center.v1.email_binding`；额外受 AUTH_EMAIL_BINDING_ENABLED 开关控制，默认不启用。DIRECT 不得将空/坏 Session 清理成缺失 Session。

UC012 追加独立的邮箱登录 DIRECT 路由，见 [邮箱登录协议](../../platform/contracts/auth-email-login-v1.md)：

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/email-logins` | EmailLoginService/BeginEmailLogin | DIRECT | 200 |
| POST | `/v1/email-logins/{operation_id}/completion` | EmailLoginService/CompleteEmailLogin | DIRECT | 201 |

EmailLoginService package 为 `auth_center.v1.email_login`，由 AUTH_EMAIL_LOGIN_ENABLED 独立控制，默认关闭；两个入口拒绝任何已提供的 x-iwut-session。Complete body 为 code 和 proof，路径 operation_id 覆盖体中值。

UC013 追加两个必需有效 Session 的 DIRECT 路由，字段与认证约定见 [Developer 自助申请协议](../../platform/contracts/auth-developer-application-v1.md)：

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/users/me/developer-application` | DeveloperApplicationService/ApplyForDeveloper | DIRECT | 200 |
| GET | `/v1/users/me/developer-eligibility` | DeveloperApplicationService/GetOwnDeveloperEligibility | DIRECT | 200 |

DeveloperApplicationService package 为 `auth_center.v1.developer_application`，由默认关闭的 AUTH_DEVELOPER_APPLICATION_ENABLED 控制。Apply body 必须包含 developerHandle（例如 `{"developerHandle":"alice"}`）；GetOwn 无 body；均拒绝 query。DIRECT 保留 Session，不提前交换 Developer JWS。部署恢复就绪声明见 UC013，不由客户端提供。

ReviewerPermissionService package 为 `auth_center.v1.reviewer_permission`，四个管理/查询方法均由 Auth 校验 auth.reviewer.manage；路由 SESSION 身份本身不授予管理权。旧 reviewer-permission 路由继续只操作版本审核权限；新路由的目标 allowlist、消息字段和兼容规则唯一见 [UC004 API 扩展与兼容](../use-cases/UC-AUTH-004-manage-reviewer-permission.md#api-扩展与兼容)。新路由属于 2026-10-03 扩展，Auth/API/Gateway 实现与联合验收已完成，见 [交付记录](../implements/README.md#2026-10-03-uc004010-应用审核权限扩展)；生产部署仍沿用下述用户入口开关。

ApplicationOperationsPermissionService package 为 `auth_center.v1.application_operations_permission`，两个方法由 Auth 校验当前完整平台管理员资格；SESSION 身份本身和 App 操作权限都不能管理他人权限。精确 allowlist、共享 revision、邮箱恢复门禁及投影边界唯一见 [UC027](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md)。入口默认关闭；App Center 的暂停/恢复业务路由不属于本契约。

AcademicYearPolicyService package 为 `auth_center.v1.academic_year_policy`，两个方法由 Auth 在线复核当前完整平台管理员资格；精确时间、递推、并发和审计语义唯一见 [UC029](../use-cases/UC-AUTH-029-manage-academic-year-rollover.md)。管理入口由独立 `AUTH_ACADEMIC_YEAR_POLICY_ENDPOINTS_ENABLED` 控制且默认关闭；关闭管理入口不影响 Auth 内部消费已 provision 的时间表。

ApplicationUserStorageService package 为 `auth_center.v1.application_user_storage`。本人清除使用 SESSION 身份，`application_id` 仅由路径绑定，一次删除该用户与 Application 的 TEST/GREY/STABLE 数据，不返回应用 key/value。第三方读写另使用 `POST /v1/application-user-storage:batchGet` 与 `POST /v1/application-user-storage:mutate`；两者是 Auth 直接验证 opaque OAuth Bearer token 的 HTTP-only 资源端点，不经 SESSION 转换、不生成原生 gRPC 第三方方法。三个入口均由 `AUTH_APPLICATION_USER_STORAGE_ENABLED` 控制且默认关闭，精确语义见 [UC030](../use-cases/UC-AUTH-030-manage-application-user-storage.md)。

AuthenticationService package 为 `auth_center.v1.authentication`；UserProfileService package
为 `auth_center.v1.user_profile`。DIRECT 不代表无鉴权：各方法继续遵守设备证明、token 定向
撤销或有效 Session 的独立边界。SESSION 路由须经 Gateway 签发 `iwut-auth-center` audience
的可信用户 JWS；直接调用 Auth 时仅传 Session 不能访问资料接口。

Scope Catalog、UC002 内部批量 Developer 状态查询、SYSTEM principal 查询及 UC010 Session-to-JWS 签发
继续是内部 gRPC API，不增加 HTTP annotation，也不开放终端路由。

#### JSON 与载体

- POST/PUT/PATCH 使用 `Content-Type: application/json`，消息遵循标准 ProtoJSON；`bytes` 为 Base64，
  `int64` 响应为十进制字符串，Timestamp 为 RFC3339；JSON 字段推荐 lowerCamelCase。
- 审核与应用运维权限管理的 subject_auth_id 由路径绑定，写方法还绑定 permission，覆盖消息体中同名值。旧 reviewer 方法不接受新增 permission 字段；各自 allowlist 和错误规则见 UC004 与 UC027。学年时间表 PUT 只接受 nextRolloverAt、expectedRevision 和 reason，不接受客户端提交 currentAcademicYear。
- 设备登录的 Complete 消息体仅需 `proof`；`operation_id` 由路径绑定，覆盖消息体中同名值。
  邮箱 Complete 消息体为 code 和条件必需的 registrationProof，路径 operation_id 同样覆盖体中值。
  凭据撤销的 `credential_id` 和应用存储清除的 `application_id` 仅来自路径。GET/DELETE 不带请求体。
- 资料编辑保留消息体中的 `expectedRevision` 和显式 ProfileValue oneof，不引入另一套
  原始 KV 或 `If-Match` 协议。具体字段值类型仍按 UC005 校验。
- 不接受 query 参数作为消息、Session 或身份来源。Session、可信用户身份载体完全遵守
  [设备认证契约](../../platform/contracts/auth-device-session-v1.md#session-载体) 与 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)。
- JSON 解码拒绝未知字段、重复字段和冲突的 oneof 分支；资料编辑还拒绝 null 操作列表、条目及值分支，
  保留 UC005 的显式编辑规则。不把解析器的原始输入内容返回给客户端。
- HTTP 请求体在分配前有界读取：认证入口默认 16 KiB（由部署配置），资料编辑 128 KiB，应用用户存储固定 16 KiB。
  业务容量限制另行生效；暂不支持压缩请求体，返回 415。非 JSON POST/PUT/PATCH 同样返回 415。
- 所有响应设置 `Cache-Control: no-store`；撤销成功响应为 `{}`。错误 reason 复用 gRPC，
  HTTP 状态遵守各 UC：大小超限 413、限流 429、版本冲突/耗尽 409。
- 限流来源使用连接的 socket peer；不信任客户端的 Forwarded / X-Forwarded-For。
  经过 Gateway 时按代理来源计算，部署需按聚合流量设置限额。

#### 部署开关与验收

生产 Wire 同时启动 HTTP 和 gRPC Server；默认地址分别为 `:8000`、`:9000`，
通过 `AUTH_CENTER_HTTP_ADDR`、`AUTH_CENTER_GRPC_ADDR` 配置。
`AUTH_USER_ENDPOINTS_ENABLED=false` 时不注册上述 HTTP 用户路由，与 gRPC 开关一致。
TLS 与公网可达性由部署和 Gateway 决定，监听 HTTP 不代表公网入口已经交付。

验收使用生产 Wire、真实 HTTP/gRPC listener 和 MongoDB 副本集，覆盖修订后的资料/认证方法及退役无邮箱路径拒绝、Reviewer/应用运维权限方法、两个学年时间表管理方法及应用用户存储 HTTP/本人清除方法、
生成客户端、当前用户隔离、重复/替代身份头拒绝、严格 JSON、资料 CAS、撤销幂等性及内部 RPC
不暴露为 HTTP。保留原生 gRPC 回归测试。

### `platform/contracts/trusted-identity-v1.md`：可信身份 JWS v1 契约（trusted-identity-v1）

#### 目的与范围

本契约定义一个短期、audience 绑定的身份凭证在系统内的线格式与校验语义。它只规定跨系统的信任边界，不规定任一服务内部如何实现签发或验签，也不规定某个 UseCase 如何消费身份。跨系统选择本身见 [ADR-PLAT-001](../../platform/adr/ADR-PLAT-001-trusted-identity-jws.md)。

签发方是 Auth Center；Gateway 只转发；App Center 及未来的其它消费方各自本地验签。

#### 传输载体

- HTTP：请求头 `x-iwut-identity`（HTTP 头名大小写不敏感）。
- gRPC：metadata 键 `x-iwut-identity`（gRPC metadata 键为小写）。
- 值统一为一个 compact JWS：`<base64url(header)>.<base64url(payload)>.<base64url(signature)>`。
- 不允许 `Bearer ` 前缀或任何包裹；出现即视为无效身份。
- 一个请求最多携带一个身份值；出现多个值时全部拒绝，不得任取其一。

#### Claims

payload 是 JSON 对象。公共身份字段始终必填；能力字段保持在同一个 v1
线格式中按消费用例条件必填。新增能力字段不改变 JWS 算法、载体、audience 或
信任边界，因此不建立 v2。

| 字段 | 类型 | 必需 | 语义 |
| --- | --- | --- | --- |
| `iss` | string | 是 | 签发方；必须等于本地配置的 issuer |
| `sub` | string | 是 | Auth 的 opaque `authId`；非空；成为可信身份主体 |
| `aud` | string 或 string 数组 | 是 | 目标 audience；必须包含本地配置的 audience（App Center 为 `iwut-app-center`） |
| `iat` | number（Unix 秒） | 是 | 签发时间 |
| `nbf` | number（Unix 秒） | 是 | 生效时间 |
| `exp` | number（Unix 秒） | 是 | 失效时间 |
| `jti` | string | 是 | 该 token 的唯一标识；非空 |
| `account_revision` | string | Auth audience USER 必需 | 规范无前导零的正 int64 十进制字符串；Auth 在线比较当前 ACTIVE 主体版本，规则见 UC-AUTH-022/BR-ACC-004；其他 audience 不要求或推导此字段 |
| `developer_status` | string | 可选 | 仅 Developer 主体携带；取值 `PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED`、`WITHDRAWN` 之一；普通用户省略 |
| `permissions` | array&lt;string&gt; | 条件必需 | 权限用例必需；元素必须是非空、无首尾 whitespace 的唯一字符串，按精确字符串匹配；未知权限可以透传但不能产生隐式授权 |

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 运行版本审核消费精确值 `app.version.review`，公开资料审核消费 `app.profile.review`，平台暂停与恢复分别消费 `app.application.suspend` 与 `app.application.restore`；四项互不隐式授权。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含目标能力要求的精确权限时按权限不足拒绝：运行版本审核要求 `app.version.review`，公开资料审核要求 `app.profile.review`；Reviewer 不需要 `developer_status`。
- Application 平台暂停与恢复入口分别要求 `app.application.suspend` 与 `app.application.restore`；Application 管理员关系、Reviewer、Developer 或平台管理员身份不能替代精确权限。
- 同一主体可以同时携带两类字段，但任一字段都不能替代另一类字段。
- 已按旧版 v1 签发、只含合法 `developer_status` 的 Developer token 继续有效；增加 `permissions` 不改变既有字段含义。

#### 时间与有效期

- 所有时间字段都是 JSON number，表示 Unix 秒；允许小数秒但校验以秒为粒度。
- 必须满足 `exp > iat`，且 `exp - iat <= maxTTL`。`maxTTL` 由消费方启动配置注入，默认 5 分钟。
- 必须满足 `exp > nbf`。
- 以消费方时钟为准，允许 `clockSkew` 的容差（默认给一个小值，例如 30 秒，具体由启动配置决定）：
  - `now <= exp + clockSkew`，否则视为过期；
  - `nbf - clockSkew <= now`，否则视为尚未生效；
  - `iat <= now + clockSkew`，否则视为签发时间在未来。
- `maxTTL` 以 `exp - iat` 度量，不叠加 clockSkew；clockSkew 只用于与当前时间比较。

#### 校验顺序

消费方必须按以下顺序校验，且在任何一步失败时立即以认证失败结束，不继续解析后续内容：

1. 从 HTTP header / gRPC metadata 取 `x-iwut-identity`；缺失、为空或存在多个值 → 认证失败。
2. 按 `.` 切分 compact JWS，必须恰好三段且每段非空 → 否则认证失败。
3. base64url 解码并解析 JOSE header；必须为 JSON 对象。
4. 校验 `alg = RS256`、`typ = JWT`、`kid` 非空且存在于本地 kid→公钥表。
5. 用该 kid 的 RSA 公钥对 ASCII 串 `<header>.<payload>` 做 RS256 验签；验签失败 → 认证失败。
6. base64url 解码并解析 payload；必须为 JSON 对象。
7. 校验 `iss`、`aud`、`sub`、`jti` 的存在性、类型和值；若能力字段存在，同时校验 `developer_status` 与 `permissions` 的类型和值。
8. 校验时间声称（见「时间与有效期」）。
9. 构造包含 `authId`、可选 Developer 状态和权限集合的可信身份并注入请求 context；具体入口再投影为自己的最小身份类型。

签名验证必须先于对 claims 的任何业务判断。步骤 3–5 只允许基于 header 选择公钥，不允许基于未验签的 payload 做授权决定。

#### 错误边界

- 消费方对「身份缺失」和「身份无效（含签名、算法、kid、issuer、audience、时间、claims、状态非法）」都返回**认证失败**：HTTP `401 Unauthorized`，gRPC `UNAUTHENTICATED`。
- 认证失败返回消费能力自己的稳定 reason；Developer 入口继续使用 `ERROR_REASON_DEVELOPER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_DEVELOPER_IDENTITY`，Reviewer 决定入口使用 `ERROR_REASON_REVIEWER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_REVIEWER_IDENTITY`。客户端按 reason 区分，不解析 message。
- 认证失败的 message 不得回显 token、公钥、kid、时钟细节或底层 crypto 错误。内部日志可保留 cause，但不得记录完整 JWS。
- 认证失败先于业务校验发生；身份未通过时不进入 UseCase，也不产生配额或写入副作用。
- `developer_status` 缺失、或存在但不是 `APPROVED`，以及可信 Reviewer 身份不含目标权限，
  都属于**授权失败**，由 UseCase 决定，映射为 HTTP `403` / gRPC
  `PERMISSION_DENIED`，不属于本契约的认证失败。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-029`（use-cases/UC-AUTH-029-manage-academic-year-rollover.md）：主流程/查询、主流程/修改、变更记录
- `UC-AUTH-005`（use-cases/UC-AUTH-005-edit-own-user-profile.md）：目标与范围、参与者与前置条件、输入、输出、主流程、持久化与返回说明、异常与 transport 映射、API 与交付依赖、测试与验收、非目标、变更记录
- `platform/contracts/auth-center-api-routing.md`（docs 根级共享文档）：校园认证入口（UC031）、UC032 本人设备凭据管理、治理工作包路由、UC020 同账号 Session 管理
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-029-manage-academic-year-rollover.md` | 170 | `e45e42899d0c` |
| `use-cases/UC-AUTH-005-edit-own-user-profile.md` | 340 | `a2e87a33efad` |
| `platform/contracts/auth-center-api-routing.md` | 142 | `c300b311eaac` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
