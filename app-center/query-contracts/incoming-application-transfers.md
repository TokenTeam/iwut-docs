# 本人待接收 Application 转让读契约

状态：`ACCEPTED`。

## 权威与投影

集合/身份/过期/分页/错误以 [UC050](../use-cases/UC-APP-050-query-incoming-application-admin-transfers.md) BR-APP-059–062为唯一权威。生命周期和命令仍引用 [UC026](../use-cases/UC-APP-026-transfer-application-administration.md)。

```text
IncomingApplicationAdminTransferItem {
 transferId, applicationId, applicationName
 fromAuthId, toAuthId, status=PENDING
 requestedAt, expiresAt
}
IncomingApplicationAdminTransferPage { items[], nextPageToken?, asOf }
```

## 组合与消费

技术名称来自同一snapshot的Application，不需要公开Profile或Auth。toAuthId等于本次可信调用者；不返回源/目标资料、secret、配额、原始revision栅栏或私有配置。必要来源和申请归属绑定损坏整页失败，不合成空名或部分页。

列表只用于发现事项，点击后由原GetApplicationAdminTransfer重新读取当前事实；接受/拒绝仍使用UC026，不能把列表状态、前端倒计时或旧页当作资格。列表排除逻辑到期项但不写EXPIRED；没有事项明确items=[]。

分页不承诺跨页冻结。任何新状态均以新的服务端读取为准，已有transferId链接仍有效，不建立通知已读或历史收件模型。
