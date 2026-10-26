# 账号禁用与恢复后的私有读取

状态：ACCEPTED / IN_PROGRESS（2026-10-26，自行接受；依据持续目标授权）。

## 目的与权威输入

补齐既有 UC001 会话恢复、UC002 管理读取与 UC006 审核读取在正式账号禁用/恢复后的有限证据，不增加账号治理 UI。账号状态、revision、旧 Session 不复活的语义由 [UC-AUTH-022](../../auth-center/use-cases/UC-AUTH-022-disable-and-restore-user-account.md) 拥有；Console 只消费现有 Session 错误恢复。管理 API 使用官方固定 API `6fea3db899d3d096d4d3dfc59b2c85432a4b9eb6` 生成，不手写第二套协议。

WITHDRAWN 另包：必须先正式关闭 App、得到持久关闭回执，再撤回资格并读 CLOSED 历史；转让后失去管理权或直接 seed 不足以证明这一点。本包不借账号禁用证据关闭 WITHDRAWN，也不实现关闭/撤回 UI。

## 已接受的有界方案

1. 在独立测试运行时开启正式账号管理入口。复用非平台管理员的 review owner（已正式 Apply、拥有 App 和双 Reviewer 权限）及完整平台管理员 G，不增加账号、App 或配额。控制器仅允许固定 subject 的 observe / disable / restore / old-session-check；不接收业务参数、不披露凭据。
2. 两次正式 CAS 管理写构成 ACTIVE/revision1 → DISABLED/2 → ACTIVE/3。每次写前正式读回当前 revision；写结果未知时只 Get 确认，不自动重放、不补偿 finally 写。并发、跳相位、漂移及不一致回执失败关闭。重复已确认相位只读，不再变更 revision。
3. 三个串行真实浏览器测试放在最后的 `zz-account-status.real.spec.ts`，不使旧 owner Node Session 的永久失效污染前面既有 118 项。专项只执行这三项时，按实际读回冻结原 App/Review（可为 PENDING）；全量时可为原审核终态。不写死两种运行都 APPROVED，不修改业务状态适配测试。
4. 同一 owner 在 Developer / Admin 各自原生 origin 正式 EMAIL 建立独立设备与 BFF Session，私钥不可导出、不复制；遵守真实邮件冷却。另一个 Reviewer 独立 Session 是不受影响见证。真实生产 React 加载管理详情和审核详情后，DISABLE 使 Developer 下一次真实业务请求实际 401 SESSION_INVALID，并触发该 surface 既有恢复、清除私有视图；不声称没有请求时另一页会主动获知。
5. RESTORE 后先用尚未访问的旧 Admin 会话请求真实审核 API，仍实际 401；控制器同时以禁用前捕获的普通 Session 访问正式 Auth API，仍被拒绝。两个旧 BFF 会话不得自行复活，设备钥匙保持，另一用户不受影响。G 读回确认账号恢复、资格/权限未被撤销。
6. 用户明确 DEVICE 重新登录，各 origin 使用其自己的原钥匙，获得新 Session / generation、同一 authId；原 App/Review 通过正式 API 和生产 React 恢复读取，业务对象和权限事实保持。零审核决定、转让、资格治理或额外业务写，不把短期离线 App JWS 的残余窗口说成瞬间撤销。

实施前核对修订：UC004 的权限管理查询只返回可登录 USER，DISABLED 目标应是精确 `404 REVIEWER_SUBJECT_UNAVAILABLE`。本包禁用阶段记录权限查询不可用（revision/权限集合为 null），不复制 ACTIVE 基线假装当前读成功；恢复后再以正式 G 查询验证权限与 revision 均保持。Developer 管理查询按 UC023 可返回 DISABLED 目标，仍实际验证资格与 revision。专项/全量的 Developer revision 可能分别为1/3，冻结实际初始值，不硬编码成相同。

## 验证与停止条件

先增加纯相位控制器测试（包括未知写只读、重复/并发/漂移与回执拒绝），再跑完整普通测试、严格类型、官方 API 生成漂移、Edge。冻结产品/runtime/runner/spec 后，每轮重新 pull published latest 并在轮内固定 ID；先三项专项，再默认无参数 121 项全量，原缓存头和隐私断言不删。任何实际后端不符保留失败，不编译相邻源码或换本地 artifact。每轮核验退出码与容器/network 清理，legacy 本地/远端不变，不 push。

本包完成只关闭上述账号状态读取链，不自动关闭完整 UC、WITHDRAWN、App 政策发布回执或 33+ 迟到 Cookie carrier 的架构问题。若出现新的外部契约/架构阻塞，记录实际证据后停止该链，不无限扩测试排列。
