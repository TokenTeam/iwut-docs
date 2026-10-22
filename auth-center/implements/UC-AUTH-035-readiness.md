# 宿主 OAuth 与账号客户端续作检查

状态：`DESIGN_BLOCKED`；UC035 为 `DRAFT / NOT_STARTED`，不表示已接受。

## 2026-10-22 检查范围

用户澄清第三方主要在 iWUT 应用内启动，通过 RPC 或自己的后端完成 OAuth 登录，不要求独立网页登录；授权自行建立 UC、使用 subagent 和实施，但要求遇设计问题中止。父任务与三个只读 subagent 核对当前 Auth `e99ae89`、Gateway `3e8a59c`、Console `52d2598` 及本地文档工作树后，因授权/交付边界尚未冻结而停止代码实现。

本轮仅建立 [UC-AUTH-035](../use-cases/UC-AUTH-035-authorize-application-in-host.md) 草案、索引和检查记录，不自动 ACCEPTED、不开公开端点、不改旧协议或生产开关。不涉及提交、推送、部署。

后续用户已确认官方宿主可信 consent 界面，并给出正确参考 `TokenTeam/native-rpc-h5`。已只读检查 H5 SDK HEAD `87ce6d8` 与 npm `@token-team/native-rpc-h5@0.0.1`（两者 gitHead 不同），补充[RPC 适配设计说明](../design-notes/host-oauth-rpc-design.md)。库仅作调用模型参考，不自动满足 Native caller/代际/确认保护；code 交付与两类 client 协议仍需冻结，实际 Native 集成归宿主交付。UC035 保持 DRAFT，未生成 brief 或实施代码。

最新职责澄清：RPC 传输与 Native 内部实现由宿主负责，不再列为 Auth 后端开工依赖。Auth 仅冻结平台 Session 下的授权交互、当前用户/client/scopes 绑定、最终校验及 code 交付/兑换语义；宿主负责原页面接收隔离与可信 UI。实际 Native 集成仍须在宿主启用前验收，不据后端测试宣称完成。

## 2026-10-22 API 兼容与文档发布批次

用户授权检查 API 更新影响，无阻塞后提交并推送。`a5d504c → 27c9743` 仅修改 App 审核查询的两份 Proto 及对应 Go 生成物：新增审核检查定义与当前已发布资料读模型，无现有字段号/类型或 RPC 变化；Auth Proto、Auth 生成物和 Go 依赖均无差异。检查开始时 Auth 固定 `a5d504c`；期间其他并行工作产生仅对齐 API pin 的 Auth `8b803db`，固定到 `27c9743`，本批未修改该指针。新增读模型不等于旧 App 服务已能返回新内容，不能以 wire 兼容替代各消费者的功能验收。

API `proto-check`、`go test ./...` 和已固定 `27c9743` 的 Gateway `make check`（含 race、Wire、生成物及路由配置）通过；Auth `8b803db` 的 `make check` 重新通过，未重跑真实 Mongo 全仓。Console 当前固定 `27c9743`，本批未修改或重新验收 Console。刷新远端后 API master 已为 `27c9743`；本批只操作文档提交/推送，不重复操作这些代码仓库的并行发布。

本批文档从刷新后的 docs `main@917b23e` 建独立分支，只携带 Auth 交付记录、相关 brief 和 UC035 草案/职责收敛；不把旧检查分支的 App/Console 提交混入，不直接推送 main。UC035 仍未 ACCEPTED，不包含宿主授权 API 实现、生产开关或部署。

## OAuth 宿主入口

UC014 的 grant/code 核心与最终重查已实现；Auth 有同源 Cookie 桥及 consent HTTP，但没有宿主创建/读取/确认授权交互 RPC。当前 `oauth-oidc-v1` 明确使用门户、系统浏览器、登记 HTTPS callback 和 303，不是可直接实施的宿主 RPC 协议。新方向不要求单开网页，但必须补受信 caller/consent/结果归属机制，而不是把 Session 或用户密码交给第三方。

App UC023 的 launch descriptor 不拥有 bridge/consent/token，capabilities 也不是授权凭据。具体阻塞和推荐选项唯一见 UC035，审核前不冻结 wire/Proto，不创建第二套 grant 或登录身份。

## 第二项：Gateway 与资源服务

已有 UC-GW-002（当前 `PROPOSED / NOT_STARTED`），无需重复建立新 Gateway UC。可拆为：

- 标准 discovery/JWKS/token/revoke/UserInfo 的精确 HTTP DIRECT 接入及载体清理；
- Auth UC030 的 HTTP Bearer storage 精确接入，Auth 自己消费 opaque token；
- Gateway→独立资源服务的 UC019 委托链及资源验签/业务授权。

前两项不要求凭空新增业务 scope，第三项当前没有权威真实 routeId→scope→audience→allowedChannels 清单与已交付独立资源验证器。`items.read/resource-service` 仅为示例；不得据此开放 App 管理权限。UserInfo 与 Auth Storage 已有直接 Bearer 验证，不能包装成 UC019 独立资源委托验收。第三方仅需登录/资料时，不必以通用资源委托链为前置。

Gateway 目前拒绝 OAuth Bearer/委托策略；其工作包按自身 README 直接读取 UC/ADR/契约，当前脚本不支持 Gateway brief，不能伪报已生成。用户要求遇设计问题中止，本轮不接受 UC-GW-002 或开始部分代码。

## 第三项：账号客户端

Auth UC006/011/020/032/033/034 与 Gateway 的对应公开 RPC 路由已存在。默认密码登录宜修订 UC-CONSOLE-001，不重复创建 Auth 登录 UC。Console 当前 API pin 已含 password Proto；缺生成选择、客户端、BFF、浏览器验证与 UI 的消费，不是缺 Auth 密码协议。

注册、密码恢复/修改、邮箱管理、设备和 Session 管理不在原 UC-CONSOLE-001 范围。应在明确目标客户端后分别建立功能 UC，不把注册/授权/凭据撤销混成一个登录动作。需决定通用账号创建/管理是否进入 Developer/Admin Console，还是只由移动宿主承担。未作决定前不在任一客户端自动新增页面。

另一个重要工程边界：当前 Console AGENTS 指向的已接受 Session v2/fencing 文档位于同一 docs 仓库的 `iwut-docs-console-uc002` 工作树（调查时 `console-uc002@475f4dc`），并非当前 `/docs/console` 的旧 Cookie 基线。已核对该工作树中的 ADR-CONSOLE-005、console-session-v2 和 login-flow-fencing。不得在陈旧 Console 文档分支新增/覆盖安全协议，也不能把代码中已有持久 fencing 当作未实现。

密码登录本身可在该基线上分包：UC001 增加 PASSWORD flow、同 root 设备恢复、跨副本 CAS 和迟到响应隔离；密码不持久化至 flow、Cookie、Query、日志或请求指纹，完成未知/已完成用原钥 UC007 恢复。正式改密换发 Session 的 CAS/未知结果恢复则需所属管理 UC 明确定义，不能直接向 Cookie 写入新 token。

## 继续实施的前置条件

Auth UC035 先冻结并审核宿主→Auth 的交互接口、确认保护与 code 交付/兑换，不以 Native 内部实现或通用账号 UI 归属为前置。账号客户端另行确定 UI 落点；若要求通用资源委托链，则另指定首个真实资源能力与路由政策。各自依赖闭合后按用户既定流程接受 UC/修订、生成所支持的 brief，再实施与相应验收。当前不把草案记录或只读调查视为实现完成。
