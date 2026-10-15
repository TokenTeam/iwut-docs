# UC003：Version 分页、正式错误码与恢复

状态：`ACCEPTED / IN_PROGRESS`，2026-10-16，按用户持续授权自行决定。UC005完整真实门禁已收齐28通过/1条App响应头失败；本包开始实施，仍须独立红绿与真实验证，不能把其它包的绿灯转记本包完成。

## 已核对的问题

Console `versions.tsx`把坏token reason比较为短名`INVALID_APPLICATION_VERSION_PAGE_TOKEN`，现有组件fixture也使用该短名；固定API的正式ProtoJSON/错误响应值是`ERROR_REASON_INVALID_APPLICATION_VERSION_PAGE_TOKEN`。因此真实400不能进入“从头刷新”分支，仍提供重试失效token的操作。下一页错误还可能同时进入顶部和底部两个错误呈现分支。须以正式reason先取红，再修复，不能只修fixture使既有错误值继续通过。

Version client直接fromJson，尚未像Profile/Tester一样区分成功DTO错误与真实网络TypeError；成功列表目前只将pages.flatMap呈现，未正常标出每批数据时间。后者在本包明确补为每批独立asOf，不制造跨页统一时间；不是修改后端一致性语义或规定视觉布局。

输入继续固定API `a5d504c058c62cd91be451074d21608d69789918`。边界引用[UC-CONSOLE-003](../use-cases/UC-CONSOLE-003-query-owned-application-versions.md)、[UC-APP-034](../../app-center/use-cases/UC-APP-034-query-owned-application-versions.md)及[私有读取边界](../query-contracts/private-read-boundary.md)，不实现Reviewer、Publication推导或Version业务写命令。

## 实施决定

1. 两个成功DTO的必要结构/fromJson错误统一无原文/cause的ApiResponseError；fetch和成功正文断流TypeError保持网络分型，HTTP ApiError透传。列表仍累计加载更多，不改成另一种后端分页契约。
2. 正式坏token400或畸形成功立即隐藏并精确回收当前列表累积投影/详情，不清Session、不建App权限黑名单。明确错误不因focus/reconnect自动重试；只有明确从头读取或新成功可恢复，随后503不能复活已退场内容。正常同上下文网络/5xx仍保留各批原asOf。400提供唯一“从头刷新”，不同时暴露两个同义错误/按钮，也不再展示可继续使用的旧token入口。
3. 专用真实账号通过正式Developer/DEVICE/Create建立主App和空App。受validator/index约束准备25个四状态Version及一对一OAuth配置，含无Review DRAFT、恢复并再次编辑的DRAFT+最近REJECTED、PENDING/APPROVED/REJECTED关系及大于JS安全整数的revision；所有状态关系以App权威和真实validator为准，读取seed不宣称写/审核/恢复命令已执行。
4. 真实列表20+5、单状态筛选重置、空态、详情当前内容与latest摘要分离、bigint原样、运行URL/scopes/redirect惰性文本、同管理员跨App child404和token跨App/filter/类型/篡改400分别验证。token探针只证明真实协议，页面不会主动混用token；键盘/持久存储最小披露沿用已有规则。

## 不可套用其它包的语义

Version结束token为字符串空值；UC034 token绑定caller/App/filter/排序键，不能假设它具有Tester的ownershipRevision绑定，更不能直接改DB ownershipRevision冒充真实UI坏token或业务转让。当前正式API/UC034没有Profile的2MiB预算/ResponseTooLarge错误，不制造Version 413验收，也不在前端追加审批policy/checks或完整历史。

真实响应来自发布latest镜像，不编译相邻后端。继续保留[App详情404 no-store缺口](2026-10-16-management-access-loss.md)；focused只诊断，完整门禁、资源清理与本地提交分层登记。本包不关闭UC001/fencing或全部生命周期/资格矩阵，UC006–007仍未接受。

## 实施与分层验证

正式reason替换原fixture后先取得1红/10绿，扩展后API4项红、页面7项红，随后修复。Version独立projection仅处理400/ApiResponseError，先遮蔽正文，再在layout阶段核对捕获Query实例、error identity与errorUpdatedAt并清data，不触及其它Query或Session；原实例已被替换、已更新成功或错误代次变化时不清新内容。保留明确错误防focus/reconnect重试，不从Profile复制413语义。

页面保留原累计列表，正常区旁路展示每批独立时间，不把时间节点伪装成Version行。下一批网络故障保留原批及其asOf，用户可明确重取该批；从头刷新仍主动重置全部旧页。API请求和成功正文读取不放进DTO解码catch，真实TypeError/HTTP错误维持原分型，成功结构/fromJson失败只暴露静态ApiResponseError。

当前普通门禁：452项Vitest、32项Node通过，完整严格类型及固定输入生成漂移检查通过；其中Version页面/projection22项、API全包74项、Developer全包135项。上述是单元/组件与类型证据，不是实际后端/浏览器证据。

专用真实fixture由Developer/DEVICE及两次正式Create建立App/ownership/quota，再受Mongo validator约束准备25Version、25OAuth、20Review。恢复后编辑链source1→提交2→拒绝3→恢复4→编辑5，seq25 revision精确9007199254740993；正式policy/check ID只作历史读fixture元数据，不声称运行preflight/审核/恢复命令。新独立真实spec正验收20+5、筛选、空态、最小披露、当前详情/最近摘要、跨App隐藏及单次正文TRUNCATE；结果未收齐前不得登记通过。
