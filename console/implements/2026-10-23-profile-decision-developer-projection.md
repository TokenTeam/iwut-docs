# UC004/007：真实资料批准结果贯穿Admin与Developer只读页面

状态：`ACCEPTED / NOT_STARTED`，2026-10-23，按用户持续授权自行接受。当前09f7805的114项全量仍运行，本包不修改其冻结源码；待其终态记录后才实施。

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
