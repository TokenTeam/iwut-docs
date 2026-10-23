# UC007：资料详情加载后的管理关系变化

状态：`ACCEPTED / IN_PROGRESS`，2026-10-23，依据用户持续授权自行接受。承接[Profile并发与迟到回执](2026-10-23-profile-decision-concurrency-and-late-receipts.md)，只补UC007 BR-CRV-005/008及其引用BR-CRV-003/004的Profile加载后CURRENT_ADMIN场景；不缩减完整Console目标，不新增Developer或治理写UI。

## 固定资源与相位

保留原18项顺序，在末尾追加一项。复用原owner和主Reviewer Node DEVICE transport、主Reviewer BrowserContext/Session及设备钥匙，在`resources[1].applicationId`正式创建/提交第三份Profile C（固定名称`Decision_Profile_conflict`，description/icon显式null）。必须正式读回前份B已APPROVED/当前公开且工作位为空；不seed PENDING或改公开指针，不新建账号/App/quota/BrowserContext/登录。

扩展原固定准备器为A→B→C有限相位；C仅在B正式APPROVED后开始，沿用原一次Create/Submit及未知结果仅正式List/Get/ReviewerDetail确认，不按名字认领或重发。历史A/B重复观察允许新的C占工作位，但仍校验原目标和实际终态；不能以放宽历史读取绕过C的完整绑定与PENDING准备要求。

主Reviewer在原第15项已正式Apply为APPROVED，该事实不可逆且继续保留；本包不再次Apply。以[UC026](../../app-center/use-cases/UC-APP-026-transfer-application-administration.md)的正式Initiate/Accept KEEP把此App转给主Reviewer，再反向转回原owner。使用独立固定factory实例，初始资格明确APPROVED；旧Version实例保持原NONE→一次Apply模式及不可重入语义。两实例分别固定不同App，不调用已结束的旧转让相位。

新实例首次只读校验旧四权限相位完成、旧App管理权已恢复revision3/无pending、主Reviewer精确双权限及原handle/APPROVED。新App初始ownershipRevision1，转入为2、转回为3；owner配额30→29→30，主Reviewer0→1→0，不改配额配置。双方资格、权限revision和Session不因转让人为重建。

## 控制与未知写安全

新增四个精确loopback bearer控制：`prepare-profile-conflict`、`observe-profile-conflict`、`transfer-profile-to-main`、`restore-profile-from-main`。只允许POST、application/json、无query空对象；不接收App、subject、transfer、handle、revision、credential handling、DB或URL。前三元目标及最小管理权/权限观察外不返回凭据/业务正文。转让控制在C准备完成前拒绝，不偷偷创建资料或补Apply。

转让factory仅内部增加明确的初始资格模式；省略保持NONE旧模式，APPROVED模式严格核对原handle且绝不调用Apply。所有读/写保持固定参与者、App、ownershipRevision、transferId与KEEP绑定。同命令in-flight共享promise、不同命令失败。Initiate/Accept/Cancel未知回执只读相同申请与正式ownership确认，不能凭网络错误重发。原factory的Cancel与Accept竞争、反向未知写、权限漂移、脱敏及终态不重入回归必须保留，并新增APPROVED模式对应负例。

## 真实生产React验收

1. 准备C后，主Reviewer真实读取同Review PENDING/eligible；记录snapshot、createdBy/submittedBy、revision和B的正式currentPublishedProfile。另两页加载不同App的同能力终态资料及另一能力终态Version，记录原DOM。
2. 主页面键盘选择REJECT、填写理由、预览。随后正式转入管理权，不刷新详情；核对目标GET计数不变、决定POST0/Session DELETE0。
3. 旧确认仅提交一次，实际HTTP403 `ERROR_REASON_APPLICATION_PROFILE_REVIEW_CONFLICT_OF_INTEREST`及private/no-store。React聚焦明确未确认/同Review重读说明，不误报RESULT_UNCERTAIN、不卸载整个资料capability，不自动重发。
4. 键盘重读精确同Review，实际GET200仍PENDING且只有CURRENT_ADMIN；snapshot、历史归因和原公开资料B均不变。禁止确认/提交，旧理由确认不复用。其它App同cap与另一cap原DOM保持，明确刷新仍200，Session与non-extractable钥匙不变。
5. 正式转回owner后，原页明确刷新同Review仍PENDING、eligible无冲突；主动切APPROVE后两项checks均未勾选、预览禁用，仍展示正式B对照。无新决定或Publish，累计POST1/DELETE0、权限revision与Session/钥匙保持。

本例只证明DOM/网络与固定权限变化，不宣称全heap或所有资格/生命周期组合。finally仅对已尝试的转让做有限恢复、关闭自身页面/计数handler；无法确认恢复须使本例失败，不能DB重置、补决定或把未完成清理算通过。C最终保持正式PENDING直到整轮隔离环境销毁，Profile无取消草稿/撤回Review入口。

## 门禁与保留项

先新增工厂和adapter的Node合成红绿回归，再普通测试、strict、官方固定pin生成漂移及Edge。冻结runtime/runner/spec，每轮重新pull已发布latest：先19项审核决定专项，再默认无参数107项完整门禁，以实际终态数量为准。旧25条Application错误缓存头断言不删除、不代理补头；全量仍红不push，不编译相邻后端或替换本地artifact。

不同修订公开指针UI并发可达性、策略退休/Scope/全部依赖故障、完整决定跨Session、其它角色/生命周期及UC001/fencing继续OPEN。单一working约束与UC007的不同修订并发要求不能靠非法双PENDING seed“补齐”；需另行记录和论证可达流程。本包不关闭完整UC006/007或整体目标。

## 实施与预检

Console已本地提交并冻结`040cfc78dba70f5ced2375a124f23542effd5efb`，只改固定准备器、runner及真实spec/合成回归，无生产UI变化。工厂新增10项先RED后GREEN（旧27项仍通过，最终37/37）；包括C前置Get与基线List之间B公开指针漂移仍必须拒绝。adapter新增1项，首轮暴露控制未静态包装、随后合成List summary错误包含完整history字段，按既有生成Schema修正后22/22通过；不是修改生产Proto或放宽unknown字段。验证原三DEVICE、唯一一次Apply、两个独立固定App转让、C前置/重复只读、正反KEEP及无新资源，合成证据不当真实命令证明。

统一`pnpm test`903项Vitest＋183项Node全部通过，`pnpm typecheck`、官方同pin`pnpm generate:check`和`pnpm edge:e2e`均exit0；真实spec strict、Node语法、仓库独立性（288文件）及diff检查通过。已启动19项published-latest专项，运行期不改runtime/runner/spec，真实终态及后续无参数全量证据待补；未push。

## Published 专项终态

`iwut-console-real-65940`在干净冻结`040cfc78dba70f5ced2375a124f23542effd5efb`下执行`pnpm test:real tests/real/review-decisions.real.spec.ts`，实际19/19通过（浏览器2.2分钟、exit0，无skip/retry）。新增第19项7.1秒：第三份资料正式准备、APPROVED资格零重复Apply、旧表单唯一403后同Review重读仅CURRENT_ADMIN、双向KEEP转让与原公开B/其它视图/Session/钥匙保持、恢复后两检查未确认均收齐。决定POST1/Session DELETE0，最终C仍PENDING，未补决定清理。

23个实际决定响应的private/no-store均真：Version 200×7、403×4、409×1；Profile 200×7、403×2、409×2。原18项完整保留并再次通过，专项不关闭完整UC或替代全量。

三个后端latest重新pull后解析ID与前包相同：Auth `sha256:c2f06d8fe4ca2734a32e07e70f6ab7ba8c0207932336222c2c92986e073de8b9`、App `sha256:2af4af71e8eb8f1ea46e92bfdaa3e8e14944cb0bc4ca46b95c9a05db6c46340a`、Gateway `sha256:2953ae7fb81da7d06586b735340e4d3d320e523bb67f7700cc2571602e728303`；Mongo `sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3`、Traefik `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0`。沿用显式103地址NSS测试输入，不冒称部署DNS证据。

终态后专项容器（含退出）和network均为空，源码仍干净。已另起默认无参数完整门禁、逐轮重新pull，运行期间继续冻结runtime/runner/spec，终态待补；未push。

## 默认无参数完整门禁终态

`iwut-console-real-71728`在同一干净冻结`040cfc78dba70f5ced2375a124f23542effd5efb`下执行默认`pnpm test:real`，实际107项：**104通过、3失败，无skip/retry**，浏览器18.8分钟、exit1。原106项及新增加载后Profile关系变化均实际执行；全部19项决定再次通过，第19项7.2秒。旧表单实际403、同Review仅CURRENT_ADMIN、正式转回后的PENDING/eligible与清空检查、旧公开B/其它审核视图/Session/钥匙保持、一次决定与零Session DELETE证据再次收齐。

23个决定响应private/no-store全部true，分布与专项逐项相同，afterAll通过。原Admin查询56条错误头继续通过。全量前置strict/报告隐私/生产build通过，运行期未改runtime/runner/spec或来源；五镜像每轮重新pull，解析ID与专项逐项相同，无local-compat/相邻后端编译替代。

全部25条失败逐条对应原缓存头断言，没有新增非缓存硬失败：

| 场景 | 断言数 | 可信失败坐标及含义 |
| --- | --- | --- |
| 管理权转让 | 3 | `management-transfer.real.spec.ts:257:29` ×3，Application GET404缺no-store |
| owned游标负例 | 10 | `owned-application-pagination.real.spec.ts:200:57` ×4、`:201:58` ×4、`:220:66` ×1、`:221:67` ×1，五个List400各缺private/no-store |
| 非owner角色读取 | 12 | `qualification-read-matrix.real.spec.ts:368:54` ×6、`:368:116` ×6，六个Application GET404各缺private/no-store |

soft断言继续使对应三用例及完整门禁失败，功能和最终Session断言仍收齐；不删断言、补代理头或把失败算通过。发布接线已满足本例，当前全量发布缺口仍是上述Application错误头，不是缺Gateway路由。

进程终态后，本轮及全部real测试前缀容器（含退出）/network均为空，源码仍为原冻结且干净。本地legacy为`e68851e343bd0e077e5ccd0b680fe6813216ced0`；本次远端首次只读查询网络超时，收尾有界重试成功且SHA相同，不将超时当远端已验证。提交仅本地、未push。

本包所列Profile加载后冲突已实施并取得专项/完整回归证据；整体门禁与完整Console目标仍IN_PROGRESS。保留前述不同修订公开指针可达性、策略/Scope/依赖故障、完整决定跨Session、其它角色/生命周期及UC001/fencing缺口，不把本19项扩大为所有矩阵完成。
