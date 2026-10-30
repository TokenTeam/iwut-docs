# Console 新管理能力集中验收

状态：`ORDINARY_VERIFIED / FULL_REAL_PENDING`，2026-10-30。用户要求集中必要验证、避免每次UI修改后跑整套；本页登记UC008–015这一批接入的整体验证，不代替各用例或历史门禁。

## 输入与范围

- Console原有UI/发布工作已保存为 `869e2f9` 与 `checkpoint/2026-10-30-console-workspace`；原 `legacy=e68851e` 保持不变。
- 新应用/版本/资料写入、测试/OAuth/Filter、归档/转让和Admin治理均按接受的UC实现；UC010拒绝后新建预填继续收尾。UC016只完成接受设计，尚未实施，不纳入本轮产品成功声明。
- 固定官方API为 `6fea3db899d3d096d4d3dfc59b2c85432a4b9eb6`。显式本地Gateway `9d6a27f / 90cf10f0…` 配合published Auth/App latest；默认发布runner仍保留pull策略，不编译相邻后端。
- 代表实链已分别通过[P0/P1两专项](2026-10-30-developer-management-writes.md)及[归档/交接专项](2026-10-30-application-ownership-writes.md)。Admin治理的独立真实链与最终无筛选门禁尚待运行，旧128绿结果不作为新源码的完整证明。

## 第一轮普通门禁

`pnpm generate:check` 与完整 `pnpm typecheck` 均exit0；官方生成器从固定远程API重新验证全部输入。仓库独立性与diff空白检查通过。文档brief72份、App注册表367行检查通过；这两个工具不机械检查Console注册表，Console链接/编号另行人工核对。

第一轮 `pnpm test` exit1。Node共385项通过，无skip/cancel；共享packages、双BFF已完成的子批次通过。Developer为548通过/2失败，Admin子进程因递归首错停止，不能当作完整Admin通过。

两条失败分别为：

1. 原 `versions.test.tsx` 要求“网络写入未接通”且无提交按钮，已不符合本轮接受的默认写入。修订保留URL/Scope惰性内容断言，改为已有DRAFT提供明确送审/放弃、打开不发送任何写请求，不靠删除测试隐藏行为变化。
2. UC010新的取消导航用例发现当前TanStack blocker取消后navigate Promise可能不resolve；仅在finally清理内存handoff会留下可被后续直接新建误领的预填。按接受的增量修复：正文只在短命内存，导航state仅携带无内容/身份的随机关联token；目标精确匹配Session/应用/token并在commit后消费，刷新或已消费token不能恢复正文。继续以StrictMode取消、普通新建与重新进入回归核对，不用timeout猜测导航已完成。

本轮类型与单测执行时UC010最后一条仍在收尾，因此不是最终冻结。修复后需完成相应组件批次及集中门禁，不能直接把上述exit1改记为成功。

## 收尾进展

UC010已完成49组件（新增预填10＋原编辑/读取39）、client7与Developer strict。最终实现不在click时暂存正文，而在blocker允许后的精确Router导航事件内stage，取消导航没有正文残留；目标commit后精确消费，StrictMode、取消后普通新建、后退/前进旧token均有回归。本文第一轮观察及原因保留，具体功能决定见UC010。

第二轮 `pnpm test` 的Developer为550通过/1失败，UC010已全绿；唯一失败是根代理新增“不发写请求”断言把侧栏正式POST `applications:search`错误计为命令。已按精确method/path仅豁免该正式读取，不允许任何其它POST/PUT/PATCH/DELETE；版本URL/Scope惰性及独立审核分区断言保留。修订后版本25/25通过。第二轮仍为exit1，不据此宣称完整默认test已通过。

完整 `pnpm build` 已exit0，双静态Web及所有共享/BFF包成功；Vite仍报告现有大于500kB的chunk体积提示，未调高阈值隐藏。本批新增全页管理代码暂未另行做路由拆包；功能验收与后续体积优化分别处理。

Admin治理实际页面spec及正式准备已落盘，待最终types/privacy与完整runner执行。P0 spec继续补入新草稿明确放弃的既有能力，保留原七次写入并增加创建/放弃两次，正式DELETE/If-Match/回执和列表读回均按契约断言；尚未执行该新增动作。恢复被拒绝版本仍未有本轮独立真实证据。

Edge配置验证还存在无条件pull的工具差异，正在复用同一本地镜像policy；默认latest门禁不变。此工具改动完成后集中执行最后普通门禁，再提交/运行全量。

## 最终普通门禁

收尾后的完整 `pnpm test` **exit0**：**1595项Vitest＋392项Node**，没有skip/cancel。包含Developer551、Admin234、API client459，原两类审核、私有读取/Session及本轮新命令均在同一默认普通入口通过。原两轮exit1保留，不以定向通过替换默认门禁。

最终完整 `pnpm typecheck` **exit0**，包括新增UC015正式fixture与P0放弃草稿spec；先前 `governance-write-fixture.ts` TS7022仅通过为循环中的previous显式标注bigint修正，没有更改业务准备。`test:real:privacy` **1/1、exit0**。官方 `generate:check`、完整build、独立性检查均通过；最后只有测试和工具收尾，没有再改已构建的产品源。

Edge工具收尾复用同一policy，32项CI/CLI回归通过并纳入上述392项。实际执行 `E2E_GATEWAY_IMAGE=iwut-gateway:console-local-9d6a27f E2E_GATEWAY_PULL=false pnpm edge:e2e` **exit0**，CLI来源为explicit-local-gateway，renderer确实使用immutable `90cf10f0…`；原双surface静态/私有边界、六审核读写隔离与伪造头拒绝均通过。这只是独立无上游的路由失败关闭门禁，不冒充成功业务链。

Console改动文档的26个文件相对链接全部存在；brief72份与App注册表367行门禁再次通过。Console注册表含UC016且Next017已人工核对。原legacy与checkpoint分支仍指向原提交。

## 提交与真实冻结

产品、生成物、runner与spec已本地提交为 Console **`61dd9b3`**（`:sparkles: feat: enable Console management workflows`）。这是待完整真实验收的候选，不冒称全量通过；没有push，legacy仍为e68851e。文档与源码跨仓分别提交，不把无关resource-hub纳入。

## 待完成

- UC015实际页面治理成功链、P0新增放弃草稿与完整真实回归；按实际总数、镜像和终态登记，不提前固定通过数。UC010预填已有组件证据，未凭原实链扩证。
- 记录文档提交和完整真实终态；不覆盖legacy，不自行push。无关 `resource-hub/` 工作不进入Console文档提交。

账号资料UC016、特殊凭据/BFF、正式IP部署、独立运维权限发现与Cookie传输边界仍是后续工作，不因这一批验收关闭完整goal。
