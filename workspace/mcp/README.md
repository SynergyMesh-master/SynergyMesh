# MachineNativeOps Unified Pipeline & MCP Integration (world_class_validation baseline)

> **說明**：此子專案為 MachineNativeOps MCP 集成與統一管線配置草案，對應 world_class_validation 基線，提供可執行的 YAML manifest、JSON Schema、TypeScript 型別與 Python 載入器。

## 架構總覽
```mermaid
graph TB
  subgraph "輸入統一層"
      I1[GitHub/GitLab Webhook]
      I2[MCP 協議接口]
      I3[CLI 命令輸入]
      I4[API REST/gRPC]
      I5[事件總線訂閱]
  end

  subgraph "核心調度引擎"
      C1[統一事件路由器]
      C2[即時任務分解器]
      C3[資源競合調解器]
      C4[動態負載均衡器]
      C5[同步屏障控制器]
  end

  subgraph "執行管線層"
      P1[量子驗證管線]
      P2[重構執行管線]
      P3[安全合規管線]
      P4[部署交付管線]
      P5[監控告警管線]
  end

  subgraph "MCP 集成層"
      M1[MCP 服務器]
      M2[工具協議適配]
      M3[資源管理接口]
      M4[實時同步引擎]
      M5[跨平台協調器]
  end

  subgraph "輸出統一層"
      O1[統一審計日誌]
      O2[證據鏈聚合]
      O3[狀態報告生成]
      O4[自動修復觸發]
      O5[多平台通知]
  end

  I1 & I2 & I3 & I4 & I5 --> C1
  C1 --> C2 --> C3 --> C4 --> C5
  C5 --> P1 & P2 & P3 & P4 & P5
  P1 & P2 & P3 & P4 & P5 --> M1
  M1 --> M2 & M3 & M4 & M5
  M2 & M3 & M4 & M5 --> O1 & O2 & O3 & O4 & O5
```

## 主要產物
- YAML manifest：`workspace/mcp/pipelines/unified-pipeline-config.yaml`
- JSON Schema：`workspace/mcp/schemas/unified-pipeline.schema.json`
- TypeScript 型別：`workspace/mcp/types/unifiedPipeline.ts`
- Python 載入器：`workspace/mcp/tools/load_unified_pipeline.py`

## 快速檢視
- 配置驗證（JSON Schema）可用於 CI 早期檢查。
- Python 載入器提供型別化讀取，便於後續 MCP 服務端整合。
- TypeScript 型別可在 MCP 工具協議實作中直接導入。
