# 显式本地 Gateway 镜像联调

状态：`IMPLEMENTED / LOCAL_POLICY_VERIFIED`，2026-10-30。用户授权 Gateway 自仓本地构建以加快前端接入；本包只补 Console runner 的消费方式，不改变默认发布验证或业务认证链。依据[交接清单](2026-10-30-gateway-console-capability-gaps.md#本地构建与交付方式)。

## 行为与决定

- 默认 `pnpm test:real` 保持 `published-latest`：每轮 pull Auth/App/Gateway 的 CNB `latest`，再固定该轮实际镜像 ID。
- 已有 `E2E_*_IMAGE` override 默认仍 pull，来源保持 `explicit-image-override`。
- 只有同时指定 `E2E_GATEWAY_IMAGE` 与 `E2E_GATEWAY_PULL=false`，才跳过 Gateway pull，来源为 `explicit-local-gateway`。`false` 不允许缺失、空白或选项形状的镜像引用；flag 只接受精确 `true` / `false`。
- 跳过 pull 仍必须成功执行 `docker image inspect` 并得到完整不可变镜像 ID；缺失或损坏即失败，不 pull 回退、不换 `latest`、不编译源码。其余角色的 pull 行为不变；renderer/runtime 继续共用本轮解析后的 Gateway ID。
- 历史 `test:real:review-compat` 仍校验既有三份固定 artifact ID，只对这些固定后端跳 pull，Mongo/Traefik照常准备；拒绝任意新旧镜像/拉取 override，不混成新模式。
- 不添加相邻仓库路径或将本地镜像硬编码进 runner。快速联调、发布镜像验证和历史兼容验证分别标识来源，不能互相冒充。

## 使用示例

```bash
E2E_GATEWAY_IMAGE=iwut-gateway:console-local-9d6a27f E2E_GATEWAY_PULL=false pnpm test:real tests/real/version-read-matrix.real.spec.ts
```

镜像应先由 Gateway 自身构建；替换上述标签即可消费其他显式本地产物。去掉 spec 会运行完整真实套件，保留 spec 是有限诊断，不代表全量通过。Auth/App 未设置 override 时继续使用发布 `latest`。

## 代码与证据

`scripts/real/backend-artifacts.mjs` 集中校验来源/拉取策略并解析镜像；`scripts/test-real-services.mjs` 在创建测试资源前读取策略，在原镜像准备阶段使用该解析器。八项配置/命令适配回归覆盖默认全部 pull、旧 override、新模式只跳 Gateway、非法输入、缺失本地镜像无 fallback、镜像 ID 校验以及固定历史模式隔离；已纳入 `test:ci-policy`，因此进入默认 `pnpm test`。

- 定向 Node 批次：新增 8 项 + 原 Withdrawal wiring 6 项 + CI/installer 17 项，共 **31/31** 通过。
- 首轮同批次为 30/31：唯一失败是原 CI policy 测试精确断言旧二文件命令。更新该断言以包含第三份 artifact 测试后重跑 31/31；未删除原两份门禁或放宽断言。
- `node --check scripts/test-real-services.mjs` 与 helper 通过，限定文件 `git diff --check` 通过。
- 通过同一 helper 对实际 `iwut-gateway:console-local-9d6a27f` 做只读解析：只调用 `docker image inspect`，得到 `sha256:90cf10f0ea832812ee756e686362e0114d493e090b2286aef76dd9304007fdd7`，来源 `explicit-local-gateway`；未调用 pull/build/run。

本包没有启动完整 real suite、修改运行中的预览容器或消费真实个人数据。配置/镜像解析证据不等于新增写 UI 或实际业务成功链已验收，后者由对应功能包继续完成。

## Edge 门禁统一镜像策略

同日收尾发现，`scripts/test-edge-config.sh` 仍自行执行无条件 Gateway `docker pull`，因此显式本地镜像与 `E2E_GATEWAY_PULL=false` 无法贯穿 Edge 门禁。已移除该独立 shell 规则，新增薄入口 `scripts/real/resolve-gateway-artifact.mjs`，直接调用本页既有 `loadBackendArtifactPolicy` / `resolveBackendArtifact`，不复制策略、不修改真实业务 runner。

CLI 标准输出只有经既有解析器严格验证的完整 immutable image ID，pull 进度、Docker 诊断与来源信息走标准错误。Edge 只捕获该 ID，并将它交给 `/gateway-config` renderer；不再在解析后使用可能变化的 tag。默认仍 pull 已发布 latest，旧 image override 仍默认 pull；仅明确本地模式跳过 pull、强制 inspect。缺失镜像、非法配置和损坏 metadata 退出失败，不 build、不回退、不输出可误用的 ID。

```bash
E2E_GATEWAY_IMAGE=iwut-gateway:console-local-9d6a27f E2E_GATEWAY_PULL=false pnpm edge:e2e
```

新增七项 Node 回归实际 spawn 薄 CLI 和隔离的假 Docker executable，覆盖默认 pull、local 仅 inspect、旧 override、缺失镜像、非法 flag/参数、损坏 metadata、stdout/日志隔离与 Edge 使用解析后 ID。它们不访问 Docker daemon、网络或容器，也不运行 renderer；不能当作真实 Edge 通过证据。已追加到 `test:ci-policy`，并更新 workflow 测试的精确命令断言，原 installer、CI 和 artifact policy 断言全部保留。

本次集中定向批次为原 **25 项 + 新 7 项，共 32/32**、exit0；CLI `node --check`、Edge `bash -n`、`scripts/build/tsconfig.json` 的 TypeScript 检查通过。本次没有运行实际 `edge:e2e` 或创建/停止容器，没有改 Web/BFF、API 生成物或真实业务 runner；真实 Edge 验证由后续集中门禁登记。
