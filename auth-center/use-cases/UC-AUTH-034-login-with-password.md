# UC-AUTH-034：使用登录邮箱与密码登录

状态：`ACCEPTED`

## 目标与范围

用户以当前唯一登录邮箱＋平台密码进入原 iWUT 账号，后台证明本机私钥持有、登记或复用当前有效设备凭据并建立 Session。密码登录作为默认主动登录入口，UC012 邮箱码登录保留为备用，UC007 继续记住登录；不要求每次额外邮件码。

2026-10-13 用户授权开始实现，协议及工程参数作为本工作包接受。不自动注册，不改邮箱/密码/校园认证/权限，不接受非登录学校地址，不把新生成设备密钥当作第二因子或标准 WebAuthn。入口须等 UC033、注册/邮箱及全部认证消费者交付并验收后才能启用。

## 参与者与依赖

- ACTIVE USER 已有 UC033 安全密码材料及 UC011 当前唯一已验证登录角色。
- 客户端准备系统安全存储的 P-256 新密钥，或使用原账号当前仍有效密钥；Auth 不接收私钥/自报 authId。
- 两个匿名入口明确不带 Session，不以已有身份决定目标，不能认证失败后创建账号。
- 硬依赖 UC033 策略/hash/统一代际与凭据下界、UC011 登录角色查询、UC007 Session/LRU 及所有消费路径；当前尚无实现。

## 输入与输出及 API 提案

独立 `auth_center.v1.password_login/PasswordLoginService`，HTTP/JSON/native gRPC，Gateway DIRECT；精确 byte/message/载体见[密码协议草案](../../platform/contracts/auth-password-v1.md)。

```text
BeginPasswordLogin { requestId, loginEmail, credentialProposal }
PasswordLoginStarted { operationId, challenge, signingPayload, protocolVersion, expiresAt }
CompletePasswordLogin { operationId, password, proof }
PasswordLoginResult { authId, credentialId, session: SessionEstablished }
```

Begin 不带密码，以避免把明文秘密存入挑战；Complete 经 TLS 带密码及本机签名。不返回验证码/邮箱存在/owner/内部版本，不调用 SMTP。不改变设备 `iwut-device-v1`，不复用 LOGIN 或 LOGIN_WITH_EMAIL 签名。

## 主流程

1. 用户明确密码登录，提交当前登录邮箱、公钥提案和 requestId；客户端保留对应私钥。
2. Auth 规范地址/公钥，保存独立 5 分钟挑战及当时登录角色/账号/密码版本，或不可登录占位；Begin 不登记凭据、不验证密码。
3. 客户端核对用途/部署/邮箱/公钥/期限，后台签名，Complete 提交密码与签名。
4. Auth 在共用昂贵额度下验证密码与新签名，最终事务再次确认 owner、ACTIVE、角色/密码/账号版本、操作、凭据状态和下界。
5. 同事务登记或复用合法凭据、建立 `PASSWORD_AND_DEVICE` Session、按 UC007 LRU 管容量、消费挑战/审计；确定提交后一次性返回 token。
6. 以后自动登录用 UC007；忘记密码可选择 UC012 备用登录或 UC033 明确重置，不把失败自动变成注册。

## 业务规则

<a id="br-lgn-031"></a>
### BR-LGN-031：唯一登录邮箱与默认密码入口

只认 UC011 当前唯一已验证登录角色，不从邮箱列表任意匹配，备用邮箱码入口保持同样条件。密码存在只允许校验账号既有秘密，不能用“任意已验证地址＋正确密码”更改账号归属或绕过角色选择。未知/非登录/禁用等 Begin 固定不可接受，之后创建/换角色/恢复不会使旧操作有效。

普通密码登录不强制邮件码；前台选择密码或验证码是便利性分支，不改变账号、设备/Session/密码危险动作要求。无密码数据或旧测试缺字段失败关闭，不填默认密码/代际，不因本机密钥缺失自动注册。

<a id="br-lgn-032"></a>
### BR-LGN-032：独立挑战与密码验证

purpose=`LOGIN_WITH_PASSWORD`、challenge CSPRNG 32 字节、5 分钟、最多 5 次密码/签名验证失败；时刻等于到期即拒绝。签名 Frame 唯一由平台密码协议定义，绑定操作/邮箱/完整公钥/期限/预配 serviceId/applicationId，不包含密码。Complete 不能覆盖提案或由客户端指定验证结果。

密码验证遵守 UC033 Argon2id/NFC/昂贵限额；对不存在或不可接受账号使用同成本受控 dummy verifier，并统一认证错误，不承诺网络层严格等时。需要先捕获密码快照，最终比较版本，不能接受开始验密后发生改密/重置的旧结果。

每次验证失败计数原子更新，依赖故障不伪装为错误密码；一般请求也限流，不能换 challenge 绕过账号/地址桶。Begin 幂等按受保护规范地址＋requestId 24 小时，同键异提案冲突，不重造/延长挑战；容量有界。所有公开占位操作也占容量，不能无限登记任意公钥。

<a id="br-lgn-033"></a>
### BR-LGN-033：原子登录与不可复活

新公钥登记 credentialRevision=当前 accountRevision；同 owner 公钥只有未撤销且不低于 UC033 下界时可复用。已撤销/退休/他人公钥一律不能绑定或推进版本，须生成新密钥；只有 UC033 正常改密事务能保留当时的当前有效凭据。

Session 方法固定 `PASSWORD_AND_DEVICE`，必需 credentialId、passwordRevision>0、accountRevision 和认证时间；密码版本为签发快照，后续密码变更通过统一账号代际使旧 Session 失效，不用参数重哈希升级踢人。其 Session/LRU/检查/JWS/管理权限与其它合法方法一致，不要求一直保留短期登录操作作为 Session 可用依赖。

最终复核/凭据登记/Session/LRU/操作消费/审计同事务；密码与签名验证外部快照在事务重试时重新确认，旧校验不得穿过版本栅栏。密码/码/设备三种流程不因证明丢失互相降级。

已完成操作不再次披露 token，返回 PASSWORD_LOGIN_ALREADY_COMPLETED；响应未知保留本机私钥，通过 UC007 新挑战确认原账号。与改密/重置并发导致原公钥退休时，旧登录不得返回成功或复活凭据，应由用户重新明确登录并后台换新钥。

<a id="br-lgn-034"></a>
### BR-LGN-034：失败、隐私与交付

所有匿名失败不区分账号存在、登录角色、密码错误/版本变化、占位或挑战状态；已证明原账号密码/设备控制后才能披露受控公钥冲突。日志/审计只有必要操作标识/结果/时间，无密码/hash/完整邮箱/签名/token。

输入/载体错误 400；认证失败 401；同键异提案或已完成 409；共享昂贵验证/挑战容量 429；存储/hash/审计/提交未知 503。具体 reason/字段号采用已接受密码契约，公开向量与实现逐项交付；默认关闭，不以 UC012 备用入口掩盖 UC034 未交付。

验收必须含两种前台登录、默认/备用明确 UI、非登录地址拒绝、dummy 验证、NFC、挑战/版本/部署/用途串用、5 次失败、幂等/未知提交、同公钥并发和退休拒绝、与改密/重置/换邮箱/禁用/注销竞争，以及所有认证方法 HTTP/native gRPC/Wire/Mongo race/Console/Gateway 回归。

## 依赖与变更记录

[UC033/034 readiness](../implements/UC-AUTH-033-034-readiness.md)记录真实代码缺口，2026-10-13 用户授权实现，生成 UC034 brief 后开工；Proto/vector/consumer 完整检查是启用门禁，不迁移旧数据。

- 2026-10-12：建立默认邮箱密码＋后台设备证明登录 DRAFT；保留 UC012 备用码登录及 UC007 自动登录，新增 PASSWORD_AND_DEVICE 和密码/角色/统一代际门禁，待完整审核。
