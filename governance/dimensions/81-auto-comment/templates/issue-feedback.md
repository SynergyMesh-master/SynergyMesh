## {{ emoji }} 自動反饋：Issue #{{ issue_number }}

**反饋類型**：{{ feedback_type }}
**觸發來源**：{{ trigger_source }}
**時間戳**：{{ timestamp }}

---

### {{ status_emoji }} 狀態更新

{{ status_message }}

{{ #if details }}
### {{ detail_emoji }} 詳細資訊

{{ details }}
{{ /if }}

---

{{ #if related_items }}
### {{ link_emoji }} 相關項目

| 類型 | 編號 | 標題 | 狀態 |
|------|------|------|------|
{{ #each related_items }}
| {{ this.type }} | #{{ this.number }} | {{ this.title }} | {{ this.status }} |
{{ /each }}
{{ /if }}

---

{{ #if action_items }}
### {{ action_emoji }} 行動項目

{{ #each action_items }}
- [ ] {{ this }}
{{ /each }}
{{ /if }}

---

### {{ progress_emoji }} 進度追蹤

{{ #if progress }}
**當前進度**：{{ progress.current }}/{{ progress.total }} ({{ progress.percentage }}%)

{{ progress.description }}
{{ /if }}

---

### {{ metrics_emoji }} 相關指標

| 指標 | 值 |
|------|-----|
{{ #each metrics }}
| {{ this.name }} | {{ this.value }} |
{{ /each }}

---

### {{ governance_emoji }} 治理資訊

- **事件類型**：{{ event_type }}
- **事件 ID**：`{{ event_id }}`
- **治理維度**：81-auto-comment
- **依賴維度**：39-automation, 71-feedback-loops

<sub>
此反饋由 **Auto-Comment Engine** 自動生成
事件已記錄到 `governance/index/events/registry.json`
</sub>
