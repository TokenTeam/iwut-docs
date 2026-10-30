# Console 所需 Gateway 能力缺口与本地交付请求

状态：`REQUESTED`（2026-10-30）。用户要求前端整理缺口并交由 gateway 补全，同时授权 Gateway 本地构建以加快联调。本页是交接清单，不是新的后端业务规则或 UC 接受记录；Gateway 应先按既有文档流程登记实施范围，已有普通凭据矩阵内的 P0/P1 可实施，新增信任/凭据设计另行列出。

## 交付更新

2026-10-30：P0/P1 普通入口已由 Gateway `9d6a27f` 补齐，共新增47个目录项的surface配置（49个surface声明）；全目录130 RPC、74项至少有一个surface，Developer53/Admin24。既有凭据矩阵未改。`make check`和既有协议链通过；新增47项并非逐业务成功验收。已本地构建并接入 `iwut-gateway:console-local-9d6a27f` / `sha256:90cf10f0ea832812ee756e686362e0114d493e090b2286aef76dd9304007fdd7`，renderer/runtime同镜像，保留回滚实例及数据。

前端 [P0真实写链](2026-10-30-developer-write-workspace.md)已通过1/1：应用创建、版本/资料创建保存送审；显式本地镜像runner已补齐，不再要求其远程pull。随后[P1与P0联合专项](2026-10-30-developer-management-writes.md)2/2通过，覆盖Tester、OAuth和Filter代表写链；归档/转让仍独立验收。P2只有受控独立entrypoint方案，未正式实现；账号安全/BFF分类仍是独立设计/功能工作。下文是请求发出时的基线和验收约束，不把已完成的47项重新登记为Gateway缺失。

## 核对基线与责任

- Gateway 本地基线 `5efc9d5`，唯一目录为 [routes.v3.yaml](https://github.com/TokenTeam/iwut-gateway/blob/5efc9d5/config/routes.v3.yaml)。API 输入仍为 `6fea3db899d3d096d4d3dfc59b2c85432a4b9eb6`；以各仓 source lock/submodule 核对，不因本清单自行升级。
- 当前目录共 130 条外部 RPC（Auth 66、App 64），已有 27 条至少声明一个 Console surface：Developer 20、Admin 8，`GetOwnProfile` 两端共有。其余 103 条没有 Console surface，不能把这 103 条全部视为缺陷或批量对两端开放。
- 已有 Gateway 公开协议路由不等于 Console Cookie 入口已接通；Console 入口不等于页面或业务资格已经交付。
- 业务语义分别归 Auth/App UC；普通浏览器链路归 [UC-GW-007](../../gateway/use-cases/UC-GW-007-compose-console-session-forward-auth.md) 与 [ADR-CONSOLE-004](../adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md)。页面职责见 [页面规划](../page-architecture.md)。

本次请 gateway 负责：逐项核对、补全适用 surface、官方生成/漂移检查、既有认证矩阵和真实链路验证、本地 Gateway 镜像。Console BFF/Web 代码及当前预览环境切换由前端负责；不要求 gateway 修改 Auth/App 业务或直接操作运行中的预览容器。

## P0：先解锁开发者从创建到送审的闭环

下列目录项已存在，当前均未声明 Console surface。请求仅开放 `DEVELOPER`，不向 `ADMIN` 开放开发者管理命令。RPC method 以既有目录和固定 Proto 为准。

| 功能 | 精确 route ID | Console 现状 |
| --- | --- | --- |
| 创建应用 | `app.create-application` | 尚无创建页 |
| 创建版本 | `app.create-application-version` | 整页表单/client 已有，当前写开关关闭 |
| 更新版本草稿 | `app.update-application-version` | 自动保存实现已有，当前写开关关闭 |
| 提交版本审核 | `app.submit-application-version-review` | 尚无命令入口 |
| 驳回版本恢复草稿 | `app.restore-rejected-application-version-to-draft` | 尚无命令入口 |
| 放弃未提交版本草稿 | `app.abandon-application-version-draft` | 尚无命令入口 |
| 新建公开资料修订 | `app.create-application-profile-revision` | 当前只读 |
| 更新公开资料草稿 | `app.update-application-profile-revision` | 当前只读 |
| 提交公开资料审核 | `app.submit-application-profile-revision-review` | 当前只读 |

这些命令沿用既有 App USER exchange 与最终业务授权。不得把缺少 Developer 资格、配额、生命周期、Scope/URL/OAuth 或 OCC 冲突改为 Gateway 代判。完整替换 body、If-Match/ETag、query 和业务错误应按原有契约透传，不生成第二套 DTO。

第一批完成即可先交付独立可用的本地镜像，不必等待 P1 全部完成后才通知前端。

## P1：随后补齐已有管理能力的普通入口

每项仍为显式 allowlist，不继承整个服务/前缀。下列为请求的目标 surface；Gateway 应复核实际凭据矩阵和既有特例，若不满足 UC-GW-007，应报告具体 route 和阻塞，转入后文 BFF/设计清单，不能削弱校验后勉强开放。

| 目标 surface | 功能 | 精确 route ID 集合 |
| --- | --- | --- |
| DEVELOPER | 测试邀请与成员管理 | `app.create-or-rotate-tester-join-link`、`app.revoke-tester-join-link`、`app.remove-application-tester` |
| DEVELOPER | OAuth 客户端与凭证元数据 | `app.register-oauth-client`、`app.get-application-oauth-registration`、`app.set-oauth-client-status`、`app.get-oauth-client-credential-metadata`、`app.rotate-oauth-client-secret` |
| DEVELOPER | 完整 Filter 读写 | `app.get-application-filter`、`app.set-application-filter`、`app.clear-application-filter` |
| DEVELOPER | 应用归档 | `app.get-application-archive-state`、`app.archive-application`、`app.unarchive-application` |
| DEVELOPER | 管理权与转让 | `app.get-application-ownership`、`app.initiate-application-admin-transfer`、`app.get-application-admin-transfer`、`app.accept-application-admin-transfer`、`app.reject-application-admin-transfer`、`app.cancel-application-admin-transfer` |
| DEVELOPER | 关闭应用前后的普通读取 | `app.get-application-closure-preview`、`app.get-application-closure`；**不含**实际 `CloseApplication` |
| DEVELOPER、ADMIN | 本人资料编辑 | `auth.get-profile-editing-schema`、`auth.edit-own-profile`；`auth.get-own-profile` 已有，保留 |
| ADMIN | 两项独立审核权限管理 | `auth.manage-application-review-permission`、`auth.get-application-review-permissions`；既有 `auth.get-reviewer-permission` 保留，不扩展旧兼容写入口 |
| ADMIN | 应用暂停/恢复权限管理 | `auth.manage-application-operations-permission`、`auth.get-application-operations-permissions` |
| ADMIN | 平台管理员管理 | `auth.manage-platform-administrator`、`auth.get-platform-administrator`、`auth.list-platform-administrators` |
| ADMIN | 账号禁用/恢复 | `auth.manage-user-account-status`、`auth.get-user-account-status` |
| ADMIN | 开发者资格暂停/恢复 | `auth.manage-developer-status`、`auth.get-managed-developer-status` |
| ADMIN | 应用暂停/恢复 | `app.get-application-platform-availability`、`app.suspend-application`、`app.restore-application` |

入口 surface 不是平台管理员/Reviewer 授权。用户定位、独立权限、最后管理员保护、事务审计和状态机继续由后端执行。没有全平台用户搜索/应用搜索时，不为页面编造相应 RPC。

OAuth secret 与 Tester join URL 的一次披露仍由业务响应和 Console 特定交互负责；Gateway 不记录、缓存或重放这些材料，响应缓存/内部头边界维持既有要求。

## 账号与安全流程：给出分类，不直接批量开放

以下公共 API 多数已有，主要缺 Console BFF/Web 编排。请 gateway 核对内部精确入口是否完整、报告缺陷；不要求把它们全部变成浏览器直调 surface，更不要求本次代写 BFF。

| 类别 | 涉及能力/route | 交接要求 |
| --- | --- | --- |
| 注册、密码登录、邮箱登录 | `auth.begin-email-registration` / `complete-email-registration`、`auth.begin-password-login` / `complete-password-login`；现有设备/邮箱登录保持 | 登录响应可能产生原始 Auth Session，沿用/扩展 BFF-owned exact 流程；不得直接交还浏览器或借 ambient Console Cookie 污染匿名登录 |
| Developer 资格 | `auth.apply-for-developer`、`auth.get-own-developer-eligibility` | 当前 DIRECT Session 策略已有；请评估普通 chain 的适用性与 BFF 归属，列出最小接入方案，不向浏览器暴露 Session header |
| 邮箱与校园认证 | v3 邮箱列表/添加/切换/删除，校园认证 Begin/Complete/Get | 沿用各自密码/设备证明和限流；不要回退到已退役 v1 修改接口 |
| 密码、设备、会话管理 | 密码修改/恢复，凭据列表/命名/撤销，会话列表/批量撤销 | 明确撤销当前凭据/Session 后 BFF 与客户端的状态处理，不能只以后端 HTTP 200 当作完整交付 |
| 授权与用户数据 | `auth.list-own-application-grants`、`auth.revoke-own-application-grant`、`auth.clear-own-application-user-storage` | 逐项分类 DIRECT Session / USER exchange；后者虽属普通链能力，是否加入 Console 产品范围由后续功能包确认 |
| Developer 退出 | Prepare/Confirm/Cancel/GetDeveloperWithdrawal | 有独立协调和恢复语义；请提供路径分类，不重写 Auth 状态机 |
| 账号注销 | Begin/Prepare/Confirm/Cancel/GetAccountClosure | confirmation/receipt 是专用凭据；继续 UC-GW-005，不能统一换为普通 Cookie→Session |
| 关闭应用 | Begin/CompleteApplicationCloseReauth、`app.close-application` | Auth 近期重新认证、App USER identity 与 high-risk proof 组合不变；UC-GW-006/007 首版不能通过加 surface 绕过，需要另行明确 BFF/契约方案 |

学年管理与 Scope 运维入口已有后端/公共路由，但 Console 产品范围尚需单独确定；本次只登记建议，不要求开启 Admin surface 或构造新策略。宿主 OAuth consent 属未完成独立设计，不计为 Gateway 漏接。内部 service-provider RPC、OAuth Bearer/Portal Cookie、原生 gRPC 的浏览器 Cookie 化均不在本次补全范围。

## P2：IP 加端口的正式本地配置能力

用户当前使用 NetBird，希望不改 hosts/DNS 即可开发访问。当前需要的浏览器 origin 为：

- Developer：`https://100.76.198.140:37117`。
- Admin：`https://100.76.198.140:37118`。

现有 renderer 只接受两个不同的精确 DNS Host，不能直接描述同 IP、不同端口的双 surface。当前前端宿主运行配置临时按外部监听端口校验 authority、覆盖本地路由标记并转换生成规则，BFF origin/HMR 已使用真实 IP/端口；它只是本机临时联调适配，不是 Gateway 已交付或生产协议。

请 gateway 提供正式方案，优先评估独立受控 Traefik entrypoint/精确 authority 配置，并明确需要前端部署侧配合的部分。生成器、环境变量/CLI、冲突校验及文档必须一致；保留现有双域名部署模式。不能信任浏览器可伪造 header 来决定 surface，不能通过 Origin rewrite、关闭 Fetch Metadata、允许任意 Host、通配 CORS 或共用 BFF 密钥解决。

若需要修订 UC-GW-007 的部署边界，先给出具体设计和影响，再实施这部分；不要让 P2 阻塞 P0 普通路由本地交付。正式方案就绪后由前端替换临时适配；gateway 不直接修改正在服务的宿主配置。

## 本地构建与交付方式

本次用户明确授权 Gateway 本地构建；之前为前端 published-latest 门禁设置的不编译后端约束，不阻止 **gateway 在其自身仓库** 为本次开发构建镜像。

1. 从 Gateway 当前源码和固定 API 构建一个显式本地标签，例如 `iwut-gateway:console-local-<commit>`；若有未提交改动，报告 dirty 状态/内容指纹。不要覆盖 CNB `latest` 标签，也不以本地镜像冒称远程 CI 产物。
2. 使用已有正式 Dockerfile，确保同镜像包含匹配的 Gateway 二进制、`/gateway-config` 和 `/config/routes.v3.yaml`。报告镜像 ID、源码 commit/dirty 指纹、API commit、路由摘要和构建命令；前端后续用该镜像 ID 一次性绑定 renderer 与 runtime。
3. Auth/App 继续使用各自已发布 `latest` 镜像，本次不要求拉源码编译它们，不需要 push、触发 CI 或生产部署。
4. 优先完成 P0 后通知前端所需 tag/ID、生成变量与路由列表。已有 `make check`、相关真实 Console/三协议门禁按改动执行并报告实际结果，不把生成 YAML 或 mock 通过当成真实链路通过。
5. 当前预览使用已有容器/数据库/密钥；前端接入时保留数据和回滚配置。请勿自行停止/删除预览容器、数据库、会话或 OTP 收件箱。
6. 本地开发与发布门禁保留两个入口：快速联调可选显式本地 image 且不强制远程 pull；默认发布验证仍拉 CNB `latest` 并解析实际镜像 ID。当前 Console real runner 虽有 `E2E_GATEWAY_IMAGE`，但 override 仍无条件 pull；这属于 **Console runner 缺口**，由前端另补本地不拉取模式，gateway 不必跨仓修改。

## 交付检查与回复格式

- 提供逐 route 的新增 surface 和仍不开放的原因；保留现有发布六路由与双审核入口，不批量开放两端。
- 完整保持普通 chain：scrub → 对应 BFF Session ForwardAuth → remove-cookie → Gateway ForwardAuth → post-auth scrub。BFF 内部入口无 Cookie、非递归、未知 method/path 拒绝。
- 验证正常路径、错误 surface、无 Cookie、跨站、伪造身份/Session/Forwarded、OCC 头/query 原样传递、下游 `Set-Cookie` 不外泄，以及失败 `private, no-store`。
- 对新增写入口验证有权限成功与无权限不抵达；依赖默认关闭时明确记录配置，不能通过放宽生产默认值伪造可用。
- 回复区分：已实施/已本地构建/已验证/仍需 Console BFF 或新设计；给出最先可接入的镜像信息。本清单不表示所有页面已获准实现，也不关闭已有 UC/goal。
