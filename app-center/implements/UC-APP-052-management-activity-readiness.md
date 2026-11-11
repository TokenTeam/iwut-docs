# UC-APP-052：Application管理动态实施记录

设计：`ACCEPTED`。App后端实现：`COMPLETE`（仅本轮App范围）。2026-11-09。

## 范围与依赖

用户授权仅实施App Center；共享App Proto/生成物交API agent，明确不推进Console。权威为[UC052](../use-cases/UC-APP-052-query-application-management-activity.md)、BR-APP-067–071及[读契约](../query-contracts/application-management-activity.md)。UC034仅增加独立历史查询引用，原latestReview不变。

API agent已在App/API完成本地提交`7651f96ceb85f11784660521b0f3c8a7c30d7d57`（父a57bb969），包含新服务、两个RPC/HTTP annotation、六类kind、互斥target、Value字符串/null理由及生成物；其proto-check和Go测试通过。后续用户授权Gateway接入及四后端commit/push；四处API现已统一到该提交，最终发布状态见下节。

## 实现覆盖

| 规则 | 实现与验证定位 |
| --- | --- |
| BR-APP-067 | 当前owner授权在snapshot内，非APPROVED Developer仍可读；转让前后/重新获得管理权的旧token；UseCase、Mongo、Wire E2E |
| BR-APP-068 | Version/Profile提交与决定稳定定位；原拒绝/恢复/新attempt、自动拒绝复用源事实；Mongo历史与新attempt专项 |
| BR-APP-069 | 列表无理由，详情最小原始理由/明确null，无Reviewer/策略正文/凭据；Transport及HTTP/native生成客户端 |
| BR-APP-070 | majority只读snapshot、必要源与批量父关系校验、损坏/不可用失败关闭、512KiB编码预算；Mongo故障/并发快照和Transport预算 |
| BR-APP-071 | 四来源各pageSize+1、全序合并、只推进实际返回项；归属/主体/筛选HMAC、显式0043索引及查询plan；Mongo/Domain/Cursor专项 |

没有活动集合、个人收件/已读字段、业务审计/访问写入、outbox或worker；不调用Auth/Scope/DNS。普通启动不建索引，部署前显式执行0043 migration，readiness要求最新ledger。

## 最终验证

Go 1.25.5标准`make check-full` **24/24 PASS**，`changed_sources=[]`。最终报告为App仓库`.artifacts/verification/20261109T145017Z-nsyjpfp3/report.json`；Mongo race 2275.135秒、生产Wire HTTP/gRPC E2E 278.440秒，末项退出码0，完整报告已正常收尾。

| 冻结输入 | 版本与内容指纹 |
| --- | --- |
| App | HEAD `3c611d910f605cfc394726095926d3d21607bf2c`加本轮未提交改动；sha256 `c41ecb23c2d5be22b7871ecaaf14ec55a9b3990a935a38bc2b68e9d8305459d5` |
| App/API | 本地提交`7651f96ceb85f11784660521b0f3c8a7c30d7d57`，工作树干净；sha256 `045f0e64d5563d1aa031908ea49e8beee2bde08ccfabec885dcf942579a2f696` |
| 独立文档快照 | 提交`5ddb44af80a22942cb88491bb4c4503d5686ecff`；sha256 `61cc87d53adb5e19bb2e4b68ba31847194e708b26c7312f2f007a9a65ad75843` |

验收使用独立已提交文档快照；本节和导航中的完成状态是验收后附记，不修改已验收App/API内容。该轮验收在App提交前完成；后续App原样提交与四仓库push状态见下节。未修改共享Auth身份行为，因此未要求cross-service tier。

## 后续Gateway接入与提交推送（2026-11-09）

用户追加授权Gateway接入，并要求API→Gateway→Auth→App串行commit/push；Console不推进。该阶段已完成，四仓库工作区及API副本均干净，远端分支SHA已逐个核验。

| 仓库 | 已推送分支 | 最终提交 |
| --- | --- | --- |
| API | integration/script-query-api-20261106 | `7651f96ceb85f11784660521b0f3c8a7c30d7d57` |
| Gateway | auto/script-routing-c9f2 | `1959056e650909bc35e233bd427b4037310d9199` |
| Auth | master | `8921b8354f3252a66f735e5e74489d6e62bfe749` |
| App | auto/script-review-uc043 | `921cd4062db05ab6dae9a560461b690d31d0f847` |

三个服务gitlink与四处API工作树均为7651f96，tree `08e6636894861d668c2c3888731028bb69ed6403`。App提交tree `f17949284e370affda27c65c3ae759af4728e83f`，提交前后逐文件内容/权限比较完全一致，沿用上述完整门禁证据；本地证明在`.artifacts/uc052-commit-proof.json`。

Gateway新增两条UC052路由，外部方法总数165；check、完整协议E2E及scratch运行镜像`/gateway-config`渲染检查通过。真实Auth Session→Gateway→App/Traefik的HTTP/JSON、native gRPC、gRPC-Web均验证owner列表/历史详情200、非owner404、拒绝理由原值、提交项显式null、最小投影与private,no-store；Developer surface可达、Admin无该surface，含CSRF及伪造身份清理。Gateway完整记录见代码仓库`docs/verification/2026-11-09-application-management-activity.md`。

| 固定镜像输入 | 镜像ID |
| --- | --- |
| Auth 8921b83 / API7651f96 | `sha256:7c9a73d3a1b9508ddd8e6ab884f6f1a36ab06bee2c649025df3f1789609dffb4` |
| App 921cd40 / API7651f96 | `sha256:c3eac14a20d90d0385229822c9c686d7270964c4810d4ba7e6a07d06fffa733f` |

Auth owner完成UC027/038/039全部已接受后端的本地提交、check、race及真实Mongo/Wire专项，保留待审脚本本人读取设计。仅git提交/推送与本地镜像联验，未合并其他服务分支、未部署，也未推进Console实现。文档工作区不在本次四后端push范围。

## 2026-11-11 主分支与镜像发布

用户后续授权后端主分支合入与镜像核实，App GitHub/CNB `master` 已快进并推送至 `db01313ea76198461b3dc75561bf1804e1bcf676`，API gitlink 为 `241d56de6f8a3f68ed91969a4239a8c9fe32baad`。GitHub 同步和 CNB 构建均成功，提交标签 `db01313e` 与 `latest` 的 OCI index digest 均为 `sha256:19be6256c85b32ebf6c9c43f78e75575f866340deb995ad7cbfe04cfbb974fdd`。完整输入、当前依赖补验和 published-image 交接见[发布记录](2026-11-11-accepted-backend-release.md)。

上文 11 月 9 日的 Console 不推进、仅本地联验及文档未推送均保留其当轮历史含义。后续 Console UC023 已接受，其实现和发布由 Console owner 维护；App 文档本轮在独立 clone 提交。未新增通知、后台实时加载或其他新业务能力。

## 早期试跑记录

以下保留诊断和恢复证据；其中进行中/中断状态均已由上述最终验收关闭，不代替最终结果。

初轮真实Mongo专项23.455秒通过；加入生产Wire HTTP/native及生成客户端后的专项Mongo26.577秒、Wire7.808秒通过。补充的新attempt/查询plan/race专项Mongo35.027秒、Wire9.950秒通过。首轮完整门禁前23项通过后，检查发现既有迁移测试的精确索引预期需要同步0043新增索引，主动中止该轮（报告20261109T133620Z-4mjyj6u9，非通过证据）；已补齐两个测试文件的预期，保留精确集合断言。迁移专项随后发现ledger精确编号清单仍停在0042，已同步expectedIntegrationMigrationIDs和逐项升级链为0043；未弱化数量/顺序/幂等断言。最终迁移race专项32.150秒通过，Wire本轮无匹配测试。UC052专项已通过，重新冻结完整backend进行中，最终以报告为准，不把专项等同完整门禁。

## App独立实现阶段边界（历史）

最初App实现阶段未修改Auth/Gateway/Console源，未通知Console实施；其后的Gateway接入与四仓库push已按用户追加授权在上节关闭。Console页面及浏览器UI实现仍不推进，未进行部署。

### 聊天中断后的恢复

第二轮冻结门禁`20261109T134112Z-suindrrt`在聊天意外中断后，其独立子套件继续完成，日志记录Mongo2313.383秒及HTTP/gRPC E2E290.232秒均为ok。但主runner已退出，report停留running/23项，未记录末项退出码和最终源核对，因此不把该report改写为完整PASS。

恢复后核对App/API内容指纹与开始时一致，使用同一已提交文档快照f4ced9bd923545f53af23a538b0eee0826968079重新运行标准check-full。该轮为`20261109T143220Z-u_cz7xdd`，由独立进程直接写日志和报告，不依赖聊天连接；该轮在代码自检发现重复稳定ID校验缺口后主动中止，report为interrupted、changed_sources=[]，不计为通过。前述两轮启动之间没有修改App/API业务内容。

### 必要窗口的重复稳定定位校验

自检发现Domain页校验只保护全序，未拒绝同一activityId以不同occurredAt重复出现。新增Domain回归先复现失败（返回nil），随后补齐稳定ID去重校验；Mongo在最终页及必要lookahead内同样失败关闭，不允许重复定位进入下一页。加入删除隔离测试库Review唯一索引后插入重复源的真实Mongo回归，验证列表/提交筛选/单项均500且无部分结果。正常同Review提交和决定的ID不同，仍保留两项。该修复落在既有BR-APP-068/070损坏边界内，不增加API/UC语义；已按新App内容指纹完成上述完整验收。

修复后的Domain/Transport专项通过；真实Mongo+迁移race专项74.442秒、生产Wire HTTP/gRPC10.416秒通过（run-vaSpd9fu）。最终完整门禁使用此修复后的冻结输入，早先报告不替代最终结果。
