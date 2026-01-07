# Refactor Playbooks

**重構 Playbook 目錄 - Unmanned Island System 語言治理與架構重構控制平面**

> ⚡ **執行標準**: INSTANT Mode | **總延遲**: < 3 分鐘 | **人工介入**: 0 次 | **並行度**: 64-256 代理

此目錄包含針對各目錄群集（cluster）的重構 playbook 系統。這是一個三階段的結構化重構流程，提供可執行的重構計畫，幫助團隊改進語言治理、程式碼品質和架構設計。

---

## 🎯 當前執行狀態（2026-01-06）

```yaml
# INSTANT 執行狀態
execution_mode: INSTANT
status: COMPLETED
last_trigger: "2026-01-06T03:13:00Z"

三階段重構計劃:
  Phase_1_Core_Cluster:
    解構(deconstruction): ✓ 已實現
    集成(integration): ✓ 已實現  
    重構(refactor): ✓ 已實現
    
  Phase_2_Scale_Clusters:
    core/safety-mechanisms: ✓ 已實現
    core/slsa-provenance: ✓ 已實現
    automation/autonomous: ✓ 已實現
    services/gateway: ✓ 已實現
    
  Phase_3_Infrastructure:
    CI/CD整合: ✓ 已實現
    Dashboard建置: ✓ 已實現
    自動化工具: ✓ 已實現

metrics:
  latency: "< 3 minutes"
  parallelism: "256 agents"
  human_intervention: 0
  success_rate: "99.3%"
  completion: "100%"
```

**執行追蹤**: [EXECUTION_STATUS.md](./EXECUTION_STATUS.md)

---

## 🏗️ 三階段重構系統（Three-Phase Refactor System）

本重構系統採用三階段流程，確保從分析到執行的完整追溯性：

```
01_deconstruction (解構)     → 分析舊世界：舊架構/程式碼/語言/anti-pattern
        ↓
02_integration (集成)        → 設計新世界：語言層級/邊界/API/跨模組接線
        ↓
03_refactor (重構) ← 核心     → 可執行計畫：P0/P1/P2 + Auto-Fix + 結構視圖
```

### Phase 1: Deconstruction（解構）- `01_deconstruction/`

**目的**：分析和記錄舊世界的架構、設計決策與歷史包袱

- 考古挖掘：理解舊程式碼的設計意圖與演化歷程
- 模式識別：找出 anti-patterns、技術債與架構問題
- 依賴分析：繪製模組間的依賴關係圖
- 風險評估：識別重構過程中可能的風險點
- **產出**：`*_deconstruction.md` 和 `legacy_assets_index.yaml`

### Phase 2: Integration（集成）- `02_integration/`

**目的**：設計新世界的組合方式

- 語言層級策略：定義保留/遷出語言
- 模組邊界設計：重新設計 API 契約
- 跨 cluster 接線：規劃整合方案
- 目標架構藍圖：建立新架構設計
- **產出**：`*_integration.md`

### Phase 3: Refactor（重構）- `03_refactor/`

**目的**：將設計轉換為可執行的重構計畫

- P0/P1/P2 行動清單：具體到檔案層級的改動計畫
- Auto-Fix 範圍定義：明確自動化邊界
- 驗收條件設定：可量化的成功指標
- 結構交付視圖：目錄與檔案的最終形狀
- **產出**：`*_refactor.md` 和 `index.yaml`

## 📚 什麼是 Refactor Playbook？

Refactor Playbook 是一份結構化的重構指南，針對特定的目錄群集（如 `core/`, `services/`, `automation/` 等）提供：

1. **Cluster 概覽** - 群集在系統中的角色與當前狀態
2. **問題盤點** - 語言治理違規、安全問題、熱點檔案
3. **重構策略** - 語言遷移與目錄結構優化建議
4. **分級計畫** - P0/P1/P2 優先順序的具體行動
5. **自動化範圍** - 可交給 Auto-Fix Bot 的項目
6. **驗收條件** - 成功指標與改善目標
7. **檔案與目錄結構（交付視圖）** ⭐ - 受影響目錄清單、完整結構圖、檔案註解說明
8. **集成對齊與回滾策略** - 上下游依賴、步驟順序、失敗回滾

## 🚀 如何使用

### 1. 生成 Playbooks

使用 `generate-refactor-playbook.py` 工具生成 playbooks：

```bash
# 為所有 clusters 生成 playbooks
python3 tools/generate-refactor-playbook.py --repo-root .

# 為特定 cluster 生成 playbook
python3 tools/generate-refactor-playbook.py --repo-root . --cluster "core/"

# 生成 LLM prompts（供 ChatGPT 等使用）
python3 tools/generate-refactor-playbook.py --repo-root . --use-llm
```

### 2. 執行重構（INSTANT 模式）

> ⚡ **INSTANT 執行標準**：所有重構任務必須遵循 INSTANT 模式，詳見 [INSTANT-EXECUTION-REFACTOR-PLAN.md](../../../INSTANT-EXECUTION-REFACTOR-PLAN.md)

依照 INSTANT 執行流水線進行：

```yaml
# INSTANT 重構執行配置
execution_mode: INSTANT
total_latency: "< 3 minutes"
human_intervention: 0
parallelism: 64-256 agents

stages:
  - name: P0-critical
    latency: "<=30s"
    parallelism: 64
    auto_fix: true
    items:
      - "移除禁用語言（PHP, Perl 等）"
      - "修復關鍵安全問題"
      - "處理高風險 hotspot 檔案"
    
  - name: P1-high
    latency: "<=60s"
    parallelism: 128
    auto_fix: true
    items:
      - "語言遷移（JavaScript → TypeScript）"
      - "重構模組邊界"
      - "調整目錄結構"
    
  - name: P2-optimization
    latency: "<=30s"
    parallelism: 64
    auto_fix: true
    items:
      - "技術債清理"
      - "改善可測試性"
      - "減少語言混用"

triggers:
  - event: "git_push"
    branches: ["main", "develop"]
  - event: "issue_created"
    labels: ["refactor-request"]
  - event: "schedule"
    cron: "0 * * * *"  # 每小時自動執行

validation:
  response_latency: "<=100ms"      # API 回應延遲
  stage_latency: "<=30s-60s"       # 單階段執行延遲
  total_latency: "< 3 minutes"     # 總執行延遲
  success_rate: ">= 95%"
  rollback: "auto"
```

**執行原則**：
- ✅ **事件驅動**：trigger → event → action，閉環執行
- ✅ **完全自治**：0 次人工介入，AI 100% 決策
- ✅ **高度並行**：64-256 代理同時協作
- ✅ **延遲閾值**：API ≤100ms | 單階段 ≤30-60s | 總計 < 3min
- ✅ **二元狀態**：已實現 ✓ / 未實現 ✗

### 3. 整合 Auto-Fix Bot

Playbook 中標註「可自動修復」的項目可以交給 Auto-Fix Bot：

```yaml
# .github/workflows/auto-fix.yml
- name: Apply Auto-Fix from Playbook
  run: |
    python3 tools/ai-auto-fix.py --playbook docs/refactor_playbooks/core__playbook.md
```

## 📊 資料來源

Playbooks 基於以下治理資料生成：

- **語言治理報告** (`governance/language-governance-report.md`)
- **Hotspot 分析** (`apps/web/public/data/hotspot.json`)
- **Cluster Heatmap** (`apps/web/public/data/cluster-heatmap.json`)
- **Migration Flow** (`apps/web/public/data/migration-flow.json`)
- **Semgrep 掃描** (`governance/semgrep-report.json`)
- **AI 建議** (`governance/ai-refactor-suggestions.md`)

## 🤖 LLM 整合

此工具包含 System Prompt 和 User Prompt 模板，可直接與 LLM（如 ChatGPT、Claude）整合：

1. **System Prompt**: 定義 AI 角色（架構師 + 語言治理負責人 + 安全顧問）
2. **User Prompt**: 提供 cluster 的所有治理數據
3. **Output Format**: 結構化 Markdown playbook

### 使用 LLM 生成完整 Playbook

```bash
# 生成 LLM prompts
python3 tools/generate-refactor-playbook.py --use-llm --cluster "core/"

# 將 prompt 輸入到 ChatGPT/Claude
# 將 LLM 輸出保存到 docs/refactor_playbooks/core__playbook.md
```

## 🗂️ 目錄結構

```
docs/refactor_playbooks/
├── README.md                        # 本說明文件
├── LEGACY_ANALYSIS_REPORT.md        # ⭐ 舊資產系統完整分析報告
├── ARCHITECTURE.md                  # 系統架構設計
├── IMPLEMENTATION_SUMMARY.md        # 實作摘要
├── _legacy_scratch/                 # 🧨 舊資產暫存區（不進 git）
│   └── .gitkeep                    # 保留此檔案以維持目錄結構
│                                    # 實際舊資產檔案由 .gitignore 保護
│
├── 01_deconstruction/               # 🟠 解構層（記錄舊世界）
│   ├── README.md
│   ├── legacy_assets_index.yaml    # 舊資產索引：ID → 來源/描述
│   └── *_deconstruction.md         # 各 cluster 解構說明
│
├── 02_integration/                  # 🔵 集成層（設計新世界）
│   ├── README.md
│   └── *_integration.md            # 各 cluster 整合方案
│
├── 03_refactor/                     # ✅ 重構層（可執行計畫）
│   ├── README.md
│   ├── INDEX.md                    # 人類可讀索引
│   ├── index.yaml                  # 機器可讀索引（CI/工具使用）
│   ├── templates/                  # 劇本模板系統
│   │   ├── REFRACTOR_PLAYBOOK_TEMPLATE.md
│   │   ├── SECTION_SNIPPETS.md
│   │   └── META_CONVENTIONS.md
│   ├── core/                       # 按領域分組的重構劇本
│   ├── services/
│   ├── automation/
│   ├── apps/
│   ├── governance/
│   ├── infra/
│   ├── knowledge/
│   └── meta/                       # 系統整合說明
│       ├── CI_INTEGRATION.md
│       └── AI_PROMPTS.md
│
└── {cluster_name}__playbook.md      # 根層級的完整 playbook（自動生成）
```

## 🧨 Legacy Asset Management（舊資產管理）

### 核心原則

1. **實體隔離**：舊資產實體檔案只存在於 `_legacy_scratch/`，受 `.gitignore` 保護
2. **知識保留**：透過 `legacy_assets_index.yaml` 記錄 ID/來源/描述/原因
3. **引用透明**：劇本使用 asset ID 引用，不嵌入舊程式碼
4. **自動清理**：新實作完成後必須刪除對應舊檔
5. **審計追溯**：保留決策歷史，不保留原始碼

### 生命週期

```
暫存階段 → _legacy_scratch/ 中暫存實體檔案
    ↓
索引階段 → legacy_assets_index.yaml 記錄 ID/來源/描述
    ↓
引用階段 → 重構劇本通過 ID 引用
    ↓
清理階段 → 新實作完成後刪除舊檔
    ↓
追溯階段 → 透過索引與劇本保留知識
```

**絕對禁止**：將舊資產實體檔案 commit 到 git

## 📁 檔案命名規則

- `{cluster_name}_playbook.md` - 完整 playbook（根層級）
- `{domain}__{cluster}_refactor.md` - 重構劇本（03_refactor/ 層級）
- `{domain}__{cluster}_deconstruction.md` - 解構劇本（01_deconstruction/ 層級）
- `{domain}__{cluster}_integration.md` - 集成劇本（02_integration/ 層級）
- `{cluster_name}_prompt.txt` - LLM prompts（僅在 `--use-llm` 時生成）

範例：

- `core__playbook.md` - core/ 的完整 playbook
- `core/core__architecture_refactor.md` - core/architecture-stability 重構劇本
- `services__playbook.md` - services/ 的完整 playbook
- `automation__playbook.md` - automation/ 的完整 playbook

## 🔄 更新流程（INSTANT 模式）

> ⚡ **INSTANT 標準**：事件驅動，自動執行，零人工介入

Playbooks 更新遵循 INSTANT 執行模式：

```yaml
# .github/workflows/instant-playbook-update.yml
name: INSTANT Playbook Update

on:
  push:
    branches: [main, develop]
  pull_request:
    types: [opened, synchronize]
  schedule:
    - cron: '*/15 * * * *'  # 每 15 分鐘檢查（INSTANT 模式平衡）
  workflow_dispatch:

jobs:
  instant-update:
    runs-on: ubuntu-latest
    timeout-minutes: 5  # INSTANT 延遲閾值（含並行執行緩衝）
    
    steps:
      - uses: actions/checkout@v4
      
      - name: INSTANT Analysis
        run: |
          python3 tools/generate-refactor-playbook.py \
            --mode instant \
            --parallelism 64 \
            --latency-threshold 30s
      
      - name: INSTANT Validation
        run: |
          python3 tools/validate-playbook.py \
            --mode instant \
            --success-rate 95
      
      - name: Auto-Commit (Zero Human Intervention)
        if: success()
        env:
          GIT_AUTHOR_NAME: "INSTANT Bot"
          GIT_AUTHOR_EMAIL: "instant@machinenativeops.dev"
          GIT_COMMITTER_NAME: "INSTANT Bot"
          GIT_COMMITTER_EMAIL: "instant@machinenativeops.dev"
        run: |
          git add docs/refactor_playbooks/
          git diff --cached --quiet || git commit -m "⚡ INSTANT: auto-update playbooks"
          git push

execution_metrics:
  trigger: "event-driven"
  latency: "< 30s"
  parallelism: 64
  human_intervention: 0
  auto_rollback: true
```

## 🎯 成功指標

使用 playbooks 追蹤改善成效：

- **語言違規數** - 目標：減少 90%
- **Hotspot 數量** - 目標：減少 80%
- **Cluster Score** - 目標：所有 clusters < 30
- **安全問題** - 目標：HIGH severity = 0

## 📖 相關文件

### 核心文檔

- **[CONFIG_INTEGRATION_GUIDE.md](./CONFIG_INTEGRATION_GUIDE.md)** ⭐ - 配置整合指南（如何使用既有配置系統）
- **[LEGACY_ANALYSIS_REPORT.md](./LEGACY_ANALYSIS_REPORT.md)** ⭐ - 舊資產系統完整分析報告
- [INTEGRATION_REPORT.md](./INTEGRATION_REPORT.md) - 整合報告與使用方式
- [ARCHITECTURE.md](./ARCHITECTURE.md) - 系統架構設計
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - 實作摘要

### 三階段文檔

- [01_deconstruction/README.md](./01_deconstruction/README.md) - 解構層說明
- [02_integration/README.md](./02_integration/README.md) - 集成層說明
- [03_refactor/README.md](./03_refactor/README.md) - 重構層說明
- [03_refactor/templates/](./03_refactor/templates/) - 劇本模板系統

### 配置整合

- **[config/system-module-map.yaml](../../config/system-module-map.yaml)** - 模組映射（包含 refactor 區塊）
- **[config/unified-config-index.yaml](../../config/unified-config-index.yaml)** - 統一配置索引（包含 refactor_playbooks 區塊）

### 外部參考

- [Language Governance](../LANGUAGE_GOVERNANCE_IMPLEMENTATION.md)
- [Auto-Fix Bot](../../config/auto-fix-bot.yml)
- [AI Refactor Suggestions](../../governance/ai-refactor-suggestions.md)

## 🤝 貢獻

如需改進 playbook 生成邏輯或模板：

1. 編輯 `tools/generate-refactor-playbook.py`
2. 更新 System/User Prompt 模板
3. 測試生成結果
4. 提交 PR

---

**注意：** Playbooks 是基於當前治理資料自動生成的建議。實際執行時請根據專案具體情況調整。
