# UC-CONSOLE-018：查看并申请本人 Developer 资格

状态：`ACCEPTED`，2026-11-01。依据持续 goal 对前端设计、自行接受和实现的授权建立。本文只定义 Console 功能与安全交互，不规定布局、配色或后端业务规则。

## 目标与范围

已有账号登录 Developer Console 后，可以查看本人资格、了解服务端返回的申请条件、明确申请或为历史资格补设开发者 ID，再主动进入创建应用。修复“测试准备器已开通资格，而普通用户只能在创建页收到资格不足”的产品断点。

业务权威引用 Auth [UC013](../../auth-center/use-cases/UC-AUTH-013-apply-for-developer.md) 的 BR-DEV-006–012 和[自助申请协议](../../platform/contracts/auth-developer-application-v1.md)。应用创建仍由 [UC009](UC-CONSOLE-009-create-application.md) 与 App UC001负责。登录继续沿用 [UC001](UC-CONSOLE-001-establish-console-session.md)，不把登录失败转为注册或自动申请。

本用例只接入本人资格读取与 Apply；不新增注册、邮箱管理、人工资格审核、暂停/恢复、退出资格、改名、名称可用性探测或批量授权。Admin 的人员治理不能代替本人申请。本次仅在 Developer Console 提供入口，不向 Admin 增加这一 BFF surface。

## 页面与路径

- 独立账号页 `/account/developer`，与本人资料并列；无需已是 Developer、拥有 Application 或加载应用列表才能进入。
- 已登录的账号操作区提供“开发者资格”入口。创建应用遇到正式资格不足时提供同页入口，不自动离开、申请或重发创建。
- 匿名直达可沿用原登录组件在该路径完成登录，保持目的地；不先跳到所有应用或要求资格证明。已有账号资料页行为保持。
- 页面展示资格状态、本人公开开发者 ID、服务端 canApply 与 blockers 的可理解解释。状态/字段缺失按正式 presence 表达，未知或损坏响应不解释为“尚未申请”。正常操作不展示技术修订、token 或后端原始错误正文。
- APPROVED 的用户可以明确进入现有创建应用页；这不是配额、应用审核或创建结果的承诺。历史 APPROVED 没有 handle 时，按正式 canApply 提供一次补设；不把补设解释为重新开通，也不因缺少 handle 擅自撤销已存在资格。

## BFF 与正式 API

两条 Auth 路由已有 Gateway DIRECT Session 策略，没有浏览器 Console surface。依 [ADR004](../adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md) 增加精确 Developer BFF 编排，原始 Session 仅存在服务端私有闭包，不要求 Gateway 或 Auth 修改路由/业务。

| Developer BFF | 固定内部 Gateway 请求 |
| --- | --- |
| `POST /api/account/developer-eligibility/read` | `GET /auth-center/v1/users/me/developer-eligibility`，无 body/query |
| `POST /api/account/developer-application` | `POST /auth-center/v1/users/me/developer-application`，正式 body 仅 developerHandle |

BFF 只接受当前公开 contextBinding/generation，申请另含 developerHandle；无动态目标、URL、authId、角色、邮箱或客户端就绪标志。读取使用 POST 只是携带明确的 Console 会话目标，不执行申请。请求有同源 Origin/Fetch Metadata、JSON 及有界正文检查，严格拒绝额外参数与字段；两端点及错误均 no-store。Edge 逐项放行 Developer 的精确 POST，不新增通配代理。

BFF 使用 Authority 的有效当前会话，核对捕获的绑定/代后以闭包内原 token 调用固定 Gateway 路径；不转发浏览器的 Cookie/身份头，不跟随重定向。返回前再核对当前会话，拒绝采用跨代结果。返回仅包含公开会话目标与固定 API 生成类型的正式业务 payload；上游 token、Cookie、Auth Session 原文或签名能力不能进入返回、日志、缓存、持久存储或异常 cause。不新建登录流程、载体、Session 或 Mongo 写协议。

固定 API 输入仍为 `6fea3db899d3d096d4d3dfc59b2c85432a4b9eb6`，复用已生成的 developer_application / developer_status，不手写另一份业务 DTO。消息大小、超时和成功/错误解码有界；HTTP 200 只有在 schema、合法状态/presence、规范 handle 等正式契约成立时才可确认为成功。429 仅按合法重试时间表达，不自动重放。

## 前端规则

<a id="br-cda-001"></a>
### BR-CDA-001：本人资格与业务边界

只读取/申请当前 USER 本人，依据正式 canApply/blockers 决定申请或历史补设入口。不能从空应用列表、登录成功、邮箱字符串或 Admin 资格推断 Developer；不能根据查询先行授予任何资格。SUSPENDED/REJECTED/PENDING/WITHDRAWN 等按正式状态解释，不提供自助审批、恢复或以旧成功结果重开资格。读取失败不伪装为业务 blocker。

<a id="br-cda-002"></a>
### BR-CDA-002：明确 ID 与申请确认

开发者 ID 规则与不可改名含义引用 Auth BR-DEV-011。前端可以校验并预览正式规范小写值，不 trim 或静默清除非法字符，不自动生成名字、不探测占用。用户必须明确确认公开且不可改名后单次提交。ID、当前资格或会话变化会使原确认失效；在途阻止重复提交。历史补设单独说明不重置已有开通历史。

<a id="br-cda-003"></a>
### BR-CDA-003：回执、读回与未知结果

成功 ACK 与正式资格读回分别表达，ACK 不直接伪造查询快照。申请后读取本人资格，用户明确选择继续创建；不自动创建 App、重新登录或申请其它权限。读回失败保留已确认结果并允许明确重读。

超时、断网、损坏成功响应或结果未知时暂停写入，保留本页原目标，先明确查询本人资格，不把仍可申请解释为原请求必未执行。若需要重试，只能对原规范 ID 重新明确确认并依 Auth 相同名称幂等规则发送；不得自动改名重放或根据历史成功恢复状态。观察到当前资格/handle 是事实，不证明未知请求由本次客户端完成。明确业务拒绝按稳定 reason 解释，名称占用不泄露他人身份。

<a id="br-cda-004"></a>
### BR-CDA-004：会话隔离与私有内存

查询、确认、写入和读回绑定原 context/generation 及捕获的 Query 实例/data；旧请求不能修改新 Query、确认、输入或页面导航。真正 Session 拒绝沿用原按代恢复，不能清另一代或另一 Console。资格业务拒绝不冒充登录失效，也不清理仍合法的应用历史或独立 Reviewer 权限。

表单、待确认 ID、未知操作信息只保存在页面内存；离页/换会话清除，不存 localStorage、URL、持久 Query/Mutation 缓存或日志。原不可导出设备钥匙保持；不为申请导出、替换或新建登录凭据。

<a id="br-cda-005"></a>
### BR-CDA-005：完整可达路径与验收

资格页独立于 App 管理关系；匿名直达、已登录普通用户、已开通/历史补设、暂不可申请及拒绝/未知恢复均有明确可达状态。大量输入不放弹窗，状态与错误可由键盘及辅助技术读取，不规定视觉样式。

集中验证应包括：严格 BFF 双端点与 Developer-only Edge、固定上游/无秘密输出、非法/跨代/迟到请求；正式 nullable/presence/blockers 与 handle、一次确认/一次写、未知先读和同名明确重试；替换 Query/新会话/离页清理。真实代表链使用未 Apply 的独立普通账号、SMTP 邮箱登录和原不可导出钥匙，在生产 React 自申请后通过原 Session 实际创建 App；准备器不能先授予该账号 Developer。另核对正常查询/进入页面不写、零自动登录及退出/资料入口回归。镜像继续 latest，源码/fixture/组件证据不冒充实链完成。
