# UC001 邮箱重发与浏览器恢复控制增量

状态：`ACCEPTED / IMPLEMENTED`（客户端增量；UC001 整体仍为 IN_PROGRESS）。

本工作包依据用户持续授权由 Console agent 自行接受，实施 BR-CSE-005–008 中当前客户端可以独立保证的交互，并保留 BFF Cookie 并发的真实缺口，不改变认证协议或后端规则。

## 决定与范围

- 同一页面一次只进行一个登录方式；邮箱流程打开时不再并发发起设备登录。组件卸载或流程替换会中止浏览器请求并丢弃其迟到的页面回调，浏览器适配器在签名和凭据接管前检查取消。
- 首次邮箱 Begin 保存规范化邮箱、requestId 与 localId，之后原请求恢复固定这些值；Begin 不确定或暂不可用时不生成新密钥或改变邮箱。只有明确的重发操作会更换 requestId，且仍复用 localId。
- 收到有效 challenge 后按服务端 resendAfter 提供可访问的倒计时和重发按钮。重发先清除旧验证码与签名上下文，再用新 requestId 发 Begin；结果不确定时恢复这个新请求，不回退到旧操作。
- 到 expiresAt 后立即清除验证码、challenge 和 signingPayload，停止 Complete，保留同一设备密钥与可重新发送的最小上下文。请求期间不允许再提交或切换方式。
- Complete 的网络/超时、5xx、已完成 reason 或不可解释成功响应进入结果待确认；提供已有设备探测及原操作有效时的明确重试。不会自动再次提交，不解释为确定失败。
- 合法 Retry-After / retryAfterSeconds 约束显式重试，计时期间不轮询登录 API。错误摘要可聚焦，倒计时采用文本表达。

交互取舍：请求进行中禁用本页取消和方式切换，避免主动制造第二个并发登录请求；离开页面仍会中止请求并隔离回调，但不把它表达为服务端取消。Complete 在有效期内已发送而等待响应时，到期清空页面的一次性材料，不据此猜测服务端提交结果；有效成功响应仍可以完成登录，不确定结果仍提供同一设备探测。到期只禁止再次提交旧 Complete，不清除设备密钥或已经存在的结果待确认状态。HTTP 503 的合法 Retry-After 即使被分类为结果未知也继续生效。

组件没有能力撤回已经到达浏览器的 Set-Cookie；BFF 的跨请求/跨副本 fencing 和已发出响应的 Cookie 到达顺序问题另在 [登录 flow fencing 缺口](../query-contracts/login-flow-fencing.md) 跟踪。本工作包不将 UI AbortController 等同于服务端事务取消，不宣称 BR-CSE-005 全部通过。

## 验证

Testing Library 覆盖同参数 Begin 重试、新 requestId/同 localId 重发、倒计时、到期擦除、取消/卸载迟到回调、登录方式互斥、结果未知与限流。浏览器适配器覆盖取消前不签名/不接管、已完成和畸形成功响应进入未知。真实镜像 SMTP 浏览器测试继续验证主链并增加明确重发后登录，不通过改写服务端时钟或配额缩短冷却。

全量生成漂移、类型、单测、build 和 fixture/真实浏览器门禁沿用现有命令。UC001 在服务端并发缺口和完整恢复矩阵收口前保持 `IN_PROGRESS`。

## 2026-10-16 实现与证据

Console 实现 commit：`b0b2614`。

- 两个 Console 共用独立的邮箱流程组件，使用每次请求的 AbortController 身份和组件生命周期约束异步消费；设备与邮箱方式用同步互斥保护，不依赖 React 下一次渲染才能阻止重复提交。取消/卸载不删除设备私钥。
- 浏览器适配器在读取设备、公钥校验、签名、响应和凭据接管的异步边界检查取消；Complete 的 5xx、已完成、不合法/已到期成功摘要和本机 credentialId 保存失败均作为结果未知。上游 Retry-After 与 Kratos metadata 只投影规范化等待秒数，不转发私有诊断字段；未知结果保留等待秒数。
- Testing Library 覆盖原邮箱/requestId/localId 重试、显式重发、到期清理、未知恢复、键盘错误焦点、取消/卸载与重复提交。有效协议 frame 的适配器测试证明取消前不签名/不接管以及未知分类；它们不证明服务端事务回滚或 Cookie 响应顺序。
- `pnpm test:real` 2 项通过；Developer 用真实 SMTP 第一封邮件建立等待状态，等待服务端 resendAfter 后用键盘明确重发，确认新 requestId/相同邮箱与公钥、旧验证码为空，再用第二封邮件成功登录。最终 IndexedDB 仍只有一把 non-extractable 私钥；Admin 独立邮箱/设备登录和 UC002–005 管理读取及真实 Session 失效基线继续通过。
- 本次仍拉取 CNB latest，实际 Auth/App/Gateway digest 与上一真实镜像工作包一致；无后端源码编译，无时钟/配额改写，无 sudo；临时容器和网络已清理。
- 全量 strict typecheck、生成输入漂移、Vitest、production build 和 fixture Playwright（8 项通过、4 项按 Admin surface 跳过）通过。真实 E2E 运行 production build，不依赖 Vite fixture response。

保留缺口仍以 UC001 原文为准：跨标签页/跨副本/在途 Set-Cookie fencing、服务端取消确认与完整恢复矩阵尚未实现。这些缺口不是本增量的完成声明；不得把结果未知时的 mock 设备探测与原 Complete 重试组合解释为真实后端全部恢复路径已通过。
