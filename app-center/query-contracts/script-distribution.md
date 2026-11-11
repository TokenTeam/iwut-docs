# 独立脚本分发与应用精确依赖读契约

状态：`ACCEPTED`。2026-11-07 用户接受，2026-11-08 落实。

## 定位与权威

本文定义 [UC047](../use-cases/UC-APP-047-resolve-application-script-content.md) 四个查询的投影、分页和组合语义。资格及固定依赖以 BR-SCR-019–022 为唯一权威；HTTP/RPC、错误、文本与传输预算见该 UC 的正式分发接口及后续章节。查询不写访问事实、业务 revision 或审计，不构成运行租约。

## 身份与查询边界

四个查询只向可信 ACTIVE USER 开放。独立分发不要求应用关联、Developer、Tester 或五项脚本管理权限。应用入口根据 PURE_TEST/UNIFIED 选择既有运行解析规则，再验证请求的精确 ApplicationVersion；不信任用户自报身份、channel、cohort 或 Membership。

所有返回只使用同一次一致读取的必要事实。未授权目标、未发布正文及运维/审核私有信息不通过状态差异或字段披露。整个 manifest 校验后才能返回，内容请求重新验证当前目标和全部依赖，不信任前一次查询结果。

## 独立推荐列表

ListPublishedScripts 依 [BR-SCR-022](../use-cases/UC-APP-047-resolve-application-script-content.md#br-scr-022) 选取当前 AVAILABLE 且 head 非空资源，返回：

```text
PublishedScriptItem {
  resourceId, name, purpose
  head: { versionId, versionLabel, contentFormat, digest, byteLength }
}
PublishedScriptPage { items[], nextCursor?, asOf }
```

name/purpose 是当前资源元数据；head 是精确发布事实，不返回正文、人员、理由、私有 revision 或未发布版本。发布 head 的必要关系损坏时整页失败，不能用普通隐藏掩盖。

按资源 createdAt/resourceId 稳定倒序，limit 默认20、范围1–100；游标采用独立签名用途并绑定可信调用者、过滤条件和最后已消费资源位置。每页重新读取 gate，不跨页冻结。扫描预算500，响应预算2 MiB；可返回短页/空页及 nextCursor，不越过尚未返回的合法项。不返回 totalCount，不使用 offset。正常不可推荐项消耗扫描位置，不消耗返回条数。单个合法项必须能独立返回。

## 应用 manifest

ResolveApplicationScriptManifest 返回：

```text
ApplicationScriptManifest {
  applicationId, applicationVersionId
  publicationRevision, channel, rpcApiMajor
  scripts: [{ resourceId, versionId, contentFormat, digest, byteLength }]
  asOf
}
```

scripts 的精确来源、0..16上限、明确空列表及规范排序以 [BR-SCR-019](../use-cases/UC-APP-047-resolve-application-script-content.md#br-scr-019) 和 [BR-SDP-001](../use-cases/UC-APP-048-manage-application-script-dependencies.md#br-sdp-001) 为准。它不跟随 head、不返回备用依赖，不包含 launch URL、scopes、Filter、Tester/cohort 材料或其他槽位。publicationRevision 只表示本次解析事实，不冻结随后内容请求。

## 单份精确内容

独立 GetPublishedScriptContent 返回 resourceId、versionId、contentFormat、digest、byteLength、contentText 和 asOf。应用 GetApplicationScriptContent 在相同内容字段外返回本次 applicationId、applicationVersionId、publicationRevision、channel、rpcApiMajor。字段全部来自同一事实组合，不返回管理/审核人员、决定、理由或策略。

每次只返回一份完整文本，正文及摘要按 [BR-SCR-021](../use-cases/UC-APP-047-resolve-application-script-content.md#br-scr-021) 和 UC047 内容预算校验。ClearHead 后历史精确内容仍可用；Suspend 后新内容请求不可用。已取得文本不提供服务端追回承诺。

## 既有消费入口

[UC047 稳定映射](../use-cases/UC-APP-047-resolve-application-script-content.md#既有入口的稳定映射)固定各入口的业务不可用、损坏及故障分类。UC012/023 保留原运行资格和能力分支；UC024 独立验证 Stable 基线并消费最终目标；UC038 保留本人的参与事实，增加 SCRIPT_DEPENDENCY_UNAVAILABLE 卡片状态；UC019 两个运行查询复核 gate，sector 回调查询不承担运行授权。

脚本 gate 不省略固定依赖、不替换版本、不把存储失败伪装成无候选、不返回部分“可运行”结果。对应管理/审核历史继续按各自权限读取。
