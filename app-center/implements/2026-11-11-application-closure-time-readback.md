# UC027 关闭回执与持久化时间一致性

状态：`COMPLETE`（App 后端验证与发布完成）。2026-11-11，真实 Mongo race 专项 5/5 与完整 backend 24/24 均已通过，输入未变化；App 修复 `48b3b14682754eb33a8bb04e74ebae739a26a056` 已合入并推送 master，GitHub 同步、CNB 构建和固定 digest 拉取均成功。Console UC024 的已发布跨端实链复验由 Console owner 继续维护。

本包由 Console 关闭实链核查触发，沿用户既有“后端统一时间”的授权处理。依据 [UC027 / BR-APP-026](../use-cases/UC-APP-027-close-application.md#br-app-026) 的持久收敛与幂等，以及 [BR-APP-028](../use-cases/UC-APP-027-close-application.md#br-app-028) 的关闭事实持久化要求，修复 Mongo 存储表示与命令回执之间的差异。不新增业务规则，不修改 UC、BR、Proto 或 schema。

## 根因与修复

App 基线 `db01313ea76198461b3dc75561bf1804e1bcf676` 的 `ApplicationClosureRepository.Start` 将原始纳秒时间写入 BSON Date 后，直接以内存中的 `applicationClosureDocument` 生成回执。Mongo 保存日期的精度为毫秒，后续 Get 从数据库重建结果，因此同一 closure 和 lifecycle revision 的 `closingStartedAt` 不同。并发使用同一 proof 时，首次写入的回执与读取既有记录的幂等回执也会不同。

`Complete` 存在相同表示差异。首次回执的 `authAppliedAt` / `closedAt` 保留纳秒，Get 返回毫秒；再次提交相同原始 Auth receipt 和 appliedAt 时，终态比较用已持久化的毫秒时间对比纳秒输入，错误返回 `ApplicationClosureStateInconsistent`。

`internal/adapter/mongo/application_closure_repository.go` 在 Start 进入事务前，将 `now` 一次转换为 UTC 毫秒时刻；关闭记录、配额、转让终止、Tester 链接撤销、OAuth 禁用、调度时间和回执共享该值。Complete 保留空 receipt / zero appliedAt 的原有检查，再于事务外将 appliedAt 一次转换为相同精度，用于首次写入、回执和重复回执比较。事务重试复用固定输入，不重新取时，也不在提交后另作无版本查询拼装回执。

proof 签名、有效期和主体绑定校验未变，ownership/lifecycle CAS、proof JTI 绑定、一次性 revision 推进和错误回执边界保持。不同 receipt 或不同持久化毫秒的 appliedAt 仍失败。已持久化的 BSON Date 本身已为毫秒精度，不需要历史数据迁移；Console 保留同记录时间的严格校验。

## 回归与专项证据

修改 `internal/adapter/mongo/application_closure_repository_integration_test.go`，使用真实事务型 Mongo 与现有正式 Repository 夹具。

- Start 输入固定的非零亚毫秒和非 UTC 时区，比较原始 ACK、Get、同 proof 重试与全部相关持久化时间，保留 ownership/lifecycle OCC 和配额不变断言。
- 独立的 Complete 回归以另一非 UTC 时区、非零亚毫秒 appliedAt 验证 ACK、Get、相同原始回执重入，以及不同 receipt、相差 1 毫秒、空 receipt 和零时间的拒绝；终态和 lifecycle revision 保持不变。
- 既有并发同 proof 测试改用亚毫秒输入，要求每个回执都保留同一 closure 与持久化时刻；OAuth 关闭回滚与共享写栅栏竞争测试继续执行。

| 阶段 | 结果 | 本地证据 |
| --- | --- | --- |
| 修复前 | 5 项中 3 项失败，分别为 Start 回执/读回、Complete 回执/读回及相同回执重入、并发 Start 回执；其余 2 项通过 | App `.artifacts/closure-time-before.log`，诊断 `.artifacts/integration/run-fBosR36K` |
| 修复后 `-race` | Mongo 专项 5/5 PASS，29.506 秒 | App `.artifacts/closure-time-after.log`，诊断 `.artifacts/integration/run-XiIMRQRD` |

修复前 Start 的直接证据为同一记录分别返回 `2026-11-11T07:00:00.123456789Z` 与 `2026-11-11T07:00:00.123Z`。Complete 的同类差异为 `.987654321Z` 与 `.987Z`，相同回执重入返回内部状态不一致。修复后专项全部通过，未放宽回执与读回的一致性断言或错误断言。

上述专项运行的 `cmd/app-center` 包显示 `[no tests to run]`，不将它计为 Wire/HTTP/gRPC 通过；专项也不替代完整后端门禁。

## 冻结输入与完整门禁

Go `1.25.5` 的标准完整 `check-full` 于 `2026-11-11T07:51:19Z` 启动。报告为 App 仓库 `.artifacts/verification/20261111T075119Z-fziveiqk/report.json`，主日志为 `.artifacts/closure-time-full.log`。本轮于 `2026-11-11T08:31:40Z` 收尾，报告状态 `timeout`、`changed_sources=[]`。前23项通过，第24项 `mongo-and-http-grpc-e2e-race` 执行2402.820秒后退出124，日志显示runner终止子进程；没有完整包结果或测试断言失败输出，因此不声明完整PASS。测试进程和隔离Mongo容器已清理。

| 冻结输入 | 版本与起始内容指纹 sha256 |
| --- | --- |
| App | `db01313ea76198461b3dc75561bf1804e1bcf676` 加本包两个文件改动；`185c0556522888a50433c82fa2ea98420e67e699e234ce36cf5bb59cc91245f7` |
| API | `241d56de6f8a3f68ed91969a4239a8c9fe32baad`，干净；`49b70dbaf486be99c8161fd5e8781801ec20806194ee4e099674f60b46c82e80` |
| Docs | 已提交 `81a628f0d70ae2c8db1af18975370d2b04d13687`，门禁使用独立干净副本；`8cbb58f852c04aa8de606a2ce5dfffcdc6a4669473438cc0fcb3025a9afa7b29` |

本实现记录草稿在另一独立 Docs clone 中准备，不改变门禁的冻结输入、共享 Docs 工作区或 App/API 源码。原超时报告保持原样，后续完整PASS与提交证明见下节。

首轮 Mongo 诊断日志直到 `08:31:37.694Z` 仍在新测试库初始化，前一测试库刚清理。全轮涉及353个测试库、约2.4万条 `createIndexes` 相关记录；已记录的测试库命令最大耗时363ms，未发现Mongo E/F级错误。这支持累计初始化耗时的判断，不能证明某个具体慢查询或死锁。首轮Go输出未给出逐项测试名，数据库递增ID也不能反推出超时瞬间的具体用例。

## 完整重跑通过

协调方确认按既有授权提高外层时限并增加诊断。第二轮使用 `python3 -B scripts/verify.py backend --timeout 3600`、`GOFLAGS=-v`，Go1.25.5及子Go45分钟上限不变，所有用例与断言保留。启动前逐文件内容、权限及API gitlink与第一轮冻结快照完全一致。

报告 `.artifacts/verification/20261111T083445Z-pmukmcwe/report.json` 于 `2026-11-11T09:16:56Z` 正常收尾，**24/24 PASS**、`changed_sources=[]`。最后阶段退出0、2509.666秒；Mongo race包2503.278秒，生产Wire HTTP/gRPC包315.782秒。全轮起始时间 `2026-11-11T08:34:45Z`，上述三项内容指纹与第一轮相同。原40分钟外层上限不足以覆盖本轮实际完整套件耗时，未通过缩减测试或放宽断言绕过。

App提交 `48b3b14682754eb33a8bb04e74ebae739a26a056`，tree `0e6fed44809c952a9a924a77363c07675846333d`。665个tree条目的内容/权限/API gitlink与测试前冻结清单逐项相同，提交证明为 `.artifacts/closure-time-commit-proof.json`。仅修改关闭Repository及其真实Mongo回归文件，API保持 `241d56de6f8a3f68ed91969a4239a8c9fe32baad`。

## 发布记录

| 项目 | 已核实结果 |
| --- | --- |
| App master | `48b3b14682754eb33a8bb04e74ebae739a26a056`，从 `db01313` fast-forward 后正常推送；工作区干净 |
| API gitlink | `241d56de6f8a3f68ed91969a4239a8c9fe32baad`，保持不变 |
| GitHub 同步 | [run 42993934309](https://github.com/TokenTeam/iwut-app-center/actions/runs/42993934309)，`success` |
| CNB 构建与发布 | [cnb-4s5-1k74uc5gd](https://cnb.cool/TokenTeam/iwut-app-center/-/build/logs/cnb-4s5-1k74uc5gd)，`success`；构建、commit tag 推送和 latest 推送三阶段全部通过 |
| 镜像 tag | `docker.cnb.cool/tokenteam/iwut-app-center:48b3b146`；核验时 `latest` 指向同一 index |
| OCI index digest | `sha256:dee598b31dd16c651e78b20d090965a054c654eae1981cfacce46008b76c0a14` |
| linux/amd64 manifest digest | `sha256:e1806f276620184aea3a4836047ff2115a97860361a262b8e35c39f408e7d8d1` |
| image config digest | `sha256:a264199daedc7848d6ef6ec2dd966afbf5029f9820ae3c40ec06f363b385fbb1` |

镜像 provenance 的 VCS revision 精确对应 `48b3b14682754eb33a8bb04e74ebae739a26a056`，与源码中的 API gitlink 分别核对。公共证据保存在 App `.artifacts/closure-time-registry-ci-proof.json`；执行 `docker pull docker.cnb.cool/tokenteam/iwut-app-center@sha256:dee598b31dd16c651e78b20d090965a054c654eae1981cfacce46008b76c0a14` 成功，返回相同 digest。此前 [db01313 主分支与镜像发布记录](2026-11-11-accepted-backend-release.md)保留为不含本修复的历史基线。

Console UC024 接下来使用上述固定镜像复验关闭实链的严格回执/读回检查；本记录不将源码完整门禁或镜像发布等同于该跨端验收完成。没有修改 Auth、Gateway、Console 或 API 源码，也未操作生产数据库或部署环境。
