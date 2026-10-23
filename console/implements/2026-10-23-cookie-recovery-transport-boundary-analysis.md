# Cookie超限恢复：应用解析与传输解析的不同边界

状态：`ACCEPTED / ANALYZED`，2026-10-23。持续目标恢复后对[33+carrier开放项](2026-10-23-console-stage-closeout.md#不应继续用局部实现掩盖的设计边界)进行有限诊断；接受的是本次分析结论，不是新认证协议或恢复接口。不变更UC/ADR005，不把35/35及115/115全绿外推为此问题已交付。

## 当前实现事实

[ADR005](../adr/ADR-CONSOLE-005-durable-session-and-login-fencing.md)要求登录前后载体分离、不同generation随机carrier、精确旧名清理及迟到响应不替换/恢复/清除当前身份；固定同名Cookie或把匿名context直接提升为认证bearer不是等价替代。

[接线契约](../query-contracts/console-session-v2.md#公共值与载体)固定8192字节Cookie头和32个本surface carrier。当前Console `ConsoleSessionAuthority.cookies()`在查询权威状态前执行这些限制；bootstrap、confirm、reset、Session读取和clear都经过该解析器。已有真实32次签发后的reset不是绕过Cookie上限的清理路径。

两个生产BFF启动器均把`node:http.createServer`交给`@hono/node-server`，未在启动参数中指定`maxHeaderSize`。因此还须区分应用自行返回的431与HTTP解析器在应用handler执行前拒绝的431；后者不能靠修改某个Hono路由恢复。这里不推断Tencent EO、Traefik或所有部署环境的头限制。

## 本地有限实验

Node v24.22.0运行时实际`http.maxHeaderSize=16384`。使用临时loopback原生HTTP server（无自定义maxHeaderSize），只累计固定诊断path的handler调用次数；无真实账号、Session、carrier、邮件或私钥，未记录Cookie值，finally关闭server/browser/context。

先用原生HTTP客户端确认：106字节合成Cookie得到204、handler调用1次；20006字节合成Cookie得到431、handler调用0次。这只是传输层控制，不证明浏览器接受单个巨大Cookie。

随后使用当前已安装Chromium建立全新临时BrowserContext，注入多个各自短小的HttpOnly/Strict合成Cookie；名称不是生产carrier，值不对应任何权威记录。导航到同一loopback诊断server，实际结果：

- 33个Cookie，浏览器保留33个，合成Cookie头3529字节，HTTP200、handler调用1次。
- 160个Cookie，浏览器保留160个，合成Cookie头17118字节，HTTP431、handler调用0次。

浏览器实验首版server返回204导致正常导航ERR_ABORTED，没有用该次结果支持结论；改为普通200诊断页面后上述两组均完成、命令exit0。没有改变任何生产响应或为产品测试伪造成功。这不是HTTPS/Traefik/双BFF/Auth联合验收，不宣称所有浏览器有相同Cookie容量，也不把合成Cookie当正式认证签发证据。

## 决定与不成立的替代

1. 不把“给新清理接口放宽到64/128个Cookie”当任意33+迟到carrier的完整恢复。它只能覆盖HTTP解析器仍愿意接收的有界子集；以上真实浏览器反例中的请求根本到不了接口。
2. 不靠扩大Node/Edge头上限宣称消除问题。提高有限阈值只是移动边界，且改变资源/拒绝服务预算；不处理迟到Set-Cookie、浏览器存储容量与旧清理回执的身份不变式。
3. 不使用统一同名认证Cookie、wildcard删除或删除整个站点存储来换取测试通过；它们不能作为当前不同代fence/设备钥匙保留要求的等价实现。
4. 当前不实施局部清理路由，不新增模拟恢复成功的产品case。完整恢复需单独架构工作包，同时说明请求到达应用前被拒绝的恢复方式、精确清理/迟到回执、新旧context及既有设备钥匙边界；须先证明再修改ADR/协议与生产实现。

这是对候选局部方案的反例分析，不是证明所有可能恢复架构均不可能，也不是以“难”为由取消UC要求。当前仍按既有431表达失败关闭并保留设备钥匙，不把该边界登记为已修复。

## 其它继续条件的当前核对

官方API仓库`refs/heads/master`实际只读查询仍为`27c9743d2d7476511932a83563e103aee5b4e28e`，与Console固定输入一致；没有据此启动相同完整测试或编译后端。既有策略/Scope在线变更与不同修订并发准备问题仍按各权威UC处理，不能由本次传输实验或镜像缓存头修复关闭。

Console产品/runtime/runner/spec均未改，原全绿证据仍限定原35/115套件；未push、未联系其它聊天，临时诊断资源均关闭。后续选择仍是正式跨系统契约处理或完整Cookie恢复架构，不自动增加无限测试排列。
