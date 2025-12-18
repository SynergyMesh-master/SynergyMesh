# 五骨架自主框架

## 骨架構成

1. **感知骨架**：感測器、資料融合、異常偵測
2. **決策骨架**：任務規劃、路徑最佳化、風險評估
3. **執行骨架**：控制迴路、裝置協調
4. **安全骨架**：Fail-safe、冗餘、手動接管
5. **治理骨架**：審批、審計、策略同步

## 系統流程

```
Input → Perception → Mission Planner → Control Stack → Telemetry Feedback
```

## 整合點

- Drone Coordinator (`automation/drone-coordinator.py`)
- Auto-Pilot (`.devcontainer/automation/auto-pilot.js`)
- Zero Touch Deployment (`automation/zero_touch_deployment.py`)

## 測試策略

- 數位分身模擬
- 受控試飛
- Canary 編隊
