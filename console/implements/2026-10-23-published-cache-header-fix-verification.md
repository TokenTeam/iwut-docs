# 已发布App/Gateway错误缓存头修复复验

状态：`ACCEPTED / IN_PROGRESS`，2026-10-23。用户通知修复镜像可能已更新，按[阶段收口继续条件](2026-10-23-console-stage-closeout.md#继续条件与验证顺序)仅复验原缓存头门禁，不扩展业务或关闭其它设计边界。

## 输入与不变项

Console冻结`6b8834e2687aac5562c8865b53ed808bd07a524c`，产品/runtime/runner/spec与32e83da的115项轮次相同，后续提交只更新记录。工作区干净，原29条失败断言全部保留；不补代理头、不编译相邻后端、不使用local compat、不替换400/404/401或伪造业务响应。

实际重新pull published latest：

| 输入 | 本次解析ID | 相对上次 |
| --- | --- | --- |
| App | `sha256:8e4995008f342daeea61b0a5116087c10d3c65b88485e76d4b8d45d0d2838a9d` | 从2af4af71更新 |
| Gateway | `sha256:509acf9669f69b0f59557c86dd10124404214f89416ff6b9d1675eec97b63b7f` | 从2953ae7f更新 |
| Auth | `sha256:c2f06d8fe4ca2734a32e07e70f6ab7ba8c0207932336222c2c92986e073de8b9` | 未变 |
| Mongo | `sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3` | 未变 |
| Traefik | `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0` | 未变 |

固定官方API27c及显式NSS fixture不变。每轮仍重新pull latest并在轮内固定解析ID，不把人工拉取标签本身当修复证明。

## 路由前置与35项专项终态

新Gateway的`pnpm edge:e2e`通过，六ADMIN查询/决定入口隔离、伪造头不能旁路、Developer api-deny及认证上游失败关闭保持。不是仅凭route存在宣布业务成功。

执行`pnpm test:real tests/real/management-transfer.real.spec.ts tests/real/owned-application-pagination.real.spec.ts tests/real/qualification-read-matrix.real.spec.ts tests/real/review-decisions.real.spec.ts`，轮次`iwut-console-real-285252`，35项全部通过（4.4分钟、exit0、无skip/retry）；严格类型/报告隐私/生产build前置通过，轮内源码不变。

原29条失败断言在真实Browser/BFF/Gateway/Auth/App链上全部通过：转让后Application管理GET404的3条no-store；owned-list五个无效/跨caller/filter游标POST400各private/no-store共10条；资格/角色六个管理GET404各private/no-store共12条；Version/Profile旧401和旧DELETE204交错中实际决定POST401的4条private，原no-store仍通过。决定afterAll不再标红；不是把DELETE204改为期望401，不删断言。

全部原功能断言保持通过，包括统一隐藏、token绑定、权限/Session隔离、实际决定/未知恢复及Admin→Developer只读投影。此证据证明这组已发布组合链路恢复，不单靠浏览器结果归因某一后端内部修复点。专项容器（含退出）及network已核对为空，未push。

## 默认完整门禁

同一冻结继续无参数`pnpm test:real`，预期115项，以实际终态为准。当前尚无全量结果，专项35/35不替代完整门禁，也不关闭策略/Scope正式变更、不同修订并发可达性或33+carrier架构开放项。
