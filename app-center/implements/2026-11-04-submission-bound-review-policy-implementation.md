# 提交绑定审核政策：实施与验收

状态：`COMPLETE`（App/API 后端；跨端消费与正式新政策发布联合验收待准备）；2026-11-04。设计已由用户接受，文档接受提交 `5dc6351`。本记录描述 UC004/005/015/016/030/031 的新增后端实现，不替代原基线证据。

## 实现范围

- Version 与 Profile 在成功提交的同一 Mongo 事务中选择唯一 ACTIVE 完整政策、完成真实 coordinationRevision 条件写，并持久化必需的 policyBinding.version。与发布发生写冲突时重试整个事务；新提交不能带旧快照跨过已经提交的退休。
- 决定及 Reviewer 详情按 attempt 绑定读取完整不可变定义，允许 RETIRED；决定不写政策栅栏。请求版本不匹配为 PolicyMismatch；绑定、引用或定义损坏为 INTERNAL。既有状态冲突、权限、利益冲突、Scope/URL/OAuth/资格门禁及 Profile 公开指针 CAS 保留。
- 初始模型只创建完整 Version v3、Profile v1。所有 Review 必须有绑定，终态 decision 政策版本必须等于绑定。无旧记录回填、ID-only 分支、sidecar 或新旧客户端兼容。
- 专用部署 migration 的内部发布原语同事务完成退休、插入新政策及最小 ledger 成功标识。历史同 ID 重读核对原清单、定义与当前 ACTIVE，不重新激活；不同清单拒绝。没有新增线上策略 CRUD、通用 CLI 或生产 B/C 政策。
- API `2dc002e`：两类详情字段4直接改为 reviewPolicy，Profile 增加完整检查定义，错误枚举直接改名。生成输入及输出一并提交，漂移检查和相关生成包编译通过。未修改 Auth、Gateway、Console 源码。

## 分层验证

App 本地提交 `a95bd13`，API 本地提交 `2dc002e`；以下专项补充最终完整门禁，均不冒充已部署联合链证据。

- `go test ./...` 通过（无 URI 时 Mongo 测试跳过）。包括退休绑定仍执行实时 Scope/URL/OAuth 失败及资格自动拒绝、定义损坏 INTERNAL 与既有状态冲突分类。
- Version A→B 专项通过：A 退休后批准/拒绝、新提交及拒绝后重提绑定 B、历史保留、提交/发布两种胜序、ledger 重读和回滚。日志 `.artifacts/version-binding-release-target.log`。
- Profile 串行专项通过：同类 A→B 矩阵、现有提交/决定/公开指针回归、两类提交的缺政策/缺定义/计数溢出无部分写入、Profile unknown commit 原事务恢复。Mongo 包 `230.156s`；日志 `.artifacts/profile-binding-release-target.log`。
- 补充异常数据、竞争发布、两类 unknown commit、HTTP/gRPC 与初始化专项全部通过：Mongo `128.788s`，真实 E2E `20.493s`；日志 `.artifacts/review-binding-final-target.log`。最终完整门禁仍待通过。

以上切换使用明确命名的隔离测试政策，只是组件/事务层证据。真实联合发布必须另有获批的真实新政策和环境发布授权，目前未准备，不能以测试政策冒充已上线。

## 消费者交接

Gateway 沿用既有路由/权限，更新 API descriptor 并核对新 reason 透传。Console/BFF 重新生成并严格解码 reviewPolicy，展示两类完整定义；A 下提交、B 后仍按 A 决定，不因人工政策发布清确认或强制重提。Scope、权限、指针冲突及未知决定结果恢复继续按既有契约。

本轮未通知其他聊天、未 push、未部署、未访问或重建用户数据库。隔离测试 Mongo 按新模型创建；故障注入只在测试容器开启 enableTestCommands。

## 首轮完整门禁与夹具修复

冻结 App 工作树、API `2dc002e`、docs `5edb551` 的首轮 `check-full` 前23项通过，第24项失败，`changed_sources=[]`。报告 `.artifacts/verification/20261103T171934Z-nejgdixt/report.json`；真实 HTTP/gRPC E2E 通过，Mongo 包未通过，不能记为 backend 完成。

158 条 Mongo 失败均来自两个共用批准夹具仍只确认 `content-reviewed`。最终事务现在会核对绑定政策的完整检查集合；已将发布/运行消费链及版本管理链的两处夹具改为 v3 四项正式检查，未放宽校验，未修改 Auth 或业务规则。

修复后串行运行版本管理、发布 migration、UC038 Tester 投影及 UC036 清空 Test 消费链的真实 Mongo race 专项，全部通过（Mongo `26.536s`），日志 `.artifacts/review-binding-consumer-fixture-target.log`。随后重新冻结输入执行完整门禁，结论见后续最终记录。

## 最终完整门禁

`make check-full` / backend **24/24 PASS**，`changed_sources=[]`。报告：`.artifacts/verification/20261103T175414Z-39loaggx/report.json`；Go 1.25.5，固定 API `2dc002e`、权威文档 `46c8bb5`。最后一项耗时 1382.134s。验证在提交前工作树进行，服务起始指纹 `597b145edb5a48225bcc527fd2a845be5eca8e801c67ffb2c8a432ffc250d0b6`；本地提交仅改变 Git 记录，文件内容与验证时保持一致。

文档随后只更新实现状态与证据并重新生成 briefs、检查 freshness/registry；没有修改业务规则。未更改共享 Auth/身份契约，本轮未执行新的 check-auth-app，历史跨服务通过记录不替代本次 Gateway/Console 新契约消费验收。未发布镜像或部署。
