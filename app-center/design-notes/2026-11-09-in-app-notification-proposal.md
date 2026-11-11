# 原个人收件箱／站内通知草案的范围调整

原 `PROPOSED` 方案未被接受。2026-11-09 用户明确要求：当前只处理 Console 管理场景，用户客户端及未来应用开放的通知应单独设计，当前能力最好不要称为通知。

原个人收件箱、固定收件人、逐条已读及通知生成事务方案已退出本轮。[Console 管理动态草案](2026-11-09-console-management-activity-proposal.md)随后收敛为已接受的 [UC052](../use-cases/UC-APP-052-query-application-management-activity.md)，App后端已完成；[Console UC023](../../console/use-cases/UC-CONSOLE-023-query-application-management-activity.md)也已于2026-11-10获接受，其实现、验收与发布由Console owner维护。2026-11-11收尾范围继续排除个人通知、自动加载、long polling与WebSocket。

真实通知的跨客户端展示、应用发送授权、受众、投递渠道、偏好、读状态、配额/费用及可靠投递没有在本轮设计或接受。先前草案的名称和“同业务事务保存个人收件记录”建议不构成这些能力的实现授权。原草案链接保留为范围调整说明，不作为兼容接口或第二份权威。
