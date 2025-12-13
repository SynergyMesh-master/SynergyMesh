## {{ emoji }} 自動評論：CI 驗證{{ status_text }}

**工作流程**：{{ workflow }}
**執行 ID**：{{ run_id }}
**Commit**：{{ commit }}
**時間戳**：{{ timestamp }}

---

### {{ error_emoji }} 錯誤摘要

{{ error_message }}

{{ #if error_details }}
<details>
<summary>展開完整錯誤訊息</summary>

```
{{ error_details }}
```

</details>
{{ /if }}

---

### {{ fix_emoji }} 修復狀態

{{ #if auto_fixed }}
**已自動修復並提交**

修復類型：{{ fix_type }}
修復命令：`{{ fix_command }}`
提交 SHA：{{ fix_commit }}
{{ else }}
**需要人工修復**

{{ fix_suggestions }}
{{ /if }}

---

### {{ suggestion_emoji }} 建議修復步驟

{{ #each fix_steps }}
{{ @index }}. {{ this }}
{{ /each }}

---

### {{ doc_emoji }} 相關文檔

{{ #each docs }}
- [{{ this.title }}]({{ this.url }})
{{ /each }}

---

<sub>
此評論由 **Auto-Comment Engine** (81-auto-comment) 自動生成
事件 ID：`{{ event_id }}`
已寫入 `governance/index/events/registry.json`
</sub>
