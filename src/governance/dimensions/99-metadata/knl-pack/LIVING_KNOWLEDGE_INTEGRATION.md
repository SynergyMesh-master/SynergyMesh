# 活體知識庫與 DAR-First 整合 (Living Knowledge Base Integration with DAR-First)

## 概述

本文檔說明如何將現有的**活體知識庫（Living Knowledge Base）**完整整合進 **DAR-First 架構**，實現「倉庫一有變動，立刻同步更新知識圖譜和相關內容」的核心特色。

---

## 🎯 整合目標

1. **保留現有功能**：維持活體知識庫的四層架構（感知 → 建模 → 診斷 → 回饋）
2. **DAR-First 增強**：用治理優先的方式組織和執行知識更新
3. **自動同步機制**：倉庫變動自動觸發知識重建和相關內容更新
4. **完整紀錄**：每次變動都儲存完整記錄，包含變動內容、相關內容、高度相關內容

---

## 📁 活體知識庫原有組件

### 現有工具鏈

位於 `tools/docs/`：

1. **`generate_mndoc_from_readme.py`**
   - 從 README.md 提取結構化信息
   - 生成 `docs/generated/generated-mndoc.yaml`
   - 系統「說明書」

2. **`generate_knowledge_graph.py`**
   - 掃描倉庫結構
   - 建立節點（系統、子系統、元件、設定、文件、工作流）
   - 建立關係（隸屬、依賴、覆蓋、連結）
   - 生成 `docs/generated/knowledge-graph.yaml`

3. **`project_to_superroot.py`**
   - 將知識圖譜投影到 SuperRoot ontology
   - 生成 `docs/generated/superroot-entities.yaml`
   - 提供 Component、ConfigParam 等實體

### 執行方式

通過 `Makefile` 目標：

```bash
# 單獨生成
make mndoc          # 生成 MN-DOC
make kg             # 生成知識圖譜（依賴 mndoc）
make superroot      # 投影到 SuperRoot（依賴 kg）

# 一次性生成所有
make all-kg         # 執行 mndoc + kg + superroot
```

---

## 🔗 整合架構

### 整合映射表

| 活體知識庫層次 | DAR-First 層級 | 整合方式 |
|---------------|---------------|---------|
| **感知層** (Perception) | **Layer 5: Automation** | 事件驅動：Git push, workflow 完成 → 觸發同步任務 |
| **建模層** (Modeling) | **Layer 2: Reasoning** + **Layer 4: Artifacts** | 執行 `make all-kg` → 產物存入 artifacts/ |
| **診斷層** (Self-diagnosis) | **Layer 2: Reasoning** | DAR.diagnose() 基於知識圖譜檢查問題 |
| **回饋層** (Feedback) | **Layer 5: Automation** + **Layer 1: Governance** | 記錄到 trust-chain、更新治理索引、通知 |

### 整合後的數據流

```
1. 倉庫變動（Git Push / PR Merge）
   ↓
2. 事件觸發（automation/events.yaml: git.push）
   ↓
3. 執行 sync-knowledge 任務（reasoning/tasks/sync-knowledge.yaml）
   ├── 3.1 偵測變動（git diff analysis）
   ├── 3.2 分類變動（governance / schema / code / docs）
   ├── 3.3 重新生成知識圖譜（make all-kg）
   │   ├── generated-mndoc.yaml
   │   ├── knowledge-graph.yaml
   │   └── superroot-entities.yaml
   ├── 3.4 向量搜尋找到相關內容（vector_search）
   │   ├── 相關 artifacts（similarity > 0.7）
   │   └── 高度相關內容（similarity > 0.85）
   ├── 3.5 影響分析（impact_analysis）
   │   ├── 哪些 artifacts 受影響
   │   ├── 依賴關係變化
   │   └── 斷掉的引用
   ├── 3.6 更新治理索引（governance/index.json）
   ├── 3.7 更新治理 DAG（governance/dag.graphml）
   ├── 3.8 更新向量索引（retrieval/vector-index/）
   └── 3.9 儲存完整記錄（state/change-records/change-{sha}.yaml）
   ↓
4. 記錄到證據鏈（governance/trust-chain.json）
   ↓
5. 通知（如有問題，創建 GitHub Issue）
```

---

## 📝 核心任務：sync-knowledge

位於 `reasoning/tasks/sync-knowledge.yaml`

### 特色功能：完整紀錄

每次倉庫變動都會產生一個完整的變動記錄，存放在 `state/change-records/change-{commit_sha}.yaml`：

```yaml
commit:
  sha: "abc123..."
  author: "developer@example.com"
  timestamp: "2025-12-19T03:00:00Z"
  message: "Add new governance policy"

changes:
  - file: "governance/policies/new-policy.yaml"
    type: "added"
    category: "governance"
    lines_added: 50

impact:
  affected_artifacts: 5
  new_artifacts: 1
  modified_artifacts: 3
  deleted_artifacts: 0

related:
  - id: "policy:naming-convention"
    similarity: 0.82
    reason: "Similar policy structure"
  - id: "schema:governance-base"
    similarity: 0.75
    reason: "Referenced in policy"

highly_related:
  - id: "policy:metadata-completeness"
    similarity: 0.91
    reason: "Very similar governance patterns"

broken_refs: []

knowledge_artifacts:
  mndoc: { status: "success", path: "docs/generated/generated-mndoc.yaml" }
  knowledge_graph: { status: "success", path: "docs/generated/knowledge-graph.yaml" }
  superroot: { status: "success", path: "docs/generated/superroot-entities.yaml" }

governance_updates:
  index: { status: "updated", artifacts_added: 1 }
  dag: { status: "updated", edges_added: 2 }
  vectors: { status: "updated", embeddings_created: 3 }
```

### 查詢變動記錄

```bash
# 查看最近的變動
ls -lt knl-pack/state/change-records/ | head -5

# 查看特定 commit 的完整記錄
cat knl-pack/state/change-records/change-abc123.yaml

# 查詢某個 artifact 的所有相關變動
grep -r "artifact-id" knl-pack/state/change-records/
```

---

## 🔄 自動同步機制

### 觸發器配置

在 `automation/events.yaml` 中已定義：

```yaml
event_handlers:
  - event: "git.push"
    triggers:
      - task: "sync-knowledge"
        delay: "immediate"
        priority: "high"
  
  - event: "ci.pr_merged"
    triggers:
      - task: "sync-knowledge"
        delay: "immediate"
        priority: "high"
  
  - event: "scheduled.knowledge_sync"
    schedule: "0 */6 * * *"  # Every 6 hours
    triggers:
      - task: "sync-knowledge"
        priority: "low"
```

### 實現方式

#### GitHub Actions Workflow

創建 `.github/workflows/knowledge-sync.yml`：

```yaml
name: Knowledge Base Auto Sync

on:
  push:
    branches: [ main, develop ]
  pull_request:
    types: [ closed ]
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours

jobs:
  sync-knowledge:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 2  # Need previous commit for diff
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install pyyaml
      
      - name: Run Knowledge Sync
        run: |
          # 執行 sync-knowledge 任務
          # 這會調用 make all-kg 和相關分析
          python knl-pack/reasoning/tasks/run_sync_knowledge.py
      
      - name: Commit updated artifacts
        if: github.event_name != 'pull_request'
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add docs/generated/ knl-pack/governance/ knl-pack/state/
          git commit -m "chore: Auto-sync knowledge base [skip ci]" || echo "No changes"
          git push
```

#### 本地鉤子（Git Hooks）

創建 `.git/hooks/post-commit`：

```bash
#!/bin/bash
# Auto-sync knowledge base after commit

echo "🔄 Syncing knowledge base..."
make all-kg

# 可選：如果有 Python 環境，執行完整同步
if command -v python3 &> /dev/null; then
    python3 knl-pack/reasoning/tasks/run_sync_knowledge.py --local
fi

echo "✅ Knowledge base synced"
```

---

## 📊 向量搜尋與相關內容

### 向量索引結構

`retrieval/vector-index/` 包含三個維度：

```
vector-index/
├── content-vectors.db          # 內容向量（文件、註解、說明）
├── structure-vectors.db        # 結構向量（schema、DAG、依賴）
└── governance-vectors.db       # 治理向量（policy、tag、owner）
```

### 相關內容查詢

當倉庫變動時，`sync-knowledge` 任務會自動查詢：

1. **相關 Artifacts**（similarity > 0.7）
   - 使用 content + structure 向量
   - 找出語意相似或結構相似的資源
   - 例如：新增一個 schema，找出相似的 schema

2. **高度相關內容**（similarity > 0.85）
   - 更嚴格的相似度閾值
   - 通常是同類型、同模式的資源
   - 例如：新增命名規範 policy，找出其他命名相關 policy

3. **影響範圍**（dependency traversal）
   - 基於治理 DAG 追蹤依賴
   - 找出會被影響的下游資源
   - 例如：修改 base schema，找出所有依賴它的 schema

### 示例查詢結果

```yaml
# 當添加 governance/policies/api-versioning.yaml 時

related_artifacts:
  - id: "policy:naming-convention"
    similarity: 0.78
    type: "policy"
    reason: "Similar policy structure and governance patterns"
  
  - id: "schema:api-base"
    similarity: 0.72
    type: "schema"
    reason: "Referenced in policy, structural dependency"

highly_related:
  - id: "policy:breaking-changes"
    similarity: 0.89
    type: "policy"
    reason: "Very similar API governance approach"
```

---

## 🎓 使用場景

### 場景 1：開發者提交新的 Schema

```
1. 開發者提交：governance/schemas/user-profile.yaml
   ↓
2. Git push 觸發 sync-knowledge
   ↓
3. 系統自動：
   ✅ 重新生成知識圖譜（加入 user-profile schema 節點）
   ✅ 找到相關 schemas（例如：user-base, profile-metadata）
   ✅ 找到高度相關內容（例如：類似的用戶資料 schema）
   ✅ 檢查是否違反命名規範
   ✅ 更新治理索引和 DAG
   ✅ 儲存完整變動記錄
   ↓
4. 如有問題（例如命名不一致），自動創建 Issue
```

### 場景 2：CI/CD Workflow 失敗

```
1. GitHub Actions workflow 失敗
   ↓
2. workflow.completed 事件觸發
   ↓
3. sync-knowledge 記錄失敗事件
   ✅ 找到相關的 workflows（類似配置或依賴）
   ✅ 找到高度相關內容（可能導致失敗的變更）
   ✅ 更新知識圖譜（標記 workflow 狀態）
   ↓
4. 生成診斷報告，通知相關負責人
```

### 場景 3：定期健康檢查

```
1. 每 6 小時排程觸發
   ↓
2. 完整掃描倉庫，重新生成所有知識圖譜
   ↓
3. 診斷層檢查：
   ✅ 孤兒元件
   ✅ 死設定
   ✅ 重疊工作流
   ✅ 斷鏈文件
   ↓
4. 更新健康報告和儀表板
```

---

## 🔧 實現步驟

### 第一步：基礎整合（已完成）

- ✅ 創建 `sync-knowledge.yaml` 任務定義
- ✅ 定義事件觸發器（`automation/events.yaml`）
- ✅ 規劃數據流和存儲結構

### 第二步：連接現有工具（進行中）

- [ ] 創建 Python 執行器 `run_sync_knowledge.py`
- [ ] 整合 `make all-kg` 到任務流程
- [ ] 實現向量搜尋功能

### 第三步：自動化部署（待完成）

- [ ] 創建 GitHub Actions workflow
- [ ] 設置 Git hooks（可選）
- [ ] 配置權限和認證

### 第四步：監控和優化（待完成）

- [ ] 添加性能監控
- [ ] 優化向量搜尋速度
- [ ] 增加快取機制

---

## 📈 預期效果

### 核心特色實現

✅ **即時同步**：倉庫變動 < 3 分鐘內完成知識庫更新  
✅ **完整紀錄**：每次變動都有完整記錄，可追溯可查詢  
✅ **智能關聯**：自動找到相關和高度相關內容  
✅ **影響分析**：清楚知道每次變動影響哪些資源  
✅ **自動診斷**：檢測問題並主動通知

### 對比傳統方式

| 特性 | 傳統手動更新 | 活體知識庫 + DAR-First |
|------|-------------|----------------------|
| 更新時機 | 手動執行 | 自動觸發（< 3 分鐘） |
| 相關內容 | 手動搜尋 | 自動找到（向量搜尋） |
| 影響範圍 | 手動分析 | 自動分析（DAG 追蹤） |
| 記錄保存 | 散落各處 | 統一儲存，可查詢 |
| 問題檢測 | 定期手動檢查 | 即時自動診斷 |

---

## 🔗 相關文檔

- [活體知識庫原始文檔](../../../docs/LIVING_KNOWLEDGE_BASE.md)
- [DAR-First 架構](./DAR_FIRST_ARCHITECTURE.md)
- [自動化層配置](./automation/events.yaml)
- [推理任務定義](./reasoning/tasks/)

---

**版本**: 1.0.0  
**最後更新**: 2025-12-19  
**維護者**: governance-bot  
**狀態**: 🟢 Ready for Implementation
