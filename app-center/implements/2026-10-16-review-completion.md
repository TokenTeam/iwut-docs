# 审核依赖补齐与串行接入

状态：`IN_PROGRESS`。用户于 2026-10-16 接受两份审核补齐设计并授权继续。

业务权威已收敛至 UC005/030/031、UC016 的查询来源引用及资料查询契约；设计提交 `3b16200`。两份原提案保留为审核记录，不替代正式 UC/BR。

## App/API 工作包

- API 本地提交 `27c9743d2d7476511932a83563e103aee5b4e28e`，未 push。固定工具链生成，`proto-check`、Go 1.25.5 全仓编译与 JSON/protobuf presence 验证通过。
- Version 详情增加 `currentPolicy.requiredCheckDefinitions`，按正式声明顺序返回 id/title/description，与 requiredCheckIds 对齐。`0033_version_review_check_definitions` 原子退役 v2、激活 v3，精确核对不可变内容，保留 v1/v2 历史。
- Version 最终决定事务增加政策技术写栅栏，退役与决定串行化；业务策略内容保持不可变。旧 policy 输入拒绝，确认集合和历史决定规则不变。
- Profile 详情增加 Reviewer 专用 `currentPublishedProfile` oneof：`{none:null}` 或 `{published:{profileRevisionId,displayName,description?,icon?}}`。同一 snapshot 验证公开指针、修订及批准事实，不通过管理员管理查询或普通 Catalog 推断。
- 审核查询在 HTTP 与 gRPC 成功及错误路径使用 private, no-store；身份错误使用 Reviewer reason。修复的是既有查询契约的遗漏，不扩大权限。

## 验证记录

普通 Domain/UseCase/transport/architecture 全仓测试通过。真实 MongoDB 专项覆盖迁移幂等、内容冲突回滚、旧政策拒绝、不完整定义失败关闭、公开资料损坏、指针 CAS 与批准期间的 snapshot 一致性。

真实 HTTP/gRPC 专项通过：四项正式定义及顺序、v2 决定 409、首次公开 NONE、已公开资料替换预览、Reviewer 权限隔离，以及成功/401/403 的 no-store。

第一轮 `make check-full` 报告 `.artifacts/verification/20261016T064927Z-3xbs0thh/report.json` 为 FAILED：唯一失败是新 validator 的多字段 map 使全新/逐步升级的 BSON 字节顺序不同。Mongo 套件耗时 1085.282s；HTTP/gRPC E2E 162.166s 通过。新增确定性回归先复现失败，再以有序 BSON 修复；修复后的真实迁移/查询专项 38.694s 通过。

最终完整后端门禁 `make check-full` 24/24 PASSED，报告 `.artifacts/verification/20261016T070959Z-1fde649h/report.json`，changed_sources=[]。Mongo race 1162.880s、HTTP/gRPC E2E 157.694s。测试输入为服务 c633270 加最终 staged 内容（SHA-256 `e2bfb3ee837b0d3f49d9f4e827cff14795bdee674de5b415f7ca88b8b7c93b56`），内容相同地提交为服务 `3a83152`，API `27c9743`、设计 `3b16200`。App 工作区干净；未重复验证仅由提交身份变化造成的 fingerprint 变化。

## 跨服务夹具兼容边界

追加运行 `make test-uc002-gateway-auth` 时，Auth latest 已变为 `sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3`。UC002–004 的真实 Session/Scope/OCC/OAuth/提交链路通过；UC005 在管理员 bootstrap 准备阶段失败，尚未执行 Reviewer grant/revoke 和决定。诊断目录 `.artifacts/integration/run-s8iJOOrA`。

当前 App 夹具只准备旧 `auth_email_bindings` 形状；新 Auth bootstrap 读取新的邮箱 binding/directory 事实。此结果说明旧夹具需要适配，不能记为 App 决定失败，也不能宣称最新 Auth 的 UC005 已通过。不修改 Auth 实现或业务规则。

已另行固定此前验收的 Auth 镜像 `sha256:902dbad234b21951be12c01719bf06f2f5223c7445c6bb8832231405bd821c04` 复验，UC002–005 全部通过（12.349s），诊断目录 `.artifacts/integration/run-Afx9IkPF`。Gateway 输入 `f4d5e5e935ccabfd718cfc493bf51a398776c8ae` / API `a5d504c058c62cd91be451074d21608d69789918`；Traefik digest `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0`。该证据是固定镜像与 API Session 路径验收，不替代新版 Auth 夹具适配或 Console ADMIN Cookie 接线。

## Gateway 完成与 Console 激活

Gateway 本地提交 `3e8a59cd8b309c8f1e096ea95cac25a624738ba4`，API `27c9743`。两个既有决定路由仅开放 ADMIN；Go 1.25.5 `make check` 与最终完整 protocol gate（42.11s）通过。后者使用新 Auth `22795e...` 与固定 App artifact，验证 18 条 App 路由的三协议拒绝边界、字段保真、Console v2 Cookie、跨 surface、CSRF、伪造身份、缺 Session 和 Set-Cookie 隔离。

证据分层：真实 App 决定请求证明无 Reviewer 权限被拒绝；ADMIN 正向与字段保真使用签名验证 Recorder，不冒称真实成功决定或授权撤销。详细记录在 Gateway 仓库 `docs/verification/2026-10-16-review-decisions-integration.md`。

供 Console 消费的固定本地 artifacts（均未 push/部署）：

- App `iwut-app-center:review-3a83152`，ID `sha256:b6d0b68f921eca043d75708182bcdc5d9ac7d82da1cf0488f7485005cae2cee8`。干净提交/API、Go 1.25.5 CGO0；固定已发布 runtime base，仅替换 binary。
- Gateway `iwut-gateway:review-3e8a59c`，ID `sha256:951d4a2b3aa923743623a0323f8cbcc445d53d54c438d4fd12d36e4869bbe886`。最终提交/API archive、Go 1.25.5 CGO0、scratch＋CA；容器内生成配置对照通过。

Console owner 已激活第 3 步，仅实现已有已接受审核 UC 内的决定操作。默认 published-latest 门禁保留，单独的 local compatibility 验证应明确记录来源。当前不登记 Console 决定已实现或整体验收完成。

## Console 验收反馈与决定响应修复

Console 真实调用发现：Version 决定 HTTP 200 缺少 Cache-Control；Profile 决定 HTTP 200/409 仅有 no-store；两类决定的原生 gRPC metadata 也未声明私有缓存边界。这是既有私有审核事实传输约束的遗漏，不增加业务规则、权限或写命令。

App 本地修复提交 `52ea87aff89e66d32621d508bc2eb6cd486bd984`：两个决定入口、身份 middleware、HTTP 早期过滤及错误编码统一使用 `private, no-store`。新增真实生成 handler/原生 gRPC 回归，先复现失败再通过，覆盖成功、401/403/409/500、Version 503 和 HTTP JSON 绑定 400；原有真实决定 E2E 也补充响应头断言。

修复后 `make check-full` 24/24 PASSED，报告 `.artifacts/verification/20261016T081304Z-muguvlfv/report.json`，changed_sources=[]；Go 1.25.5，Mongo race 1279.308s、HTTP/gRPC E2E 162.054s，最终集成 stage 1285.093s。被测来源为 `3a83152` 加 staged patch SHA-256 `2243592d3da95f2dd40c93529c3decc18ce407c2ad0aa09d2c58e3ec24eb78af`，逐字节相同地提交为 `52ea87a`；API 仍为 `27c9743`，App 工作区干净。

Console 当前使用的修复 artifact 为 `iwut-app-center:review-cache-candidate`，另有等价 tag `iwut-app-center:review-52ea87a`，两者均指向 ID `sha256:a34ff33dd624ca55a162006c51580282aecf73ea42c676b81582c654568cf166`。该镜像是在正式提交前从上述冻结 patch 构建，标签如实保留 `3a83152+review-cache` 及 patch hash；Go 1.25.5 CGO0，仅替换固定 runtime base 中的 binary。它替代上节的初始 App artifact，Gateway artifact 不变；未 push/部署。

Console 冻结提交 `543fe2a` 的固定镜像决定专项已 12/12 通过（浏览器 1.2m）：Version 批准/拒绝、Profile 显式 NONE 首次公开和已观察 UUID 替换、错误 pointer 409 保持原态、真正重叠的单次决定串行化、已提交响应正文截断后的未知结果回读、在途请求/30 秒 deadline/PENDING 不自动重放、页面退场与迟到回执隔离、精确权限/跨 surface/利益冲突、正式撤权与重授，以及 APPROVE 终检实际 SYSTEM REJECTED。决定 200/403/409 的私有缓存头已在该真实链路观察通过。

该 12 项是 focused 证据，不替代 Console 完整门禁。其无参数 full compatibility 和最终冻结 published-latest 全量尚在执行。默认早期诊断轮为 pre-70 working snapshot（运行期间来源变更，不能作为最终冻结提交验收），100 项中 84 通过、4 失败、12 个新决定用例明确 skip；四个失败仍为既有查询错误缓存头矩阵。Console 所有用例暂不登记 COMPLETE。

## 后续串行交接

1. App/API 已完整验收并本地提交，Gateway owner 已激活第 2 步： 更新固定 API，给两个决定 RPC 增加精确 `ADMIN` surface。特别验证 HTTP JSON 不因旧 Proto decoder 丢失新增 definitions/公开资料字段，以及反向 surface、Cookie、CSRF 和伪造身份拒绝。
2. Gateway 验证完成后，Console owner 更新固定生成输入与严格校验，再接入已有审核用例内的批准、拒绝、指针确认、409 重新确认和未知结果回读。任何新业务设计缺口按用户约定暂停审核。
3. Console 的既有 Application 管理详情/列表错误 no-store 失败仍是独立已知问题；本包只补齐审核查询的缓存头，不将其当作整个 Console 门禁已通过。

所有提交、兼容镜像及验证仅在本地完成，不 push、不部署。不改 Auth、客户端 Catalog/Filter、受控 icon 或其他暂缓功能。
