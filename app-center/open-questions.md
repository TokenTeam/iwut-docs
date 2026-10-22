# App Center 开放问题

2026-10-22 按已接受 UC 和最新实现记录核对。本页只把真正未决定的扩展保留为开放问题；38 个现行 ACCEPTED UC 的 App 后端已完成，固定输入的完整门禁为 2026-10-20 的 28/28 PASS，见[验收记录](implements/2026-10-20-uc033-036-oauth-fixture.md)。这次同步不改变 UC/BR、设计状态或此前暂缓决定。

## 仍需后续设计的问题

- 是否需要双人批准、按风险分配 Reviewer、SLA 或系统内申诉？现行 UC005/016 仍使用单次、一次性决定；新增工作流需独立设计。
- 外部自托管 URL 内容可在 URL 不变时变化。现有正式人工检查已描述弱保证；内容变化检测、摘要或平台托管仍属后续能力。
- requiredCapabilities 是否需要独立命名目录与治理上下文？现有兼容范围和能力匹配不因本问题暂停。
- Scope 删除、deprecated/retired 后，已批准 Version 与已授权 token 的联合处置如何扩展？新提交/批准的 scope 校验和 Auth 在线授权已有当前门禁；新的撤销政策需单独确定。
- 如何提升已有应用创建配额：人工调整、业务公式或独立申请流程？初始默认值已经确定，不再开放。
- 是否新增 CreateApplication 幂等键？现行创建仍按 UC001 的名称唯一和配额事务执行。
- 已完成审核决定的独立纠错/推翻与版本批准资格撤销如何审计并影响发布/OAuth？这些扩展暂缓，现有 decision 不原地改写。
- 受控 icon 资产由哪个上下文拥有，如何上传、固定内容版本、失效并迁移旧字符串？当前 icon 仍为不透明字符串，该扩展暂缓。
- 可靠告警投递如何衔接已有日志、审计和 outbox？投递闭环暂缓。
- AI DRAFT 审核读取哪些内容、怎样标识模型与政策版本、结论如何生效？当前不实现，也不增加 AI 状态或自动迁移。

## 已闭合的问题与接受依赖

- **初始配额**：[UC001](use-cases/UC-APP-001-create-application.md) 已确定进程配置 `APP_CENTER_INITIAL_APPLICATION_QUOTA`，未配置默认 10；首次建档使用该值，已有记录的 limit 保持权威。
- **Developer/账号状态消费**：[UC025 / BR-APP-011](use-cases/UC-APP-025-coordinate-account-owner-exit.md#br-app-011) 已确定普通身份、开发者写入口与角色敏感的审核批准门禁。Version 资格撤销不由状态投影隐式新增；相关扩展仍见上节。
- **Reviewer 权限与真实 USER**：权限管理由 [Auth UC004](../auth-center/use-cases/UC-AUTH-004-manage-reviewer-permission.md) 拥有，Session→USER 由 [Auth UC010](../auth-center/use-cases/UC-AUTH-010-issue-user-identity-from-session.md) 拥有；App 的真实 grant/revoke、权限隔离和待审决定联合验收已完成，不再等待 Auth 重设计。
- **正式检查政策**：UC005/030 已交付不可变 v3 正式检查定义、历史策略与当前策略投影；UC031 已交付同一快照的当前公开 Profile/指针，见[审核补齐记录](implements/2026-10-16-review-completion.md)。
- **审核自动拒绝**：现行角色资格门禁和 SYSTEM principal 解析由 UC005/025 与 Auth 契约确定，依赖故障保持 PENDING，不使用占位身份或把故障当作资格不符。
- **关闭证明与持久撤销**：Auth application tombstone 已纳入授权/换码/token/refresh/UserInfo/delegation；当前密码加同设备新签名签发 app.close proof，App 只消费 proof，不接收密码。真实关闭、重试与收敛已经验收，见[关闭认证记录](implements/2026-10-20-application-close-auth-fixture.md)。
- **Test clear、本人测试查询和主动退出**：UC036、UC038、UC040 的后端已实现；不再列为未决用例。
- **管理员资料历史**：UC039 已实现并验收，公开资料审核读取上下文也已由 UC031 补齐。
- **Filter**：UC022 已固定 ApplicationFilterRevision、`profile-filter-v1` 和无审核的立即发布；规则管理/分发已实现。客户端目录与求值器仍按用户要求暂缓。
- **转让/关闭/暂停/归档/灰度**：UC026、027、028、033、021 均已接受并实现。平台强制接管、争议仲裁和通用工作流仍为后续扩展。

## 相邻边界与旧实现

Reviewer 打开自托管页面的隔离环境、Console 页面、官方客户端和生产部署分别维护，不计为 App 后端未实现目标。Auth 拥有用户身份、资格、权限及 grant/code/token；App 通过现行契约消费，不复制其业务规则。

旧实现只保留需求参考；不为旧 API 或数据增加兼容。被废弃的 UC017 资料恢复和 UC032 技术名称修改不是待实现工作。本文和概述中的设计状态不因实现完成自动升级；未来新业务仍先审核设计，再实现。
