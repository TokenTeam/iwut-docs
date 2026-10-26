# 124项门禁后的完成性核对

状态：ACCEPTED / AUDITED（2026-10-27，按持续目标自行核对，不改变UC完成标准）。Console `8ea144e`、文档 `5e2a5be` 为本次核对起点；124项真实通过仍固定在产品/runtime/runner/spec `ae46e5c`。本页只记录发现与下一动作，不把审计等同功能实现。

## 当前实际完成与有限缺口

| 条目 | 直接证据与判断 | 后续 |
| --- | --- | --- |
| 原有Console提交及legacy | legacy本地/远端仍为e68851e343bd0e077e5ccd0b680fe6813216ced0；源码/文档本地提交干净 | 保留不可变备份，不push |
| UC002–005只读产品与角色链 | 现有列表/详情/分页/错误恢复、正式管理权转让、SUSPEND/RESTORE、账号状态和WITHDRAWN链均有已记录真实证据；最后124项门禁通过 | 不重新登记为全部缺失，不自动扩成全部状态×页面 |
| Developer拒绝后的键盘焦点 | 审计起点PrivateReadBoundary卸载原子树后没有聚焦。随后有限修复已由组件与正式转让代表链完成 | [焦点修复包](2026-10-27-private-denial-focus.md)已VERIFIED：3专项/126全量，不外推全部页面 |
| UC001文档CSP | 审计起点缺文档policy；随后加入真实构建hash/SRI/meta和静态Edge防嵌入头，双surface实际强制拒绝及正常认证/私有链通过。不是对生产EO配置的验证 | [Strict CSP包](2026-10-27-strict-static-csp.md)已VERIFIED：3专项/126全量，首轮错误负例和Docker拉取EOF保留 |
| UC001协议/损坏记录 | 当前protocol比较代码已有上下文与到期护栏，但protocol.test的5项不足以逐项证明验收3点名的跨purpose/application/operation/locator、等于到期、双重哈希等。store.assertRecord只看长度/04和私钥type/extractable，keys.signPayload未核对namedCurve；不能以真实成功登录证明损坏输入在协议签名前失败 | 下一有限包须先直接复现，再加固现有适配器并验证公开向量；不能重新定义平台协议、导出/修复私钥或把全部缺证认定为产品漏洞 |
| UC001公开向量CI | 向量已在pnpm test；当前仓库没有workflow/CNB配置，124轮是本地证据，尚无可核实的CI run交付 | 另补可复现CI定义/证据；不由“没找到文件”断言外配CI不存在，不未经授权push或触发远端作业 |
| UC006/007审核 | 精确能力、正式决定定义、批准/拒绝/System拒绝、并发/未知/权限/关系/Session变化、App→Auth断链、Scope正式变化均有实际证据。UC007验收4已按单工作位正式分层，既有真实错误pointer409/顺序替换及组件清确认分别存在 | 不重列决定surface/指针来源/不可达平行PENDING为缺口；正式政策变化仍见下项 |

## 不可由本包越过的外部和架构边界

App工作区干净、本地HEAD及实际远端master同为 `4f62badc199139c73fad920f40cbcf56e9b391aa`；官方API远端master与Console pin同为 `6fea3db899d3d096d4d3dfc59b2c85432a4b9eb6`。当前App只有serve/migrate；migration ledger只有ID/appliedAt，策略apply后另写ledger；未有政策原子回执、未知结果恢复或policy-status。Profile定义投影与唯一ACTIVE验证也仍按App权威记录为PARTIAL，现有0033只是已应用v3基线，不是下一份获批政策。这与[UC005正式发布要求](../../app-center/use-cases/UC-APP-005-decide-application-version-review.md#策略正式发布与运维读回)、[ADR004](../../app-center/adr/ADR-004-mongodb-transactions-and-schema-management.md)及[App实现索引](../../app-center/implements/README.md)相符。不编译/修改App、不改库造政策、不虚构v4、不向其它聊天发需求；待对应所有者交付后再接真实变化链。

Cookie33+保持[已接受传输边界结论](2026-10-23-cookie-recovery-transport-boundary-analysis.md)。普通网页冷启动可能在第一HTTP parser之前无法取得恢复代码；仅应用层cleanup、扩大有限阈值、Service Worker已安装前提或Cookie-free API改造本身，均不足以证明原origin必达、遗留HttpOnly精确清理和无限迟到响应的身份不变式。受管浏览器guardian或新的入口/PoP协议会新增客户端/部署/跨系统信任边界，不是当前公网React小修；本轮不接受或安装扩展、不买迁域、不变更Gateway契约。该研究没有提供可上线实现，不能宣布不可能或已修复。

本次只推进已有UC内确定的可访问性与CSP缺口；协议/CI作为有限明确后续，不以外部问题掩盖本地可做工作，也不借审计增加未接受业务UI。密码入口、退出/设备治理、Developer写UI及Tester本人入口仍非范围。完整UC/goal不标完成；本页不是新的永久待办生成器。

## 本地凭据缺口的有限直接复现

在CSP/焦点源码冻结29aa09b的真实全量期间，仅对当前browser-auth源码做内存TypeScript转译/导入，使用临时Node Web Crypto P-256 non-extractable私钥与合成无身份store，未写文件、未变更冻结、未调用Auth/网络或记录任何密钥/签名字节。构造65字节04前缀、坐标全零公钥及32字节零fingerprint的损坏记录：当前fingerprintPublicKey接受该输入；p1363ToStrictDer接受全零r/s；StoredDeviceCredentialAccess.getPublicMaterial及sign均成功。命令exit0，仅输出四个布尔观察值，说明此项不只是“未找到测试”。这不是远端利用证明，也不改变已验证正常链；下一包须依平台公开协议确认精确拒绝边界、先回归复现再修复，不导出/猜测/修复私钥或以修改Auth协议代替客户端要求。
