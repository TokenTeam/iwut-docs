# UC001浏览器凭据与签名边界加固

状态：ACCEPTED / IN_PROGRESS（2026-10-27，持续目标授权下自行接受；未宣称验收完成）。起点Console fe6666a，原126项真实门禁冻结29aa09b。

## 范围与权威

本包实现[UC001 BR-CSE-002/003及验收2/3](../use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-002)已经要求的损坏记录失败关闭与签名前核对。字节、曲线、整数及期限规则只引用[设备协议](../../platform/contracts/auth-device-session-v1.md)和[邮箱登录协议](../../platform/contracts/auth-email-login-v1.md)，不改变后端协议，不重写历史REGISTER向量为现行登录能力。

起点的[直接复现](2026-10-27-completion-audit.md#本地凭据缺口的有限直接复现)表明非法曲线点、零DER整数和损坏记录确实被接受；已有上下文比较仍有效，不把缺少命名测试一概称作实现漏洞。

## 接受的实现决定

- 通过原生Web Crypto导入完整P-256公钥验证曲线点；对记录重新计算fingerprint。签名私钥须为真实non-extractable ECDSA/P-256 CryptoKey，且仅具sign用途。localId为本机不透明选择器，不新增UUID限制；返回记录必须匹配所请求localId。可选credentialId遵守平台规范，缺失仍保留fingerprint登录。
- 不可导出私钥无法直接读出其公钥，故在适配器内部用域分离、32字节随机数的一次性本地消息做sign/verify配对检查。它不是LOGIN payload、不是Auth proof，不持久化、不外传、不进入日志/错误/React或Query状态；失败时不得签署LOGIN payload。对实际协议payload仍恰好执行一次SHA-256/ECDSA。此检查不证明防XSS，也不增加可信客户端能力。
- 捕获记录及字节副本后再await；读材料、列摘要、签名与持久化均校验，不用先前缓存的通过结果替代当前记录验证。不导出、修复、删除或自动换钥匙，不做schema迁移。签名输入也在await前捕获副本，避免调用者修改。
- P1363转DER先检查两个标量的合法范围；保留合法high-S/low-S。公开向量及有限命名的跨上下文、Frame/UTF8、等到期和单次哈希测试纳入普通pnpm test，不增加任意组合矩阵。

## 有限验收与证据层级

1. 钥匙/存储回归先RED复现，再GREEN：非法点、fingerprint损坏、错误曲线/用途/导出性/伪CryptoKey、未知版本/缺私钥/错localId、合法公钥但不配对、异步字节变动；合法缺credentialId、正常签名和IDB克隆仍可用。错误为稳定无敏感内容，损坏记录保留。
2. 按权威公开向量精确验证payload/fingerprint/DER与命名的签名前拒绝；实际Web Crypto证明签名验证原payload通过、验证SHA256(payload)失败，合法high-S/low-S及标量边界不靠随机样本推断。
3. 两个真实origin各一项native Chromium/IndexedDB适配器负例，使用独立合成测试记录，不冒充真实账号/业务链，不增加邮件/Session/App写或修改生产记录；原126项published-latest默认全量保留并重跑，正常EMAIL/DEVICE链验证兼容。新测试必须遵守既有隐私harness，不记录私钥或签名字节。
4. strict、普通测试、官方API生成检查、Edge与docs检查通过后冻结本地提交；真实专项与默认全量按同冻结记录。每轮重拉published latest，不编译后端；清理精确测试资源，legacy本地/远端不变，不push。

本包不把本地测试叫作CI run；可复现CI定义/实际远端证据仍单列后续，未经授权不push/触发远端。App正式政策发布和Cookie33+新信任边界仍独立开放，完整UC/goal不随本包标完成。

## 实际结果

尚未实施或验收；本节后续追加真实结果，不提前登记通过数。
