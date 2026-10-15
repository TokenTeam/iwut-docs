# 真实浏览器失败报告隐私护栏

状态：`ACCEPTED / IMPLEMENTED`，按用户持续授权自行接受。仅补强测试设施，不改变 UC001/ADR005 语义，也不关闭其剩余验收缺口。

## 范围与决定

Playwright 的 `PLAYWRIGHT_NO_COPY_PROMPT` 仅抑制默认页面快照；定位器断言仍可能通过 matcher 的 ARIA snapshot 写入 error-context，fill API 的错误文本也可能携带输入值。不能仅因成功路径全绿就宣称未来失败诊断安全。

真实 spec 共用公开 API 的自动 fixture 与 hook 包装，在标准 list reporter/error-context 消费前去掉任意错误文本/快照，替换为静态失败标识与安全源位置。保留错误数量、failed 状态和退出码；诊断能力让位于认证材料保密，不保留 expected/actual 或原调用日志。beforeAll/afterAll 不执行普通 test auto fixture，须独立捕获并清理错误，保留 hook 的标题、参数注入和 this。

用独立合成 Playwright 配置验证 locator、fill API、beforeEach、beforeAll 四个故意失败场景和一个通过场景。随机虚拟标记只放环境/运行时，不写入源码；父 Node 测试扫描 stdout/stderr 及全部本轮临时产物，要求无标记且仍4失败/1通过、退出1。配置不被常规 real/fixture 套件发现；子进程有界并回收本轮资源，不接触真实后端、邮件或密钥。

该浏览器隐私门禁作为 `test:real` 前置，普通不要求浏览器的单元测试不增加依赖。范围限当前标准 reporter；不承诺任意自定义 JSON/step reporter 或测试自行 console 输出材料也被拦截。仍禁止认证材料日志，并继续关闭 trace、截图和视频。

## 验证计划

先运行合成负面回归、strict typecheck 和普通测试；再用共用 fixture 重跑全部13项真实 Browser/BFF/Gateway/Auth/App latest 测试，确认正路径和失败控制没有被吞掉。结果单独登记，不改写前一工作包已记录的13项证据。

## 2026-10-16 验证结果

- `pnpm test:real:privacy` 通过，子 Playwright **4 failed / 1 passed、exit1**，标准输出/错误及全部临时产物均无随机标记，error-context 无 ARIA YAML；负面失败没有被转换为通过。最终接线后再次独立运行也通过。
- `pnpm test` 通过：22项 Node 传输/有界进程回归与279项 Vitest；`pnpm typecheck` 通过，包含 real/privacy 两份 strict 配置。接线期间漏导出 Playwright Response 类型被类型检查阻止，补齐类型再完整重跑通过，没有忽略检查。
- `pnpm test:real` 完整退出0：隐私前置通过，随后生产 build 与 **13项真实 Browser/BFF/Gateway/Auth/App 全通过**（浏览器阶段约4.8分钟，无重试/跳过）。四份 real spec 均从共享隐私 fixture 导入，不改原断言及业务故障目标。
- 本轮重新拉取 published latest，Gateway digest `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9`、Auth `sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3`、App `sha256:6f20c469a0e9566e045a5966fd51d81ce0b1293c650e2b277fa62bc3b5a3579b`，没有读取或编译相邻后端源码，也没有修改三个后端。
- repository independence、diff、71份 brief 与367行 registry检查通过。本轮进程已终止，owned Docker容器/网络无遗留；合成测试只删除自己创建的临时目录。

UC001及fencing继续 `IN_PROGRESS / OPEN`：迟到Begin实际取消/替换、真实私有DOM/Query cache与旧SESSION_INVALID迟到矩阵，以及context签发上限显式重建仍须后续工作包。报告脱敏降低了错误细节可见性，不代替这些功能验收。
