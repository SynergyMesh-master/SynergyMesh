# 99-元數據整合指南 (Metadata Integration Guide)

## 概述 (Overview)

本文檔說明 **99-元數據管理中心** 如何與 MachineNativeOps 系統的其他組件整合。

## 與活體知識庫的整合 (Living Knowledge Base Integration)

### 整合架構

99-元數據管理中心是**活體知識庫（Living Knowledge Base）**的治理層實現。活體知識庫的四個層次完全整合在元數據管理框架中：

```yaml
99-元數據管理中心 (Metadata Management Center)
├── 1. 感知層 (Perception Layer)
│   └── 觸發器: Git提交、工作流結果、定期掃描
├── 2. 建模層 (Modeling Layer)
│   └── 輸出: generated-mndoc.yaml, knowledge-graph.yaml, superroot-entities.yaml
├── 3. 診斷層 (Diagnosis Layer)
│   └── 檢查: 孤兒元件、死設定、重疊工作流、斷鏈文件
└── 4. 回饋層 (Feedback Layer)
    └── 行動: 儀表板更新、維護者通知、自動修復
```

### 關鍵文檔連結

- **主文檔**: [docs/LIVING_KNOWLEDGE_BASE.md](../../../docs/LIVING_KNOWLEDGE_BASE.md)
- **架構設計**: [docs/architecture/components/LIVING_KNOWLEDGE_BASE.md](../../../docs/architecture/components/LIVING_KNOWLEDGE_BASE.md)
- **治理維度**: [src/governance/dimensions/99-metadata/](.)

## 與其他治理維度的整合

### 依賴維度

99-元數據管理中心依賴以下治理維度：

#### 必需依賴 (Required Dependencies)

1. **61-lineage (血緣治理)**
   - 提供數據血緣追踪基礎
   - 關係: 元數據管理中心擴展血緣追踪功能
   - 集成點: LineageGraph 資源類型

2. **62-provenance (來源治理)**
   - 提供數據溯源基礎
   - 關係: 元數據管理中心記錄完整溯源鏈
   - 集成點: ProvenanceRecord 資源類型

3. **07-audit (審計治理)**
   - 提供審計記錄功能
   - 關係: 所有元數據操作產生審計軌跡
   - 集成點: 審計日誌輸出

4. **24-registry (註冊治理)**
   - 提供資源註冊功能
   - 關係: 元數據條目在註冊表中註冊
   - 集成點: 元數據目錄

#### 可選依賴 (Optional Dependencies)

1. **38-sbom (軟體物料清單)**
   - 提供構建物料清單
   - 關係: 溯源記錄可包含 SBOM
   - 集成點: Artifact 屬性

2. **63-evidence (證據治理)**
   - 提供證據收集
   - 關係: 元數據可關聯證據
   - 集成點: Evidence 連結

3. **64-attestation (證明治理)**
   - 提供認證和證明
   - 關係: 溯源記錄可包含認證
   - 集成點: Attestation 屬性

## 資料流整合 (Data Flow Integration)

### 1. 元數據收集流程

```
數據源 → 元數據收集器 → 分類器 → 驗證器 → 元數據目錄
   ↓                                            ↓
感知層 ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← 建模層
```

### 2. 血緣追踪流程

```
數據源 → 血緣提取器 → 血緣圖構建 → 影響分析 → 可視化
   ↓                                        ↓
61-lineage ← ← ← ← ← ← ← ← ← ← ← 99-metadata
```

### 3. 溯源記錄流程

```
Git/構建/運行時 → 溯源收集器 → 認證/簽名 → 溯源記錄
        ↓                                    ↓
   62-provenance ← ← ← ← ← ← ← ← ← 99-metadata
```

### 4. 知識圖譜更新流程

```
變更事件 → 感知層 → 建模層 → 知識圖譜 → 診斷層 → 健康報告 → 回饋層
                                                           ↓
                                                    GitHub Issue
                                                    儀表板更新
```

## API 整合 (API Integration)

### REST API 端點

```yaml
# 元數據管理 API
GET    /api/v1/metadata                      # 列出所有元數據
GET    /api/v1/metadata/{id}                 # 獲取特定元數據
POST   /api/v1/metadata                      # 創建元數據條目
PUT    /api/v1/metadata/{id}                 # 更新元數據條目
DELETE /api/v1/metadata/{id}                 # 刪除元數據條目

# 血緣圖 API
GET    /api/v1/lineage/{dataset}             # 獲取數據集血緣
POST   /api/v1/lineage                       # 創建血緣關係
GET    /api/v1/lineage/{dataset}/impact      # 影響分析

# 溯源記錄 API
GET    /api/v1/provenance/{resource}         # 獲取資源溯源
POST   /api/v1/provenance                    # 記錄溯源信息

# 知識圖譜 API
GET    /api/v1/knowledge/graph               # 獲取知識圖譜
GET    /api/v1/knowledge/health              # 獲取健康報告
POST   /api/v1/knowledge/diagnose            # 觸發診斷
```

## 配置整合 (Configuration Integration)

### 統一配置文件

元數據管理中心使用統一配置文件與其他組件集成：

```yaml
# 位置: config/metadata.yaml
apiVersion: config.machinenativeops.io/v1
kind: UnifiedMetadataConfig

metadata:
  name: metadata-management-config

spec:
  # 集成 61-lineage
  lineage:
    enabled: true
    dimension_ref: "61-lineage"
    
  # 集成 62-provenance
  provenance:
    enabled: true
    dimension_ref: "62-provenance"
  
  # 集成 07-audit
  audit:
    enabled: true
    dimension_ref: "07-audit"
    log_all_operations: true
  
  # 集成 24-registry
  registry:
    enabled: true
    dimension_ref: "24-registry"
    auto_register: true
```

## 事件整合 (Event Integration)

### 事件發佈

99-元數據管理中心發佈以下事件：

```yaml
events:
  # 元數據生命周期事件
  - metadata.created
  - metadata.updated
  - metadata.deleted
  - metadata.validated
  
  # 血緣事件
  - lineage.discovered
  - lineage.updated
  - lineage.broken
  
  # 溯源事件
  - provenance.recorded
  - provenance.verified
  
  # 知識庫事件
  - knowledge.updated
  - knowledge.diagnosed
  - health.degraded
  - health.restored
```

### 事件訂閱

99-元數據管理中心訂閱以下事件：

```yaml
subscriptions:
  # Git 事件
  - git.commit.pushed
  - git.branch.created
  - git.tag.created
  
  # CI/CD 事件
  - workflow.started
  - workflow.completed
  - workflow.failed
  
  # 部署事件
  - deployment.started
  - deployment.completed
  - deployment.rolled_back
```

## 監控整合 (Monitoring Integration)

### Prometheus 指標

```prometheus
# 元數據指標
metadata_entries_total{classification="technical|business|operational|governance"}
metadata_coverage_ratio{source="kubernetes|database|filesystem"}
metadata_quality_score{dimension="completeness|accuracy|consistency"}

# 血緣指標
lineage_completeness_ratio{dataset="*"}
lineage_depth{dataset="*"}

# 知識庫指標
knowledge_health_score
orphan_components_count
dead_configs_count
broken_links_count
```

### Grafana 儀表板

推薦的 Grafana 儀表板配置：

- **元數據概覽**: 總體統計和趨勢
- **血緣可視化**: 血緣圖和影響分析
- **知識庫健康**: 健康得分和診斷結果
- **溯源追踪**: 溯源鏈和完整性檢查

## 工作流整合 (Workflow Integration)

### GitHub Actions 工作流

建議的 CI/CD 整合：

```yaml
# .github/workflows/metadata-update.yml
name: Metadata Management Update

on:
  push:
    branches: [main, develop]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  update-metadata:
    runs-on: ubuntu-latest
    steps:
      - name: Collect Metadata
        run: |
          python knowledge/runtime/build_mndoc.py
          python knowledge/runtime/build_knowledge_graph.py
      
      - name: Diagnose Health
        run: |
          python knowledge/runtime/diagnose_health.py
      
      - name: Update Dashboard
        run: |
          python knowledge/pipelines/update_knowledge_layer.py
```

## 安全整合 (Security Integration)

### 權限控制

元數據管理中心遵循 RBAC 權限模型：

```yaml
roles:
  - name: metadata-admin
    permissions:
      - metadata:*
      - lineage:*
      - provenance:*
  
  - name: metadata-reader
    permissions:
      - metadata:read
      - lineage:read
      - provenance:read
  
  - name: metadata-writer
    permissions:
      - metadata:create
      - metadata:update
      - lineage:create
```

### 敏感數據處理

PII 和敏感數據的特殊處理：

1. 自動識別和標記敏感數據
2. 強制要求數據所有者
3. 記錄所有訪問和操作
4. 遵循 GDPR/CCPA 合規要求

## 故障排除 (Troubleshooting)

### 常見問題

1. **元數據收集失敗**
   - 檢查數據源連接
   - 驗證權限配置
   - 查看審計日誌

2. **血緣追踪不完整**
   - 增加追踪深度
   - 啟用自動發現
   - 手動補充血緣關係

3. **知識庫診斷問題**
   - 確保建模層正確執行
   - 檢查診斷規則配置
   - 查看診斷輸出日誌

## 未來擴展 (Future Extensions)

計劃中的整合功能：

1. **ML 模型元數據**: 與 ML 平台整合
2. **實時流處理**: 與 Kafka/Flink 整合
3. **多雲支持**: AWS/Azure/GCP 元數據收集
4. **增強分析**: AI 驅動的異常檢測

---

**版本**: 1.0.0  
**最後更新**: 2025-12-19  
**維護者**: governance-bot
