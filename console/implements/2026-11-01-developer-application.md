# 本人 Developer 资格与首次开通入口

状态：`DESIGN_ACCEPTED / IMPLEMENTATION_IN_PROGRESS`，2026-11-01。依据持续goal授权建立并自主接受 [UC018](../use-cases/UC-CONSOLE-018-apply-for-developer.md)，没有新增后端规则或外发消息。本页只记录交付边界，不把文档接受或fixture开通当产品实现。

## 已确认的断点与可用输入

Console有创建应用和Admin资格治理，但没有用户自申请入口。真实写入准备器会先为测试owner正式Apply，不能证明普通USER能在生产页面取得资格。创建页目前只解释DEVELOPER_APPROVAL_REQUIRED，无法在工作台内完成下一步。

Auth UC013与固定API6fea已经提供本人GET资格/POST申请、规范公开handle、nullable状态和canApply/blockers。Gateway9d6a27f已保留这两个DIRECT Session入口但未开放浏览器surface。Authority.readSession已有服务端受保护token，可以用两个固定Developer BFF端点复用内部Gateway；无需改Auth/App/Gateway，也不通过USER exchange或浏览器Session header绕过。原始Session不离开BFF。

## 已决定的有限范围

- Developer的独立`/account/developer`页，匿名保持路径登录；账号操作入口与创建资格错误提供明确导航，不先要求App权限。
- 两个BFF精确POST：`/api/account/developer-eligibility/read`、`/api/account/developer-application`。请求捕获context/generation，前后核对；正式Auth类型保持固定API，不提供可配置代理目标。
- 状态/handle/blockers与首次/历史补设分开，正常界面不显示技术revision。不填资料/学生材料，不加人工资格审核或条款管理。
- 申请必须明确确认公开ID不可改名；未知先读取并只对原规范名称明确重试。提交和读回区分，原Session/设备钥匙保持；再明确导航现有创建页，不自动创建。
- 注册比本包涉及更多匿名协议/密码/首个Session编排，作为后续独立范围；登录失败不自动注册。邮箱管理不借本包绕过既有证明流程。

## 验证与实施顺序

先完成当前冻结8344af8的旧clear同document专项终态，再集成产品，避免改变正在实测的源码/dist。可以在隔离前端工作区准备UC018实现；普通测试集中运行，真实链使用新的未Apply普通账号，不能挪用旧P0 owner或提高邮件/Session限额。Auth/App继续拉取latest，Gateway保留显式本地artifact，不从相邻仓编译后端。

实施应覆盖BFF/验证/Edge、Web完整状态及入口，之后在生产React自助开通并用同Session创建App，分别记录类型、组件、固定上游协议与真实证据。旧130项通过/3失败/143中断仍见[集中验收](2026-10-30-console-integration-gates.md)，不因接受本包而关闭旧门禁。

已创建隔离前端分支并离线按锁文件安装依赖。BFF/验证/Edge与Web/客户端分别实现，职责目录分开，普通检测集中；主工作区保持旧clear实链候选e24b98d冻结。业务payload统一复用API包的官方生成类型解码器，避免BFF与Web各写一套资格规则。此阶段尚无产品集成、构建或真实申请成功的声明，未push。
