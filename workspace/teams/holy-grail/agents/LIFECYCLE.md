# Agent 生命週期

## 狀態機

```text
UNASSIGNED → ACTIVATING → RUNNING → COLLABORATING → COMPLETED
             ↘─────────────── RETRYING ─────────────↗
```

## 關鍵階段

1. **Birth**
   - 需求偵測器觸發
   - 生成 Agent 實例與上下文
2. **Growth**
   - 取得任務，查詢知識庫
   - 記錄決策依據
3. **Collaboration**
   - 透過 Orchestrator 與其他 Agent 協作
   - 解決衝突與狀態同步
4. **Retirement**
   - 回寫學習成果
   - 釋放資源

## 監控指標

- 啟動延遲 (Activation Latency)
- 任務成功率
- 協作輪次
- 知識回寫大小

## 操作流程

```bash
# 觀察 Agent 狀態
island-cli agents:list

# 查看詳細活動
island-cli agents:trace --id=<agent-id>

# 強制終止
island-cli agents:stop --id=<agent-id>
```
