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
- Tester初始读取同时发送三RPC。旧401场景须分别暂缓三路真实401，避免未受控兄弟先触发Session清理；B建立后先释放本例主目标，完成B生产视图协调，再放兄弟旧401并确认无新清理/旧投影。三个gate均独立核验并清理，不把额外两路当增加场景数，也不伪造其业务结果。
- 原透明proxy只允许一个非终态gate。为上述协调增加原子、有界2–3项的独立RESPONSE/HOLD batch，拒绝重复method/path、其它action/phase或与活跃single/batch混用；原single行为不放宽。loopback控制只允许本轮A的三条Tester读取组成完整batch，不接受任意地址/路径集合。主401协调时产品可能取消兄弟，此时须已先证明真实401为HELD，再接受DROPPED而不强求读取被取消正文；仍HELD的才释放。纯传输Node回归单独证明batch不修改上游status/headers/body及释放/取消隔离。
- 旧204须先建立A真实视图，令其Session失效并触发产品清理，确认真实旧DELETE已提交且204仍HELD。另一标签页建立B后，原SPA通过header Router Link确认B，经正式入口/链接建立同类B页面；再释放旧204，检查同一document、B路由/内容/各独立时间投影、权威Session和carrier属性保持，无额外Session/业务/DELETE/导航。后续明确刷新仍可读取B。仅被动包装fetch计数/status且返回原参数、Promise、Response，不读认证body。
- B拥有自己不同资源，不用伪造空数据或A的管理权限替代。各成功200检查private/no-store，401/204保留既有no-store和reason/status契约。不同区域时间来自各真实asOf，页面分钟格式不能被夸大成DOM纳秒精度证明。
- 故障gate每例清理；未命中ARMED仅可用捕获的精确真实读取或预期旧binding/generation DELETE有界消耗，再释放HELD，不能留下影响后续例的fault。无页面响应拦截、MSW、QueryClient调试接口、外部资产读取、业务写请求或Auth资料补查。

## 验证与完成边界

准备器/控制先做Node红绿及负例，API pin保持不变；运行普通测试、strict、生成漂移、build、fixture浏览器、Edge。运行时源码冻结后从空隔离环境重新pull Auth/App/Gateway latest，先专项、再无参数完整门禁；不因已知App错误头删断言或代理补头，不编译后端源码、不重启仍存活轮次。

本包的25场景只证明相应真实跨Session读取/回执交错，不覆盖全部生命周期/角色/权限下降组合或全浏览器heap。App缓存头、fixture偶发未定因、任意33+迟到carrier容量、完整UC001及审核决定依赖仍OPEN；实际准备、场景数、image ID、失败原因与清理结果逐轮登记，未过门禁不push。

## 实现与前置证据

准备器/固定控制首12项因缺导出/模块全部RED，后新增固定三路batch校验2项RED→GREEN，共14项通过；qualification原默认资源13项回归保持不变。透明proxy新增4项batch测试先全部RED，最小实现后通过，另补真实TLS三响应回归；最初TLS测试错误传递listener额外配置导致一项失败，已只修测试配置，随后统一837项Vitest＋122项Node全部通过。batch最多三响应、完整验证后才原子注册、与原single互斥，保留TLS trust、原status/body/header/Cookie数组和逐连接取消，不扩大为通用并发故障工具。

strict与Edge路由隔离/fail-closed通过。API漂移首轮固定pin远程fetch低速超时，尚待相同命令重试成功；build/fixture和真实25场景尚待终态，不能记作交付完成。本地/远程legacy已再核验仍为`e68851e343bd0e077e5ccd0b680fe6813216ced0`，未push。

同固定pin漂移重试已成功，build通过；原fixture浏览器本轮10通过/6非目标skip，不关闭此前偶发异常因果。运行时与spec均已冻结，开始新拉latest的25项专项；真实终态仍待记录。

## 首轮真实专项终态

冻结Console `6043f31`，隔离轮次`iwut-console-real-138939`，命令`pnpm test:real tests/real/developer-private-view.real.spec.ts`。25项全部通过（浏览器3.8分钟、exit0），Application/Version/Profile各6项、Tester7项，无跳过、无重试。旧200/401的18项和旧DELETE204的7项均执行完成，包括Tester三路真实401暂缓、同document非空B视图保持及随后明确刷新。仅已有注册密码限流按原合法Retry-After等待，没有新增登录重放或放宽断言。

本轮重新pull已发布latest，解析到的镜像ID如下；一轮内固定所解析ID，不依赖后端源码：

| 角色 | 实际镜像ID |
| --- | --- |
| Auth | `sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3` |
| App | `sha256:6f20c469a0e9566e045a5966fd51d81ce0b1293c650e2b277fa62bc3b5a3579b` |
| Gateway | `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9` |
| Mongo | `sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3` |
| Traefik | `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0` |

终态后核对本轮容器与网络均为空。继续保持同一源码/spec冻结，另起全新隔离环境运行无参数`pnpm test:real`；预期88项，但须以实际终态为准，不以本专项替代完整门禁，现有App缓存头缺口与上层UC仍OPEN，未push。
