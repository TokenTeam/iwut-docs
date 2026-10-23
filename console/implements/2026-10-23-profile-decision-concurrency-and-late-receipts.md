# UC007：资料审核并发、真实超时与迟到回执

状态：`ACCEPTED / IN_PROGRESS`，2026-10-23，按用户持续授权自行决定并接受。承接[加载后关系变化](2026-10-23-review-loaded-conflict-recovery.md)之后的候选，补UC007 BR-CRV-008引用的BR-CRV-003/004真实交错；不新增业务用例或Developer写UI，不以Version证据冒称Profile分支已验收。

## 资源与准备决定

原15项保留顺序，在其后追加3项普通serial场景。复用`resources[1].applicationId`、原owner Node transport、主Reviewer context/driver及profileOnly context/driver。App原Profile已REJECTED且无工作位，主Reviewer在前包正式Apply后仍为APPROVED、管理权已转回；不重复转让factory，不新建账号/App/quota/BrowserContext/Session或seed。

仅正式Create/Submit两份新Profile：A先完成双Reviewer重叠REJECT并释放工作位，B先完成真实deadline/PENDING恢复，下一独立case在同一B上经用户重新评审确认提交APPROVE并观察迟到回执。B的第二次请求是新的明确用户提交，不是第一次未知请求的自动重放；两个case累计POST明确计为2。Profile批准自动公开仍取当前详情的正式revision/指针，不硬编码NONE，不提供第二Publish。

## 固定准备控制与未知写

仅增加`/fixtures/review-decisions/prepare-profile-overlap`和`prepare-profile-timing`两个loopback bearer控制，精确POST、application/json、无query空对象。不接收subject、App、profile/review ID、content、revision、DB或URL。内部固定App、创建者与两份完整内容（icon/description显式null），返回三元定位值，不返回凭据、原始Auth响应或审核正文。仅当前包既有权限四相位完成、主Reviewer已正式开通且前次管理权转回的正式观察通过后可进入；不通过调用准备控制补做转让或Apply。

按[UC013](../../app-center/use-cases/UC-APP-013-create-application-profile-revision.md)、[UC015](../../app-center/use-cases/UC-APP-015-submit-application-profile-revision-review.md)、[UC039](../../app-center/use-cases/UC-APP-039-query-owned-application-profile-revisions.md)正式准备，不改变后端规则。A→B有限相位；不同准备并发失败关闭，同命令in-flight共享promise；重复完成只读确认原目标。B创建前必须读回A的同一Review REJECTED、修订终态及空working，不能创建平行工作修订。

Create无幂等键，displayName非唯一。每一阶段写前正式List捕获全部旧ID/最大sequence、固定公开指针及空working，完整页必须无后续cursor；登记attempt后仅一次Create。未知回执只能List/Get确认唯一新增sequence=max+1、旧ID集合未变、working指针匹配、完整固定content/createdBy/revision1/DRAFT。没有新项不能证明未在途，保持未知并失败，不再次Create。已知Create响应仍须正式读回，不仅信名字/response。

Submit同样登记attempt，仅一次expectedRevision=1写；已知或丢失回执后仅Get同一修订/历史，确认SUBMITTED revision2、工作指针不变、唯一attempt1/sourceRevision1/PENDING/decision=null，再以真实Reviewer详情核对三元、snapshot/提交归因及eligible。仍DRAFT、无历史或读失败不能作为重试理由。不能借管理员投影伪造Reviewer snapshot。未知状态重复准备只读原相位，不能跳到B；错误静态包装，无数据库兜底。

## 三项真实生产React场景

1. **同Profile Review双Reviewer重叠**：主context与profileOnly真实加载A并预览REJECT。透明代理只扣留主请求REQUEST/HOLD，确认HELD后另一个Reviewer正常提交并实际200 REJECTED。释放未修改的主请求，实际409 `ERROR_REASON_APPLICATION_PROFILE_REVIEW_ALREADY_DECIDED`及private/no-store；主页聚焦明确重读说明，键盘重读同Review实际终态及peer决定归因，不重发。两人各一次POST、零Session DELETE，双方Session/设备钥匙保持。此场景不是不同修订公开指针并发。
2. **真实30秒deadline后仍PENDING**：主页面真实加载B、逐项确认两项APPROVE检查、预览并提交一次，透明REQUEST/HOLD直到实际AbortSignal deadline使请求DROPPED，React必须实际进入RESULT_UNCERTAIN。键盘重读精确同Review实际GET200/PENDING，焦点说明PENDING不能证明旧请求未在途；两项checks清空、确认禁用，原Session/钥匙保持，POST仍一次。不能仅用gate推断JS失败或把PENDING称为原写失败。
3. **重新明确提交后的迟到成功回执**：新case复用同一B，重新真实读取、重新主动确认并明确APPROVE（累计第二POST）。透明RESPONSE/HOLD实际已获上游200后，SPA返回资料审核队列，捕获新页投影；在30秒deadline前释放原成功回执并确认浏览器完整响应结束。新队列/URL不得被旧终态、理由、snapshot或确认表单污染，Session/钥匙保持、无第三POST或Session DELETE；再明确打开B才显示实际APPROVED/自动公开、无第二Publish。不把超时取消当迟到成功，也不把此次决定归因成第一次未知请求完成。

DOM/网络证据不扩大为同QueryClient或全heap验收。所有错误与未知说明、检查和恢复通过键盘操作并核对焦点；业务响应来自真实App，不伪造JSON或policy。

## 清理、门禁与开放边界

HELD只释放原请求/响应，ARMED不得通过重复业务POST消耗；未命中或未解决gate令本例及后续serial失败。deadline须实际DROPPED，不为清理补决定。Profile没有放弃草稿/撤回Review/删除命令，失败DRAFT/PENDING留至隔离环境销毁，不能seed终态或用决定“清理”。finally关闭各case自己的页面/handler，释放已知HELD，不触碰既有账号/权限相位；未知准备不得假称通过。

先新增准备相位/严格绑定/未知回执/并发/最小披露Node合成红绿测试，再普通回归、strict、官方固定pin生成漂移和Edge。冻结runtime/runner/spec后，每轮重新pull发布latest，先18项决定专项，再默认无参数106项完整门禁，以实际运行/失败/skip数为准。原25条Application错误缓存头保留，不代理补头、不编译后端/本地artifact替代，完整门禁红时不push。

本包只补所列Profile交错。Profile加载后关系冲突、不同修订公开指针并发、策略退休/Scope/全部依赖故障与完整决定跨Session矩阵、UC001/fencing仍OPEN。新产品问题须终态清理后最小修复、重新冻结复验；不以18项通过关闭完整UC006/007或全部Console目标。

## 实施与预检

Console冻结`a89e2e4`，仅固定准备器、runner控制和3项浏览器spec增量，无产品UI改动。工厂直接使用固定生成Proto的List/Get/ReviewerDetail，新增11项先RED（缺factory）后GREEN，adapter另1项合成接线：提前相位不产生外呼写、固定App/原REJECTED Profile ID、owner/reviewer三原DEVICE保持、未知写只读确认及多候选/指针/历史/snapshot拒绝。12项新增Node不当作真实Create/Submit或治理命令证明。

统一`pnpm test`903项Vitest＋172项Node全部通过，`pnpm typecheck`、`pnpm generate:check`官方同pin、`pnpm edge:e2e`均exit0，Node语法与diff检查通过。开始18项published专项，运行期冻结runtime/runner/spec，未push。

本次Cloudflare HTTPS DNS再次查询`www.wikipedia.org`所得CNAME为`dyna.wikimedia.org`、A为`103.102.166.224`，与此前轮次`198.35.26.224`不同。因此冻结前将两入口共用的测试App显式NSS fixture和日志同步到103地址；不修改后端网络规则、不访问外部HTTP，也不当部署DNS/内容安全证据。每轮published latest依然必须重新pull、轮内固定解析ID；本输入变化不回写此前轮次历史。

## Published 专项终态

冻结Console `a89e2e41b4955b9d81fb3281d20e54ca6e7f503a`，`pnpm test:real tests/real/review-decisions.real.spec.ts`实际18项全部通过（2.1分钟、exit0，无skip或retry）。原15项全部保留并通过；新增Profile重叠决定5.1秒、真实deadline恢复32.6秒、重新确认后迟到成功回执3.1秒。22个实际决定响应的private/no-store均为真：Version 200×7、403×4、409×1；Profile 200×7、403×1、409×2。

本轮`iwut-console-real-34189`容器及network在进程终态后均核验为空。专项不代替默认完整门禁，也不关闭完整UC。随后已启动同冻结源码的无参数全量，运行结果待终态确认；运行期间不改变runtime/runner/spec，不push。

两轮均重新pull published latest；当前全量拉取所得Auth/App/Gateway ID与专项相同，支持组件ID亦记录如下，不能用标签不变代替实际解析ID：

| 组件 | 本轮专项解析的镜像ID |
| --- | --- |
| Auth | `sha256:c2f06d8fe4ca2734a32e07e70f6ab7ba8c0207932336222c2c92986e073de8b9` |
| App | `sha256:2af4af71e8eb8f1ea46e92bfdaa3e8e14944cb0bc4ca46b95c9a05db6c46340a` |
| Gateway | `sha256:2953ae7fb81da7d06586b735340e4d3d320e523bb67f7700cc2571602e728303` |
| Mongo | `sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3` |
| Traefik | `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0` |

## 默认无参数完整门禁终态

`iwut-console-real-41545`在相同干净冻结`a89e2e41b4955b9d81fb3281d20e54ca6e7f503a`下执行`pnpm test:real`，实际106项全部执行：**103通过、3失败，无skip/retry**，浏览器18.7分钟、exit1。原103项和新增3项均运行，不用专项代替完整门禁。源码、runner/spec及artifact来源运行期间未变；严格类型、标准报告隐私前置和生产build通过。

全部18项决定再次通过；新增Profile重叠决定4.5秒、真实deadline/PENDING恢复32.7秒、重新确认后的迟到成功回执3.2秒。22个决定响应的private/no-store再次全部为真，分布与专项一致。原Admin查询56条错误头断言继续通过；未知结果不自动重放、正式双向转让和权限恢复等原矩阵未被跳过。

25条失败断言逐条核对可信源码坐标和实际断言，全部仍为原Application管理查询错误响应缓存头，没有新增非缓存硬失败：

| 场景 | 断言数 | 可信失败位置与含义 |
| --- | --- | --- |
| 管理权转让 | 3 | `management-transfer.real.spec.ts:257:29` ×3，Application GET404缺no-store |
| owned游标负例 | 10 | `owned-application-pagination.real.spec.ts:200:57` ×4、`:201:58` ×4、`:220:66` ×1、`:221:67` ×1，五个List400各缺private/no-store |
| 非owner角色读取 | 12 | `qualification-read-matrix.real.spec.ts:368:54` ×6、`:368:116` ×6，六个Application GET404各缺private/no-store |

soft断言仍令三个用例和完整门禁失败，未补代理头、删断言或改变成功标准。管理权/角色的其它功能与最终Session断言照常收齐。当前发布接线已支持审核决定链路；待后端发布补齐上述错误头后再拉latest复验，不把此问题误报为Gateway未接入。

本轮五镜像逐轮pull的解析ID与上表专项逐项相同，来源仍是published-latest，没有编译相邻后端或回退local-compat。轮内显式NSS输入保持103地址，仅属测试fixture。终态后本轮及全部real测试前缀容器（含退出）与network均为空，源码仍为上述冻结且干净；legacy本地/本次远端只读核验均为`e68851e343bd0e077e5ccd0b680fe6813216ced0`。提交仅本地、未push。

本包所列三项已实现并获专项/完整回归证据；整体门禁仍IN_PROGRESS，原Console完整目标不缩减。Profile加载后关系冲突、不同修订公开指针UI并发可达性、策略退休/Scope/全部依赖故障、完整决定跨Session、其它资格/生命周期组合及UC001/fencing继续OPEN。不同修订指针场景须遵守单一working修订约束，不能seed出平行PENDING或用故意错误pointer协议负例冒充UI并发。
