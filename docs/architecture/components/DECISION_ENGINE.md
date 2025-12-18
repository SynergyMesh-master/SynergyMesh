# 決策引擎

## 功能

- 收斂多 Agent 建議
- 套用治理規則與權重
- 做出最終建議/行動

## 模組

1. **Signal Collector**：彙整代碼/監控/安全事件
2. **Policy Evaluator**：OPA/Rego 驅動的規則
3. **Scoring Engine**：多指標量化，考慮風險/成本/收益
4. **Action Router**：指派後續工作流或人類審核

## 決策流程

```
Signals → Normalize → Policy Check → Score → Action
```

## Policy 範例

```rego
package island.decision

default allow = false

allow {
  input.level == "L2"
  input.change_type == "doc-update"
}

allow {
  input.level == "L3"
  input.tests_passed
  input.risk_score < 0.4
}
```

## 可觀測性

- 決策原因記錄於 `decision_log` topic
- 支援 `island-cli decisions:explain <id>`
