# UC-CONSOLE-020：审核平台脚本版本

状态：`ACCEPTED`，2026-11-10，用户授权自行设计、接受并实现脚本管理范围。实现：`LOCAL_VERIFIED`。

## 目标与权威引用

独立脚本 Reviewer 在 Admin Console 读取固定受审内容，作出一次明确的批准或拒绝，并查看拒绝级联的实际进度。业务权威为 App [UC043](../../app-center/use-cases/UC-APP-043-submit-script-version-review.md)、[UC044](../../app-center/use-cases/UC-APP-044-decide-script-version-review.md)、[UC045](../../app-center/use-cases/UC-APP-045-query-script-management-and-reviews.md)、[UC049](../../app-center/use-cases/UC-APP-049-cascade-script-rejection.md)。共同交互与 AUTH-D1 依赖见[总案](../design-notes/2026-11-09-console-completion-design.md)。

## 页面结构与内容组织

建议 `/reviews/scripts` 为与应用版本/资料平级的独立队列；详情为 `/scripts/$resourceId/versions/$versionId/reviews/$reviewId`，可从队列或版本历史直达。返回队列恢复合法分页，不要求先逐层进入资源。

详情以审核身份和快照为中心，组织为：用途与版本概况、受审原文与摘要、完整绑定政策与检查项、利益冲突/当前可决定状态、决定记录与级联状态。资源当前元数据如另行展示须标注为当前资料，不能替代提交时的快照。原文只作为文本阅读，不执行，不使用 App 运行内容接口绕过审核读取。

## 决定流程

1. 正式 GetScriptReview 取得同次一致详情；使用 canDecide/conflicts 表达能否决定及原因，不仅凭前端比较创建者 ID。拥有维护或 App 审核权不代替脚本审核权。
2. 检查项逐项展示服务端返回的完整定义，按 mandatory 与 checkId 组装确认，不在前端硬编码政策项语义。界面明确这是人工审查声明，不声称有运行/机器检测结果。
3. 批准或拒绝前重读详情。固定受审事实与绑定定义相同、当前仍可决定时可保留同一工作位的有效确认；事实变化使旧确认失效。当前全局政策切换不重绑这个提交。
4. 批准确认显示目标与完整必检确认；拒绝要求原因，发送空检查确认集合。原因与长度按 UC044；理由编辑与最终确认同源，不提交未经展示的内容。
5. 每次确认只发一次 DecideScriptVersionReview，携带正式详情的 revision 与 policyVersion；不客户端伪造决定人或决定时间。返回终态后只读展示，不提供终态覆盖/互转。

并发决定、冲突或资格变化要求读回，不自动再决定。响应丢失先按原 reviewId 读取唯一决定与级联事实；“当前已批准/拒绝”只说明当前终态，不能将他人决定认作本人提交成功。

## 拒绝级联呈现

拒绝成功只表示脚本终态与持久级联义务已保存。页面分别呈现决定成功与级联 PENDING/RUNNING/COMPLETE，不用“全部依赖应用已拒绝”替代未完成事实。

显示服务端实际 taskId、观测时间、已处理/实际拒绝/既有终态/关闭豁免计数和允许披露的失败类别，不编造总数或进度百分比。详情打开时可以有界只读刷新，离页/失权停止；没有合法总量时只展示实际计数。没有依赖也等待后端完成判定。前端不触发 SYSTEM 级联、不提供“重试全部”命令，不列举没有读契约的受影响应用。

## 验收安排

独立脚本 Reviewer 与维护/发布/App Reviewer 权限分离；创建者、内容贡献者、提交者冲突；完整策略确认、拒绝原因、旧政策绑定；两个决定竞争和未知结果恢复；终态出队但历史可达；级联未完成/完成/受控失败忠实呈现。真实链覆盖脚本拒绝→待审应用受阻→级联收敛，客户端观察不能代替后端收敛证据。
