# UC-APP-022 开工检查

日期：2026-10-04

状态：`READY`

## 结论

UC-APP-022 没有未满足的运行时依赖，可以独立实现。Filter 管理只依赖已交付的 Application、当前管理员关系、Application 写栅栏、可信 Developer 身份、MongoDB 事务和双协议基础设施；不依赖 Publication、Catalog、Auth Profile 服务或客户端求值器已经完成。

## 已确认决定

- Filter 是 Application 级独立能力，同一当前 Revision 作用于公开 Grey/Stable 候选；Test 不执行。
- 不需要审核。每次真实 Set/Clear 创建不可变 Revision 并立即发布。
- 不存在聚合等价于 revision 0 的 ALLOW_ALL；Clear 发布显式 ALLOW_ALL Revision，保留历史。
- 规则采用 `profile-filter-v1` 类型化有界树；字段 key/标量与 Auth ProfileFieldDefinition 同构，但 App Center 不在线查询 Auth。
- App Center 不接收用户资料、不执行规则；客户端本地确定性求值。Filter 不是安全边界。
- 使用独立 OCC，不修改 Publication revision；真实提交复用 Application 写栅栏处理管理员转让竞争。

## 依赖核对

| 依赖 | 结论 |
| --- | --- |
| Application 与管理员关系 | UC001 已交付，Application repository 已支持事务写栅栏。 |
| 可信 Developer 身份 | 既有 HTTP/gRPC middleware 与 developerStatus 规则可复用。 |
| ID 与 Clock | 既有 UUIDv7/Clock ports 可注入并做 deterministic tests。 |
| MongoDB | 显式 migration、严格 validator、事务重试与 integration harness 已具备。 |
| API/Wire | 独立 Proto package、HTTP/gRPC transport、Wire 和 E2E 模式已具备。 |
| Auth 字段目录 | 非运行时依赖；只复用稳定 key 语法和值类型，未知字段按客户端缺失语义处理。 |
| Catalog/客户端 | 后续消费者；不阻塞 Filter 管理纵切片。 |

## 实现与验收边界

- API 子模块先提交 Proto 与生成物，服务随后更新 gitlink。
- 服务新增 `internal/filter/{domain,usecase,port}`、Mongo repository/migration、transport 与 composition wiring。
- Domain 覆盖全部规则结构、类型、深度/节点数、日期、等价/no-op；repository 覆盖 immutable Revision、OCC、写栅栏和损坏数据。
- 真实 MongoDB 覆盖首次 Set、更新、Clear、no-op、并发 Set/Clear、管理员转让竞争与回滚。
- HTTP/gRPC E2E 覆盖 Get 合成默认值、Set、Clear 和错误映射。
- 最终验收使用 `make check-full`；本工作包没有 Auth 运行时/共享 Auth provider 变化，不要求 `check-auth-app`。

## 非目标

统一启动解析、Catalog、前端求值器/UI、生产用户字段清单、test clear、Application disable/suspension、历史列表和回滚均不进入本工作包。
