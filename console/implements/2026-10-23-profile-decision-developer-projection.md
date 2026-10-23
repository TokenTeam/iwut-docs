# UC004/007：真实资料批准结果贯穿Admin与Developer只读页面

状态：`ACCEPTED / IN_PROGRESS`，2026-10-23，按用户持续授权自行接受。前09f7805的114项全量已终态110通过/4失败并清理；本包在该轮结束后实施，不借前包证据证明改后源码。

## 用户价值与有限范围

开发者应能在自己管理的Application中看见管理员已实际批准的资料、哪份当前公开、哪份旧修订仅保留APPROVED历史，而不是只在Admin看到“已自动公开”。引用[UC004 BR-CMG-007/008](../use-cases/UC-CONSOLE-004-query-owned-profile-revisions.md#br-cmg-007)、[UC002管理概览](../use-cases/UC-CONSOLE-002-query-owned-applications.md)、[UC007](../use-cases/UC-CONSOLE-007-review-application-profiles.md)。后端决定/指针规则由其权威UC拥有，本包不重新定义。

这是尚未覆盖的跨端联合证据，不是已确认页面未实现。只加一个贯穿闭环，不扩成每个决定×每个页面组合，也不引入Developer创建/编辑/提交/发布UI。现有Profile只读组件已表达指针及最小审核事实；若真实读回揭示违约，先记录再最小修复，不伪造响应或放宽断言。

## 资源、身份与流程

复用原决定第3项已经正式APPROVED的两份资料：`resources[0].profile`和该项`next-profile`返回的replacement。只保存这两个实际ID供下一只读场景；不再创建/提交/批准、seed或改变quota。其Application未参与后续管理权转让；第3项失败则保持serial失败，不为准备下一例补写或换目标。不得把其它App的Profile并发/迟到准备混作这两份修订。

在现有26项决定专项末尾追加一项，预期专项27/默认115，以实际终态为准。既有owner在Developer origin通过正式EMAIL独立建立一个BrowserContext和non-extractable钥匙，仅此一次新登录；不复制Admin Cookie、storageState、设备私钥或Node Session。该登录可复用受测协议driver，必须明确其证据只是正式Auth/BFF主链；随后所有业务投影通过生产Developer React页面读取，不把driver当新的完整认证UI证明。尊重真实邮件冷却，未知签发不自动重放。

1. 正式确认Developer Session为原owner，读取原Application管理概览，实际currentPublishedProfileRevisionId应是replacement，working为空；只从响应投影表达，不从列表推断。
2. 经正式资料导航读取列表，两份修订均APPROVED，只有replacement具有当前公开标记；旧APPROVED不能显示为当前公开，不增加“再次发布”或回滚入口。当前指针与页级asOf从各自响应取得，不拼接跨页冻结快照。
3. 分别进入两个详情，正式latestReview/历史Review ID和APPROVED结果对应Admin实际决定，允许披露的policyVersion、reason、时间等事实从实际管理读回逐项对照；UI按既有最小字段展示。不补查Reviewer资料，不显示submittedBy/decidedBy/confirmedCheckIds/currentPolicy或Reviewer完整snapshot。决策历史policyVersion不等于当前策略。
4. 两详情的profileState仍指向replacement且working为空；列表、详情与概览均无Publish/创建/编辑/提交/回滚等新写入口，无新增业务POST/PATCH/DELETE。独立surface Cookie/Session/钥匙保持，不产生跨origin请求或私有响应持久化，private/no-store原断言保持。

现有概览仍有“具体Version管理将在UC003交付”的过时占位文案；允许最小更新为已实现只读范围的准确说明，不新增发布管理能力。该文案更新不是Version全决定跨端验收。

## 有限收口与真正开放项

完成当前全量后，实施索引要按“已实现/已实际覆盖/未覆盖/依赖外部能力”整理，历史失败与中断保留在对应工作包，不再把过时“待验收”段落反复当成新任务。不得因索引整理删除测试、抬高完成状态或把局部证据称完整UC。

明确继续开放：原25条Application错误缓存头与4条Gateway Session401缺private；策略发布/退休与Scope启停缺正式变更API；UC007不同修订并发准备受单一工作修订约束，不能seed平行PENDING；任意33+迟到carrier的无损Cookie自助恢复仍需独立架构处理。它们不由本只读闭环关闭。密码入口/设备治理/Developer写UI等未在当前阶段接受的功能不顺手扩入。

## 验证与交付

若只是补spec和占位文案，仍运行统一测试、strict、官方固定pin生成及Edge；冻结后每轮pull published latest完成27项专项和默认115项全量，不借前26/114替代。真实私有DOM/网络证据不扩大为全heap审计。所有既有缓存头失败继续作为红门禁，不编译后端、不用本地compat、不push红门禁；完整UC/外部依赖的最终收口需单独审计。

## 实施进展

已追加第27项独立Developer owner场景，保存原第3项两次真实决定的Review结果，对照管理概览、资料列表及两份详情的指针/审核事实与生产DOM；独立EMAIL/钥匙、不复制Admin凭据，业务请求只读、无跨origin或Session清理。概览过时Version占位文案先RED（1失败/30通过）后改为准确只读说明，同文件31项GREEN。实施索引已分开当前有界覆盖、有限开放项与历史，不再将首包待验收重复当作当前缺失。统一检查与本包27/115真实轮次仍待终态，不宣称跨端闭环已真实通过。

本次冻结前`pnpm test`为954 Vitest＋221 Node全部通过，仓库独立性294文件通过；`pnpm typecheck`、从官方固定27c输入的`pnpm generate:check`、`pnpm edge:e2e`及`git diff --check`通过。Edge重拉Gateway latest仍为2953ae7f，六ADMIN路由隔离/失败关闭通过；legacy本地与本次远端均为e68851e、未变。以上不是本包真实跨端验收结果，下一步须冻结后执行27专项和115无参数全量。

## published专项终态

冻结Console `32e83da`，轮次`iwut-console-real-186885`，27项全部执行、无skip/retry：26通过/1失败（3.0分钟、exit1）。27项body功能断言全部完成，新跨端只读场景用时5.4秒；最后一项仅被afterAll原4条Gateway Session401缺private标红，四个安全坐标均`review-decisions.real.spec.ts:44:143`，没有新增功能失败。原缓存头断言未删除；不能把body完成称专项全绿，Application另25条仍须默认全量重验。

真实独立owner在Developer origin正式EMAIL建立Session及一把non-extractable设备钥匙，没有Admin Cookie。生产概览实际读取replacement公开指针/无工作修订；列表两份均APPROVED、只有replacement当前公开。两个详情及各自latestReview/单条历史逐项对应原Admin实际Review ID、attempt、sourceRevision、提交/决定时间、策略版本、reason与APPROVED；旧批准修订不显示当前公开，两详情指针均保持replacement。原文与实际snapshot字段对照，不将Developer正文标成Reviewer snapshot；DOM不含未授权审核字段、写入口或外部媒体。业务GET均实际private/no-store，观测窗口零业务写/跨origin/Session DELETE，Session/carrier/设备钥匙保持。登录driver只证明正式协议链，不冒称新的完整React认证UI验收或全heap审计。

本轮重新pull published latest且轮内固定：Auth `sha256:c2f06d8fe4ca2734a32e07e70f6ab7ba8c0207932336222c2c92986e073de8b9`，App `sha256:2af4af71e8eb8f1ea46e92bfdaa3e8e14944cb0bc4ca46b95c9a05db6c46340a`，Gateway `sha256:2953ae7fb81da7d06586b735340e4d3d320e523bb67f7700cc2571602e728303`，Mongo `sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3`，Traefik `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0`。五ID与前09轮一致，API同pin、显式NSS fixture未改，runner strict/报告隐私/生产build前置通过。轮次容器（含退出）和network已核对为空，未编译后端、未改运行期产品/runtime/runner/spec、未push。

同一32e83da冻结继续默认无参数115项全量，尚未有终态；专项不替代全量，不以此关闭完整UC/外部门禁或其它有限开放项。

## 同冻结无参数全量终态

冻结`32e83dafaf00c460aae56a75949b58bab1b2c977`，轮次`iwut-console-real-193498`，默认无参数`pnpm test:real`完整执行115项、无skip/retry：111通过/4失败（19.5分钟、exit1）。全部27项决定body功能断言再次完成，新Admin→Developer只读闭环用时4.8秒；实际两份APPROVED与唯一replacement公开指针、管理概览/列表/两详情及真实Review事实/DOM、独立Session/钥匙/零写与隐私边界均按上述断言完成。不是把前114或专项替代本轮全量。

逐项核对29条失败的安全坐标：管理转让`management-transfer.real.spec.ts:257:29`×3；owned游标`owned-application-pagination.real.spec.ts:200:57`×4、`:201:58`×4、`:220:66`×1、`:221:67`×1（共10）；资格角色`qualification-read-matrix.real.spec.ts:368:54`×6、`:368:116`×6（共12）；决定afterAll `review-decisions.real.spec.ts:44:143`×4。前25条仍是Application错误响应缓存头；后4条仍是Gateway决定Session401缺private，no-store存在。没有新增非缓存硬失败，不删断言、不由代理补头，不把最后case因afterAll标红误当新跨端body失败，也不称门禁全绿。

本轮重新pull published latest，五解析ID与上方专项完全相同，轮内固定；API27c与显式NSS fixture不变，strict/报告隐私/生产build前置通过。运行期product/runtime/runner/spec未改，Console工作区干净；轮次容器（含退出）与network均为空，未编译后端、未push。本地与本次远端legacy仍`e68851e343bd0e077e5ccd0b680fe6813216ced0`。

所列跨端投影实现和真实联合证据已收齐；本包/完整UC的门禁状态仍IN_PROGRESS。后续按[有限开放项](README.md#有限开放项与外部边界)收口：先由对应后端published镜像修复原缓存头，策略/Scope正式变更与不同修订并发准备可达性不能靠前端伪造，33+迟到carrier架构问题不以32次显式重建替代。本包不自动扩成决定×所有页面/身份的无限排列，也不因外部未解决而新增未接受的业务UI。
