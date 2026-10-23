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

统一`pnpm test`903项Vitest＋160项Node全部通过，`pnpm typecheck`、`pnpm generate:check`（官方同pin）与`pnpm edge:e2e`均exit0；Admin158组件亦独立通过，diff/Node语法检查通过。已再次通过当日Cloudflare HTTPS DNS查询核验显式NSS fixture的公共A仍为198.35.26.224，不访问其HTTP内容，也不当部署DNS证据。随后按顺序执行published-latest 15项专项与无参数全量，实际终态见下文；runtime、runner与spec保持冻结，未push。

## Published专项终态

`iwut-console-real-302865`在干净冻结`77201dd`下运行`pnpm test:real tests/real/review-decisions.real.spec.ts`，终态15/15通过（浏览器1.7分钟、exit0，无skip/retry）。第15项实际7.9秒，正式Apply与双向转让均完成；旧已加载REJECT仅一次实际403 CONFLICT_OF_INTEREST、无预先刷新，React明确拒绝并聚焦同Review重读，未撤销整个capability或误报unknown。重读GET200仅CURRENT_ADMIN，原snapshot/createdBy/submittedBy保持；同cap另一目标和另一cap原DOM及明确刷新200通过。正式转回后同Review仍PENDING、eligible、无冲突，四批准检查均未确认，无新决定/Session DELETE，原Session/设备钥匙保持，权限及revision不变。主Reviewer此时确为APPROVED，不冒称恢复普通USER。

每轮重拉published-latest：Auth `sha256:c2f06d8fe4ca2734a32e07e70f6ab7ba8c0207932336222c2c92986e073de8b9`、App `sha256:2af4af71e8eb8f1ea46e92bfdaa3e8e14944cb0bc4ca46b95c9a05db6c46340a`、Gateway `sha256:2953ae7fb81da7d06586b735340e4d3d320e523bb67f7700cc2571602e728303`，Mongo `sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3`、Traefik `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0`，均与上一发布轮次相同，无本地backend编译/替代。全部决定响应private/no-store为true。

专项进程exit0后检查所有该prefix容器（含退出）及network为空，才在同源码/spec/runner冻结下启动另一空环境的默认无参数103项。不能用15项专项替代它；原25条错误缓存头及全部未列明矩阵继续开放，未push。

## 无参数全量终态

`iwut-console-real-310582`执行默认无参数`pnpm test:real`，冻结源码`77201dd91a6905bde2a6e53197c1ddfbffc6d09b`全程干净。终态103项：**100通过、3失败，无skip/retry**，浏览器22.5分钟、exit1。原102项和新增第15决定场景均实际执行，全部15项决定再次通过，第15项10.4秒；正式双向转让、仅CURRENT_ADMIN的重读和恢复、跨目标/capability/Session保持、一次决定与零Session DELETE证据再次收齐。生产build、严格类型及标准报告隐私前置通过，没有为使测试通过改产品UI。

25个错误的可信坐标逐条与上一轮相同，且全部仍为原缓存头断言：

| 场景 | 断言坐标与次数 | 缺口 |
| --- | --- | --- |
| 管理转让 | `management-transfer.real.spec.ts:257:29` ×3 | Application GET404缺no-store |
| owned游标 | `owned-application-pagination.real.spec.ts:200:57` ×4、`:201:58` ×4、`:220:66` ×1、`:221:67` ×1 | 五个List400各缺private/no-store，共10条 |
| 资格/角色 | `qualification-read-matrix.real.spec.ts:368:54` ×6、`:368:116` ×6 | 六个Application GET404各缺private/no-store，共12条 |

无新增非缓存硬失败。Admin查询原56条错误头继续通过；19个实际决定响应为Version200×7/403×4/409×1、Profile200×5/403×1/409×1，private/no-store全部true，afterAll通过。没有删soft断言、补代理头或把3个失败算通过，原管理/角色功能及最终Session断言仍执行完整。

本轮再次pull五个latest，全部ID与上述专项一致，没有本地兼容artifact或后端编译。终态后检查所有本轮容器（含退出）与network为空，本地和本次远程只读核验legacy仍为`e68851e343bd0e077e5ccd0b680fe6813216ced0`。提交仅本地、未push；所列Version加载后利益冲突真实证据已补齐，但Application错误头完整门禁仍红，UC006/007及全部其它明确开放矩阵继续IN_PROGRESS。

## 后续候选（本轮历史，已由后续独立包实施）

下列候选在本15项轮次尚未实施；随后由[Profile决定并发与迟到回执](2026-10-23-profile-decision-concurrency-and-late-receipts.md)独立接受/实施，published专项18/18、默认完整106项103通过/3个既有缓存头用例失败。不将后续证据归入本轮冻结`77201dd`，其它开放项不因此关闭。

下一候选是UC007同Review双Reviewer决定、真实deadline后的PENDING恢复、离开后迟到决定回执。可复用`resources[1].applicationId`、现有main与profileOnly两个context及原Node owner transport，按[UC013](../../app-center/use-cases/UC-APP-013-create-application-profile-revision.md)/[UC015](../../app-center/use-cases/UC-APP-015-submit-application-profile-revision-review.md)先后正式Create/Submit两份新资料：A供双Reviewer重叠决定并终态释放工作位，B供deadline与后续用户重新确认的独立明确提交/迟到响应。需要另建接受工作包，不在本轮中实现；不重新调用本包已结束的转让factory，不增加账号/App/quota/登录。主Reviewer仍为APPROVED，不能回写成普通USER。

Create没有客户端幂等键、displayName不唯一，不能只按名字认领未知结果。候选准备须写前正式List固定已有ID/最大sequence及空working，单writer只发一次Create；未知后仅List/Get确认唯一新增sequence、同一工作指针、完整content/creator/revision1/DRAFT。Submit同样只尝试一次，之后按[UC039](../../app-center/use-cases/UC-APP-039-query-owned-application-profile-revisions.md)读同修订/审核历史确认SUBMITTED revision2、唯一attempt/sourceRevision/PENDING，再以Reviewer正式详情核对三元与snapshot。仍DRAFT或查不到新项不是未在途证明，不能据此重放。没有取消/删除草稿或撤回Review入口，失败残留留至隔离环境销毁，不补决定“清理”。

Profile重叠仅证明同一Review一次性决定，不是不同修订公开指针并发。deadline后新提交必须由用户重新评审并明确确认，区分初次未知请求和新请求计数；迟到成功回执候选应采用实际上游200的RESPONSE/HOLD并在30秒deadline前释放，以免冒称另一种取消。ARMED不能靠重复业务POST消耗，HELD仅释放原请求/响应，未知准备或未解决gate必须令serial场景失败。该候选尚非实施或通过证据，不关闭本包列明的其它开放矩阵。
