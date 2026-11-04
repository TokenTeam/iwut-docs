# 提交绑定审核策略：Console 接入

状态：`IMPLEMENTED / LOCAL_CHECKED / REAL_PENDING`；2026-11-04。Console 本地提交 `bd43c3acb22bfc56eca5a86174d1c3a643b45066`，提交前后文件内容核对一致。依据用户接受的[App 简化设计](../../app-center/implements/2026-11-03-submission-bound-review-policy-proposal.md)，同步 Console UC006/007；不增加新 UC。App/API 后端证据见[App 实施记录](../../app-center/implements/2026-11-04-submission-bound-review-policy-implementation.md)。

## 行为与实现

Version 和 Profile 审核详情统一读取提交时绑定的 `reviewPolicy`，决定使用该绑定版本；政策退休不使旧提交失效。前端从完整定义展示标题、正文及逐项确认，去掉 Version v3 白名单与 Profile v1 内置文案；完整合法的新版本无需更新前端政策表。终态显示原绑定定义，历史决定版本与详情绑定不一致时作为非法响应处理。

确认集合仍绑定原 Review、完整定义与决定前置事实。同一绑定及前置事实刷新后保留已勾选项和提交确认；权限、Scope、公开指针、一次性决定、结果未知重读及 Session 隔离保护继续保留。不增加存量补审、期限、自动重提或自动重放。

共享 API 固定 `2dc002ed787eddb365ea238d740c8a086c2832e2`，官方 Proto 重新生成；严格拒绝 `currentPolicy` 旧形状、缺定义、顺序/集合不一致、空白/控制字符/非法 Unicode 和终态政策不一致。错误枚举同步为两类 `POLICY_MISMATCH`，沿用既有错误恢复，不将合法退休解释为冲突。

所有五份隔离读模型夹具补齐必需的 `policyBinding.version`，Version 初始模型统一完整 v3 四项；真实浏览器 spec/Reviewer 辅助代码消费新字段及 Profile 服务端定义。这只是测试准备适配，不修改或迁移现有用户数据库，也不是正式提交/政策发布的实链证据。

## 本地验证

- 客户端完整包测试 **540/540**、Admin 完整包测试 **241/241**，同一命令 exit0。包含未知版本完整定义、Profile 自定义检查、相同绑定刷新保留确认、缺/损定义与终态版本不符；既有权限/指针/未知/Session 恢复回归保持。
- 七份相关 Node 夹具文件 **105/105**、无 skip/cancel、exit0；属于合成准备测试，不代替 Mongo/schema 或真实链。
- 完整 workspace `typecheck` 含 real/privacy TS、完整 workspace `build` 均单独实际 exit0；构建仍有既有 chunk 大小提示。
- 重新生成漂移检查与仓库独立性检查 exit0。新 API 远程 fetch 返回 not our ref，因此本地生成及漂移检查仅在该命令进程中将官方 Git URL 显式映射到已提交同 revision 的 API checkout。没有持久化 Git 配置、复制手写类型或把本地源码路径写入仓库；默认远程生成仍待 API 推送后验证。
- 旧中断前的两组测试会话终态未能回收，不记为成功；上述结果来自恢复后重新执行并保留单独退出码的有日志命令。

本批未重跑全 workspace 单测或真实139项，不把旧完整绿色结果沿用为新契约已验证。没有编译相邻后端、push 或部署。

## 部署及联合验收待办

1. 共享 API `2dc002e` 推送，使默认官方远程生成可取得固定 revision。
2. App `a95bd13` 产出并发布最新镜像。当前未上线设计不兼容旧实验数据；本批只准备新隔离夹具，没有重建用户数据库。
3. Gateway 沿用既有路由及权限，核对新 descriptor、Profile 定义和 reason 透传。只读检查本地 Gateway 仍为 `9d6a27f`、API pin 仍为 `6fea3db`；HTTP 经 Traefik 转发，不能仅凭旧 pin 断定必然阻断 JSON 新字段，需要以新 App 实链核验。三协议契约同步仍由 Gateway 所有者承接，本批未修改其代码或委托其他聊天。
4. 输入准备后运行两类审核、原提交/拒绝重提/发布闭环与相关私有隔离集中实链。真实 A→B 发布仍需获批正式政策及目标环境；后端隔离测试政策和前端刷新保持回归不冒充正式联合发布。

不以构建成功、单测或 App 自身 24 项通过宣称新前后端链已完成。任意超量 Cookie 恢复及非平台运维精确权限发现继续按原独立边界记录，非本工作包新增范围。
