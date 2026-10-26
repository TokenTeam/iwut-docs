# UC001浏览器凭据与签名边界加固

状态：ACCEPTED / VERIFIED（2026-10-27，仅所列有限凭据/协议与联合验收，完整UC/goal不关闭）。起点Console fe6666a，原126项真实门禁冻结29aa09b。

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

已实现keys/内部native-key验证、store快照/曲线/fingerprint/配对probe、DER标量范围及protocol精确上下文。keys首轮6 RED/1 GREEN后7/7；store首批62 RED/3 GREEN，修复后加5项异步快照共70/70；协议新增14项中6 RED（含device/email BOM及同畸形expectation）后19/19，原有有效比较与其它命名负例保持通过。另8项ProtoJSON Base64别名测试验证现有拒绝，不冒称新增缺陷。

全仓初次普通检查在account-owner的5项旧合成用例失败，独立withdrawal-owner另有4项失败：它们把App UUIDv7生成器用于Auth DEVICE credentialId/operationId。按平台契约仅修7个合成fixture的这两种ID为v4；App目标v7、opaque authId、原断言及次数不变，不放宽产品校验，也不改变application-close-reauth独立协议。account46/withdrawal49及其它5文件70项定向复验通过；首轮失败保留，不把测试资料错误当后端故障。

双origin原生IDB spec已接线：独立临时DB的真实non-extractable CryptoKey克隆/禁止导出、健康无credentialId的material/sign/verify；4种raw注入的合成坏记录，经生产material/list/sign/put拒绝且记录保留。只返回13个固定bool，临时DB精确删除；默认DB不改、零Auth mutation/App/外域请求。它是适配器验收，不冒充UI或真实注册链。预期专项为2 native＋原console2共4项，默认无参数128项（原126保留），实际结果仍待冻结后记录。

统一普通检查实际通过：1056 Vitest（browser-auth 183，原84保留）＋359 Node；strict含构建helper及真实/privacy spec、官方远程固定API6fea生成检查、published Gateway/Traefik Edge接线、docs72 brief/367行8退休编号及diff检查均通过。尚无本冻结真实浏览器结果；开始先本地提交冻结，再重新pull镜像验证，不能以普通测试代替真实门禁。

## published latest 专项

产品/runtime/runner/spec冻结 `ec343754256f41b7df9b4c2f7b3a3dc771658cb6`。专项 `iwut-console-real-434706` 实际 **4/4通过，1.4分钟浏览器阶段，exit0，无skip/retry**：`pnpm test:real tests/real/credential-validation.real.spec.ts tests/real/console.real.spec.ts`。两origin原正常邮件/设备登录、独立Cookie与管理读取保留；两native项的13个固定bool均true，默认DB仍为空、Session仍SIGNED_OUT、零Auth mutation/App/外域请求，CSP保持、五个临时DB各自精确清理。坏记录material/list/sign/put均拒绝且保留，健康IDB结构化克隆/不可导出与签名验证实际通过。

准备期间真实Auth密码限流按Retry-After等待，仅重试同一完成正文，不改额度/时钟；它不是跳过或浏览器retry。五镜像重新pull后轮内固定：Auth `sha256:518b0917ec8302f9f6cb28bd2e12aa59033cfe6db45c82a81a0afcb1bac5aa16`；App `sha256:68ee32b1e92145734bfa7fe61d003ee7e2ed2bb8b20fd944f861704a8f48ad01`；Gateway `sha256:444c75a71fc74fb14840718b259aeec14fbe2bbcda0a9832340c70b64ed099b0`；Mongo8.2.12 `sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3`；Traefik `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0`。专项容器（含停止项）/network已核验为空，代码冻结仍干净；不编译后端、不push。

## 同冻结默认完整门禁

`iwut-console-real-441036` 使用同冻结ec34375、默认无参数 `pnpm test:real`，实际 **128/128通过，23.9分钟浏览器阶段，exit0，无skip/retry**。原126完整保留，新native两项再次通过；正常邮件/设备、原EMAIL响应丢失后的fingerprint设备恢复、两origin 32次签发/明确重建、Session/权限/管理权/审核、正式Scope变化、WITHDRAWN和账号禁用恢复等原链全部通过。不把新的合成坏记录探针当真实注册或UI证明，也不扩成全浏览器/全heap保证。

本轮五镜像均重新pull latest后固定ID，与上列专项完全相同；准备同样尊重真实Auth密码限流/邮件冷却，未改变时钟或额度。完整轮次容器（含停止项）/network及Edge烟测残留均为空；测试期间Console HEAD与工作区保持ec34375/干净，legacy本地和实际远端均仍 `e68851e343bd0e077e5ccd0b680fe6813216ced0`。未编译/修改后端、不向外部聊天发需求、不push。

本包只关闭已列本地损坏凭据和命名协议护栏；[公开向量CI定义](2026-10-27-protocol-vector-ci.md)及真实远端run另列，不以128绿代替CI。App正式政策发布、Cookie33+新信任/部署边界和完整UC/goal仍开放，不自动扩业务UI或生成无穷矩阵。
