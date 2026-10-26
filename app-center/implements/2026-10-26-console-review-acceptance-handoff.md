# Console UC006/007 已接受设计的文档交接

状态：`ACCEPTED / DOCS_APPLIED`，2026-10-26。用户已同意两项审核设计草案，并要求编写/修改相应用例。本文件保留已接受文字的交接与落地记录，不是第二份 Console UC 权威正文，也不是实现或跨聊天消息授权。

App权威调整已写入UC005/016/030/031和ADR004。初次交接遵循用户分工，未修改Console专用工作区。2026-10-26用户随后要求解决docs问题并整合全部分支；核对console-uc002仍为干净的534f02f后，在整合main中将下列已接受文字写入Console UC006/007并同步实现索引。Console专用工作区和业务代码不改，未运行新增联合验收，不能据文档落地宣称实现或门禁完成。

## 来源与边界

- 原文为 docs `console-uc002@534f02f` 的 [UC006](../../console/use-cases/UC-CONSOLE-006-review-application-versions.md)及 [UC007](../../console/use-cases/UC-CONSOLE-007-review-application-profiles.md)。落地时先核对所有者是否有更新，不覆盖其未提交内容。
- App 当前业务权威：[UC005 正式发布流程](../use-cases/UC-APP-005-decide-application-version-review.md#策略正式发布与运维读回)、[UC016 BR-PRF-028](../use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-028)、[BR-PRF-030](../use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-030)、[UC031 兼容门槛](../use-cases/UC-APP-031-query-application-profile-reviews.md#策略版本兼容门槛)。不在 Console 复制 App 发布状态机、政策文本或 Scope 写模型。
- 缓存头的已发布专项35/35、完整115/115为已完成证据，不重开旧故障，不把新增设计误记为已实现。
- Scope管理归Auth，其独立接受的[UC036](../../auth-center/use-cases/UC-AUTH-036-release-scope-enablement-changes.md)与[CORE_COMPLETE / FULL_REGRESSION_PENDING交付记录](../../auth-center/implements/UC-AUTH-036-readiness.md)已合入；App草案的接受不代替Auth审核或真实联合验收。

## UC006：替换验收第4项

> 4. 两个 Reviewer 并发、依赖故障、响应丢失/断网及 PENDING/终态重读经真实后端验证。策略变化使用获批的 App 正式发布变更，Scope 失效使用 Auth 所有者的正式变更入口；页面加载旧事实后，真实旧请求被拒绝，重读并清空确认，禁止自动重放。组件恢复测试与事务并发测试分别标记层级，不能替代上述真实变更链；正式变更准备条件未具备的项继续待验收，不以错误版本输入或直接改库关闭。

同时将 UC006“依赖事实、缺口与实现选项”中旧缓存头仍红的当时描述注明为历史：当前缓存已由已发布复验关闭；正式策略发布回执/运维读回仍待实现；Auth Scope管理核心实现已完成但完整回归与接入/联合准备尚未闭合。Version 现有正式定义、ADMIN surface、权限链不再作为缺失项。保留 BR-CRV-002/003 的确认绑定、重读和禁止自动重放。

Scope 验收遵循 App ADR001 的实际 TTL/实例/在途窗口，不假定 Auth 变更瞬时跨库生效，不直接清缓存或伪造 Clock；正确策略下的 Scope 400错误与策略409分开标识。真实下一份政策须另审，不制造同义 v4 或回激活旧 v2，仅为证明一条测试。

## UC007：替换验收第4项

> 4. 同一 Review 的双 Reviewer 决定经真实链路验证最多一个成功，另一个按稳定冲突 reason 重读，不自动重放。按单工作位规则验证首次批准后顺序创建、提交并批准下一修订，以及当前公开指针与历史投影。公开指针前置冲突单列为协议防御验收：一条合法 PENDING 使用与正式当前指针不相符的 expected 值时真实返回409且无部分写；该负例不称为“不同修订并发”。前端对该 reason 的重读、展示替换目标、清空确认和重新评审由明确标注的组件/状态恢复证据验证，不伪造为当前可达的浏览器业务竞态。revision、策略变化、响应丢失与权限撤销仍按规定恢复；需要正式准备能力的项保持待验收。

保留 BR-CRV-006、真实 pointer 来源、显式 NONE/缺失区别，以及批准自动公开、拒绝不改变旧公开资料的既定规则。把依赖段/实现索引中“不同修订并发准备缺口”同步为“按用户已接受的单工作位可达性分层验收”，不添加第二工作位、seed 平行 PENDING 或历史重新发布能力。

## 覆盖索引与证据标签

| 证据 | 正确标记 | 不得冒称 |
| --- | --- | --- |
| 现有同 Review 实际200/409 | 一次性决定真实竞争 | 不同修订公开指针竞争 |
| 错误 expected pointer 实际409 | 协议防御负例 | 页面从有效旧指针遭遇不同待审修订抢先批准 |
| 顺序批准和 Admin→Developer 投影 | 单工作位释放、顺序替换及真实读回 | 两份同时 PENDING |
| PublicationConflict 组件输入 | 前端重读/清确认/不自动重放恢复 | 生产链发生真实不同修订竞态 |
| 获批政策发布/Scope 正式变化 | 具备准备入口后才执行真实变化验收 | 当前仅有设计就已验证 |

落地只调整文档、验收层级和覆盖标签，不删除实际断言或把缺失的真实发布链改称已完成；若后续改测试，实现与门禁单独授权和执行。本次整合已修改Console UC006/007及文档索引并形成本地提交；没有修改业务源码、发送跨聊天消息或push。
