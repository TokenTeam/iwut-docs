# Console 查询契约

本目录记录页面读取后端事实所需的应用层语义和依赖状态，不保存 mock response 作为权威数据模型。

若 Auth Center 或 App Center 已拥有对应 query contract，Console 只引用它并补充页面消费方式；不得复制后形成第二份状态定义。后端尚无查询时，可以在此记录结构化需求，但最终业务读模型仍由拥有数据的 bounded context 接受并实现。
