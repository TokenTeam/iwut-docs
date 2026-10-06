# ADR-PLAT-004：跨服务交付使用统一 API 集成基线

状态：`ACCEPTED`

日期：2026-10-06

## 背景

Auth Center、App Center 与 Gateway 都从独立 API 仓库固定生成代码和 Proto descriptor，但各服务可以在自己的工作分支上先行提交 API 变更。服务局部开发时允许这些指针暂时分叉；跨服务验收时，如果没有一个同时包含各方已接受契约的共同 API commit，就会出现以下问题：

- Gateway 只能装载一个 `api/` revision，无法同时消费互不包含的 Auth 与 App API tip；
- 单个服务的编译通过不能证明调用方、提供方和路由 descriptor 使用的是同一线格式；
- 实现记录只写服务 commit、未写共同 API 基线时，之后无法准确复现联合验收；
- 从某个服务工作树复制 Proto 或生成物可以暂时绕过冲突，却会产生第二份可执行契约权威。

业务语义仍由本仓库的 UC、BR、ADR 和共享契约拥有；独立 API 仓库只拥有可执行 Proto/API。本决定只约束跨服务变更如何汇合、固定和验收，不把 Proto 复制进设计仓库，也不替 API 仓库规定日常分支名称。

## 决定

### 统一集成基线

每个涉及两个或以上可部署服务的交付批次，必须在独立 API 仓库形成一个**统一 API 集成基线**：它是一个不可变 commit，并且是该批次全部已接受 API 变更 tip 的共同后代。相同字段、HTTP annotation、service/method 和生成选项只在这一个提交图中汇合。

局部实现期间可以继续固定各自的 API 分支 commit，但这类分叉只表示工作进行中，不能作为跨服务 `COMPLETE` 或发布候选的依据。进入联合验收前：

1. 先把本批次需要的 Auth、App 和共享 API 变更汇合成共同后代，解决 Proto package、字段编号、HTTP binding 和生成物冲突；
2. 参与联合验收的 Auth、App、Gateway 及其它消费者固定到同一个基线 commit；若之后任一方需要新的 API commit，必须形成新的共同基线并重跑受影响门禁；
3. 服务仓库只提交 submodule pointer 与从该 revision 生成/校验的代码，不复制另一分支的 Proto 文件或手工拼接 descriptor；
4. 实现状态记录同时写明统一 API commit、各服务 commit、Gateway commit和验收报告位置，不能只写“latest”或分支名。

API commit 必须已经存在于团队可获取的远端或同等持久存储，CI/部署不能依赖某个本地对象库里独有的 commit。设计正文不固定某个永久 SHA；每个工作包在实现记录中固定它实际验收的 SHA。

### 兼容与推进规则

同一 API major 内优先使用向后兼容的追加变更：已发布字段编号和语义不得复用，已发布 RPC/HTTP binding 不得静默改指向其它行为。需要破坏性变化时，通过新的 package/API major 和显式迁移窗口交付，不通过让不同服务长期固定互不兼容的分支来规避。

统一基线只说明可执行契约已汇合，不自动说明某条公网路由已经开放。Gateway 仍按自己的严格路由目录逐条启用接口；内部 provider RPC 仍按 service identity allowlist 与部署网络边界开放。业务能力是否 `ACCEPTED`、实现是否 `COMPLETE`、是否生产发布继续分别记录。

### 联合验收门禁

统一基线至少通过以下门禁后，才能用于跨服务完成记录：

- API 仓库自身的 Proto lint、breaking/生成一致性检查；
- 每个参与服务在同一 API revision 上的编译、单元测试和 transport/descriptor 检查；
- Gateway 路由目录对该 descriptor 的严格校验和生成物漂移检查；
- 涉及真实远程调用时，启动真实提供方与消费者完成协议级 E2E，不以两边各自的 fake 通过代替；
- 检查各仓库记录的 submodule pointer 与验收清单一致，任何未知、不可获取或不同的 revision 失败关闭。

## 不采用的方案

### 各服务永久固定自己的 API 分支

这能支持局部开发，却不能给同时消费 Auth 与 App 的 Gateway 提供单一 descriptor，也无法形成可复现的跨服务发布集合，因此只允许作为临时工作状态。

### 在 Gateway 或服务仓库复制缺失 Proto

复制会产生第二份可执行契约权威，并让生成包身份、HTTP annotation 与 breaking 检查漂移，因此禁止。

### 使用浮动分支、自动取最新提交

浮动引用不能复现验收，且可能在未审查时改变线格式。所有消费者继续固定不可变 commit。

### 要求所有服务在任何开发时刻都固定相同 API commit

这会不必要地串行化局部实现。允许工作分支暂时分叉；约束点是跨服务联合验收、完成声明和发布候选。

## 结果

优点：

- Gateway 可以从一个 API revision 同时验证 Auth、App 和资源服务路由；
- 联合验收得到可复现的服务/API commit 集合；
- Proto 冲突在 API 集成阶段显式解决，不由运行时版本偶然组合暴露；
- 保持设计权威与可执行契约权威的既有边界。

代价：

- 跨服务工作包多一个 API 汇合和全体 repin 步骤；
- 任一参与方在冻结后追加 API 变化，都需要推进基线并重跑受影响门禁；
- 并行工作必须明确区分“局部实现可用”和“统一集成可验收”。

## 实施记录

2026-10-07 首次应用本决定：API `9f914c5` 是 Gateway 原基线 `758c426`、Auth API `359c6bc` 与 App API `a1bf6dd` 的共同后代。Gateway `0009947`、Auth `50dbbe7`、App `0d06bbf` 均固定该 revision；App 随后的空 Catalog 修复为 `b93fb25`，未改变 API pointer。Gateway 与 Auth 的 `make check`、App 的 quick verification、API `proto-check` 及真实 Auth/App/Traefik 三协议 E2E 均通过。

这些提交当前只存在于本地工作树，尚未 push；因此可复现的本地集成已完成，但在 API `9f914c5` 与三个服务提交进入团队可获取的远端前，不得把该组合用作 CI 或发布候选。形成统一基线不等于开放 OAuth/OIDC 路由或执行生产部署。

## 关联文档

- [平台共享设计文档](../README.md)
- [ADR-GW-001：Gateway 运行时、路由目录与协议适配](../../gateway/adr/ADR-GW-001-runtime-routing-and-protocol-adapters.md)
- [Gateway 实现状态](../../gateway/implements/README.md)
