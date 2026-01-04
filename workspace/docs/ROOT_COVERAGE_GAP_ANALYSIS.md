# Root 系列覆蓋缺口分析報告

**日期**: 2026-01-04
**版本**: 1.0.0
**狀態**: 🔴 嚴重缺口已識別

---

## 執行摘要

經過深度分析，發現 `root.fs.map` 和 root 系列配置**嚴重未能覆蓋儲存庫的實際結構**。這違背了「Root Layer 作為單一真相來源」的設計承諾。

### 關鍵指標

| 指標 | 數值 | 狀態 |
|------|------|------|
| 儲存庫實際目錄數 | **339** | - |
| root.fs.map 總映射數 | 152 | - |
| 指向實際儲存庫的映射 | **16** | 🔴 |
| 指向理論安裝路徑的映射 | 136 | ⚠️ |
| **實際覆蓋率** | **4.7%** | 🔴 嚴重不足 |

---

## 問題核心

### 1. 映射類型錯位

`root.fs.map` 中的映射主要分為兩類：

**A. 實際儲存庫映射（僅 16 個）**：
```
controlplane_root:./controlplane
controlplane_baseline:./controlplane/baseline
controlplane_baseline_config:./controlplane/baseline/config
controlplane_baseline_specs:./controlplane/baseline/specifications
controlplane_baseline_registries:./controlplane/baseline/registries
controlplane_baseline_integration:./controlplane/baseline/integration
controlplane_baseline_validation:./controlplane/baseline/validation
controlplane_baseline_docs:./controlplane/baseline/documentation
controlplane_overlay:./controlplane/overlay
controlplane_overlay_config:./controlplane/overlay/config
controlplane_overlay_evidence:./controlplane/overlay/evidence
controlplane_overlay_runtime:./controlplane/overlay/runtime
controlplane_overlay_logs:./controlplane/overlay/logs
controlplane_active:./controlplane/active
chatops_root:./chatops
chatops_scripts:./chatops/scripts
```

**B. 理論安裝路徑映射（136 個）**：
```
mno_root:/opt/machinenativenops              # 不存在於儲存庫
mno_bin:/opt/machinenativenops/bin           # 不存在於儲存庫
mno_db_data:/var/lib/machinenativenops/db    # 不存在於儲存庫
...等 130+ 個類似映射
```

### 2. 設計與實現的斷層

root.config.yaml 聲稱：
```yaml
paths:
  baseline: "./controlplane/baseline"
  overlay: "./controlplane/overlay"
  active: "./controlplane/active"
  workspace: "./workspace"    # ← 只定義了根路徑
```

但 `workspace/` 下有 **28+ 主要子目錄**，全部未被細粒度治理。

---

## 未覆蓋的關鍵區域

### 🔴 完全未被映射的目錄（嚴重）

#### 1. `.github/` - GitHub 自動化層（21+ 目錄）
```
.github/
├── workflows/          # CI/CD 工作流 - 未治理
├── agents/             # AI 代理配置 - 未治理
├── policies/           # 安全策略 - 未治理
├── healing-knowledge/  # 自我修復知識庫 - 未治理
├── code-scanning/      # 代碼掃描配置 - 未治理
├── codeql/             # CodeQL 查詢 - 未治理
├── scripts/            # 自動化腳本 - 未治理
└── ... 14+ 更多目錄
```

#### 2. `workspace/src/` - 核心源代碼（28+ 模組）
```
workspace/src/
├── governance/         # 40+ 維度治理框架 - 未治理！
├── ai/                 # AI 模組 - 未治理
├── autonomous/         # 自主代理 - 未治理
├── core/               # 核心引擎 - 未治理
├── services/           # 微服務 - 未治理
├── enterprise/         # 企業功能 - 未治理
├── contracts/          # 合約定義 - 未治理
├── mcp-servers/        # MCP 伺服器 - 未治理
└── ... 20+ 更多模組
```

**諷刺的是**：`workspace/src/governance/` 包含 40+ 治理維度的實現，但治理框架本身卻未被 root 層治理！

#### 3. `workspace/config/` - 配置層（21+ 子目錄）
```
workspace/config/
├── agents/             # 代理配置 - 未治理
├── governance/         # 治理配置 - 未治理
├── security/           # 安全配置 - 未治理
├── monitoring/         # 監控配置 - 未治理
├── deployment/         # 部署配置 - 未治理
└── ... 16+ 更多目錄
```

#### 4. `chatops/` - ChatOps 單體倉庫（80+ 子目錄）
```
chatops/
├── apps/               # 應用程式 - 未治理
├── compliance/         # 合規配置 - 未治理
├── deploy/             # 部署配置 - 未治理
│   ├── kubernetes/
│   ├── terraform/
│   ├── helm/
│   └── argocd/
├── observability/      # 可觀測性 - 未治理
├── policies/           # OPA 策略 - 未治理
├── proto/              # Protocol Buffers - 未治理
├── services/           # 服務實現 - 未治理
├── supply-chain/       # 供應鏈安全 - 未治理
└── tests/              # 測試套件 - 未治理
```
**現狀**：只有 `chatops_root` 和 `chatops_scripts` 被映射（2/80+）

#### 5. 其他未覆蓋區域

| 目錄 | 子目錄數 | 覆蓋狀態 |
|------|---------|---------|
| `workspace/docs/` | 30+ | 🔴 未覆蓋 |
| `workspace/scripts/` | 14 | 🔴 未覆蓋 |
| `workspace/tools/` | 12 | 🔴 未覆蓋 |
| `workspace/tests/` | 5 | 🔴 未覆蓋 |
| `workspace/deploy/` | 6 | 🔴 未覆蓋 |
| `srv/` | 5 | 🔴 未覆蓋 |
| `web/` | 2 | 🔴 未覆蓋 |
| `docs/` | 1 | 🔴 未覆蓋 |

---

## 影響分析

### 1. 治理承諾未兌現

root 系列宣稱提供：
- ✅ Controlplane 層治理 - **已實現**
- ❌ 完整儲存庫治理 - **未實現**
- ❌ 工作區細粒度控制 - **未實現**
- ❌ ChatOps 完整映射 - **未實現**
- ❌ CI/CD 配置治理 - **未實現**

### 2. 安全風險

未被治理的區域包括：
- `.github/workflows/` - CI/CD 管道可被任意修改
- `workspace/config/security/` - 安全配置未受保護
- `chatops/policies/` - OPA 策略未納入治理
- `chatops/supply-chain/` - 供應鏈安全配置未受控

### 3. 一致性問題

- 命名規範只在 controlplane 強制執行
- 驗證系統只檢查 baseline 配置
- 模組註冊表未包含實際的 workspace 模組

---

## 根本原因

### 1. 設計焦點錯位

`root.fs.map` 被設計為「生產環境安裝映射」而非「儲存庫結構映射」：
- 136 個映射指向 `/opt/machinenativenops/`、`/var/lib/` 等
- 這些路徑在儲存庫中不存在
- 實際儲存庫結構被忽略

### 2. 增量開發未同步

- Controlplane 架構完善
- Workspace/ChatOps 大量擴展
- root.fs.map 未隨之更新

### 3. 缺乏自動同步機制

- 無工具自動檢測新目錄
- 無驗證確保映射完整性
- 無 CI 門禁檢查覆蓋率

---

## 建議改進方案

### 短期（立即）

1. **擴展 root.fs.map**：新增所有實際儲存庫目錄的映射
2. **分離關注點**：
   - `root.fs.map` - 儲存庫結構映射
   - `root.install.map` - 生產安裝路徑映射（新檔案）

### 中期（1-2 週）

3. **建立覆蓋驗證**：
   ```python
   # 驗證腳本：檢查所有目錄是否被映射
   def validate_coverage():
       actual_dirs = get_all_repo_dirs()
       mapped_dirs = parse_fs_map()
       unmapped = actual_dirs - mapped_dirs
       if unmapped:
           raise CoverageError(f"Unmapped directories: {unmapped}")
   ```

4. **更新驗證系統**：將覆蓋率檢查加入 5 階段驗證

### 長期（架構改進）

5. **動態映射生成**：基於目錄結構自動生成映射
6. **分層治理**：
   - Layer 0: FHS 系統目錄
   - Layer 1: Controlplane
   - Layer 2: Workspace 模組
   - Layer 3: ChatOps/CI
7. **模組自註冊**：新模組自動註冊到 root.registry

---

## 結論

`root.fs.map` 目前只是一個**理想化的生產安裝藍圖**，而非**儲存庫的實際治理映射**。要真正實現「Root Layer 觸及每一個角落」的願景，需要：

1. 將映射焦點從「理論安裝路徑」轉向「實際儲存庫結構」
2. 覆蓋所有 339 個目錄（目前僅 16 個）
3. 建立自動化機制確保同步

**當前覆蓋率**：4.7%
**目標覆蓋率**：100%

---

*報告生成者*: Claude Code 深度分析
*最後更新*: 2026-01-04
