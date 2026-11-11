# 2026-11-11 已接受 API 发布核对

本记录更新 Gateway 当前接入状态，取代旧清单中 2026-10-07 的数量与实现基线。业务规则继续以 Auth/App 已接受 UC 为准；本轮复用 UC-GW-001/007，不新增身份策略。

## 输入与覆盖

- 统一 API：`241d56de6f8a3f68ed91969a4239a8c9fe32baad`，已发布到 API 的 `master` 与 `integration/script-query-api-20261106` 分支；已通过远程引用核对。
- 接入功能基线：Gateway `78d74f735cb631f979fbc43ab9e2b98fe98e6dc8`；发布分支 `master` 已快进并推送至 `194803122d26f5e5492fd574f739dc0126f5c755`，包含本轮补齐的权限隔离断言。
- 路由源：[config/routes.v3.yaml](https://cnb.cool/TokenTeam/iwut-gateway/-/blob/master/config/routes.v3.yaml)。描述符覆盖测试逐方法比对 HTTP annotation，typed adapter 和 Traefik 生成检查锁定同一目录。

| 范围 | 精确 Proto 外部方法数 | 目录/typed adapter/生成配置 |
| --- | ---: | --- |
| Auth | 73 | 已接入 |
| App | 93 | 已接入 |
| 合计 | 166 | HTTP/JSON、原生 gRPC、gRPC-Web |

上述数字表示传输接入，不把所有方法标为已完成完整业务流验收。真实协议门禁的覆盖和发布结果另行记录；后端开关与生产部署也不由数量推导。

| 本轮重点 | 权威业务输入 | Gateway 接入边界 |
| --- | --- | --- |
| 脚本管理、审核、发布与分发控制 | App UC041–046、048–049；Auth UC038 | Admin；App/Auth 各自 audience，业务授权由对应服务执行 |
| 脚本候选 | App UC048 | Developer；App audience |
| 脚本内容与 manifest 解析 | App UC047 | 公共 API 必需 Session；不增加 Console surface |
| 本人五项脚本权限 | Auth UC038 | 空请求精确 GET `/auth-center/v1/users/me/script-permissions`；Auth audience；Admin surface；任意有效 ACTIVE USER 可读本人 |
| 应用管理动态 | App UC052 | Developer；App audience；当前 owner 读取及隐藏语义由 App 执行 |
| 用户搜索、平台应用目录 | Auth UC039、App UC051 | Admin；对应服务 audience 与权限复核 |
| 入站管理员转让 | App UC050 | Developer；App audience |

本人权限查询不改变同服务目标 Get/Manage 的管理员门禁。内部服务 RPC 仍未公开；旧注册、可变邮箱绑定入口仍关闭。UC-GW-002 的八个 OAuth/OIDC 标准 HTTP 端点仍未启用。本轮不涉及个人通知、自动加载、long polling 或 WebSocket。

## 发布门禁

代码仓库的 `make check` 已通过，检查全部 166 个外部方法、策略矩阵、生成一致性、race、vet、Wire 与固定 Proto 生成物。

本轮补充同一普通用户访问目标 Get/Manage 的三协议 `403 / PermissionDenied` 断言，使用合法 subject 与当前 revision，并复查本人权限快照未改变。原本人读取五项显式 false、管理动态 owner 成功/非 owner 隐藏，以及 Console Admin/Developer 隔离门禁继续执行。

固定已发布 Auth/App 镜像的完整 `make protocol-e2e` 已通过，使用以下输入：

- Gateway：本地构建已提交的 `194803122d26f5e5492fd574f739dc0126f5c755`。
- Auth：`docker.cnb.cool/tokenteam/iwut-auth-center@sha256:8824836f46cdc81df000e0cd9b3a578d02af7998ac5ff47ae16c366c00a4fe69`。
- App：`docker.cnb.cool/tokenteam/iwut-app-center@sha256:19be6256c85b32ebf6c9c43f78e75575f866340deb995ad7cbfe04cfbb974fdd`，对应源码 `db01313ea76198461b3dc75561bf1804e1bcf676`。

通过项包括本人五项权限与目标 Get/Manage 隔离、37 项管理/查询/决策/分发边界、真实管理动态 owner/non-owner 读取、三协议投影，以及真实 Developer/Admin BFF 的共享 Traefik Session 与 surface 隔离。

最初拉取的旧 App `latest` `sha256:18eacd03c1f0cd9b4841bd9b141b61c0d5dde89f6d0045f00322a056541b4027` 对入站转让 POST 返回 405；该次失败未计为通过。随后固定 UC052 本地镜像的兼容性联调与上述新发布镜像联调均通过，最终发布依据采用上述已发布 digest。

## 镜像发布

Gateway `master` 的 [CNB 构建 cnb-jma-1k74mg2df](https://cnb.cool/TokenTeam/iwut-gateway/-/build/logs/cnb-jma-1k74mg2df#001) 已成功。拉取后确认 `docker.cnb.cool/tokenteam/iwut-gateway:19480312` 与 `latest` 指向相同 registry digest：

`sha256:404c34db98e0bee07bcc9fa0209ee4e77941df1631cc9ac8758ccfca1f8e7ab9`

发布镜像用户为 `65532:65532`，默认入口为 `/iwut-gateway`。已在只读、无网络容器中执行其 `/gateway-config`，输出的 Traefik 配置与同环境变量下提交源码生成的配置逐字节一致。完整协议 E2E 使用上述 Gateway 源码构建；镜像另行通过配置生成器运行检查，二者不混称为 Gateway 发布容器的完整业务验收。

发布只将已验证 Gateway 变更合入 `master` 并由既有 CNB push 流水线构建 commit tag 与 `latest`；镜像发布不等同生产部署。
