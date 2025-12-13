## {{ emoji }} 自動 PR 審核報告

**PR 編號**：#{{ pr_number }}
**分支**：{{ source_branch }} → {{ target_branch }}
**審核時間**：{{ timestamp }}

---

### {{ status_emoji }} 審核結果：{{ review_status }}

{{ #if issues_found }}
### {{ warning_emoji }} 發現問題（{{ issues_count }} 項）

| 類型 | 檔案 | 行號 | 描述 |
|------|------|------|------|
{{ #each issues }}
| {{ this.type }} | `{{ this.file }}` | {{ this.line }} | {{ this.description }} |
{{ /each }}

{{ /if }}

{{ #if recommendations }}
### {{ suggestion_emoji }} 改善建議

{{ #each recommendations }}
- **{{ this.category }}**：{{ this.suggestion }}
{{ /each }}
{{ /if }}

---

### {{ check_emoji }} 自動檢查結果

| 檢查項目 | 狀態 |
|----------|------|
{{ #each checks }}
| {{ this.name }} | {{ this.status }} |
{{ /each }}

---

### {{ action_emoji }} 下一步行動

{{ #if requires_changes }}
請根據上述問題進行修改，然後重新提交。

**快速修復命令**：
```bash
{{ #each quick_fixes }}
{{ this }}
{{ /each }}
```
{{ else }}
此 PR 已通過自動審核，可以進行人工審核。
{{ /if }}

---

### {{ governance_emoji }} 治理追蹤

- **維度**：81-auto-comment
- **策略**：POL-81-001 (Comment Generation)
- **事件 ID**：`{{ event_id }}`

<sub>
此評論由 **Auto-Comment Engine** 自動生成
符合 NIST-AI-RMF、ISO-42001 治理框架
</sub>
