# iWUT Console 设计注册表

状态：`ACTIVE`

本文件索引 Console 的 UC、BR 与 ADR。它不复制权威正文。当前注册表人工维护，尚未接入 `tools/registry.py`。

## Use Cases

| ID | 标题 | 状态 | 权威位置 | 备注 |
| --- | --- | --- | --- | --- |
| `UC-CONSOLE-001` | 建立浏览器 Console Session | `ACCEPTED` | [UC-CONSOLE-001](use-cases/UC-CONSOLE-001-establish-console-session.md) | 共享认证入口；Gateway 路由已交付，实现进行中 |

## Business Rules

| ID | 标题 | 类型 | 权威位置 | 备注 |
| --- | --- | --- | --- | --- |
| `BR-CSE-001` | 认证路径与账号边界 | Console Session Establishment | [UC001](use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-001) | 不把登录解释为注册或授权 |
| `BR-CSE-002` | 浏览器设备密钥保管 | Console Session Establishment | [UC001](use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-002) | Web Crypto + IndexedDB |
| `BR-CSE-003` | 签名前验证与规范编码 | Console Session Establishment | [UC001](use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-003) | 复用平台向量 |
| `BR-CSE-004` | BFF Session 与 Cookie 隔离 | Console Session Establishment | [UC001](use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-004) | 两个 Console 独立会话 |
| `BR-CSE-005` | 同源建立、并发与迟到响应 | Console Session Establishment | [UC001](use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-005) | 登录 CSRF 与竞态边界 |
| `BR-CSE-006` | 结果不确定与幂等恢复 | Console Session Establishment | [UC001](use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-006) | 不复原旧 token |
| `BR-CSE-007` | 错误、失效与隐私表达 | Console Session Establishment | [UC001](use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-007) | 按稳定 reason 映射 |
| `BR-CSE-008` | 功能可访问性与秘密生命周期 | Console Session Establishment | [UC001](use-cases/UC-CONSOLE-001-establish-console-session.md#br-cse-008) | 不规定视觉样式 |

## Architecture Decisions

| ID | 标题 | 状态 | 权威位置 |
| --- | --- | --- | --- |
| `ADR-CONSOLE-001` | Console 仓库与应用边界 | `ACCEPTED` | [ADR-CONSOLE-001](adr/ADR-CONSOLE-001-repository-and-application-boundaries.md) |
| `ADR-CONSOLE-002` | 前端功能文档与视觉设计边界 | `ACCEPTED` | [ADR-CONSOLE-002](adr/ADR-CONSOLE-002-functional-documentation-boundary.md) |
| `ADR-CONSOLE-003` | Console 首版技术基线 | `ACCEPTED` | [ADR-CONSOLE-003](adr/ADR-CONSOLE-003-frontend-technology-baseline.md) |
| `ADR-CONSOLE-004` | Console 混合 BFF 与 Session ForwardAuth 流量边界 | `ACCEPTED` | [ADR-CONSOLE-004](adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md) |

## Next IDs

| 空间 | 下一个编号 |
| --- | --- |
| Console UC | `UC-CONSOLE-002` |
| Console BR-CSE | `BR-CSE-009` |
| Console ADR | `ADR-CONSOLE-005` |
