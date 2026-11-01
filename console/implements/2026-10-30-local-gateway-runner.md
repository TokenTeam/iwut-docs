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

## 2026-11-01：基础镜像的显式缓存模式

UC018联合专项4/4通过后，完整503436在拉取固定Mongo8.2.12时遇DockerHub referrers EOF；同一版本手动重拉又在manifest HEAD出现EOF。该轮已terminal exit1、没有进入构建/浏览器，也没有遗留容器/network；不是测试观察超时或业务断言失败。Auth/App镜像的latest策略没有失效证据，不能因此改为旧后端镜像或源码编译。

据持续自主工程授权接受一个独立、显式的基础设施缓存模式：默认仍对五类输入按原规则pull；仅当操作者设置`E2E_INFRASTRUCTURE_PULL=false`并同时提供`E2E_MONGO_IMAGE`与`E2E_TRAEFIK_IMAGE`的不可变引用时，跳过这两项pull。引用必须是完整sha256:imageID或无tag的repo@sha256:digest，不接受latest/版本tag/模糊前缀；必须inspect成功并严格核对ID或RepoDigest。不会在pull失败后自动回退，不混入历史review兼容模式，不构建镜像。

Auth/App保持原始pull策略；Gateway继续本页既有显式local规则。新模式单独输出基础设施来源，不能将这一轮写成默认全发布来源。它只使用已经完成实链的同一基础镜像：Mongo`sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3`、Traefik`sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0`；业务状态/协议、SMTP与业务超时不改变。

实现与定向Node门禁进行中；完整真实门禁必须分别记录业务镜像latest重拉后的ID、显式本地Gateway及缓存基础设施来源。此决定不改变后端latest联调意图，也不自行更新系统Docker代理或重启daemon。

实现已提交 `87901b4`，只改artifact policy、其Node回归、runner两个基础image env接线及检查点。相关backend/resolver Node24/24、两个脚本语法和diff检查通过；完整CI policy **57 Node＋21 Vitest** exit0。默认对象形状与五类pull、Gateway原规则保持，Auth/App不因新flag而跳过pull；非法/缺少/可变ref、metadata不匹配、与兼容模式冲突均失败，不build或自动回退。后续完整无参数轮次使用明确缓存的同一两基础ID，真实终态尚待，不将Node假Docker实验当作实链通过。
