# Application Filter v1

状态：`ACCEPTED`

## 目的与边界

本契约固定 App Center 与官方客户端之间的 `profile-filter-v1` 规则线格式和求值语义。权威业务规则位于 [UC-APP-022](../../app-center/use-cases/UC-APP-022-manage-application-filter.md)。

App Center 保存并分发规则，不读取用户资料或执行规则。客户端只使用本地资料求值。Filter 只影响 Grey/Stable 候选的展示，不授予任何服务端权限；Test 入口不执行 Filter。

## 规则线格式

规则是 oneof group/predicate 的树：

```text
Rule {
  oneof node {
    Group group
    Predicate predicate
  }
}

Group {
  GroupOperator operator // ALL, ANY, NOT
  Rule[] children
}

Predicate {
  string fieldKey
  PredicateOperator operator
  optional ProfileScalar value
}

ProfileScalar {
  oneof value {
    string stringValue
    int32 integerValue
    bool booleanValue
    string dateValue
  }
}
```

字段 key 语法和值类型与 Auth ProfileFieldDefinition 对齐，但客户端不得把规则中的 key 当作用户已提供该字段、已授予第三方读取权限或字段当前存在的证明。

## 结构限制

- schemaVersion 固定 `profile-filter-v1`。
- 最大 128 节点、深度 8；ALL/ANY 为 1–32 children，NOT 恰为 1。
- EQ/NE 支持四种标量；LT/LTE/GT/GTE 只支持 INTEGER/DATE；EXISTS/NOT_EXISTS 不携带值。
- STRING 最大 4096 Unicode code points；DATE 是严格 `YYYY-MM-DD` 公历日期。
- 未知 enum、未设置 oneof、类型错配或超限均为无效规则。

## 求值

普通比较遇到缺失字段或本地类型不匹配时为 false。EXISTS 只在存在支持类型的字段时为 true，NOT_EXISTS 为其反值。NOT 正常反转 child 的结果。字符串精确比较，不 trim、归一化或折叠大小写；INTEGER、BOOLEAN、DATE 按类型值比较。

没有 Filter 或 mode=`ALLOW_ALL` 时允许展示。客户端遇到未知 schemaVersion、节点或操作符时 fail closed，不展示该候选。客户端不向 App Center 返回原始字段、求值轨迹或命中结果。

## 版本与缓存

Catalog 返回 applicationId、ApplicationFilter revision、当前 filterRevisionId、schemaVersion、mode 和 rule。客户端可按 `(applicationId, filterRevisionId)` 缓存已解析规则；新的 Revision 使旧缓存失效。Revision 不与 Publication revision、Version 或 Profile revision 合并。

## 共享验收向量

服务端 Domain 与各官方客户端应共享覆盖以下行为的固定向量：ALL/ANY 短路、NOT、四种标量、日期和整数端点、缺失字段、类型不匹配、EXISTS/NOT_EXISTS、ALLOW_ALL，以及未知 schemaVersion fail closed。向量不包含真实用户资料或生产字段名。
