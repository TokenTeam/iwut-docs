# 已接受 App 后端的主分支与镜像发布

状态：`COMPLETE`（App 主分支合入、推送与镜像发布）。2026-11-11。

## 范围

用户授权各后端 owner 完成已接受功能的接口接入、代码合入、提交推送与镜像核实。本记录覆盖 App 父仓库及 App 所属文档。系统尚未上线，直接采用已接受的提交绑定审核策略；不以 A→B 迁移或新增 Version v4/Profile v2 候选政策作为前置。个人通知、自动加载、long polling、WebSocket 不在本轮。

本轮未更改 App 业务源码。`master` 从 `5b42ed7` 快进至已推送功能分支的 `db01313`，纳入提交绑定审核策略、UC041–049 脚本能力、UC050 待接收转让、UC051 平台目录和 UC052 管理动态。

## 固定输入与远端结果

| 输入 | 最终值 |
| --- | --- |
| App GitHub / CNB `master` | `db01313ea76198461b3dc75561bf1804e1bcf676` |
| App `api` gitlink | `241d56de6f8a3f68ed91969a4239a8c9fe32baad` |
| App 文档提交的 Auth 依赖基线 | Docs `0f20622a8d2837487c5b8989cb77a6f998a30aa5`，含 UC003 和共享 SYSTEM principal 契约 |
| GitHub 同步 | [42976219761](https://github.com/TokenTeam/iwut-app-center/actions/runs/42976219761)，`success` |
| CNB 构建 | [cnb-5fg-1k74mf1qn](https://cnb.cool/TokenTeam/iwut-app-center/-/build/logs/cnb-5fg-1k74mf1qn)，`success`，88.541 秒 |

CNB 的 build image、push commit image、push latest image 三阶段均成功。镜像仓库为 `docker.cnb.cool/tokenteam/iwut-app-center`，`:db01313e` 与 `:latest` 指向同一产物。

| 产物 | SHA256 |
| --- | --- |
| OCI index digest | `19be6256c85b32ebf6c9c43f78e75575f866340deb995ad7cbfe04cfbb974fdd` |
| linux/amd64 manifest | `7a668a49b70616ef9abf0612e7096b21258d81a0c6901431895c9dd788eebf96` |
| Image config digest | `0918f868b13597bfde1df6ac6385df688f2484f03c293a4730d9097a203eddca` |

Registry provenance 的源码 revision 与上述 App SHA 相同，source 为 CNB App 仓库；其中未单列 API submodule material，API 版本通过该源码提交的 gitlink 核对。该 OCI index digest 已成功拉取到本地 Docker。公共产物证据保存在 App 本地 `.artifacts/app-master-release-registry-ci-proof.json`。

## 验证与边界

当前 App / API 输入使用 Go 1.25.5，通过 `go test ./...`、`make api-check wire-check vet`、`make fmt-check test-scripts build` 与工作区/暂存区 diff 检查。脚本工具测试 10/10 通过。App 所属文档及其已提交共享依赖通过 86 briefs、424 registry rows / 8 retired IDs 和 30/30 文档工具测试。

完整 backend 的既有 24/24 PASS 证据保留在 [UC052 实施记录](UC-APP-052-management-activity-readiness.md)。该轮 API 为 `7651f96`；其后的 `241d56de` 仅增加 Auth 本人脚本权限查询的 Proto/生成物，App 源码未变。本次补验不冒称在新 API 下重跑了完整 Mongo/race 或 cross-service tier。

已把新发布镜像 digest 交给 Gateway owner 进行 published-image 联验，其结果由 Gateway 自身记录维护。固定本地镜像的既有联验与本轮发布镜像联验分别记录。本轮未操作生产数据库或部署运行中的服务。

App 文档在独立 clone 中整理，仅提交 `app-center/` 及 `tools/brief-specs/UC-APP-*`，基于 Auth 已发布的共享契约重新校验。共享 Docs 工作区、暂存区及其他 owner 未提交文件保持原状。

## 分支清理条件

远程 `master` 已包含 `auto/script-management-uc042` 与 `auto/script-review-uc043` 的全部提交，两者可清理。当前 checkout 已切到 `master`，本轮只确认可清理条件，尚未删除分支。`legacy` 有独立历史，保留。本轮最终复核时已无 `origin/v1` 跟踪引用。
