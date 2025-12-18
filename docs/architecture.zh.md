# SynergyMesh 架構總覽

## 🏗️ 系統架構

### 整體架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                      SynergyMesh Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  MCP Servers │  │  Contracts   │  │   Advanced   │    │
│  │              │  │   Service    │  │    System    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│         │                 │                   │            │
│         └─────────────────┴───────────────────┘            │
│                           │                                │
│              ┌────────────┴────────────┐                   │
│              │  Governance Layer       │                   │
│              │  - Policies             │                   │
│              │  - Registry             │                   │
│              │  - SBOM/Provenance      │                   │
│              └─────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Monorepo 結構

### 子專案組織

```
synergymesh/
├── mcp-servers/              # Model Context Protocol 服務器
│   ├── code-analyzer.js      # 代碼分析器
│   ├── doc-generator.js      # 文檔生成器
│   ├── security-scanner.js   # 安全掃描器
│   └── slsa-validator.js     # SLSA 驗證器
│
├── core/contract_service/           # 核心契約服務
│   └── contracts-L1/
│       └── contracts/        # L1 契約管理
│           ├── src/
│           │   ├── server.ts
│           │   ├── controllers/
│           │   └── middleware/
│           └── package.json
│
├── advanced-system-src/      # 前端儀表板
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/
│   │   └── components/
│   └── package.json
│
└── governance/              # 治理配置
    ├── registry.yaml         # 模組註冊表
    └── policies.yaml         # 基線政策
```

## 🔄 資料與控制流

### CI/CD 流程

```
1. 開發者推送代碼
   ↓
2. Monorepo Dispatcher 檢測變更
   ↓
3. 僅觸發受影響子專案的 CI
   ↓
4. 可重用 CI Pipeline 執行：
   - Lint
   - Type Check
   - Unit Tests
   - Build
   - SBOM 生成
   - Security Scan
   ↓
5. 政策驗證（Conftest + Language Check）
   ↓
6. 通過後準備部署
```

### 治理流程

```
Pull Request
   ↓
┌──────────────────────────────┐
│  自動檢查                    │
│  ✓ Conftest 命名政策         │
│  ✓ 語言合規性                │
│  ✓ 安全掃描                  │
│  ✓ 測試覆蓋率                │
└──────────────────────────────┘
   ↓
┌──────────────────────────────┐
│  審查門檻                    │
│  • 1+ 審查者批准             │
│  • 所有 CI 通過              │
│  • 無嚴重漏洞                │
└──────────────────────────────┘
   ↓
自動合併（條件符合時）
```

## 🛡️ 治理鉤子

### 政策執行點

1. **PR 階段**
   - Conftest 驗證 Kubernetes manifests
   - 語言合規性檢查
   - 命名規範驗證

2. **CI 階段**
   - 依賴掃描
   - SBOM 生成
   - 安全漏洞檢查

3. **CD 階段**
   - 映像簽名驗證
   - SLSA Provenance 檢查
   - 部署前政策模擬

## 🔐 供應鏈安全

### SLSA 框架整合

```
Level 0: 無保證
   ↓
Level 1: 文檔化建置過程
   ✓ SBOM 生成
   ✓ 依賴記錄
   ↓
Level 2: 可驗證的建置
   ✓ 建置服務認證
   ✓ 簽名綁定
   ↓
Level 3: 防篡改建置
   ✓ Cosign 簽名
   ✓ Provenance attestation
```

### 安全檢查點

- **依賴管理**: npm audit, Dependabot
- **映像掃描**: Trivy, Grype（計劃中）
- **政策驗證**: Conftest, OPA
- **簽名驗證**: Cosign, Sigstore

## 🎯 關鍵組件

### 1. 可重用 CI Pipeline

**位置**: `.github/workflows/reusable-ci.yml`

**功能**:

- 參數化設計，支援不同子專案
- 自動檢測專案類型
- 條件執行（僅在相關文件存在時執行）
- SBOM 生成與安全掃描

### 2. Monorepo Dispatcher

**位置**: `.github/workflows/monorepo-dispatch.yml`

**功能**:

- 使用 `paths-filter` 檢測變更
- 矩陣策略並行執行
- 僅觸發受影響的子專案
- 彙總報告

### 3. 治理註冊表

**位置**: `governance/registry.yaml`

**功能**:

- 記錄所有模組元數據
- 定義依賴關係
- SLA 指標追蹤
- 遷移鉤子配置

### 4. 政策引擎

**位置**: `governance/policies/conftest/`

**功能**:

- Kubernetes 資源驗證
- 命名規範執行
- 安全基線檢查

## 📊 可觀測性（規劃中）

### 指標收集

- 建置時間
- 測試覆蓋率
- 部署頻率
- 政策違規率

### 告警規則

- 命名違規
- 安全漏洞
- 性能降級
- 可用性下降

## 🚀 部署策略

### 目前狀態

- ✅ CI/CD Pipeline 建立
- ✅ 政策驗證框架
- ✅ Monorepo 管理
- 🔄 Kubernetes 部署（進行中）
- 📝 可觀測性（計劃中）

### 未來規劃

1. **自動化部署**: ArgoCD 或 Flux CD 整合
2. **Canary 部署**: 漸進式推出策略
3. **自動回滾**: 基於指標的回滾
4. **策略影響分析**: Canary 階段政策模擬

## 📝 治理與合規

### 命名規範

- **Namespace**: `team-*`, `tenant-*`, `feature-*`
- **Service**: Kubernetes DNS 相容命名
- **資源**: 最大 63 字元
- **標籤**: 必須包含 `namespace.io/*` 標籤

### 審查流程

1. 自動檢查（CI）
2. 政策驗證（Conftest）
3. 人工審查（1+ 審查者）
4. 自動合併（符合條件時）

### 文檔要求

- 所有文檔優先使用繁體中文
- 技術術語保留英文並加註解
- README 必須包含架構說明
- API 文檔必須完整

## 🔗 相關文檔

- [快速開始](../QUICK_START.md)
- [貢獻指南](../CONTRIBUTING.md)
- [安全政策](../SECURITY.md)
- [治理政策](governance/policies.yaml)
- [模組註冊表](governance/registry.yaml)
