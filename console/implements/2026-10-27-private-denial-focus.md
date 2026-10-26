# Developer 私有读取拒绝后的焦点恢复

状态：ACCEPTED / NOT_STARTED（2026-10-27，按持续目标授权自行决定并接受）。

## 依据与缺口

[BR-CMG-004](../use-cases/UC-CONSOLE-002-query-owned-applications.md#br-cmg-004)要求失败和恢复有键盘、焦点、语义与异步宣告；[统一私有读取边界](../query-contracts/private-read-boundary.md)拥有拒绝后卸载、精确清理和仅明确重读的语义。本包不复制或改变权限规则。当前Developer `PrivateReadBoundary`拒绝后卸载原按钮所在子树，却没有把焦点移到新恢复界面；Admin对应边界已有聚焦标题。最新124项门禁没有证明这一具体要求。

## 接受的实现与边界

拒绝界面使用既有标题作为程序化焦点目标（tabIndex=-1），在该attempt首次拒绝后聚焦。保留原alert与“重新读取”，键盘Tab/Enter可继续明确重读；不增加自动请求、不以window focus/网络恢复解除拒绝、不新建页面永久权限黑名单。只关注仍挂载的当前attempt；旧attempt迟到结果不得抢占新页面焦点。只改功能语义，不规定视觉样式。

先用Testing Library证明刷新按钮卸载后聚焦标题、下一Tab到重读、明确Enter后恢复；覆盖初次拒绝、同attempt重复通知和旧attempt不抢焦点。真实证据复用既有管理权转让代表链，不新增业务资源/写/登录/邮件/测试矩阵；保留原private/no-store、Session与设备钥匙、旧数据清理断言，追加实际失权标题焦点和键盘重读。组件不冒充全部页面真实焦点证明。

冻结改后产品与spec，专项管理权转让及默认全量门禁均需通过；与独立CSP包同一冻结联合回归时保留两者各自断言。只本地提交、不push、不改后端、不移动legacy。该有限修复不关闭UC001 Cookie架构、政策发布或完整目标。
