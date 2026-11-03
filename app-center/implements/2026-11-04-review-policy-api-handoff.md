# 提交绑定审核政策：共享 API 实施交接

状态：`ACCEPTED`（App 业务设计）；2026-11-04。用户已接受 UC004/005/015/016/030/031 并要求开始更新。此文只交接 API 所有者的确定改动，不授权 App 任务修改非 App 的 Proto、Gateway、Console 或 Auth 代码。

## 共享 API 改动

输入基线为 API `6fea3db`。用户随后明确授权本轮直接修改 App 相关 Proto 和生成物，已本地提交为 `2dc002e`；App 消费该固定版本，不 push。非 App Proto、Gateway、Console 和 Auth 源码未修改。

- `app_center/v1/application_review_query/application_review_query.proto`：`ApplicationVersionReviewDetail` 字段4直接由 `current_policy` 改为 `review_policy`，仍用 ReviewPolicyContext（version=1、required_check_ids=2、required_check_definitions=3）。不保留旧字段、双输出、弃用过渡或只读兼容分支。
- `app_center/v1/application_profile_review_query/application_profile_review_query.proto`：`ApplicationProfileReviewDetail` 字段4直接改为 `review_policy`；`ProfileReviewPolicyContext` 增加 `required_check_definitions = 3`，每项使用本 package 的 message（id=1、title=2、description=3）。`current_published_profile = 7` 及其 oneof 不变。
- 决定错误：Version 的 APPLICATION_REVIEW_POLICY_CHANGED 改为 APPLICATION_REVIEW_POLICY_MISMATCH；Profile 的 PROFILE_REVIEW_POLICY_UNAVAILABLE 改为 PROFILE_REVIEW_POLICY_MISMATCH。HTTP409/gRPC ABORTED 表示请求版本与目标 attempt 绑定不符，不能用来报告定义损坏或存储故障。枚举前缀沿现有 ERROR_REASON 命名，未上线不提供旧枚举别名。
- 提交/决定命令和路由不变。policyBinding.version 只在 App 内部持久化，不加开发者提交响应字段，不扩大管理员查询披露。

定义均为完整纯文本，ID/顺序与 requiredCheckIds 对应；title 1–80、description 1–2000 Unicode scalar values、无首尾空白和控制字符。来源为被该 Review 绑定的不可变政策，不必仍 ACTIVE。

## 交付证据与消费者

API 所有者提交 Proto 与全部相应生成物，执行已有生成/漂移检查，回报 commit 和检查结果。App 消费该固定版本后更新 transport、HTTP/gRPC 回归；Console/BFF 按新形状重新生成并严格解码，Gateway 核对 descriptor 和错误透传，无新增路由/权限。客户端不接受 currentPolicy 或缺定义的旧响应。

App 自身可先完成 Domain、提交栅栏、Mongo 绑定、决定及内部查询模型；共享 API 交付前不能把整体六个 UC 标为 COMPLETE，也不能声称新接口已可用。没有启动旧数据兼容或真实数据库重建。

API 验证：`make proto-check` 通过，四个变更相关生成包 `go test` 通过。App transport 已接入新字段与 Profile 完整定义，双协议及最终 backend 门禁进度见[实施记录](2026-11-04-submission-bound-review-policy-implementation.md)。
