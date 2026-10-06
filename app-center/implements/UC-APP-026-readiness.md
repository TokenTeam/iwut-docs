# UC-APP-026 开工检查

日期：2026-10-06

状态：`READY`

## 结论

UC-APP-026 没有未满足的产品或运行时依赖，可以按一个跨 Application、配额、Tester、OAuth 与账号退出屏障的纵切片实现。当前管理关系、名称/配额事务、Tester 链接、CONFIDENTIAL credential 轮换、Auth Developer Status 批量查询和 account-owner-exit fence 均已交付。

## 已确认决定

- 转让采用发起—接受模型；每个 Application 同时最多一个 PENDING，固定 7 天过期。
- 发起时新鲜检查目标，接受时新鲜批量检查源与目标 ACTIVE＋APPROVED；不虚构跨服务 revision 或 reservation。
- Application 增加 ownershipRevision；全部管理员写继续复用 adapter-only coordination fence。
- 接受在一个本地事务中移动 adminId、双方配额、名称占用、转让终态、Tester 链接和可选 credential 轮换。
- 接受者显式选择 KEEP 或 ROTATE；ROTATE 覆盖所有现有 channel 的 CONFIDENTIAL credential，PUBLIC 不变。
- 转让时撤销 ACTIVE TesterJoinLink，不移除 Membership，不自动创建新链接。
- 与 UC025 共用 account_owner_exit_fences，先按 authId 字节序锁账号，再锁 Application。

## 依赖核对

| 依赖 | 结论 |
| --- | --- |
| Application、名称与配额 | UC001 已交付事务、唯一性与配额基础。 |
| Tester link/Membership | UC008–011 已交付链接轮换、撤销、加入与 Membership 生命周期。 |
| OAuth credential | UC018–021 已交付多 channel registration、独立 credential revision 与轮换语义。 |
| Auth Developer Status | 现有批量 provider 和 service identity 可供非缓存资格查询。 |
| Owner exit fence | UC025 已交付 account_owner_exit_fences、Prepare/Finish 与写入拒绝。 |
| Mongo/API/Wire | migration、事务重试、双协议、生成代码和真实 E2E harness 均已存在。 |

## 实现与验收边界

- API 子模块先提交独立 transfer package、稳定错误 reason 与生成物；服务随后更新 gitlink。
- 服务新增 ownership/transfer domain、usecase 与 port，migration 0021，Mongo transaction、transport 和 composition wiring。
- 所有既有管理员写入口在最终事务复查 current admin，并与 transfer accept 共用 Application coordination fence。
- UC025 Prepare 纳入有效入站 PENDING blocker，并在读取时收敛到期申请。
- 真实 MongoDB 覆盖双发起、接受/取消/拒绝/过期、最后配额名额、同名、owner-exit、OAuth rotation 和 Tester join 竞态。
- 最终验收使用 `make check-auth-app`，包含实际 Auth Developer Status 与 owner-exit provider 联调。

## 非目标

Application 关闭/归档/平台接管、可靠通知、管理员团队角色、Auth grant/token 转移、自动新建 Tester 链接和跨服务强一致资格 reservation 均不进入本工作包。
