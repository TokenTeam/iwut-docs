# UC001–005：Developer 全读取入口真实跨会话矩阵

状态：`ACCEPTED / IN_PROGRESS`，2026-10-16，按用户持续授权自行决定并接受。上一[消费边界加固](2026-10-16-developer-read-consumption.md)的组件证据及原Application列表三例不能代替其它页面；本包补真实生产React验收，不扩大生产业务写UI。

## 独立准备与边界

1. 隔离Auth正式注册两个新账号A/B，各自正式Apply、DEVICE、Create一个独立App、创建DRAFT Version/DRAFT Profile和首个Tester加入链接，并由对方正式Join。复用已有正式准备协议和固定API类型，不seed本包业务数据、权限、quota或Session次数。A/B不授Reviewer/平台管理员；既有角色及其有限权限/资格相位不变。
2. 两个App/Version/Profile采用不同的测试名称，关联ID来自真实响应；互为Tester不授管理权限。joinUrl/secret和Auth Session只留Node闭包，REAL_FIXTURE仅含邮箱/AuthId和App/Version/Profile/Link/Membership ID。固定G只读确认A/B为ACTIVE、APPROVED且无Reviewer权限；不额外grant或改变G。
3. 固定loopback随机bearer控制提供空JSON的observe、revoke-a-sessions、revoke-b-sessions，仅作用本轮固定两subject的`auth_sessions.revokedAt:null→Date`。拒绝query/任意target、SessionId、URL、数据库或命令；未知写不重放。它是外部Session失效fault，不冒称正式Auth撤销/账号禁用UI。

## 真实矩阵

覆盖九读取：owned-list、Application详情、Version列表/详情、Profile列表/详情、Tester概览/Membership/JoinLink。每个读取分别控制真实旧成功200与旧SESSION_INVALID401，共18例；另七页面分别控制旧代DELETE204回执，共7例。合计25个有界场景，不用serial跳过余项；准备或hook失败须明确记录实际未执行部分，不把缺证据算通过。

- 普通describe、单worker、零retry。按Application/Version/Profile/Tester四组使用独立BrowserContext，每组各EMAIL生成两把自己的non-extractable设备钥匙，后续仅DEVICE切换；每context最多2＋7×2＝16次签发，不改变既有32次上限。新context是独立浏览器配置，不复制钥匙/storageState或通过产品reset绕过上限；原真实32次测试保留。
- 跨组邮箱沿用上一正式Begin返回的resendAfter等待，DEVICE开始至少间隔2100ms；时间只尊重真实准备预算，不当正确性oracle。429使准备/该例失败，不自动重放未知Begin/Complete/DEVICE；worker失败重建造成的冷却/前置失败与产品断言分开登记。
- 旧200/401在初始深链接读取前arm透明TLS响应gate，先独立同源读取证明A有真实材料或明确失效。B由另一标签页真实登录，再释放旧响应。按真实上游status、产品在线Session协调、旧材料未进入新私有投影及B实际获权读取分层证明；保留Abort，不要求DevTools读取被正确取消的旧正文。Tester只观察被控region的独有标识，不把先成功兄弟区块或URL中的App ID误当迟到泄露。
- 旧204须先建立A真实视图，令其Session失效并触发产品清理，确认真实旧DELETE已提交且204仍HELD。另一标签页建立B后，原SPA通过header Router Link确认B，经正式入口/链接建立同类B页面；再释放旧204，检查同一document、B路由/内容/各独立时间投影、权威Session和carrier属性保持，无额外Session/业务/DELETE/导航。后续明确刷新仍可读取B。仅被动包装fetch计数/status且返回原参数、Promise、Response，不读认证body。
- B拥有自己不同资源，不用伪造空数据或A的管理权限替代。各成功200检查private/no-store，401/204保留既有no-store和reason/status契约。不同区域时间来自各真实asOf，页面分钟格式不能被夸大成DOM纳秒精度证明。
- 故障gate每例清理；未命中ARMED仅可用捕获的精确真实读取或预期旧binding/generation DELETE有界消耗，再释放HELD，不能留下影响后续例的fault。无页面响应拦截、MSW、QueryClient调试接口、外部资产读取、业务写请求或Auth资料补查。

## 验证与完成边界

准备器/控制先做Node红绿及负例，API pin保持不变；运行普通测试、strict、生成漂移、build、fixture浏览器、Edge。运行时源码冻结后从空隔离环境重新pull Auth/App/Gateway latest，先专项、再无参数完整门禁；不因已知App错误头删断言或代理补头，不编译后端源码、不重启仍存活轮次。

本包的25场景只证明相应真实跨Session读取/回执交错，不覆盖全部生命周期/角色/权限下降组合或全浏览器heap。App缓存头、fixture偶发未定因、任意33+迟到carrier容量、完整UC001及审核决定依赖仍OPEN；实际准备、场景数、image ID、失败原因与清理结果逐轮登记，未过门禁不push。
