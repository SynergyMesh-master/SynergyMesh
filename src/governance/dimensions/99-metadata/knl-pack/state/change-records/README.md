# Change Records (變動記錄)

此目錄儲存倉庫每次變動的完整記錄。

## 記錄格式

每個記錄檔案格式：`change-{commit_sha}.yaml`

例如：`change-abc12345.yaml`

## 記錄內容

每個變動記錄包含：

```yaml
version: "1.0.0"
timestamp: "2025-12-19T03:00:00Z"

commit:
  commit_sha: "abc12345..."
  commit_author: "developer@example.com"
  commit_timestamp: "2025-12-19T02:55:00Z"
  commit_message: "Add new governance policy"

changes:
  files:
    - file: "governance/policies/new-policy.yaml"
      type: "added"
      category: "governance"
  count: 1
  summary: "1 file(s) changed"

knowledge_artifacts:
  status: "success"
  mndoc: "docs/generated/generated-mndoc.yaml"
  knowledge_graph: "docs/generated/knowledge-graph.yaml"
  superroot: "docs/generated/superroot-entities.yaml"

summary:
  files_changed: 1
  knowledge_status: "success"
```

## 使用方式

### 查看最近的變動

```bash
ls -lt | head -10
```

### 查看特定 commit 的記錄

```bash
cat change-abc12345.yaml
```

### 搜尋特定檔案的變動

```bash
grep -r "specific-file.yaml" .
```

### 統計變動次數

```bash
ls -1 | wc -l
```

## 自動生成

這些記錄由 `reasoning/tasks/sync-knowledge` 任務自動生成，無需手動維護。

## 保留期限

建議保留最近 90 天的變動記錄，舊記錄可定期歸檔或刪除。

---

**維護者**: governance-bot  
**自動生成**: Yes
