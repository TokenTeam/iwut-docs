# 双 Console 静态文档的 Strict CSP

状态：ACCEPTED / VERIFIED（2026-10-27，按持续目标授权自行决定并接受；仅本包部署与有限联合验收）。

## 依据与当前事实

[BR-CSE-002](../use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-002)要求严格CSP，并明确不可导出设备钥匙不抵抗同源恶意脚本使用。当前两个Vite入口、Console Edge静态路由及真实测试静态server均未交付文档CSP；BFF默认secureHeaders不覆盖SPA响应。124项真实门禁不证明CSP已存在，也不据此断言外部EO部署没有额外策略。

选择依据为[W3C CSP3的Strict CSP与外部脚本hash/SRI规则](https://www.w3.org/TR/CSP/#strict-csp)及[Vite构建期HTML hook](https://vite.dev/guide/api-plugin.html#transformindexhtml)。以下为本项目的部署决定，不是新后端业务规则。

## 接受的构建与部署设计

1. 保持双静态构建与既有共享Traefik混合链路，不把静态资源移入BFF。生产构建在Vite最终HTML阶段，对实际输出的本地入口JS及modulepreload资源计算SHA-256，加入匹配integrity与匿名crossorigin；使用hash＋strict-dynamic，不使用固定nonce、script-src self/https通配、unsafe-inline或unsafe-eval。每次内容变更重算，HTML与资源须作为同一不可变构建发布，不手工配置旧hash。
2. 将文档策略作为head内首个CSP meta，在任何可执行脚本/资源之前生效，随HTML经过静态托管/EO缓存保留。default-src none；script-src仅本次生成hash及strict-dynamic，script-src-attr none；style-src self、style-src-attr none；img/font/connect仅self；object/base/frame/worker/manifest禁用；form-action self。不加载远端App内容、图标或URL，不启用CSP report-sample或外部上报收集私有材料。未来有资源需求须独立说明，不预先扩大allowlist。
3. meta不能替代frame-ancestors响应头。因此Console Edge仅在双静态router挂本仓拥有的headers middleware，设置 `Content-Security-Policy: frame-ancestors 'none'` 与 `X-Frame-Options: DENY`；不修改Gateway/BFF/API路由或为它们临时补安全头。EO/其它托管必须保留构建meta，并在文档响应保留等价防嵌入头；本包不操作腾讯账号/域名，不宣称已验证生产EO。
4. build插件仅用于production，Vite开发/HMR不伪装成同强度部署。缺入口、缺bundle、未知/重复/外部脚本、已有冲突policy或不能计算内容时构建失败关闭，错误不回显脚本。build-helper与两个vite配置纳入strict检查。Strict CSP是纵深防御，不保证同源受信代码安全，也不替代输出编码、依赖治理或设备协议核对。

## 有限验证与交付

先RED→GREEN验证精确hash/资源绑定、policy先于脚本、build-only、静态资源类型与异常失败；Edge回归要求仅静态router附加防嵌入头且保留原路由隔离。新增双surface各一项真实生产文档测试：正常React入口和同源能力读取可工作；实际浏览器阻止未获hash的inline脚本/事件处理、外域connect/base/object等代表行为，且不发外部网络、不记录violation sample。CSP event证据只保留固定directive，恶意输入仅本测试固定合成marker，不含Session/邮箱/密钥。DevTools注入不当作合法生产脚本来源；动态受信依赖不扩大成“任意脚本不可执行”的错误承诺。

与焦点包联合冻结时，专项为新增两项CSP＋原管理权转让代表链，默认预计126项（原124完全保留），以实际终态为准。真实全量必须仍覆盖邮件/设备/IndexedDB、生产私有读取、决定、未知结果与跨Session链，不能仅以匿名入口通过关闭安全改动。每轮pull published latest且轮内固定ID，不编译后端；资源清理、本地/远程legacy不变、只本地提交，不push。App政策发布、Cookie33+及协议/CI独立审计项继续开放。

## 首轮证据与负例修订

产品/runtime/runner/spec冻结 `ebed8972ce305a19770600b07e98a4f9f3e79b93`；957 Vitest＋354 Node、strict（含构建helper/两Vite配置）、官方同pin生成、Edge及docs门禁通过。构建10项先6失败/4通过再全绿，Edge防嵌入先1失败/2通过再3通过；两套实际production build和磁盘JS hash/SRI一致。Vite现有大chunk与未来native-loader兼容提醒保留，不以warning隐藏失败或扩大已验证的构建模式。

published-latest专项轮 `iwut-console-real-380677`：3项中**1通过/2失败、39.9秒浏览器阶段、exit1**，无skip/retry。原正式转让的全部安全、Session、数据回收及新焦点/Tab/Enter断言通过；两CSP匿名生产入口、同源能力/Session、实际hash/SRI、meta顺序和Edge响应头均通过，在负例 `inlineExecuted` 断言失败。没有删断言后计绿；尚未运行默认126。

已核对[当前CSP3元素匹配算法](https://www.w3.org/TR/CSP/#match-element-to-source-list)：strict-dynamic允许非parser-inserted脚本，包括该测试经DOM createElement创建的内联script。原负例与选定策略不一致，不证明生产策略绕过。接受将“未获hash inline拒绝”的证据精确修订为HTML解析器插入的非授权脚本；保留handler/connect/base/object拒绝和真实强制事件/无外发断言，不改变生产policy、hash或合法入口。须先用有限无身份浏览器实验确认负例确经parser及当前policy处理，再冻结spec重跑专项与完整126；不能把DevTools执行、惰性/inert脚本或移除policy后重写文档冒充CSP拒绝。

首轮容器（含停止项）/network已清空。Auth518b0917/App68ee32b1/Gateway444c75a7、Mongo e0ce8c35/Traefik24841fe2与124基线相同，均重新pull后轮内固定ID；legacy不移动，不push。

修订后的准备边界：允许真实runner仅在固定无query GET `/__real-csp-parser-probe.html` 返回本轮实际built index.html的派生文档，唯一差异是在closing head前插入固定合成无hash script marker；不得接受任意HTML/marker/URL参数。meta与全部原脚本/样式/SRI字节保持，响应no-store，仅供匿名parser负例，不作为正常生产页面或业务准备。正常首页及同源成功读取仍独立验证；在导航前仅安装不改变CSP的事件观察器，收集固定directive/enforce，不记样本。loaded页面document.write会清DOM/监听器或使已求值module不能重挂React，不采用该替代。探针HTTP确实交给浏览器parser，需与真实拒绝事件和marker未执行联合证明，不以DOM惰性或脚本惯性不执行计绿。

## 最终 published latest 联合验收

修订只增加受限parser探针与修正浏览器负例，不改生产CSP或焦点产品代码；最终产品/runtime/runner/spec冻结 `29aa09b0da1d094fd14773a260aa075336a56aac`。新增探针5项先缺模块RED后5/5，与构建10项合计15项Node；统一 **957 Vitest＋359 Node**、strict（含构建helper/两个Vite配置）、官方固定API6fea远程生成、实际Edge和docs72份brief/367行8退休编号检查通过。

修订后首次尝试（exec会话66206）在Docker Hub拉取Mongo8.2.12授权token时EOF，CLI明确exit1，尚未建立业务环境或进入浏览器，资源为空；不计3项功能结果，也不跳pull/回退缓存。随后同冻结重新pull成功：专项 `iwut-console-real-393153` 使用 `pnpm test:real tests/real/csp.real.spec.ts tests/real/management-transfer.real.spec.ts`，**3/3通过、31.6秒浏览器阶段、exit0**；同冻结默认轮 `iwut-console-real-398407` 无参数 `pnpm test:real`，**126/126通过、23.9分钟浏览器阶段、exit0**，均无skip/retry。两CSP项和焦点代表链均在全量再次通过；原124全部保留，没有把匿名CSP或单项焦点替代正常认证/私有读取/审核/恢复门禁。

双surface正常生产React首页、同源capabilities/session、实际JS字节SHA256→SRI→policy绑定、meta先于资源及frame-ancestors/XFO头均通过。正常home保留handler/connect/base/object真实拒绝；独立同源HTTP派生探针保留原meta/SRI，确认固定parser脚本确在文档中但marker不执行，收到script-src-elem/enforce。两页面只记录固定directive/disposition和CDP requestId计数；外域实际header dispatch交集/响应均0，无Auth mutation/App请求、无nonce/脚本特赦/route/MSW。该探针只证明parser负例，不冒充正常生产HTML；strict-dynamic允许受信动态依赖的边界不被隐藏。

成功专项与全量五镜像相同，均每轮重新pull后固定ID：Auth `sha256:518b0917ec8302f9f6cb28bd2e12aa59033cfe6db45c82a81a0afcb1bac5aa16`；App `sha256:68ee32b1e92145734bfa7fe61d003ee7e2ed2bb8b20fd944f861704a8f48ad01`；Gateway `sha256:444c75a71fc74fb14840718b259aeec14fbe2bbcda0a9832340c70b64ed099b0`；Mongo `sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3`；Traefik `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0`。两轮容器（含停止项）与network为空，Edge烟测容器亦无残留；全量期间工作区干净、冻结未变，legacy本地/远程仍为e68851e343bd0e077e5ccd0b680fe6813216ced0。无后端编译/改动、无外部聊天需求、无push，元数据与证据仅本地保存。

仅关闭本包Strict CSP和所列联合证据；不证明生产EO已配置、所有浏览器完全相同或同源受信代码无法使用密钥。UC001协议护栏/损坏记录与CI证据已由[独立审计](2026-10-27-completion-audit.md)列为下一有限工作；App政策发布、Cookie33+及完整UC/goal仍开放，不因126全绿关闭。
