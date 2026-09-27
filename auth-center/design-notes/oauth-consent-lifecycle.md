# 应用登录、用户 Scope 授权与撤销：设计讨论草案

状态：`PROPOSED` — 非权威的讨论材料；尚未分配 UC/BR、接受协议或启动实现。

## 本轮优先级

2026-09-27：用户决定优先设计应用登录、用户 scope 授权和收回；Scope Catalog 的在线更新与管理后台后移。目录更新频率低不改变其权威归属，既有 UC001 和跨服务契约继续有效。

本轮先明确授权闭环。后续按职责拆成正式 UC，再固定跨系统协议与实现 brief。下文均为建议；不能据此启用 Gateway OAUTH2 或把现有开发用硬编码目录视为生产授权配置。

## 首版场景待确认

候选场景是 iWUT 宿主内运行的应用，复用已有平台 Session；也可能需要外部网站/独立后端的跳转登录。已向用户询问首版范围，尚未把其中任一项作为接受决定。

场景影响 callback/redirect URI、OAuth client 类型、凭据保管和登录结果交付。以下权限边界对两种场景均适用；具体 browser/host bridge 流程等场景确认后决定。

## 三类身份和数据

| 对象 | 用途与归属建议 |
| --- | --- |
| 平台 Session | 官方客户端代表用户管理账号，继续由 Auth 拥有，不交给第三方应用 |
| OAuth client | 某个应用的具体接入实例；与 Application 的不可变 UUID 明确绑定，不用 name 或 developerHandle 鉴权 |
| 应用 access token | 应用在特定用户授权范围内访问指定资源的凭据；与平台 Session、内部 trusted-identity-v1、服务 JWS 分离 |
| Scope Catalog | Auth 定义稳定 scope 含义；首版可低频运维装载，写入管理暂缓 |
| 应用许可范围 | App 拥有版本申请、审核及发布事实；Auth 从可信服务契约取得，不信任浏览器提交的“已批准 scopes” |
| 用户 grant | Auth 保存用户对应用的具体授权、revision、撤回状态及审计 |

一个 Application 是否对应一个或多个 OAuth client、测试/正式接入如何隔离，需要在 client 注册契约中固定。首版禁止未经登记的 client 动态提供回调地址；launchUrl 不自动等于 OAuth redirect URI，developerHandle 也不等于 client_id。

## 授权闭环建议

1. 应用发起针对自身的请求；Auth 解析已登记 client 和其受信应用许可范围。
2. 官方客户端或 Auth 控制的授权界面使用当前有效平台 Session 确认用户身份。应用不拿到平台 Session，也不能自行展示“已同意”后直接声明成功。
3. 展示服务端解析的应用身份、权限含义、必需与可选项，以及本次相比已有授权增加的范围。
4. 用户同意后，Auth 原子保存 grant 及审计并建立短期、一次性授权结果；选择授权码方案时绑定 client、授权事务、grant revision、PKCE challenge 和精确回调信息。
5. 应用用授权结果取得仅限自身、指定资源和已授予范围的访问凭据；资源入口在线验证当前授权。
6. 用户可查询已授权应用，撤回部分 scopes 或整个授权；权限收缩影响旧凭据及尚未消费的授权结果，之后重新同意也不能复活旧凭据。

用户拒绝本次申请不等于撤回此前授予的权限。应用版本新增 scope 不能自动扩大旧 grant；减少 scope 也不能把缓存的旧申请集合当成新的许可。现有 requiredScopes/optionalScopes 是应用运行需求，不能剥夺用户日后撤回必需权限的权利；撤回后该功能可能不可用，由应用和宿主展示明确结果。

## OAuth 登录的含义

OAuth 解决委托访问；应用建立自己的登录身份还要固定“用户是谁”的可信输出。若要标准化外部登录，优先评估 OpenID Connect 的 code flow、ID Token 与 UserInfo；若仅提供宿主专用身份接口，应明确它是 iWUT 自有协议，不宣称完整 OIDC 兼容。

建议应用看到按 Application 隔离的稳定用户 subject，而非直接公开内部 authId；准确的 subject 生成/保留策略需后续确定。该 subject 不等于学生 association 分组，也不随 developerHandle 改变。不得因“登录”默认授予邮箱、学号、学校密码、跨应用关联标识或所有资料访问。

ID Token（如采用）用于登录断言，不充当 API access token。用户收回平台数据访问授权，也不保证能删除第三方应用已建立的本地登录 Session 或已获取的数据；产品文案和接口语义应区分这些结果。

## 访问范围的确认

一次授权和一次资源访问所允许的范围，要同时受以下事实约束：

- 此 client 对应的应用/版本经过平台允许的范围；
- 用户当前仍然同意的范围；
- 本次请求及此 token 原本获准的范围；
- 当前资源服务适用的授权策略。

scope 存在于 Catalog 只是名称合法，不构成访问授权。UC001 的 requestable 只控制新申请，不自动撤销旧授权；紧急禁止访问若有需要应另定义明确策略，不能偷换这个字段含义。资源服务还要检查数据归属和具体操作，scope 不替代所有业务校验。

当前 UC-APP-012 的 TestLaunchDescriptor 是解析时的快照，不是授权租约，也不是可直接提交给 Auth 的可信许可证明。Auth 与 App 的许可读取契约、revision 绑定、版本撤回/Tester 移除后的失效时点必须一起设计，不能把跨库调用称为同一原子事务。

## 凭据方案建议

若使用标准 OAuth 重定向流程，采用 Authorization Code + PKCE S256；公有客户端不预置可被当作秘密的共享 client secret。固定 client 注册、精确 redirect URI、issuer/请求关联校验；不使用 implicit 或学校/平台账号密码换应用 token。宿主 bridge 的具体传递方式待场景确认。

结合单机、可接受在线检查和用户主动撤回需求，首版优先评估随机不透明 access token，服务端保存摘要及 client/用户/grant/范围/资源/期限。OAuth 不要求 access token 是 JWT。先不引入 Redis，也不直接复用内部 Session-to-JWS 身份令牌；如之后签发内部委托 JWS，必须有独立类型/载体及最小授权上下文，不能把应用请求升级为普通平台用户权限。

是否签发 refresh token 等首版应用运行模式确定后决定。若需要公有客户端长期续期，必须设计轮换或发送方约束、重放检测和授权撤回传播，不能只添加一个长期字符串。若暂不提供 refresh token，则明确过期后重走授权流程的体验及已授予权限的复用条件。

## 撤回与并发建议

建议以有效平台 Session 允许用户管理自己的授权，拒绝应用替用户撤销其它应用授权。

- 全部撤回：原子标记 grant 撤回、推进 revision/epoch 并写审计，所有引用旧状态的 token 和未兑换 code 后续校验失败。
- 部分撤回：只能删除已授予范围，不能通过更新接口追加授权；首版可使旧凭据整体失效，保留剩余 grant 并允许申请更窄的新凭据，避免旧 token 继续声称原有 scope。
- 权限新增、删除后重新授予不使历史凭据重新生效；不能只比较“现在的 scope 集合恰好相同”。
- 撤回确认后开始的在线授权检查应拒绝旧凭据；撤回前已经通过检查的在途操作可能完成，不能承诺回滚已返回的数据或完成的副作用。
- Auth 不可用时受保护访问拒绝；若以后缓存校验结果，必须重新明确最大撤回延迟，不能保持“即时撤回”的旧承诺。
- 查询、重复撤回、并发同意/撤回和提交结果未知均需明确幂等/冲突语义；按当前授权 revision 确认，避免旧授权弹窗覆盖刚完成的撤回。

RFC7009 的应用 token revocation 与用户在设置页撤销整个 grant 是不同入口；是否提供标准 token revocation 端点应独立明确，不用一个含糊“logout”接口兼任所有行为。

## 建议用例拆分

下表是候选工作包，不占用 UC 编号，最终名称及拆分在场景确认后确定。

| 候选 UC | 主要结果 | 关键前置契约 |
| --- | --- | --- |
| 用户确认应用授权 | 查询授权预览、处理允许/拒绝、保存 grant 并签发一次性授权结果 | client 登记与应用许可快照；可信授权 UI/宿主入口 |
| 应用兑换访问凭据及取得登录身份 | 校验 code/PKCE、签发受限凭据；固定应用识别用户的方法 | OAuth/OIDC 或宿主专用 profile；subject 与 resource audience |
| 校验应用委托访问 | Gateway/资源服务获得当前有效 client/用户/scope 上下文 | 独立于平台身份的委托契约、token 在线检查及下游授权 |
| 用户查看及收回应用授权 | 本人授权列表/详情、部分或全部撤回和审计 | grant revision、code/token 失效与在途请求边界 |

OAuth client 注册/配置若需要开发者自行管理回调地址或秘密，应单独成为管理 UC；若首版仅支持受控宿主，也必须有明确、可信、可验证的注册方式，不能把 client_id 当作拥有应用的证明。

## 进入 ACCEPTED 前的待定项

1. 首版是宿主内应用、外部网站，还是同时支持；标准浏览器跳转与宿主 bridge 是否分别交付。
2. client 注册来源、Application 映射、测试/正式隔离、回调约束及停用方式。
3. App 向 Auth 提供应用可申请权限的可信接口与一致性/撤回时效，不采信请求自报的版本许可。
4. 用户身份输出采用 OIDC 还是限定的宿主接口；最小 subject、scope-to-resource/资料投影映射。
5. access token 寿命、是否 refresh、授予复用与重新弹窗规则，以及部分撤回导致的客户端体验。
6. 最小生产 scope 清单及用户可理解的权限说明。可以暂不建设 Catalog 写入后台，但上线前必须明确权威来源，不使用开发 fixture 提供真实授权。

## 参考

- [OAuth 2.0 Security BCP，RFC9700](https://www.rfc-editor.org/rfc/rfc9700.html)：PKCE、重定向及 refresh token 的安全边界。
- [PKCE，RFC7636](https://www.rfc-editor.org/rfc/rfc7636.html)：authorization code 与 verifier 绑定。
- [Token Revocation，RFC7009](https://www.rfc-editor.org/rfc/rfc7009.html)：token 撤销及相关凭据的传播。
- [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html)：基于 OAuth 的身份认证输出。
- [UC-GW-001](../../gateway/use-cases/UC-GW-001-authenticate-and-forward.md)：OAUTH2 目前仅为预留策略。
- [Scope Catalog 契约](../../platform/contracts/auth-scope-catalog-v1.md)：目录含义与权威边界。
- [UC-APP-012](../../app-center/use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md)：现有测试启动描述的边界。
