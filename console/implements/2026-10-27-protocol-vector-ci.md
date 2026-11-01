# 公开协议向量的可复现CI定义

状态：ACCEPTED / IMPLEMENTED / LOCAL_VERIFIED / REMOTE_WORKFLOW_VERIFIED（2026-11-01）。持续目标授权下自行接受；ec34375完整真实128项结束前只准备临时候选，结束后才集成Console。初次交付时无远端run；后续远端工作流证据见文末。

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

## 已集成定义，仍待本地统一终态

ec34375的默认128/128完成且资源清空后，才把候选通过apply_patch集成为Console `7b32305da131967dfad2e108f3e4b116a68925eb`。workflow、安装器和回归已入库；root test新增 `test:ci-policy` 为不可省略前置。根接线护栏先1 RED/4 GREEN，修复后安装/定义共17/17 GREEN。yaml2.9.1显式开发依赖及完整锁已更新；原包直接版本不变，仅新增yaml和相关可选peer绑定，未改Web/BFF/协议或real spec。

当前正在以集成后的实际安装器重新下载/校验protoc，并重演frozen install、独立性、官方生成、strict、原pnpm test、build和git无漂移检查。还会以与真实轮次相同的公开serviceId另构建两前端，比较先前保存的实际静态产物hash，不以“仅开发依赖”推断运行产物必然相同。本地统一结果尚未到达；不能把17项或候选安装当作完整门禁，更不是GitHub run。

只读GitHub元数据补充确认：Console是main默认分支的private仓库；固定输入API仓库为public/master，因此官方API生成无需新增跨私库token。没有读取或改写平台secret/权限，也未push/dispatch。

集成7b32305首轮本地重演明确exit1：真实固定protoc安装、frozen install、独立性、官方生成、strict、1056 Vitest＋376 Node均完成，但build的两个Vite命令命中旧app/node_modules/.bin/vite脚本，仍指向已移除的无yaml peer目录；根vite stub已指向新目录。故未到达无漂移/同配置产物比较，不登记整个本地门禁通过。先按当前pnpm10本机help提供的force reinstall＋frozen lockfile重新连接托管依赖，不改源代码/原断言或使用其它构建版本；该安装状态诊断不当作GitHub实际失败，也不提前认定干净安装必然成功。

## 最终本地门禁与边界

force＋frozen安装实际exit0（2分23秒，锁不变；非当前平台optional包的低速/ECONNRESET由包管理器有界重试，未改registry/版本/校验），但没有清理两个孤立app级vite stub。确认它们引用旧peer目录、当前app不声明该直接工具且根声明的vite为同版本8.3.3后，仅把这两个生成文件移入本轮临时备份，不改任何源文件。随后按根已声明CLI构建成功；最终重演仍保留workflow的普通frozen install，不把force或手工清理塞进CI，也不新增依赖自动修复逻辑。

Console产品/CI源码冻结仍为 `7b32305da131967dfad2e108f3e4b116a68925eb`（产品/runtime/real spec仍ec34375）。使用集成安装器实际下载并校验的protoc3.21.12，确认Node24.22.0/pnpm10.28.1，重新完整执行frozen install、独立性、官方固定API6fea生成、strict、**1056 Vitest＋376 Node**、两前端/两BFF等全workspace build及git无漂移检查，最后明确 **exit0**。同公开serviceId另构建两前端后，实际6份HTML/JS/CSS文件名和SHA256与128项真实验收前保存的冻结产物逐字一致；不是仅凭依赖分类推断兼容。未把该比较扩大为BFF二进制逐字证明。

既有Vite未来native config loader、大chunk及pnpm未批准esbuild build scripts提醒保持，不靠屏蔽warning或批准任意安装脚本计绿。源码/锁无漂移；平台不允许rm-f式删除，且本机gio不支持该临时挂载的回收站，故未绕过限制强删。候选、实际工具安装目录和两个已无效的生成stub精确归档到新建的隔离临时恢复目录，原两工作目录已移出，内容保留可恢复；均为可再生成工具/缓存，非用户私钥或源文件。真实轮次容器（含停止项）/network仍为空，legacy本地/远程不变，不sudo、不编译后端、不push/dispatch。

只读确认GitHub Actions当前enabled且allowed_actions=all；仍未触发任何run，不能由平台开关或本机exit0推断远端执行成功。CI定义已交付本地，实际远端run继续REMOTE_UNVERIFIED；取得push/运行授权后才可收齐该证据，不借本包关闭UC001、App政策发布、Cookie33+或完整goal。

## 2026-11-01 远端工作流核实

只读查询 GitHub Actions，已取得 [Console checks 成功运行 40429054771](https://github.com/TokenTeam/iwut-console/actions/runs/40429054771)，提交为 `53160543919c5e5eadd821c59fd4f5dc9dd5fba1`，唯一 `checks` job 及其全部步骤均为 success。包括锁定依赖安装、仓库独立性、固定官方 API 生成、严格类型、`Test including public protocol vectors`、双端与 BFF 构建以及无漂移检查。

核对该提交实际 workflow 的测试命令为 `pnpm test`，根脚本包含工作区测试，browser-auth 的正式协议测试包含公开向量。随后从同一 run 的日志归档核实 `packages/browser-auth test` 中 `src/protocol.test.ts` 的 19 项实际通过。该 workflow、browser-auth 测试脚本和协议测试与当前 `87901b4` 相同，足以关闭本工作包的公开向量远端运行证据缺口；不声称当前新增 UC018 或完整139项实链已经在远端通过。此次只读核实没有 push 或触发新作业；App 政策、Cookie33+及完整 UC/goal 边界仍独立开放。上文 REMOTE_UNVERIFIED 为初次交付时的历史事实。
