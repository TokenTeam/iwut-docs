# UC006：加载后管理关系变化的审核恢复

状态：`ACCEPTED / IN_PROGRESS`，2026-10-23，按用户持续授权自行决定并接受。承接[权限恢复增量](2026-10-22-review-uncertain-permission-recovery.md)，只补UC006 BR-CRV-001/003/004的Version加载后CURRENT_ADMIN交错，不缩减完整UC006/007，不增加Developer或治理写UI。

## 准备与范围决定

在现有14项决定之后追加一项，复用`resources[2].versions[2]`，开场用真实Reviewer GET确认仍PENDING、eligible且无冲突。不新增账号、App、quota、seed、BrowserContext或Session签发。复用主Reviewer现有浏览器context，以及决定准备时已建立的Node DEVICE transport（仅保留原闭包引用，不重新登录）。另一同cap终态用`resources[0].versions[0]`，另一cap用`resources[1].profile`。

通过[UC013](../../auth-center/use-cases/UC-AUTH-013-apply-for-developer.md)以主Reviewer本人现有DEVICE Session正式申请Developer，再按[UC026](../../app-center/use-cases/UC-APP-026-transfer-application-administration.md)原owner GetOwnership→Initiate→主Reviewer Accept KEEP。转让只改变当前管理关系，历史createdBy/submittedBy不改，故只新出现CURRENT_ADMIN。不能用G强制设置管理员或DB改归属。源30→29、主Reviewer0→1；反向正式转让恢复29→30与1→0，不扩额。

Apply是隔离测试账号的真实不可逆资格变化，不能冒称finally恢复普通USER。因此必须放在原14项之后：先验证该账号的普通Reviewer证据，再开通资格；权限grant/revision与Browser Session不变。主Reviewer资格保留APPROVED直至整轮隔离环境销毁。既有Profile PENDING已由前14项用尽，本包不虚构Profile对应证据或把终态seed回PENDING。

## 固定控制与未知回执

仅增加`/fixtures/review-decisions/observe-main-conflict`、`transfer-to-main`、`restore-from-main`三个loopback bearer控制，精确POST、application/json、空对象、无query；不收任意subject、App、revision、transferId、handle、handling、DB或URL。服务内固定目标resource和参与者，唯一handling KEEP，不扩展通用治理代理。输出只包含必要的固定App ID、当前ownership revision、资格状态与精确双Reviewer权限/revision；不返回Session、钥匙、完整Auth/transfer资源或审计原文。

准备操作固定为初始→转至主Reviewer→恢复owner；观察只读、重复完成只读，同一命令in-flight共享promise，不同并发命令失败关闭。每个Apply/Initiate/Accept（以及失败清理Cancel）在发出前登记attempt，保存已知原OCC与transferId。回执未知只能通过正式本人资格/GetOwnership/GetTransfer确认：Initiate丢回执可从源GetOwnership的pendingTransferId发现并严格核对同一App/from/to/OCC；Accept未知只读原transfer，不能重发或新建替代。查不到确定结果则保持未知并使测试失败，不根据单次无pending推断原写未在途。无任意数据库兜底，不泄漏底层错误。

finally尽力按已确认相位恢复：forward尚未accept且已知PENDING可由原source正式Cancel，再读其终态；若已ACCEPTED则由主Reviewer正式反向Initiate、原owner Accept KEEP，校验ownership revision递增。未知Cancel仍只读原transfer，若竞态得到ACCEPTED再走反向；不能盲目重复写、强制归属或把未确认恢复写成成功。任意未解决相位须令本例/该serial轮失败，最终清理整轮隔离环境。固定权限观察应证明本包没有改Reviewer权限及revision，不触碰原qualification/V-peer相位。

## 实际React场景

1. 主Reviewer原Session打开目标PENDING/eligible详情，打开同cap另一终态及另一cap终态，正常填REJECT并预览。捕获目标Review ID、submittedBy/createdBy与原snapshot，明确不是初次加载冲突。
2. 正式转让后，**不先刷新原页**，键盘提交原已加载表单一次。精确决定POST实际403 `ERROR_REASON_APPLICATION_REVIEW_CONFLICT_OF_INTEREST`且private/no-store；React聚焦明确拒绝/同Review重读说明，不应误报RESULT_UNCERTAIN或进入“版本审核不可访问”，不自动读取/重发决定。
3. 键盘“重新读取同一 Review”，精确GET200仍PENDING，decisionEligibility只有CURRENT_ADMIN、eligible=false，原snapshot和历史提交归因保持。显示冲突且不能确认/提交，审批checks清空；Session与设备钥匙不变、零Session DELETE、决定POST仍一次。
4. 同cap另一目标和另一cap既有DOM保持，明确刷新均GET200，证明不是整个版本审核能力撤销。DOM/网络证据不冒称同一QueryClient内存或全heap检查。
5. 正式反向转让恢复owner，原页明确刷新同Review仍PENDING且eligible、无冲突；旧批准检查不得恢复，须重新评审。只验证恢复，不再次提交决定。最终检查固定权限/revision未变、Session/钥匙保持与流量计数。

## 验证与完成边界

先固定相位/OCC/绑定/未知回执/错序并发/敏感错误的Node合成红绿回归，再普通903项Vitest及扩展Node、strict、官方固定pin生成漂移、Edge。冻结全部runtime/runner/spec后，每轮pull发布latest，先15项专项再默认无参数103项全量，以实际终态数为准。保留原25条Application错误缓存头断言，不代理补头、不编译后端、不用local兼容artifact。全量仍红不push。

本包只补Version所列加载后关系变化。Profile同类组合、不同修订公开指针并发、策略退休、Scope与全部依赖故障、全部决定Session交错及UC001/fencing仍OPEN。若真实链路揭示产品缺陷，终态并清理后再最小修复、重新冻结和复验，不能在运行中改源或以专项代全量。

## 实施与预检

源码冻结`77201dd`，仅新增固定准备控制及第15项浏览器spec，无产品UI变更。新增工厂首12项先RED（缺factory）后GREEN，再补4项Cancel竞态/反向readfail/只读unknown/权限漂移，以及1项正式Proto adapter合成接线，共17项新增Node。adapter拒绝早于前14项权限相位的控制调用，硬校验初始grant revision＋4后才允许任何资格/转让写；既有三个Node DEVICE保持不增。合成证据不当作真实治理命令或浏览器验证。

统一`pnpm test`903项Vitest＋160项Node全部通过，`pnpm typecheck`、`pnpm generate:check`（官方同pin）与`pnpm edge:e2e`均exit0；Admin158组件亦独立通过，diff/Node语法检查通过。已再次通过当日Cloudflare HTTPS DNS查询核验显式NSS fixture的公共A仍为198.35.26.224，不访问其HTTP内容，也不当部署DNS证据。开始published-latest 15项专项，未达终态前不算通过；runtime、runner与spec保持冻结，未push。
