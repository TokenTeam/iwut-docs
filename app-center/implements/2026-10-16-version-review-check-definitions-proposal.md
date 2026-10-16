# Version 正式审核检查定义设计草案

状态：`ACCEPTED`（2026-10-16 用户审核通过）。本文保留为非权威设计审核记录；实施以 UC005/030/031 与查询契约为准。

本提案已接受并收敛进权威正文；以下为审核时的设计记录。业务权威仍为 [UC005](../use-cases/UC-APP-005-decide-application-version-review.md#br-rev-016) 与 [UC030](../use-cases/UC-APP-030-query-application-version-reviews.md)。

## 问题与建议

当前 `ReviewPolicyContext` 仅返回 version 和 requiredCheckIds；持久化的 Version 策略也仅保存检查 ID。Console 无法据此向 Reviewer 展示有权威来源的确认条件。API Session 路径完成联合验收并不消除此缺口。

建议由 App Center 保存并返回正式检查定义，启用不可变 `app-version-review-v3`，保留 v1/v2 的既有内容和历史决定。此次补齐了规范性条件，不能将新文本追写成 v2 当年的定义。四个 ID 保持不变，含义由 policy version 与 ID 共同确定。

## 拟接受的 v3 检查文本

以下文字本身需要用户审核；接受后成为 v3 的完整人工检查基线。它不引用尚未交付的学校政策、外部内容标准或隐含评分规则。

| ID | 标题 | 定义与确认条件 |
| --- | --- | --- |
| `content-policy-reviewed` | 应用内容与声明 | 已阅读提交快照中的应用声明，并结合实际入口确认其用途可识别且与展示功能一致；未发现冒充平台或其他主体、诱骗提交账号凭据、隐瞒实际收集用途或诱导执行恶意程序的内容。无法辨明用途或无法完成这些确认时，不得确认通过。 |
| `launch-url-content-reviewed` | 实际入口内容 | 已访问该审核快照的 launchUrl，并检查入口及其正常跳转后可达的主要功能；能实际观察到与声明用途一致的应用内容，未发现伪装登录、凭据窃取或恶意下载引导。入口不可达、仅有占位内容或必须使用 Reviewer 无法取得的访问条件而无法完成检查时，不得确认通过。 |
| `requested-access-reviewed` | 请求能力与 Scope | 已逐项检查快照声明的能力和 Scope，并结合其正式目录含义与实际功能确认用途可说明、请求范围与所展示功能相符，未发现无关或明显多余的访问请求。空集合表示已明确确认该版本未声明相应访问请求；目录含义或用途无法查明时，不得确认通过。 |
| `oauth-redirects-reviewed` | OAuth 回调用途 | 已分别检查 pkceRedirectUris 与 confidentialRedirectUris 中每个回调与应用用途、接收方及对应 client type 的关系，确认回调由预期接收方使用，且无明显无关接收方。两个数组均为空时，明确确认该版本未配置 OAuth/OIDC 回调。不能确认接收方或用途时，不得确认通过。 |

人工判断针对审核快照和当次可观察内容，不承诺穷尽所有页面、实际 OAuth 运行成功、远端内容永不变化或所有恶意行为均已排除。系统继续独立执行 Scope requestable、HTTPS/DNS、OAuth 结构及 Developer 暂停门禁；人工勾选不能跳过这些检查。

现有 Version snapshot 没有用途说明正文；这里的“声明”仅指其已有 label、入口、能力、Scope 与回调配置，用途结合实际入口内容判断，不假设已存在额外说明字段，也不以当前可变 Profile 代替提交快照。

Reviewer 不能预勾选、用“全选”代替逐项确认，或在无法观察时猜测通过。不能完成检查时可以保留 PENDING；确认不满足要求并决定拒绝时，REJECT 继续使用有效 reason 和空 confirmedCheckIds，不新增第三种决定或结构化证据系统。

本提案只定义 Version 策略；Profile 策略及其已有检查文本不随同改写。

## 存储与查询契约

v3 每个 `ReviewCheckDefinition` 保存 `id`、`title`、`description`。上表第三列原文作为 description；标题及说明均是服务端拥有的 UTF-8 纯文本，不执行 HTML/Markdown，不由 Console 翻译成另一套政策。暂不引入多语言、外部链接、政策编辑 API 或独立政策服务。

约束：title 为 1–80 个 Unicode scalar values，description 为 1–2000 个；无首尾空白、无控制字符。v3 固定四项，按上表顺序保存和输出；ID 唯一。`requiredCheckIds` 等于 definitions 的 ID 集合，顺序也保持一致；决定入参和审计仍按既有规则作为集合校验、排序保存。上述长度约束与四项基线一起纳入 migration 的精确内容核对。

建议在 UC030 现有 `ReviewPolicyContext` 增加字段，保留已提交字段编号：

```protobuf
message ReviewCheckDefinition {
  string id = 1;
  string title = 2;
  string description = 3;
}
// ReviewPolicyContext 原有字段 1、2 保持不变。
repeated ReviewCheckDefinition required_check_definitions = 3;
```

查询在原有 MongoDB snapshot 内取唯一 ACTIVE policy 及其完整定义。v3 定义缺失、重复、与 requiredCheckIds 不符或不符合上述结构约束时，整次详情失败，沿用 `ApplicationReviewStateInconsistent` / INTERNAL；不能返回部分定义或让客户端补齐。正式文本由不可变存储和 migration 精确核对保护，不把政策正文硬编码进领域实体。权限、路径、队列摘要、no-store 和决定命令字段保持现有语义。

终态详情中的 `currentPolicy` 仍表示查询时策略，不表示历史决定采用的策略。Console 必须分别展示 `decision.policyVersion` 与当前策略：v1/v2 历史仅显示其已记录的版本和检查 ID，不借用 v3 文本解释为当年的确认条件。本次不增加历史策略查询 API，不伪造历史正式文本。

## 迁移和兼容

1. 新 migration 精确核对既有 v1/v2 记录，保留其检查 ID；允许预期的状态退役，不覆盖其业务内容。扩展 validator 允许旧策略仅有 ID，要求 v3 具有完整定义。
2. 在一个事务内将 v2 置为 RETIRED 并插入或精确核对 ACTIVE v3；不允许两个 ACTIVE、同版本不同内容或静默修复损坏。重复迁移应幂等。部署前备份与失败回滚沿用工程基线。
3. 未决定的旧 Review 不重新提交或重写 snapshot；其下一次决定读取当前 v3。已读取 v2 的旧请求按现有 policy OCC 失败，Reviewer 重新读取并逐项确认，不自动重发。历史已决定记录不重写。
4. 先生成共享 API 类型，交由 Console agent 升级严格 JSON 解码与校验。新客户端允许旧响应缺少 definitions 并继续只读；批准入口必须等完整 v3 定义就绪后才开放。缺失或未知策略不得回退本地文案。
5. 再协调 App migration/服务切换和 Console 页面刷新。现有 Console 使用 `ignoreUnknownFields:false`，旧页面收到新增 JSON 字段会失败；切换窗口要求刷新到兼容客户端，不能宣称仅增加 Proto 字段就对旧 JSON 页面无影响。部署由各服务负责人安排，本工作包不自动上线。

策略迁移后，不以切回旧二进制作为业务回滚：保留 v3 和历史，修复兼容问题或停用决定入口；不得重新激活旧政策并让同一批已确认输入获得另一种解释。

## 接受后的实现范围与验收

权威变更落在 UC005 的 BR-REV-016/017、正式策略小节及 UC030 的详情契约；对应 brief/spec 在同一设计提交中更新。实现再依次交付策略 Domain/Port/Mongo migration、API 与 transport、生成客户端及 Console 校验。共享 API 与其他服务改动由对应 agent 承接。

验收必须证明：

1. 四项正式文本、顺序、版本和 ID 集合在存储、HTTP JSON、原生 gRPC 一致；空白、重复、缺项和错误定义失败关闭。
2. 真实 MongoDB 迁移保留 v1/v2、精确核对 v3、重复执行幂等，故障回滚不留下双 ACTIVE；决定与策略切换竞争只接受当前策略。
3. v2 过期输入失败；v3 完整四项可批准，少项/多项/重复项被拒绝；REJECT 的空确认项及既有理由规则不变。
4. Console 不猜测 ID、不默认确认；定义不完整时不开放批准；历史 v1/v2 不套用 v3 文本。
5. 使用最长合法纯文本测量实际 JSON/protobuf 响应，保持 transport 上限；成功和错误继续 no-store，不泄露凭证。

## 审核点与后续顺序

请审核四项正文，以及采用新 v3 而保留旧版本的选择。用户接受后，才把提案收敛进上述权威来源并生成实施输入。

同一步的第二份草案是 [Reviewer 当前公开 Profile 投影](2026-10-16-reviewer-published-profile-proposal.md)。两份接受后先实现 App/API，再交接 Gateway 的两个精确 ADMIN 决定路由，最后由 Console agent 接入决定与联合验收。开发者创建、编辑、提交、发布写页面仍需其对应已接受的 Console 工作包，不能把这三项审核依赖等同于全部写页面交付。
