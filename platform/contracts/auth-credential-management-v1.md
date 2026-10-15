# 设备凭据管理协议 v1

状态：`ACCEPTED / IMPLEMENTED`（Auth/API 后端；Gateway/客户端独立交付）

## 范围与来源

用户于 2026-10-13 授权继续完成 UC032。唯一业务规则见 [UC032](../../auth-center/use-cases/UC-AUTH-032-manage-own-device-credentials.md)；不可逆目标状态见 UC009，密码/下界见 UC033。扫码、WebAuthn、批量移除均不在范围。此契约不复述名称/分页等规则，不修改原 LOGIN、注销或 app.close 字节。

## 消息与载体

package `auth_center.v1.credential_management`，service `CredentialManagementService`；四个精确 full method 的末段分别为 ListOwnCredentials、SetOwnCredentialLabel、BeginOtherCredentialRevocation、CompleteOtherCredentialRevocation，均 DIRECT，由 Auth 取唯一 x-iwut-session，不接受任何 Authorization/Cookie/身份 JWS、query 或正文凭据替代。

Proto 字段号固定：List 请求 optional uint32 page_size=1、string cursor=2；Set 请求 string credential_id=1、optional string label=2、optional int64 expected_label_revision=3（0 合法，presence 必需）；Begin 请求 string request_id=1、string target_credential_id=2；Complete 请求 string operation_id=1、bytes signature_der=2、string current_password=3（非空必需）。响应按 UC032 字段顺序从 1 连续分配，时间为 google.protobuf.Timestamp；列表页 credentials 使用 repeated，空列表仍输出 []。Complete 沿用 authentication.CredentialRevoked 空结果。

JSON 固定 lowerCamel、int64 十进制 string，bytes 标准 ProtoJSON；可选 List 参数允许省略，Set/Begin/Complete 全字段必须存在。严格拒绝 duplicate/unknown/null/非法 UTF-8，16 KiB/no-store。HTTP 413 与 native RESOURCE_EXHAUSTED 为正文大小边界；密码仅 TLS 请求秘密，不入 Frame、日志、审计或 URL。缺密码不降级。

## 设备签名字节

固定十字段 Frame（LP/U32BE/UTF8/U64BE 引用 auth-device-session-v1）：

```text
Frame(UTF8("iwut-credential-revocation-proof-v1"),
 UTF8("REVOKE_OTHER_CREDENTIAL"), UTF8(serviceId), UTF8("iwut-client"),
 UTF8(operationId), UTF8(sessionId), UTF8(callerCredentialId),
 UTF8(targetCredentialId), challenge32, U64BE(expiresAtUnixMs))
```

所有 ID 使用规范 UUIDv4 文本，不使用 UUIDBytes；serviceId 为客户端预配部署值。固定 challenge32、5 分钟期限、最多 1024 字节；严格 P-256/SHA-256/DER，high-S/low-S 均合法。客户端重建逐字匹配并核对当前账号与选中目标，不盲签。

## 最终复核与部署

Begin 捕获 passwordRevision/accountRevision、原 Session、调用/目标凭据与公钥。Complete 先证明该登记钥再在共享有界设施验当前密码；Argon 不在事务重试中执行，最终 Auth 事务重新检查全部版本、下界、期限与固定签名。错误密码/签名共五次，只有正确 owner/Session 才可消耗；已完成操作在 24 小时内的当前双证明只恢复空结果，不制造新授权。

新入口默认关闭，启用要求现有密码 runtime；列表/改名不 touch LRU。操作与必要审计/目标变更共用 Auth fence；独立 target Tx 原语不可成为另一条公开入口。操作加入既有有界存储；1 秒批次最多删除 64 条 retainUntil 到点记录，TTL 只是辅助手段；注销清理/审计保留按 UC025。

## 公开向量

向量文件 `test-vectors/auth-credential-management-v1.json`，独立 Python 生成/校验脚本 `tools/auth_credential_protocol_vectors.py`，Go 验同一 Frame/DER/跨用途负向量。固定私钥/挑战仅 PUBLIC TEST DATA，不作为运行默认。向量交付与运行验证见 UC032 readiness；Gateway/客户端/生产启用独立验收。
