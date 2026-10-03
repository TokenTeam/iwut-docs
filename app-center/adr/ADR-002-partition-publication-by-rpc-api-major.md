# ADR-002：ApplicationPublication 按 RPC API major 分区

状态：`ACCEPTED`

日期：2026-09-15

## 背景

iWUT 客户端使用 Expo 承载网页应用，并通过宿主 RPC 向网页提供能力。ApplicationVersion 使用 `[rpcApiMinVersion, rpcApiMaxVersionExclusive)` 和 requiredCapabilities 声明兼容性，不存在独立的 Android/iOS/Web 应用制品。

发布槽位必须回答：“使用某个 RPC major 的宿主，应把这个应用解析到哪个 test/grey/stable Version？”

如果整个 Application 只有一组全局槽位，一个 Version 即使只兼容部分宿主 major，也会成为全局指针；每次解析都必须再猜测回退版本，槽位本身不再具有清楚含义。

## 决定

ApplicationPublication 从第一次出现时就按以下业务键唯一：

```text
(applicationId, rpcApiMajor)
```

每条 Publication 只管理一个 RPC major 下的发布槽位和 revision。UC-APP-007 首先引入 testVersionId；grey/stable 字段只在对应真实用例出现时增加。

被放入槽位的 ApplicationVersion 必须满足：

```text
rpcApiMinVersion <= rpcApiMajor < rpcApiMaxVersionExclusive
```

requiredCapabilities 仍在客户端解析或握手时逐项判断，不成为新的 Publication 分区维度。

一个 Version 若兼容多个 major，可以由管理员分别放入多条 Publication。一次命令只改变一个 rpcApiMajor，不根据 Version range 隐式批量修改。

## 为什么不使用 platform/target

当前应用都是网页，手机端只是 Expo 宿主。影响网页能否运行的是宿主提供的 RPC 合约和 capabilities，而不是一个抽象的 `ios/android/web` target。

如果未来真的出现不同制品、不同入口或不同审核内容的平台版本，应先扩展 ApplicationVersion 的业务模型，再重新评估 Publication key；现在不为空的平台概念预留字段。

## 考虑过的替代方案

### 每个 Application 只有一条 Publication

优点是记录少、更新简单。缺点是 test/grey/stable 指针无法独立表达不同 RPC major 的兼容版本，解析规则会被迫在槽位之外寻找隐式回退，因此不采用。

### 按客户端 build version 分区

客户端 build 可能频繁变化，并不等于 RPC 合约变化。同一 RPC major 的多个客户端 build 通常可以共享发布决策，因此不采用。

### 设置 Version 时自动覆盖其 range 内全部 major

操作方便，但一次点击会修改多条发布状态，权限、并发、回滚和部分失败语义都更复杂。当前采用显式逐 major 设置；未来如有批量需求，在多个单项命令之上设计批处理，而不改变单项不变量。

## 结果

优点：

- 每个槽位天然只引用兼容当前 RPC major 的 Version。
- 不同宿主合约可以独立测试、灰度、稳定和回滚。
- Publication revision 与历史记录拥有明确的并发边界。
- 不引入虚假的 platform/target。

代价：

- 一个跨多个 major 的 Version 需要多次显式设置。
- 管理界面需要展示每个 major 的槽位状态。
- 多 major 批量发布需要额外的协调与部分失败设计。

## 适用边界

本决定只覆盖 App Center 的版本发布选择。Auth token、Expo build 升级策略和网页自己的 versionLabel 不使用这个分区键。

若未来证明系统永远只支持一个 RPC major，可以保留相同模型而只存在一条 Publication；无需把分区重新折叠进 Application。

## 关联用例

- [UC-APP-002：创建 ApplicationVersion](../use-cases/UC-APP-002-create-application-version.md)
- [UC-APP-007：设置 test 发布槽位](../use-cases/UC-APP-007-place-approved-version-in-test-slot.md)
- [UC-APP-012：为 Tester 解析 test 启动目标](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md)

## 变更记录

- 2026-09-15：选择 `(applicationId, rpcApiMajor)` 作为 Publication 唯一业务键；不使用 platform/target，也不隐式批量覆盖 Version range。
