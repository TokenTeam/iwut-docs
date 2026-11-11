# Application 管理动态读契约

状态：`ACCEPTED`。2026-11-09 用户授权实施 App Center 部分；进度见[实施记录](../implements/UC-APP-052-management-activity-readiness.md)。

## 权威与输入

授权、来源、披露、快照、分页及错误以 [UC052](../use-cases/UC-APP-052-query-application-management-activity.md) BR-APP-067–071 为唯一权威。本文件定义最小读投影，不新增事件写入或通知语义。

```text
ListApplicationManagementActivityRequest {
 applicationId
 query: { kinds[], pageSize, pageToken? }
}
GetApplicationManagementActivityRequest { applicationId, activityId }
```

kinds 为 UC052 六种审核提交/结果；省略/空表示全部。不得通过额外过滤项扩展成个人收件箱、人员目录或全平台聚合。

## 最小投影

```text
VersionReviewRef { versionId, reviewId, attempt, versionLabelAtSubmission }
ProfileReviewRef { profileRevisionId, profileReviewId, attempt, profileRevisionSequence }
ApplicationManagementActivity {
 activityId, applicationId, kind, occurredAt
 target: VersionReviewRef | ProfileReviewRef
}
ApplicationManagementActivityPage { items[], nextPageToken?, asOf }
ApplicationManagementActivityDetail {
 activity
 rejectionReason: string | null
 asOf
}
```

target 与 kind 严格配对，版本标签/资料序号亦为互斥分支。列表没有理由；详情拒绝项返回该次原始理由，其他类别为 null。activityId 稳定定位历史来源，不证明权限。内部比较键、Reviewer 身份和完整审核正文不在投影内。正式Proto把版本标签/资料序号放入各自target分支；rejection_reason使用google.protobuf.Value，服务必须填StringValue或NullValue，使HTTP为明确字符串/null，native亦能区分。其余字段编号与JSON命名以API提交7651f96为准，不因编码差异改变逻辑空值与字段缺席的区别。

## 消费组合

管理动态只有当前单 App；转让待处理和参与者详情、脚本角色历史、Reviewer 队列沿原入口。前端不得遍历全应用或调用 Reviewer API 补 owner 时间线。

“查看记录”使用 activityId 查询原历史，“查看当前资源”使用 target 中的父资源 ID 进入原管理详情。Version 旧标签、旧拒绝及 Profile 旧批准不改写成当前状态。列表结果和历史详情不携带写操作基线，不能直接触发审核/恢复/重提命令。

asOf 不冻结后续页面，显式刷新重建第一页。Session/App/kinds 变化隔离旧数据；空结果与错误分别展示。没有已读、未读、计数、后台轮询或通知发送。未来真实通知需要独立设计，不能把本投影当作接收/投递协议。
