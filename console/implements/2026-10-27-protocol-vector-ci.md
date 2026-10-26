# 公开协议向量的可复现CI定义

状态：ACCEPTED / IN_PROGRESS（2026-10-27，持续目标授权下自行接受；仅隔离临时候选已实现，当前凭据包ec34375真实全量期间不修改Console冻结）。

## 依据与事实

[UC001完成标准](../use-cases/UC-CONSOLE-001-establish-console-session.md#完成标准)要求公开协议向量纳入CI。向量已在普通browser-auth Vitest中执行，不能把本机1056项通过等同远端CI。只读查询GitHub `TokenTeam/iwut-console` 的Actions API，workflows与runs当前total_count均为0；这不证明CNB或外置系统没有流水线。此工作只交付Console自有最小定义，不操作其它仓库或平台设置。

## 接受的有限实现

- 使用GitHub托管ubuntu-24.04 x64，当前Console仓库的pull_request及main push普通检查；contents只读，不用pull_request_target、write权限、自定义secrets、持久化git凭据或artifact上传。不新增定时任务、发布、推镜像或部署。
- 主要工具精确固定Node24.22.0、pnpm10.28.1、protoc3.21.12；frozen lockfile安装。只从官方API仓库取现有固定commit6fea，不checkout相邻后端或docs，不依赖本机绝对路径。系统Git/OpenSSL等由托管镜像提供，因此不是完整hermetic环境。
- 明确依次运行独立性、官方生成漂移、strict、普通测试（含公开向量）及build；任何失败停止，不continue-on-error或静默skip，不以新增专用轻量测试代替原pnpm test。最后检查受版本管理文件及非忽略新文件没有漂移，正常dist缓存仍按ignore处理。
- Action固定官方release实际commit：checkout v7.0.1 `3d3c42e5aac5ba805825da76410c181273ba90b1`；setup-node v7.1.0 `949feb2413d6458794dcd2491c4babbbce0c15c1`；pnpm/action-setup v6.1.0 `ea17c68df8912ef543352723c149a84f56e3d413`。均通过官方Git refs API核实，pnpm annotated tag已解引用，不把移动major别名当固定输入。官方配置见[checkout](https://github.com/actions/checkout)、[setup-node](https://github.com/actions/setup-node)、[pnpm action](https://github.com/pnpm/action-setup)。
- protoc使用[官方v21.12 Linux x64归档](https://github.com/protocolbuffers/protobuf/releases/download/v21.12/protoc-21.12-linux-x86_64.zip)，下载到独立mktemp目录、校验SHA256再解压和执行，不sudo、不改系统路径、不执行远端shell。观测SHA256为 `3a4c1e5f2516c639d3079b1586e703fc7bcfa2136d58bda24d1d54f949c315e8`；旧GitHub asset digest=null，此值是本轮官方源下载观测而非官方签名证明。工具目录通过GitHub PATH机制仅作用于当前job。

本包不同时引入未验证的托管Docker/Chromium完整作业；真实Session/Mongo/Edge/published-latest浏览器命令与本地证据继续完整保留，不将其从UC门禁移除，也不把普通CI叫作前后端完整联合验收。新增远端重型门禁须明确免sudo运行环境、浏览器依赖、日志隐私和资源生命周期；不用私有后端源码构建替代镜像。

## 验收与未获得的权限

先为安装/定义的固定输入、完整命令、只读权限、失败关闭及路径隔离建立有界回归，再本地执行真实固定归档安装及普通检查；记录实测工具版本和结果。不在当前ec34375真实轮次结束前改Console，也不改生产Web/BFF/协议。

YAML和本地测试只能证明定义已建立。当前未获本轮push/远端作业触发授权，故不push、不dispatch，不伪造CI run URL或绿色状态。文档将以IMPLEMENTED / REMOTE_UNVERIFIED记录交付，直到真实远端run可核实才关闭UC的CI证据要求；完整UC/goal及App政策、Cookie架构边界保持开放。

## 隔离候选的实际进展

ec34375完整真实轮次运行期间，候选只写独立mktemp目录，不修改Console源码、依赖或node_modules。安装器12项先因文件缺失RED，再12/12 GREEN；workflow的4项同样先因文件缺失RED，再解析/结构/精确Action及完整命令16项合计全绿，不把bootstrap RED当作产品漏洞。bash语法通过。真正从固定官方URL下载、校验归档、安装并执行实际得到 `libprotoc 3.21.12`，无-I编译timestamp descriptor也通过，确认完整include默认发现；该本地安装随后精确清理，不是远端runner证据。

候选定义验证使用显式固定开发依赖yaml2.9.1解析YAML（包括重复key拒绝），不写临时自制YAML解析器、不把它发进Web/BFF构建。待当前真实轮次结束后，再通过apply_patch集成候选、根普通test接线和锁文件，运行最终本地门禁并记录实际commit；此前不登记Console已交付CI配置。
