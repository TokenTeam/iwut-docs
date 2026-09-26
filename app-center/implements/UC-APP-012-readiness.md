# UC-APP-012 开工检查

检查日期：2026-09-26。本文是实现准备记录，业务语义以 UC/BR 为准。

## 结论

前置实现已具备，无需等待其他 UC 或外部服务。App Center 服务工作树当前为 app-center/v1，已包含 UC011 和统一 API Go package 路径变更；不得使用旧 master 实现或旧 API import 路径。

## 依赖核对

| 依赖 | 证据与结果 |
| --- | --- |
| Application / Version / Review | 已有持久化文档、APPROVED decision 和不可变审核 snapshot；UC007 已验证 sourceVersionRevision+2 及内容一致性。 |
| test Publication | UC007 已交付 exact (applicationId,rpcApiMajor) 指针和对应 revision History；History 含 approvedReviewId，可取得发布时的批准事实。 |
| Tester 授权 | UC009/010 已交付 ACTIVE/REMOVED episode 和索引；UC011 撤销链接不删除已有 Membership。 |
| 可信用户身份 | 普通用户 JWS 校验与 authId 投影已交付，不要求 Developer/admin 身份。 |
| 事务及接入 | MongoDB 副本集、只读 snapshot 事务、Proto HTTP/gRPC 与 Wire 工具均可复用。 |
| 外部交付 | Auth 权威目录、前端宿主、Gateway、consent/token 不属于当前查询前置依赖；禁止把这些调用加入查询路径。 |

## 选定的实现方式

- Catalog & Resolution 使用 internal/catalog/domain、usecase、port，遵守 ADR003。
- 只读事务中先确认 ACTIVE Tester，再加载 exact-major Publication、匹配 revision 的 History 和批准 Review/Version；不写任何栅栏或业务记录。
- capabilities 按既有名称格式校验，并按 UC012 去重/排序；不增加未定义的数量策略。
- 内部不一致按原 UC012 返回503并告警；能力不足422且返回稳定排序的 missingCapabilities；private, no-store。
- 真 MongoDB 验证移除/解析、发布替换/解析两种可见性顺序；监控证明查询无业务写入、外部网络请求和其他 major/槽位回退。
- 未发现需要新增产品决策的阻塞；正式客户端如何采集宿主能力属于独立入口接入工作。
