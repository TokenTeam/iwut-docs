# UC006：正式 Scope 启停后的旧审核页面恢复

状态：`ACCEPTED / VERIFIED`（仅本包有界Scope链），2026-10-26。依据用户持续 goal 授权自行接受本有界实现方案。需求来源为 [UC006 验收4](../use-cases/UC-CONSOLE-006-review-application-versions.md#验收与完成标准)、[Auth UC036](../../auth-center/use-cases/UC-AUTH-036-release-scope-enablement-changes.md#验收与交付边界)和 [App ADR001](../../app-center/adr/ADR-001-scope-catalog-cache.md#第一阶段缓存)，不重新定义后端业务规则。专项30/30及默认全量118/118通过；完整UC与广泛goal仍未完成。

## 范围与设计决定

1. 只增加真实测试准备与既有审核页面的必要恢复修正，不增加 Scope 管理 UI、不开放新的 Console surface、不实现 Developer 写 UI。始终使用已发布 Auth/App/Gateway `latest`，每轮拉取后固定 ID；不编译本地后端。
2. 将独立 API 输入统一升级到已发布 `6fea3db899d3d096d4d3dfc59b2c85432a4b9eb6`，从官方源生成 Scope 管理类型，保留既有 API 子集与严格解码，不手抄业务 wire 类型。
3. 隔离 runner 使用显式持久 OAuth Scope manifest，保留真实 App provider 接线与独立密钥；public OAuth 仍关闭。只启用正式管理员管理能力，复用当前正式 bootstrap 的完整管理员，调用 Gateway 内部正常 Session→USER 管理路由；不伪造身份、不写目录 Mongo、不因配置额外授予 Reviewer 权限。
4. 复用原审核 owner、Reviewer 和既有 Application，通过正式 Create/Submit 准备两份含 `email` 的待审 Version。另准备仅含仍启用 `openid` 的见证 Version，使用正式提交响应中的 scopeCatalogRevision 证明该实例已实际消费新目录。不得用空 scopes、清缓存、假时钟或一次 sleep 本身作为证据。
5. 测试环境将真实 App TTL 显式设为正值 `5s`，不改生产缺省；当前部署只有一个 App 进程。经过真实 TTL 窗口后，见证提交必须取得 Auth 管理回执对应新 revision。该证据只覆盖此测试实例，不外推全生产副本同步。
6. Scope 修改按固定有限阶段 enabled→disabled→enabled，每次使用新 operationId、当前 revision/digest 和原因；读取原回执及当前管理目录核验。未知写只查询原编号，不换 ID 重做；NOT_FOUND 不代表未提交。固定阶段并发互斥，不允许任意 caller 参数或额外变化。
7. 准备 Create/Submit 每个目标仅执行一次；未知结果可读原固定目标，不自动重放，准备 promise 保持原结果，不因重复控制请求重新建资源。失败时不通过补发决定“清理”待审记录；整轮数据库由既有隔离资源清理销毁。

具体接线复用现有Traefik内部TCP TLS入口（仅额外映射宿主loopback端口供真实探测，不对公网开放），转发真实App gRPC。Auth service/OIDC/delegation三把密钥独立于USER identity；不构造虚假时钟观察。使用固定App provider方法、正式服务JWS及生成Proto codec完成真实TLS/native gRPC快照探测，不能仅凭TLS握手宣布业务接线成立。Scope准备复用已有具精确Reviewer权限但非完整平台管理员的owner Session作拒绝门禁与读回；不使用前面Session故障矩阵刻意撤销的main Reviewer后台Session，也不增加新登录绕过故障。

## 真实浏览器验收

在现有27项审核决定专项之后追加三项，不改原115项断言或skip：

- 页面加载待审 Version A 的实际 snapshot/email、正式当前策略并由 Reviewer 主动确认；正式管理员停用 email，读原回执和新目录，再由见证提交证明 App 消费该目录。旧页面原 APPROVE 必须实际422/InvalidApplicationScope，A仍PENDING、无部分决定；页面要求重读、清确认、不自动重放，保留 Session 与另一审核能力。
- 同一停用窗口中，独立待审 Version B 可由 Reviewer 明确人工 REJECT，使用真实策略和空确认集合；其结果不自动恢复或绕过 email 状态。
- 管理员用新编号/当前前置值前向恢复 email，核验原回执与新目录；第二份见证提交证明 App 已消费恢复后的 revision。A显式重读和重新确认后才发新 APPROVE，实际批准验证的 scopeCatalogRevision 与恢复回执一致；APPROVED不等于发布。总决定POST次数严格为拒绝旧批准一次、用户重新批准一次，不能后台补发。

管理操作和见证准备仅通过受控测试入口，响应最小化，不返回 Session/JWS/钥匙。真实 spec 使用共用脱敏 fixture，禁止 trace、截图、video或私有DOM转储。管理入口跨Console默认关闭保持；另以真实普通Reviewer管理请求拒绝验证其没有完整平台管理员资格。

## 门禁与交付

先对固定阶段/未知写恢复/并发与输入边界做单元失败回归，使用生成客户端严格类型和普通门禁；再冻结源码、专项真实30项、默认无参数118项。数量为计划，只有实际终态才能记通过；失败保留原因和清理事实，不把专项冒称完整门禁。若实际生产契约无法满足准备，应记录具体缺口，不改后端或用mock替代。

App策略发布回执/运维读回和下一份真实政策仍是独立依赖；本包不关闭策略变化验收、Cookie33+carrier架构边界或完整UC001/006/007。已有commit/legacy基线保留，legacy不得移动；不自动push。

## 首轮专项与状态码预期修正

输入内容指纹`7c7b975c09cb26a2b0fd4882695a444bf924dd24e4f8ac150714259eea84b002`，轮次`iwut-console-real-165463`，published-latest五镜像与新镜像基线相同。普通954 Vitest＋249 Node（新增28）、strict、官方6fea生成、Edge均通过。真实App provider服务身份/TLS/native gRPC探测通过；专项30项为27通过、1失败、2未执行，浏览器阶段3.0分钟，exit1，未执行全量。

新增第28项已完成正式email停用、原回执和管理目录核验，以及真实TTL后的openid见证提交（revision匹配）；旧页面原批准实际422且private/no-store。断言在预期400处失败，后续reason/重读/无部分写及两项尚未执行，不据此预先宣布它们通过。资源已清理。此为新增测试的状态码预期错误，不是后台允许批准或缓存未刷新的证据。

核对现有App HTTP transport：Decide对领域InvalidArgument语义错误使用422；UC005候选HTTP映射也将决定语义校验映为422，稳定Scope reason仍为InvalidApplicationScope，gRPC仍InvalidArgument。早期交接过程记录中的“Scope400”不能覆盖此传输规则。本包自行接受修正为精确422，不接受400/422任选、不改后端或放松reason/状态/回执/TTL证据；保留首轮失败并重新冻结后验证。

第二轮内容指纹`6fc67b4debe723c1ae72f6f4d3eff2c72d1cbd45d82f782f0eb309cedf0189ba`，轮次`iwut-console-real-174113`，同组published-latest。30项为29通过、1失败，浏览器阶段3.2分钟，exit1，无skip/retry。第28项已完整证明正式停用后的422/稳定reason、PENDING与revision/snapshot不变、重读清确认/无自动重放/Session与另一能力保持；第29项证明停用期间独立REJECT成功。第30项已完成前向恢复、第二份openid见证revision、旧页重读和重新确认，实际APPROVE200且approvalValidation目录revision正确；其后在confirmedCheckIds顺序断言失败，后续断言不冒称通过。资源已清理，未执行全量。

原因是新增断言将展示/请求顺序套到已持久化的集合。UC005的confirmedCheckIds使用集合语义，决定投影明定已排序且唯一。修正为“实际持久化数组精确等于本次策略IDs的排序副本”，仍验证全部项、无重复/缺失及规范顺序；发送命令仍精确比较页面本次原始确认集合。不排序实际结果掩盖服务端错误，不改生产行为，保留第二轮失败后重新冻结。

## 修正后专项终态与完整门禁

第三轮内容指纹`ba1e17066354cfe9fe5e3782199206ca983c25c350ee42b1bbe30114ff498717`，命令仍为`pnpm test:real tests/real/review-decisions.real.spec.ts`，published-latest五ID与前两轮一致。30/30通过，浏览器阶段3.1分钟，exit0、无skip/retry（执行会话88253实际终态）。原27项及新增3项全部完成；真实422/稳定Scope reason、停用窗口REJECT、前向恢复与实际APPROVE、匹配回执的目录消费证据、PENDING无部分写/清确认/无自动重放/两会话和另一能力保持均按spec证明。实际批准投影确认ID按契约规范排序，拒绝目标恢复后仍终态。测试容器（含已退出）与network已核验为空。

同一内容冻结下执行无参数`pnpm test:real`，轮次`iwut-console-real-199334`，118/118通过（19.8分钟浏览器阶段、exit0、无skip/retry）。五个镜像重新拉取latest，ID与专项一致；完整轮次的原115项及新增3项均完成，新增Scope链不是只靠专项关闭。

完整轮次结束后重算内容指纹仍为`ba1e17066354cfe9fe5e3782199206ca983c25c350ee42b1bbe30114ff498717`，运行期无源变化。测试容器（含已退出）与network均为空；legacy本地与本次远端仍为`e68851e343bd0e077e5ccd0b680fe6813216ced0`。普通954 Vitest＋249 Node、strict/官方固定6fea生成/Edge及docs72brief/registry检查通过。之后仅更新状态导航和本记录，不修改经验证的产品/runtime/runner/spec。

## 本包完成与保留边界

只关闭上述正式email启停/真实TTL与目录revision消费/旧审核页面恢复的有界验收。本次未修改产品源码；真实链证明既有4xx稳定恢复对422 Scope错误正确工作。新增代码为隔离测试环境、生成类型与测试准备，仍不提供Scope管理UI或Console新surface。未编译后端、不使用mock替代、不放松原缓存头断言、不移动legacy、不push。

App策略发布原子回执/运维读回与下一真实政策仍待外部交付；Auth自身全量回归、其OAuth门户交付和生产开关门禁不由本包替代。WITHDRAWN/账号禁用的管理读取有界验收及Cookie33+carrier架构边界仍开放，完整UC与广泛goal继续IN_PROGRESS。前两轮失败及未执行项保留原结论，不借最终绿抹去历史。
