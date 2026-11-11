# 平台 Application 目录与摘要读契约

状态：`ACCEPTED`。

## 权威与输入

授权、集合、过滤、分页及错误以 [UC051](../use-cases/UC-APP-051-query-platform-application-directory.md) BR-APP-063–066为唯一权威，不替代UC029/UC024或Auth权限定义。

```text
SearchPlatformApplicationsQuery {
 applicationId?, namePrefix?, adminAuthId?
 lifecycleStatuses[]?, platformAvailabilityStatuses[]?, archiveStatuses[]?
 pageSize, pageToken?
}
```

## 核心投影

```text
PlatformApplicationSummary {
 applicationId, name, adminAuthId, createdAt
 ownershipRevision
 lifecycleStatus, lifecycleRevision
 platformAvailabilityStatus, platformAvailabilityRevision
 archiveStatus, archiveRevision
}
PlatformApplicationPage { items[], nextPageToken?, asOf }
```

详情与每个列表项使用同一投影，不返回比较键、Version/Profile/Review正文、计数、Filter/OAuth、凭据、历史理由或Auth用户资料。未发布/无公开资料不影响核心摘要。

## 消费组合

目录只用于定位，当前摘要不是暂停/恢复等操作的确认基线。Console须按已获得的独立操作权限进入专用读取并重新确认各自revision；search权限本身不授予任何写权。

三种状态维度独立。每页snapshot可观察到不同归属或状态，旧token不是权限缓存；每次仍须验证本次身份与精确permission。界面不能以空页替代故障，也不能拼接UC029/UC024结果填充此目录。
