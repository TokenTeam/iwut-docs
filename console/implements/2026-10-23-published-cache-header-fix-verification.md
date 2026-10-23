# 已发布App/Gateway错误缓存头修复复验

状态：`ACCEPTED / VERIFIED`，2026-10-23。35项专项及默认115项完整门禁全部通过，本包验证完成。用户通知修复镜像可能已更新，按[阶段收口继续条件](2026-10-23-console-stage-closeout.md#继续条件与验证顺序)仅复验原缓存头门禁，不扩展业务或关闭其它设计边界。

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

同一冻结`6b8834e2687aac5562c8865b53ed808bd07a524c`执行无参数`pnpm test:real`，轮次`iwut-console-real-291690`，115项全部通过（19.5分钟、exit0、无skip/retry）。本轮重新pull latest、五解析ID与上方专项相同；全部原29条缓存头断言再次通过，无新功能失败，不是借35项专项替代全量。

原全部既有登录/隔离/私有读取/决定/恢复/预算/分页场景完成；正常业务错误仍是原400/404/401，权限隐藏、游标绑定和Session恢复行为不变。运行期产品/runtime/runner/spec未改，未编译后端、未由代理补头；Console与32e83da的差异只有AGENTS.md及测试README记录。

专项及全量轮次容器（含退出）与network均已核对为空，Console工作区干净，legacy本地及本次远端仍为`e68851e343bd0e077e5ccd0b680fe6813216ced0`，未push。原缓存头红门禁已在该组published镜像解除；这是当前既有套件全绿，不等于所有UC或原广泛目标COMPLETE，策略/Scope正式变更、不同修订并发可达性及33+carrier架构问题仍开放。

并行复核`pnpm test`的954项Vitest＋221项Node全部通过，仓库独立性294文件通过；`pnpm typecheck`通过。`pnpm generate:check`首轮因GitHub拉取固定27c提交时低速60秒超时而exit1，不能计作通过；未改源/配置，同一官方源有界重试一次exit0、生成物与固定输入一致。保留首轮网络失败，不回退本地mirror/后端源码，不改运行中的真实测试。
