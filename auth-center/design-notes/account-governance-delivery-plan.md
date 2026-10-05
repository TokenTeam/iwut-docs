# 账号与平台资格治理设计草案

状态：`ACCEPTED`

日期：2026-10-05

本文规划后续 UC 的边界、顺序和接受条件，不修改已接受 UC 的权限或状态契约，也不表示下列能力已经实现。五个治理用例均已分配 UC021–025 并在 design-registry 登记，均为 ACCEPTED；本轮已用脚本生成实现 brief。已有同账号 Session 管理继续由 [UC020](../use-cases/UC-AUTH-020-manage-own-sessions.md) 跟踪。

## 建议拆分与顺序

| 顺序 | 候选用例 | 操作人 | 主要结果 |
| --- | --- | --- | --- |
| 1 | [UC021：授予与撤销平台管理员资格](../use-cases/UC-AUTH-021-manage-platform-administrators.md) | 有管理管理员资格的管理员 | 后续管理员能够被正式授予和撤销；防止失去最后一个有效管理员 |
| 2 | [UC022：禁用与恢复用户账号](../use-cases/UC-AUTH-022-disable-and-restore-user-account.md) | 有账号治理权限的管理员 | 暂停整个账号的使用资格；恢复后重新登录 |
| 3 | [UC023：暂停与恢复 Developer 资格](../use-cases/UC-AUTH-023-suspend-and-restore-developer.md) | 有 Developer 治理权限的管理员 | 限制开发者活动，保留普通用户身份及应用归属 |
| 4 | [UC024：本人退出 Developer 资格](../use-cases/UC-AUTH-024-withdraw-developer.md) | 本人 | 处理完名下应用后退出资格，保留普通账号 |
| 5 | [UC025：本人注销账号](../use-cases/UC-AUTH-025-close-own-account.md) | 本人 | 完成资格及应用归属清理后，终止账号并清理其个人数据 |

禁用后的恢复与注销后的撤回是不同问题，分别设计。Developer 行政暂停和本人主动退出也分别设计，避免复用一个状态却产生不同恢复权限。

上线前建议交付管理员治理、账号禁用/恢复，以及可执行的本人注销路径。开放 Developer 平台前再满足 Developer 暂停/恢复、退出和 App 应用处置的联动条件。注销可以先覆盖没有应用归属的普通用户，但必须明确告知其适用范围；不能把尚无处置流程的 Developer 注销入口宣称为可用。

## 一、授予与撤销平台管理员资格

已展开为 [UC021](../use-cases/UC-AUTH-021-manage-platform-administrators.md)，状态 ACCEPTED。固定权限集合、在线授权、最后管理员保护、共享版本、一次性首次初始化以该 UC 的 BR-ADM-001–008 为草案规则来源；本计划不重复定义。UC004 继续只管理应用审核权限，既有接受契约需在 UC021 接受时同步调整。

## 二、禁用与恢复账号

已展开为 [UC022](../use-cases/UC-AUTH-022-disable-and-restore-user-account.md)，状态 ACCEPTED。账号状态版本、旧认证材料永久失效、恢复后重新认证、最后管理员保护和下游生效窗口以该 UC 的 BR-ACC-001–008 为草案规则来源；本计划不重复定义。接受和实现时需扩展各认证消费路径，不能只修改 accountStatus。

## 三、暂停与恢复 Developer

已展开为 [UC023](../use-cases/UC-AUTH-023-suspend-and-restore-developer.md)。资格版本、普通功能保留、暂停优先取消待提交退出、恢复邮箱门禁及 OAuth 临时受阻语义以 BR-DEV-013–017 为草案规则来源。

## 四、退出 Developer

已展开为 [UC024](../use-cases/UC-AUTH-024-withdraw-developer.md)。WITHDRAWN、首版不重新开通、永久 handle 占用和先处理名下应用的规则见 BR-DEV-018–022。App 必须提供归属屏障，不能用普通查询代替。

## 五、注销本人账号

已展开为 [UC025](../use-cases/UC-AUTH-025-close-own-account.md)。不可恢复终止、专用设备证明、CLOSED、清理与最小永久保留见 BR-ACC-009–014。禁用账号有独立证明路径；无有效密钥的受理流程、App 个人状态清理及备份恢复仍需交付。具体时间是待接受的产品和运维方案，不表示已经具备清理能力。

## 交付门禁

优先评审已展开的 UC021 和 UC022，按管理员治理、账号禁用/恢复的依赖顺序实施；两者建立后续治理的操作权限和最后管理员保护基础。Developer 暂停/恢复可以继续复用现有枚举，但仍需 App 逐入口确认生效范围。

Developer 退出和账号注销共用 [App 归属退出协调草案](../../platform/contracts/account-owner-exit-v1.md)；在 App 提供相应权威 UC 与实现、状态消费者对齐及清理/保留和备份恢复策略接受前，不生成标为可实施的 brief。这些依赖不阻止先完善普通用户治理或同账号 Session 管理。

2026-10-05：UC021–025 已接受并生成 brief，独立 subagent 工作包开始实施；App UC025 提供归属屏障/个人清理前置能力。有应用者继续 BLOCKED，应用转让/关闭不在本轮，公网部署与无密钥受理需独立验收。
