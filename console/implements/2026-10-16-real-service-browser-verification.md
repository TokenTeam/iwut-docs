# Console 真实镜像浏览器联合验收工作包

状态：`ACCEPTED / IMPLEMENTED`（成功数据链基线；完整 UC 验收矩阵仍继续实施）。

日期：2026-10-16。依据用户对本线程的持续授权，Console agent 自行接受本工程工作包并记录以下决定。功能范围沿用 UC-CONSOLE-001–005，不新增业务命令或产品授权规则。

## 目标与决定

补齐现有 fixture 浏览器测试不能证明的成功数据链：真实 Browser → Console BFF → 共享 Traefik → Gateway → Auth/App，以及真实测试邮件投递。Backend 使用 CNB 发布的 Auth、App、Gateway `latest` 镜像；每次执行先 pull 并记录实际 digest，同一次运行使用已解析的 image ID，保证一轮内一致。测试不读取本机其它仓库，不编译后端，不依赖宿主 Mongo 数据。

测试创建独立 Docker network、Mongo replica set、运行时 RSA 密钥、测试证书和两个独立 BFF；运行后回收该次资源。密钥、邮件验证码、上游 Session 与浏览器状态只存在临时目录或进程内存，不进入 Git、测试报告、trace 或 stdout。无 sudo。

浏览器通过本地 HTTPS 的两个独立 Console Host 访问正式 production build，执行真实 Cookie、Web Crypto 与 IndexedDB 流程。测试 CA 只由该测试配置接受，产品 Cookie 的 Secure/HttpOnly/__Host- 属性保持启用。测试 SMTP 只接收该次 Auth 发出的邮件；浏览器测试在驱动端读取验证码，不增加产品邮件或调试 API。

账号优先经正式注册/登录 API 建立；为后续只读管理页面准备的受控 Application/Version/Profile/Tester 数据，可以通过单次临时 Mongo fixture 写入，必须显式说明这是数据准备，不能用它证明业务写命令正确。测试不得伪造 BFF Cookie 或替换 Gateway/Auth 身份交换响应。

Session 失效验证允许在同一隔离 Auth 数据库中把本轮 Developer 的现有 Session 标记 revoked，再由真实 Auth/Gateway 拒绝受保护请求、浏览器清理私有缓存和 BFF Cookie；这是外部状态变化 fixture，不代替 Auth 撤销命令正确性测试。控制端只接受本机随机 token 且只能操作本轮固定目标，不向产品浏览器提供数据库能力。

## 验收范围

- 两个 Console 的真实邮箱登录和已有浏览器凭据登录；Cookie 不含可读上游 token，两个 surface 不相互获得 Session。
- UC002–005 在真实已登录页面中读取 Application、Version、资料修订、Tester 管理成功数据，验证 ProtoJSON 字段、enum、时间和大整数；同时验证统一不可访问与 Session 失效回收。
- 浏览器不注入路由响应 fixture；后端、认证、邮件或路由失败即报告失败，不改为 mock 或跳过成功门禁。
- 为该链路新增明确独立命令；既有轻量 fixture/edge 测试继续承担各自范围，不报告为完整联合验收。

完整 UC001 的重发协调、迟到响应与其它仍未实现的交互，仍按 UC 正文逐项实现；本工作包只在真实执行证据覆盖到相应要求后更新实现状态。

## 2026-10-16 执行结果

Console 新增 `pnpm test:real`，真实 Playwright 共 2 项通过；没有 page.route 或业务响应拦截。证据覆盖：

- 两个独立 HTTPS Console 的真实邮件 Begin/Complete、SMTP 验证码、设备私钥持久化及已有设备登录；验证 `__Host-` Cookie 的 Secure/HttpOnly/SameSite/host 边界、Session 安全摘要和双向登录隔离。
- Developer Application 列表/详情、Version 列表/详情、资料修订列表/详情/审核历史、Tester overview/Membership/JoinLink 三区域及 REVOKED 筛选均经过真实 Gateway/Auth/App；确认 no-store、ProtoJSON 字段与大整数、不可执行 URL 和纯文本 ID。
- 不存在的 Application 返回统一不可访问并回收旧 Tester 页面；返回本人 Application 后可重新读取；真实 Auth Session fixture 被撤销后，Gateway 拒绝、页面清空私有数据并移除 BFF Cookie，设备私钥仍保留。
- Auth 邮箱注册先经过正式 v3 API，邮箱登录等待其返回的共享 resendAfter 冷却，未改数据库配额或缩短业务冷却。App seed 通过严格 validator；数据准备不代表 App 创建/提交/撤销等写命令验收。
- 同轮实际镜像：Auth `sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3`、App `sha256:6f20c469a0e9566e045a5966fd51d81ce0b1293c650e2b277fa62bc3b5a3579b`、Gateway `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9`；后续运行仍 pull latest。

真实测试发现并纠正 UC005 首包误用媒体类型的问题：App 的实际 go.mod 是 Kratos v2.9.2，`application/json` 对 protobuf 已使用 ProtoJSON；误查缓存 v3 后改为 `application/protojson` 会得到 400。浏览器 App transport 已恢复正式 JSON 媒体类型，生成客户端仍按 ProtoJSON 解析；不修改或绕过后端 codec。

本轮还收口 UC005 状态边界：身份/Application 切换重置拒绝状态，401/404 当次渲染立即遮蔽三块数据，4xx 原子替换旧私有响应，仅网络/5xx 可保留旧快照；首页列表重置和全部刷新通过 generation 确保真实重发。Developer Vitest 当前 28 项通过，fixture Playwright 8 项通过、4 项按 Admin surface 跳过；全量类型/单测、生成漂移、build 与仓库独立性门禁均通过。

仍未由本基线证明：UC001 完整重发/迟到响应与结果未知恢复，各管理 UC 全状态/分页/管理权变化/生命周期并发组合，Admin Reviewer 决定，以及产品部署就绪。继续依据各 UC 的原始要求推进，不把 2 项成功数据链测试解释为所有 UC 已完成。
