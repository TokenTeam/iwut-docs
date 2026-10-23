# UC029 管理查询错误响应缓存头修复

状态：`COMPLETE`（后端修复与验收；镜像待发布），2026-10-23。用户通过 Console 联调反馈授权核查并修复 App 错误响应缓存头；本包不变更 UC、BR、授权、分页或 API 契约。App 提交 `d3f510e`。

## 缺口与责任层

Console 在固定发布输入下记录了 25 条疑似 App 缓存头失败断言，涉及两个 UC029 查询，而不是 25 个接口：正式转让后的旧管理员管理 GET 404（3 条 no-store）、5 个非法/跨 caller/跨 filter 游标 POST 400（10 条 private/no-store），以及资格角色矩阵中 6 个非管理员 GET 404（12 条 private/no-store）。400/404 与功能 body 断言原本正确。Console 另有 4 条决定 POST 的 Gateway Session401 缺 private，由 Gateway 负责，不在本包内。

当前 App 源码基线 `a3b41a3` 也存在相同缺口：成功类型在 HTTP response encoder 设置 `private, no-store`，但 `ListMyApplications` / `GetMyApplication` 未纳入共享中间件的私有响应策略，错误编码器也未识别这两个 HTTP route。错误不会经过成功编码器；原生 gRPC 成功和错误元数据同样缺头。

修复前以真实 Mongo/App/Auth/Gateway/Traefik 链路复现。App 直连及 Gateway edge 的非法游标 400、非管理员/不存在 404、正式转让后旧管理员 404 均缺 Cache-Control，而双方成功响应均已有头。故责任在 App 的源响应，不是 Gateway 丢失已有头。该证据来自本地 App 源码和真实依赖，不冒充重新执行 Console 的已发布镜像门禁。

## 修复边界与回归

- HTTP error encoder 仅为 UC029 的 POST `/v1/applications:search`、GET `/v1/applications/{application_id}` 补齐 `private, no-store`，包括发生在服务调用前的 JSON binding 错误。
- 共享 HTTP/gRPC identity middleware 在校验身份前为上述两个固定 operation 设置相同缓存元数据，覆盖身份、领域失败及成功。
- 不改鉴权、统一隐藏的 404、错误 reason/status、游标签名和 caller/lifecycle/platform/archive 绑定、业务数据及成功投影。没有 Auth、Gateway、Console、API 修改，也没有 BFF/Traefik 全局补头。
- 新增真实生成 HTTP binding/native gRPC 回归：HTTP 17 个场景、gRPC 16 个场景，覆盖成功、无效查询/游标、隐藏资源、损坏状态/内部失败、身份失败及 JSON binding。
- 在原 UC002–005 Gateway/Auth 专项中追加 UC029 对照：每条场景均实际请求 App HTTP 和真实 Traefik→Gateway→App，合计 22 个响应。涵盖默认成功、非管理员与不存在统一隐藏、5 类游标绑定失败，以及正式发起/接受管理转让后旧管理员 404、新管理员 200。转让使用正式 API，不直接改 Mongo 管理员字段。

## 当前验证

生成 transport 测试及真实链路均先 RED 后 GREEN。修复后 UC002–005 Gateway/Auth 组合专项通过，新增 22 个对照响应均符合原状态/错误语义及 `private, no-store`。固定依赖：

- Gateway 提交 `3e8a59cd8b309c8f1e096ea95cac25a624738ba4`，只构建其 committed archive，不读取邻居未提交修复；API `27c9743d2d7476511932a83563e103aee5b4e28e`。
- Auth 镜像 `docker.cnb.cool/tokenteam/iwut-auth-center@sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3`；现有固定 Session→真实 USER 测试夹具，不将其描述为当前完整注册 UI 验证。
- Go `1.25.5`；Traefik 使用 Gateway `image.lock` 的固定 digest。
- 专项诊断：`iwut-app-center/.artifacts/integration/run-tDv281tR`（修复前）、`run-xf0wAfsx`（修复后）。诊断不提交，不记录/转发凭据或私有正文。

完整 `make check-full` 冻结 App/API/committed docs 后 **24/24 PASS**，`changed_sources=[]`。最后一项真实 Mongo/HTTP/gRPC race E2E 用时 1455.324 秒，其中 Mongo package 1449.764 秒、composition/HTTP/gRPC package 165.212 秒。报告：`iwut-app-center/.artifacts/verification/20261023T072255Z-b2u0qc1h/report.json`。这是 backend tier；真实 Auth/Gateway 专项另以上述固定输入通过，不把它写成 28 项 cross-service tier。

Docs 固定 `06f849e4bc0108456d7eae800fdea0e810e47b20`，指纹 `1250c767f2d6516e4cc397a41144b1e1e945620e0ac19ba5198355e350df3f19`；API `27c9743` 干净，指纹 `85bff81fa5209ae63459fa7b104330177ecc4eb9bc81d61a6f2490b6b29286fb`。App 提交前验证输入为 HEAD `a3b41a3` 加本包改动，指纹 `eaa7df174d0400a5f8f5fa3a171e4e502197d26ee99fc3739324f4666a8adc9c`；随后本地提交为 `d3f510e`，逐文件内容/模式清单一致，未在验证后修改代码。新记录与实施索引另经 brief/registry 检查，不改权威 UC/BR 或生成内容。

## 发布与联合复验

实现验收阶段仅授权本地修复、回归和提交；2026-10-23 用户随后明确授权 commit + push。本次推送仅包含 App 修复及对应 App 文档，不带入独立 Auth 文档提交，也不扩展为产品镜像构建或部署授权。Console 记录的 App published 输入仍是 `sha256:2af4af71e8eb8f1ea46e92bfdaa3e8e14944cb0bc4ca46b95c9a05db6c46340a`；没有据本地 GREEN 将其宣称为已修复。后续需发布包含本包提交的新 App 镜像，再由 Console 保留全部断言、拉取并固定新输入，执行对应专项及完整 published 门禁。Gateway 的 4 条 Session401 修复和其它设计开放项分别处理。
