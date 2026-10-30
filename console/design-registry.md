# iWUT Console 设计注册表

状态：`ACTIVE`

本文件索引 Console 的 UC、BR 与 ADR。它不复制权威正文。当前注册表人工维护，尚未接入 `tools/registry.py`。

## Use Cases

| ID | 标题 | 状态 | 权威位置 | 备注 |
| --- | --- | --- | --- | --- |
| `UC-CONSOLE-001` | 建立浏览器 Console Session | `ACCEPTED` | [UC-CONSOLE-001](use-cases/UC-CONSOLE-001-establish-console-session.md) | 共享认证入口；Gateway 路由已交付，实现进行中 |
| `UC-CONSOLE-002` | 查询我的 Application 管理概览 | `ACCEPTED` | [UC-CONSOLE-002](use-cases/UC-CONSOLE-002-query-owned-applications.md) | 查询、分页与私有读取已实链验证；证据范围见 implements，不表示整个UC关闭 |
| `UC-CONSOLE-003` | 只读管理 Application Version | `ACCEPTED` | [UC-CONSOLE-003](use-cases/UC-CONSOLE-003-query-owned-application-versions.md) | 查询与私有读取已有实链；编辑/提交另见UC008 |
| `UC-CONSOLE-004` | 只读管理 Application 资料修订 | `ACCEPTED` | [UC-CONSOLE-004](use-cases/UC-CONSOLE-004-query-owned-profile-revisions.md) | 查询、历史与私有读取已有实链；编辑/提交另见UC010 |
| `UC-CONSOLE-005` | 只读查询 Application Tester 管理 | `ACCEPTED` | [UC-CONSOLE-005](use-cases/UC-CONSOLE-005-query-application-tester-management.md) | 2026-10-16 接受并实现；真实镜像成功读取及失效回收基线通过，完整验收矩阵继续实施 |
| `UC-CONSOLE-006` | 审核 Application Version | `ACCEPTED` | [UC-CONSOLE-006](use-cases/UC-CONSOLE-006-review-application-versions.md) | 双权限/决定与恢复已有实链；策略发布等外部边界见 implements |
| `UC-CONSOLE-007` | 审核 Application 公开资料 | `ACCEPTED` | [UC-CONSOLE-007](use-cases/UC-CONSOLE-007-review-application-profiles.md) | 决定/公开指针/开发者投影已有实链；并发按接受的单工作位方案分层 |
| `UC-CONSOLE-008` | 版本与发布工作台及版本编辑 | `ACCEPTED` | [UC-CONSOLE-008](use-cases/UC-CONSOLE-008-version-workspace.md) | 版本创建/保存/送审实链通过；恢复/放弃与完整发布链分别验收 |
| `UC-CONSOLE-009` | 创建应用 | `ACCEPTED` | [UC-CONSOLE-009](use-cases/UC-CONSOLE-009-create-application.md) | 2026-10-30自主接受；页面/客户端与真实创建链已通过 |
| `UC-CONSOLE-010` | 创建、编辑与提交应用公开资料 | `ACCEPTED` | [UC-CONSOLE-010](use-cases/UC-CONSOLE-010-edit-application-profile.md) | 草稿/保存/送审实链通过，拒绝后预填新修订已实现并定向验证 |
| `UC-CONSOLE-011` | 管理应用测试邀请与成员 | `ACCEPTED` | [UC-CONSOLE-011](use-cases/UC-CONSOLE-011-manage-application-testers.md) | 2026-10-30页面已实现；首次创建/轮换/撤销/成员移除代表实链通过 |
| `UC-CONSOLE-012` | 管理应用 OAuth 客户端 | `ACCEPTED` | [UC-CONSOLE-012](use-cases/UC-CONSOLE-012-manage-oauth-clients.md) | 三渠道组件已实现；登记/启停/轮换与一次secret披露代表链通过 |
| `UC-CONSOLE-013` | 编排应用展示规则 | `ACCEPTED` | [UC-CONSOLE-013](use-cases/UC-CONSOLE-013-compose-application-display-filter.md) | 完整树与目录独立读取，设置/清空代表实链通过；本地结构编排补强 |
| `UC-CONSOLE-014` | 管理应用归档与管理权交接 | `ACCEPTED` | [UC-CONSOLE-014](use-cases/UC-CONSOLE-014-manage-application-ownership.md) | 专用读取/参与者全局页已实现；归档与KEEP/ROTATE代表实链通过 |
| `UC-CONSOLE-015` | 管理平台人员资格与可用状态 | `ACCEPTED` | [UC-CONSOLE-015](use-cases/UC-CONSOLE-015-manage-platform-governance.md) | 已实现并定向验证，真实spec已准备；独立运维精确权限发现缺口保留 |
| `UC-CONSOLE-016` | 查看与编辑本人账号资料 | `ACCEPTED` | [UC-CONSOLE-016](use-cases/UC-CONSOLE-016-edit-own-account-profile.md) | 共享六类型/明确set-remove已实现；双端普通USER五类型代表实链通过，AcademicGrade实链未覆盖 |
| `UC-CONSOLE-017` | 显式退出当前 Console 会话 | `ACCEPTED` | [UC-CONSOLE-017](use-cases/UC-CONSOLE-017-sign-out-current-console.md) | 精确Auth撤销与按代Console清理分别确认；专用BFF/Edge/页面待实施 |

## Business Rules

| ID | 标题 | 类型 | 权威位置 | 备注 |
| --- | --- | --- | --- | --- |
| `BR-CVW-001` | 资源创建与保存状态 | Console Version Workspace | [UC008](use-cases/UC-CONSOLE-008-version-workspace.md#br-cvw-001) | 完整快照、串行、未知不重放 |
| `BR-CVW-002` | 重置与离页 | Console Version Workspace | [UC008](use-cases/UC-CONSOLE-008-version-workspace.md#br-cvw-002) | 清空与真实写回区分 |
| `BR-CVW-003` | 独立快照与能力边界 | Console Version Workspace | [UC008](use-cases/UC-CONSOLE-008-version-workspace.md#br-cvw-003) | 三槽位、精确 surface |
| `BR-CSE-001` | 认证路径与账号边界 | Console Session Establishment | [UC001](use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-001) | 不把登录解释为注册或授权 |
| `BR-CSE-002` | 浏览器设备密钥保管 | Console Session Establishment | [UC001](use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-002) | Web Crypto + IndexedDB |
| `BR-CSE-003` | 签名前验证与规范编码 | Console Session Establishment | [UC001](use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-003) | 复用平台向量 |
| `BR-CSE-004` | BFF Session 与 Cookie 隔离 | Console Session Establishment | [UC001](use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-004) | 两个 Console 独立会话 |
| `BR-CSE-005` | 同源建立、并发与迟到响应 | Console Session Establishment | [UC001](use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-005) | 登录 CSRF 与竞态边界 |
| `BR-CSE-006` | 结果不确定与幂等恢复 | Console Session Establishment | [UC001](use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-006) | 不复原旧 token |
| `BR-CSE-007` | 错误、失效与隐私表达 | Console Session Establishment | [UC001](use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-007) | 按稳定 reason 映射 |
| `BR-CSE-008` | 功能可访问性与秘密生命周期 | Console Session Establishment | [UC001](use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-008) | 不规定视觉样式 |
| `BR-CMG-001` | 管理读取与动作权限分离 | Console Management Query | [UC-CONSOLE-002](use-cases/UC-CONSOLE-002-query-owned-applications.md#br-cmg-001) | `ACCEPTED`，随 UC002 实施 |
| `BR-CMG-002` | 私有页面数据与身份隔离 | Console Management Query | [UC-CONSOLE-002](use-cases/UC-CONSOLE-002-query-owned-applications.md#br-cmg-002) | `ACCEPTED`，随 UC002 实施 |
| `BR-CMG-003` | 私有分页与刷新 | Console Management Query | [UC-CONSOLE-002](use-cases/UC-CONSOLE-002-query-owned-applications.md#br-cmg-003) | `ACCEPTED`，随 UC002 实施 |
| `BR-CMG-004` | 错误、会话与可访问性 | Console Management Query | [UC-CONSOLE-002](use-cases/UC-CONSOLE-002-query-owned-applications.md#br-cmg-004) | `ACCEPTED`，随 UC002 实施 |
| `BR-CMG-005` | 当前 Version 与审核事实区分 | Console Management Query | [UC-CONSOLE-003](use-cases/UC-CONSOLE-003-query-owned-application-versions.md#br-cmg-005) | `ACCEPTED`，随 UC003 实施 |
| `BR-CMG-006` | 版本筛选、敏感运行声明与可访问性 | Console Management Query | [UC-CONSOLE-003](use-cases/UC-CONSOLE-003-query-owned-application-versions.md#br-cmg-006) | `ACCEPTED`，随 UC003 实施 |
| `BR-CMG-007` | 原文、指针与审核摘要忠实表达 | Console Management Query | [UC-CONSOLE-004](use-cases/UC-CONSOLE-004-query-owned-profile-revisions.md#br-cmg-007) | `ACCEPTED`，随 UC004 实施 |
| `BR-CMG-008` | 资料与审核历史独立分页 | Console Management Query | [UC-CONSOLE-004](use-cases/UC-CONSOLE-004-query-owned-profile-revisions.md#br-cmg-008) | `ACCEPTED`，随 UC004 实施 |
| `BR-CMG-009` | Tester 管理事实不扩张到用户资料或凭证 | Console Management Query | [UC-CONSOLE-005](use-cases/UC-CONSOLE-005-query-application-tester-management.md#br-cmg-009) | `ACCEPTED`，随 UC005 实施 |
| `BR-CMG-010` | 概览与两类列表独立恢复 | Console Management Query | [UC-CONSOLE-005](use-cases/UC-CONSOLE-005-query-application-tester-management.md#br-cmg-010) | `ACCEPTED`，随 UC005 实施 |
| `BR-CRV-001` | 精确权限、利益冲突与在线重查 | Console Review Flow | [UC-CONSOLE-006](use-cases/UC-CONSOLE-006-review-application-versions.md#br-crv-001) | `ACCEPTED`，随所属完整UC分阶段实施 |
| `BR-CRV-002` | snapshot、当前策略与确认绑定 | Console Review Flow | [UC-CONSOLE-006](use-cases/UC-CONSOLE-006-review-application-versions.md#br-crv-002) | `ACCEPTED`，随所属完整UC分阶段实施 |
| `BR-CRV-003` | 并发变化与结果未知恢复 | Console Review Flow | [UC-CONSOLE-006](use-cases/UC-CONSOLE-006-review-application-versions.md#br-crv-003) | `ACCEPTED`，随所属完整UC分阶段实施 |
| `BR-CRV-004` | 审核敏感状态与可访问性 | Console Review Flow | [UC-CONSOLE-006](use-cases/UC-CONSOLE-006-review-application-versions.md#br-crv-004) | `ACCEPTED`，随所属完整UC分阶段实施 |
| `BR-CRV-005` | 资料审核独立权限 | Console Review Flow | [UC-CONSOLE-007](use-cases/UC-CONSOLE-007-review-application-profiles.md#br-crv-005) | `ACCEPTED`，随所属完整UC分阶段实施 |
| `BR-CRV-006` | 资料批准的公开指针前置值 | Console Review Flow | [UC-CONSOLE-007](use-cases/UC-CONSOLE-007-review-application-profiles.md#br-crv-006) | `ACCEPTED`，随所属完整UC分阶段实施 |
| `BR-CRV-007` | 资料拒绝与实际终态 | Console Review Flow | [UC-CONSOLE-007](use-cases/UC-CONSOLE-007-review-application-profiles.md#br-crv-007) | `ACCEPTED`，随所属完整UC分阶段实施 |
| `BR-CRV-008` | 资料决定确认与恢复 | Console Review Flow | [UC-CONSOLE-007](use-cases/UC-CONSOLE-007-review-application-profiles.md#br-crv-008) | `ACCEPTED`，随所属完整UC分阶段实施 |

## Architecture Decisions

| ID | 标题 | 状态 | 权威位置 |
| --- | --- | --- | --- |
| `ADR-CONSOLE-001` | Console 仓库与应用边界 | `ACCEPTED` | [ADR-CONSOLE-001](adr/ADR-CONSOLE-001-repository-and-application-boundaries.md) |
| `ADR-CONSOLE-002` | 前端功能文档与视觉设计边界 | `ACCEPTED` | [ADR-CONSOLE-002](adr/ADR-CONSOLE-002-functional-documentation-boundary.md) |
| `ADR-CONSOLE-003` | Console 首版技术基线 | `ACCEPTED` | [ADR-CONSOLE-003](adr/ADR-CONSOLE-003-frontend-technology-baseline.md) |
| `ADR-CONSOLE-004` | Console 混合 BFF 与 Session ForwardAuth 流量边界 | `ACCEPTED` | [ADR-CONSOLE-004](adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md) |
| `ADR-CONSOLE-005` | 持久 Session 与登录流程 fencing | `ACCEPTED` | [ADR-CONSOLE-005](adr/ADR-CONSOLE-005-durable-session-and-login-fencing.md) |

## Next IDs

| 空间 | 下一个编号 |
| --- | --- |
| Console UC | `UC-CONSOLE-018` |
| Console BR-CVW | `BR-CVW-004` |
| Console BR-CSE | `BR-CSE-009` |
| Console BR-CMG | `BR-CMG-011` |
| Console BR-CRV | `BR-CRV-009` |
| Console ADR | `ADR-CONSOLE-006` |
