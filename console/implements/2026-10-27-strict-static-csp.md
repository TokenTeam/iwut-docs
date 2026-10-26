# 双 Console 静态文档的 Strict CSP

状态：ACCEPTED / NOT_STARTED（2026-10-27，按持续目标授权自行决定并接受）。

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
