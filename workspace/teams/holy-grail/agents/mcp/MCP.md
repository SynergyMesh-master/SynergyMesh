# Model Context Protocol (MCP) 整合

## 為何採用 MCP

- 統一 Agent 與工具溝通語言
- 熱插拔擴充第三方模型或工具
- 標準化上下文與安全邊界

## 架構

```text
Agent ↔ MCP Client ↔ MCP Server ↔ 工具/資料源
```

## 主要概念

- **Tools**：可被 Agent 呼叫的動作
- **Resources**：可訂閱或查詢的資料
- **Prompts**：標準化請求格式
- **Eventing**：雙向串流維持狀態

## Island AI 實作

- `mcp_servers/`：預建 Server（GitHub、CI、Docs）
- `config/mcp/*.yaml`：Server 註冊資訊
- island-cli 內建 MCP Client

## 安全考量

- Server 必須註冊簽章
- ACL 控制 Agent 能調用之資源
- 審計日誌記錄所有 MCP 交互
- 支援零信任隧道（mTLS + OIDC）

## 開發新 MCP Server

1. 參考 `mcp_servers/template`
2. 定義 `tools` 與 `resources`
3. 實作 `onRequest` / `onSubscribe`
4. 撰寫 `server.yaml`
5. 透過 `island-cli mcp register` 發佈
