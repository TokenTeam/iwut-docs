# UC-APP-043：提交脚本版本审核

状态：`ACCEPTED`

## 目标与主流程

符合 [BR-SCR-002](UC-APP-041-manage-script-resource.md#br-scr-002) 的 Developer 使用 `SubmitOwnScriptVersionReview`（`POST /v1/users/me/script-resources/{resource_id}/versions/{version_id}/reviews`）提交本人的 DRAFT。输入为 resourceId、versionId、expectedRevision。服务在同一写事务检查退出栅栏、本人归属、父子关系、状态和 revision，取得 ACTIVE 脚本政策，原子保存固定快照和 PENDING ScriptReview，同时把 ScriptVersion 改为 SUBMITTED 并递增 revision。

## 业务规则

<a id="br-scr-007"></a>
### BR-SCR-007：单次提交与固定受审对象

每个 ScriptVersion 首期最多一次审核。ScriptReview.snapshot 固定 resourceId、versionId、versionLabel、contentFormat、完整原文、digest、源 revision 及贡献者，并保存提交时的资源名称、用途和元数据 revision。submittedBy/At 来自可信身份和服务时钟。版本创建者、实际贡献者和提交者须与资源所有者一致。Version → SUBMITTED 与 Review → PENDING 同成同败。重复提交或过期 revision 返回冲突，作者可按 [UC045](UC-APP-045-query-script-management-and-reviews.md) 查询当前结果。

<a id="br-scr-008"></a>
### BR-SCR-008：提交时绑定正式脚本政策

政策由后端固定管理，不复用 App v3 的检查 ID。Review 保存 policyBinding 和完整不可变政策定义；读取/决定使用该提交绑定版本，后续切换 ACTIVE 不能打断既有待审。首期为 `crawler-script-manual-v1`，每项 mandatory=true，正式文本如下：

| checkId | title | description |
| --- | --- | --- |
| `declared-purpose` | 用途符合平台说明 | 人工确认文本实现的采集用途与资源用途一致，不夹带无关行为。 |
| `client-execution` | 客户端可执行性 | 人工确认目标客户端能够按声明格式处理该文本，必要入口、规则与失败处理可用；此确认不是后端运行证明。 |
| `data-and-credentials` | 数据与凭据边界 | 人工确认不存在内置账号凭据、令牌或将用户凭据及采集数据发送到未经说明目标的逻辑。 |
| `network-and-resource` | 网络与资源使用 | 人工检查访问目标、请求频率、终止条件和资源使用，确认没有与用途无关的请求或无界采集。 |

审核详情返回完整 id/title/description/mandatory，前端不凭 ID 猜政策。无 ACTIVE 或绑定政策不可验证时送审失败，不能降级为无检查项。首期不新增运行时编辑政策后台或机器检查执行器。

<a id="br-scr-009"></a>
### BR-SCR-009：未来机器检查的事实边界

未来检查证据以固定 versionId、digest 和检查器/政策版本关联，不能改写正文或既有人工决定。本轮不创建虚假的机器通过项、自动执行器或未接受的检查状态机；是否影响最终批准须另行修订政策和 UC。

## 结果与验收

成功返回 reviewId、SUBMITTED、版本新 revision、提交时间和绑定政策；不批准、不发布、不修改引用它的应用。依赖的应用仍依 [UC048](UC-APP-048-manage-application-script-dependencies.md) 可提交。

- 提交与编辑竞争，不得得到摘要/原文混搭的快照。
- Developer 只能提交本人版本。平台治理授权不能代他人送审。非本人目标或跨资源版本统一 NotFound。
- 政策切换的两个提交胜序各绑定一个完整政策，不能取到两个版本的混合检查。
- 已提交文本不能再编辑；政策定义缺失使读取/决定失败关闭，不临时套用新政策。
