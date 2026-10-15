# UC-AUTH-029：管理下一次学年更新时间

状态：`ACCEPTED`

## 目标与范围

平台管理员在 Auth Center 中读取和修改“下一次 currentAcademicYear 增加一的时间”。读取返回当前学年和严格晚于读取时刻的下一次更新时间；例如服务端时间为 `2026-10-10` 且尚未有管理员修改时，缺省下一次更新时间为 `2027-09-01T00:00:00+08:00`。

管理员设置的是包含年份的完整未来 Instant，而不是不带年份的月/日规则。例如在 2026-10-10 可以把下一次更新时间设置为 2027-02-20；不能设置为 2026-10-10 当时或更早。到达该时间时 currentAcademicYear 增加一，其后更新时间按上一次更新时间在 `Asia/Shanghai` 公历中逐次 `+1 year`。

本用例拟替代 `AUTH_ACADEMIC_CALENDAR_FILE` 和任意开始/结束区间文件，使 UC005 的编辑 schema、ACADEMIC_GRADE 锚点及 UC028 的 UserInfo 年级投影读取同一 Auth 运行时设置。它不修改用户已确认的 profile、不批量迁移年级锚点，也不把学年更新时间解释为学校对个人学籍的验证。

首版不开放时区、直接设置 currentAcademicYear、按学院/培养阶段分别配置、临时停用、一次排队多个未来时间或直接编辑 MongoDB。字段目录在线管理、ApplicationUserStorage 和学校教务日历同步仍是独立能力。

本设计已经用户审核接受。UC005/028、资料查询契约和共享路由契约同步改用本时间表；由脚本生成实施 brief 后开始 API 与 Auth 实现。

## 参与者与依赖

- **操作人**：ACTIVE USER，持有 audience=`iwut-auth-center` 的有效可信 USER JWS，并在 Auth 当前权威记录中满足 UC021 的完整平台管理员资格。每次读取和写入都在线复核账号状态、账号版本和完整管理员集合。
- **Auth Center**：唯一保存学年时间表锚点、revision 和不可变管理审计；UC005/028 只消费其权威结果，不再各自加载文件。
- **普通用户与第三方应用**：不能调用管理 API。普通用户只通过资料 schema 观察当前 academicYear；第三方只在得到对应 scope 后观察派生的当前年级代码。

依赖 [UC021](UC-AUTH-021-manage-platform-administrators.md) 的平台管理员资格、[UC010](UC-AUTH-010-issue-user-identity-from-session.md) 的 Auth audience 身份，以及 [UC005/BR-UPF-018](UC-AUTH-005-edit-own-user-profile.md#br-upf-018) 和 [UC028](UC-AUTH-028-disclose-user-profile-to-applications.md) 的年级消费语义。

本用例复用“完整平台管理员资格在线复核”作为管理授权，不新增 `auth.*.manage` 权限、不扩充 UC021 四项固定 bundle，也不把设置管理能力投影到 App audience、OAuth scope 或 consent。若未来需要把配置管理员从平台管理员中拆分，另立 UC 调整授权模型。

## 输入与输出

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

## API 契约

独立 package `auth_center.v1.academic_year_policy`，service `AcademicYearPolicyService`：

| 方法 | Auth HTTP 路径 | 成功响应 |
| --- | --- | --- |
| `GetAcademicYearSchedule` | `GET /v1/academic-year-policy/schedule` | 200，当前学年与下一次更新时间 |
| `UpdateNextAcademicYearRollover` | `PUT /v1/academic-year-policy/schedule/next-rollover` | 200，提交后的完整时间表 |

PUT 正文只提交 nextRolloverAt、expectedRevision 和 reason；GET 无正文、无 query。两种方法同时提供 HTTP/JSON 与原生 gRPC，并以精确 full method 加入鉴权表。Gateway 使用 SESSION 路由换取 audience=`iwut-auth-center` 的 USER JWS；Auth 不接受 OAuth access token、App audience JWS、service JWS、直接 Session 或请求正文自报 actor。

响应使用 `Cache-Control: no-store`。拒绝未知/重复字段、null、非法 Timestamp、query 和超过 16 KiB 的请求。管理入口使用独立的默认关闭开关和有界读写限额；入口关闭不影响系统内部按缺省或已保存时间表计算学年。

## 主流程

### 查询

1. 验证可信身份和精确方法，在线复核操作人当前为完整平台管理员。
2. 捕获一次服务端 observedAt，在同一一致性边界读取并验证权威时间表。
3. 从已保存锚点向后推算已经发生的年度更新次数，得到 currentAcademicYear 和严格晚于 observedAt 的 nextRolloverAt。
4. 返回当前投影、observedAt、revision 和最后一次人工更新时间；查询不写回“推进后的下一次时间”，也不增加 revision。

### 修改

1. 验证身份、nextRolloverAt、reason、expectedRevision 和入口限额，并在线复核完整平台管理员资格。
2. 在 Auth 事务中捕获提交检查时刻，解析现有时间表在该时刻的 currentAcademicYear 和下一次更新时间。
3. 要求输入 nextRolloverAt 严格晚于该检查时刻，并保证它及按规则计算的后续时间可以由契约 Timestamp 表达；等于或早于当前时间均拒绝。
4. 比较 expectedRevision。若输入恰好等于当前投影的下一次更新时间，作为 no-op 返回；stale revision 仍先返回冲突。
5. 真实变化保留当前 currentAcademicYear，把输入时间保存为“使学年增加到 currentAcademicYear + 1”的新锚点，并从它重新开始逐年递推；严格增加一次 revision。
6. 时间表、revision 和 append-only 审计在同一事务提交，返回以同一提交检查时刻投影的完整结果。

## 业务规则

<a id="br-upf-019"></a>
### BR-UPF-019：权威时间表与九月一日缺省

Auth 只保存一条权威年度时间表锚点：锚点 Instant 到达时生效的 academicYear，以及配置 revision/更新时间。对任意读取时刻，服务端按 [BR-UPF-021](#br-upf-021) 推算已经到达的边界数量、当前学年和下一边界；不需要为每年生成或保存区间。

系统初始化时幂等 provision 一条确定基线，使其语义等价于每年 `09-01 00:00:00 Asia/Shanghai` 增加学年：9 月 1 日边界到达后 currentAcademicYear 为该公历年，边界之前为前一公历年。全新系统在 2026-10-10 读取时得到 currentAcademicYear=2026、nextRolloverAt=`2027-09-01T00:00:00+08:00`。多实例并发只能形成一份相同基线。

缺少部署文件不再是错误，也不会关闭 ACADEMIC_GRADE。已 provision 的设置若缺字段、BSON 类型非法、revision 非正、锚点 academicYear/Instant 不可解释或后续计算溢出，则失败关闭，不能静默重置为缺省。

<a id="br-upf-020"></a>
### BR-UPF-020：完整平台管理员在线授权

Get 与 Update 都要求当前 ACTIVE USER 的 Auth audience JWS 满足 UC021 管理身份要求，并在权威数据库在线复核完整管理员集合、accountRevision 和 permissionRevision。仅持有 Reviewer、Developer、App 运维权限、Application 管理权、SYSTEM/service identity 或历史管理员 JWS 均不能管理设置。

本能力不增加第五项平台管理员权限，也不把 `auth.platform-admin.manage` 拆成可单独授予的“日历管理员”资格。这里授权的是 UC021 定义的完整平台管理员身份；时间表本身不进入用户 permissions、OAuth Scope Catalog、第三方 token 或 UserInfo。

<a id="br-upf-021"></a>
### BR-UPF-021：未来锚点与逐年推进

Update 输入的是下一次更新时间本身，必须包含年份并严格晚于最终事务检查使用的服务端时间。设置 2027-02-20 表示到该 Instant 时 currentAcademicYear 才增加一；设置动作本身不改变当前学年。管理员可以把更新安排到明天或多年以后，相应地提前或冻结下一次学年推进，系统不另猜测其意图。

每个实际到达的边界只使 currentAcademicYear 增加一。下一边界取上一个边界在 `Asia/Shanghai` 当地时间的公历 `+1 year`，不是固定秒数或 365 天。若一次边界是闰年 2 月 29 日，下一非闰年的边界规范化为 3 月 1 日，保留当地时分秒；之后从 3 月 1 日继续逐年增加，不在后续闰年自动回到 2 月 29 日。例如 `2028-02-29 00:00+08:00` 后依次为 `2029-03-01 00:00+08:00`、`2030-03-01 00:00+08:00`。

服务停机、没有用户请求或跨过多个边界不丢失推进：读取根据锚点和 observedAt 直接得到累计次数，不能依赖 cron 每年写数据库。实现应使用有界的公历年差计算与至多常数次校正，不能按停机年数无界循环。自动跨年不会增加配置 revision、updatedAt 或管理审计。

待下一边界到达前，管理员可以使用当前 revision 再次设置另一个未来 Instant；新设置替换整条未来递推序列，但保留设置时已经生效的 currentAcademicYear。设置与旧边界竞争时，以事务内最终检查时刻为顺序：旧边界已经到达则先计入当前学年，再以输入建立下一锚点；尚未到达则由新锚点替换。

<a id="br-upf-022"></a>
### BR-UPF-022：乐观并发与不可变审计

配置使用单一正数 revision。真实变更在事务内比较 expectedRevision 并严格增加一次；并发 Update 至多一个使用同一旧 revision 成功。输入恰好等于当前投影 nextRolloverAt 时，在 revision 匹配和未来时间校验后作为 no-op 返回，不增加 revision 或审计；stale revision 一律冲突。

每次真实变更写一条不可变审计，包含 eventId、可信 actorAuthId、reason、before/after nextRolloverAt、设置时 currentAcademicYear、before/after revision、occurredAt 和新的锚点 academicYear；不记录用户 profile、学生关联、OAuth token 或第三方读取内容。时间表与审计同事务提交，审计失败全部回滚；事务重试复用 eventId，提交结果未知返回不可用，客户端先 Get 再决定是否重试。

系统首次 provision 的 9 月 1 日基线以 `source=SYSTEM_DEFAULT` 标记，不伪装成人工管理员变更。基线一经建立，数据库记录被删除或损坏不得在普通读写路径静默重建；恢复需要受控运维和审计。

<a id="br-upf-023"></a>
### BR-UPF-023：消费一致性与文件配置退役

UC005 的 schema/current academicYear、ACADEMIC_GRADE set 锚定和 UC028 的 UserInfo 派生读取同一 Mongo 权威时间表，并使用各请求捕获的一次服务端时间。涉及 profile 写入时，时间表读取、账号复核和 profile CAS 位于兼容的一致性/事务边界；涉及 UserInfo 时，时间表与当前 profile、token/grant 生命周期事实保持既有一致检查点。不得由两个进程各自缓存文件产生不同学年，也不得在依赖读取失败时降级为 9 月 1 日或旧缓存。

实施本 UC 后，代码和部署文档移除 `AUTH_ACADEMIC_CALENDAR_FILE`、区间 JSON 及 `configs/academic-calendar.example.json` 的权威作用。系统尚未部署，不设计旧文件在线迁移或双读优先级；进程不再读取该变量。外部环境中即使残留同名变量，也不作为启动错误，只是没有任何效果。测试 fixture 可以构造时间表对象，但不能成为生产配置旁路。

Profile 不含 ACADEMIC_GRADE 或 UserInfo 没有相应有效 scope 时，业务请求仍不必读取时间表；管理 API 和初始化 schema 独立存在。需要当前学年的请求遇到设置损坏、数据库故障或时间计算溢出时失败关闭，不返回部分资料或猜测学年。

## 错误语义与运行约束

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

## 验收场景

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

## 实现依赖与交付边界

实施需新增独立 API Proto、Domain/Port/UseCase、Mongo 时间表与审计 repository、严格 HTTP/gRPC transport、管理员在线 gate、默认关闭入口及真实副本集并发/故障测试。现有 profile 与 OAuth 服务的静态 `*AcademicCalendar` 依赖改为按请求读取的 schedule provider；部署和 README 删除文件说明。

UC005 BR-UPF-018 的“版本控制部署输入”和非目标、UC028 的依赖/故障描述、资料查询契约、设计说明、实现记录及部署配置随本次接受同步修订。使用 `tools/gen_brief.py` 生成 brief 后开始实现；设计接受不代表部署入口已经启用。

## 变更记录

- 2026-10-10：建立待审核草案；初稿采用不带年份的年度月日规则和必要时延迟生效。
- 2026-10-10：按用户意见改为带年份的“下一次学年更新时间”；输入必须晚于当前服务端时间，到点后逐次按上海本地公历增加一年，2 月 29 日的下一次规范化为 3 月 1 日；退役环境变量但不因残留拒绝启动。
- 2026-10-10：用户审核并接受 UC029；同步修订 UC005/028 和共享路由契约，进入 brief 生成与实现。
