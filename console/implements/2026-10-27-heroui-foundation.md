# HeroUI 组件基础接入

状态：`ACCEPTED / VERIFIED`（仅本包组件基础范围），2026-10-27。用户要求先引入 HeroUI，再依据 App Center 接口规划页面结构。

## 本包范围

- [ADR-CONSOLE-003](../adr/ADR-CONSOLE-003-frontend-technology-baseline.md)的组件基础改为 HeroUI v3，固定 `@heroui/react` / `@heroui/styles` 为 3.2.6，lockfile 记录完整解析结果。
- `@iwut/ui` 的 Button、Input、Field、Surface 使用真实 HeroUI 组件。移除已不使用的 Radix Label 和 class-variance-authority，双端共同消费同一基础层。
- 保留现有 Button 的 `intent`、原生 click handler、默认 type=button 与显式 submit；disabled 转接 `isDisabled`，不再另绑 onPress 导致重复命令。Input 保持 React Hook Form 的 ref、name、onChange/onBlur 及只读/校验属性，Surface 保持命名 section 语义。
- 双端在 Tailwind 后引入共享 HeroUI CSS，并显式扫描共享 UI 和认证组件源码；不依赖单一应用的自动扫描偶然覆盖另一应用用到的 utility。
- React Aria 3.53.1 的 press hook 会检查固定 stylesheet ID 再尝试注入 touch-action 样式；当前在外部 CSS 提供相同规则，构建时只给确实包含该规则的首个 stylesheet 标记 ID。原有 script/style CSP 指令、SRI 与最终字节校验不放宽；浏览器启动最先配置 Zod jitless，避免已捕获的动态编译探测也触发 CSP 报警。不修改 node_modules 或伪造空 style 元素掩盖缺失规则。
- [页面结构规划](../page-architecture.md)作为 `PROPOSED` 供用户审阅；只记录功能导航和字段层次，不规定视觉样式。

## 非目标

不新增业务命令、页面或菜单，不修改 Gateway/Auth/App、API pin、Session 和 Query 清理逻辑。不接入付费 HeroUI Pro、不新增 CDN 或外部字体，不放宽 Strict CSP，也不把一次组件替换当作完整 UI 改造。原128项真实镜像结果属于改动前冻结，不能挪作本包验收。

## 验证

新增8项基础组件回归，改动前3失败/5通过：缺 HeroUI variant、Input class 与 Surface class；原生按钮/表单行为已有5项基线通过。首次适配中 Surface 误用 render element 而官方3.2.6实际要求 render function，类型检查同时发现原生 prop 类型与 exactOptionalPropertyTypes 不兼容；改用官方组件 props 与函数渲染，未放松 strict 配置。随后8项及全仓 strict 类型通过。

后续补充3项样式/入口依赖检查、1项 jitless 语义回归及1项静态 CSS/CSP 回归。全普通测试1068项 Vitest＋377项 Node、strict 类型、官方固定 API 生成、frozen install 和双端/BFF production build 通过。fixture Playwright 为10通过/6既有非目标跳过，仍是 fixture 层。

真实预览抽查中，旧宿主预览进程已经退出、Docker 后端仍运行；首次抽查未能连接，不是页面加载通过。恢复原origin、静态服务、TLS SMTP 和依赖透传，保留原Auth/App数据库及用户体验的审核结果；旧临时BFF密钥已丢失，改用新的独立BFF数据库和受限临时密钥文件，需重新登录，未声称保留旧Session。恢复后两端各一次真实邮箱登录、Developer应用读取和Admin版本队列/审核工作页读取通过；主按钮有实际背景，零pageerror、零CSP违规，未提交审核决定。抽查早期曾触发React Aria inline style与Zod eval探测，随后修复；另有一次重跑命中邮件冷却429和一次Chromium将touch-action规范化为manipulation的断言误期望，均未放宽服务限额或CSP。

新增两项可重复的真实production浏览器样式/键盘/CSP spec，轮次 `iwut-console-real-129860` 的 `pnpm test:real tests/real/heroui-foundation.real.spec.ts` 专项 **2/2通过**，浏览器阶段1.0秒、exit0、无skip/retry。检查真实HeroUI按钮/输入、键盘进入邮箱表单、外部静态press样式和零CSP违规；spec不发送邮件或业务命令，runner仍按既有方式准备独立测试账号/数据，尊重真实密码Retry-After和共享邮件冷却。五发布镜像重新pull，Auth518b0917/App68ee32b1/Gateway444c75a7/Mongo e0ce8c35/Traefik24841fe2；不编译后端。

专项资源已按runner清理，与保留运行的用户预览分离。官方固定API生成、独立性、文档72份brief/367条registry及本包链接检查通过。此次不冒充完整新UI或原128项全量复验，也不把本地结果当作新远端CI；未commit/push。Vite未来native loader和JS大chunk警告仍存在，不通过抑制警告宣称解决。
