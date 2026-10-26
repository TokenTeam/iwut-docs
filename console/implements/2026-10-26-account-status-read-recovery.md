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

## 实施与首轮专项

- 实现冻结 Console `cc2edba`，接受文档 `f1f65e3`。普通954 Vitest＋286 Node、strict typecheck、官方同pin生成漂移、Edge及72份brief/registry检查通过；尚无真实成功结论。
- published-latest轮次 `iwut-console-real-249979`：专项0通过/1失败/2未执行，exit1。beforeAll准备器在真实账号状态GET200后拒绝空statusChangedAt，尚未发DISABLE。本包错误地将时间字段写成初始必填；UC022明确从未变更时允许为空，不是后端缺口。保留失败，不把未执行项算过。
- 按正式契约修订：初始revision1允许空状态时间，实际改变后必须有时间；增加独立回归（初始正常、缺变更时间则冻结且无第二写）。重新冻结后重跑专项，旧结果不改名为绿。两次治理写、完整回归、隐私/缓存头门禁不放宽。

修订冻结 `d608c30`：普通954 Vitest＋287 Node、strict检查通过；API生成/Edge相关输入未改。重新pull五镜像后专项3/3通过（1.3分钟浏览器阶段，exit0，无skip/retry；终端session11462），证明正式治理、恢复后旧Admin及普通Auth Session不复活、各origin原钥匙新DEVICE登录与原投影/独立peer保持。专项资源（含停止容器）及network为空。当前同冻结默认无参数121项正在运行，不将专项替代完整门禁。

### 完整回归暴露的测试账号邮件预算与接受修订（2026-10-27）

同冻结轮次 `iwut-console-real-266471` 无参数全量：118通过/1失败/2未执行，21.0分钟浏览器阶段，exit1。原118全部通过；新增 beforeAll 在第二个owner origin EMAIL Begin实际429，尚未DISABLE。资源及network已清空。保留失败，不把专项绿挪作完整门禁。

依据 [UC012共享限额](../../auth-center/use-cases/UC-AUTH-012-login-with-email.md#br-lgn-014)，同邮箱一小时最多5次发送且至少60秒间隔。原owner的注册＋Admin查询owner＋审核利益冲突owner＋资料投影owner已用4次；本包Developer登录是第5次，Admin登录是第6次。等完60秒并不恢复小时额度，不能据此要求Auth修复或放宽限额，也不应延长到一小时盲重试。

现自行接受取代第1项“复用owner、不增加账号/App”的准备安排：仅新增一个专用普通owner，经正式注册、Apply、两项Reviewer grant、Create一个App和Create/Submit一个Version；复用原G及peer，不增加quota上限、不seed。专用邮箱仅注册＋两个origin EMAIL共3次，仍遵守真实冷却；公开fixture只给该owner合成邮箱/authId，不提供秘密。账号相位与旧Session闭包独立，不再依赖原决定fixture准备，也不改变原118的账号/业务数据。新目标当前为正式PENDING，仍冻结实际读回而不硬编码终态。移除测试中无必要的自动Begin重试，任何未知或失败保留失败。两次账号写、原钥匙/会话边界、原断言和121项完整门禁均保持。此为测试预算修正，不是新增前端写UI或后端规则变更。
