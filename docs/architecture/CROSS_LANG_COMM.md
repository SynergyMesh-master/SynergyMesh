# 跨語言通信

## 原則

- 合約優先：所有服務以 Schema (Proto/GraphQL/OpenAPI) 為準
- 自動生成 SDK 與型別
- 版本化 + 相容性測試

## 工具

- gRPC + Protobuf
- GraphQL Gateway
- AsyncAPI for event bus (NATS/Kafka)
- `tools/schema-sync` 自動同步

## 流程

1. 於 `schemas/` 更新契約
2. 觸發 `schema-ci` pipeline
3. 產生多語言 SDK
4. Agent 驗證破壞性變更

## 驗證命令

```bash
npm run schema:lint
npm run schema:generate
```

## 治理規則

- Major 變更需要 L4 核准
- Minor 變更 L3 + 相容性測試
- Patch 變更 L2 自動放行
