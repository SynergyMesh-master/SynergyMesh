# AXIOM 到 MachineNativeOps 命名空間遷移計劃

## 📋 項目概述

本文檔詳細說明了將 AXIOM 命名空間遷移到 MachineNativeOps 的完整計劃。

## 🎯 遷移目標

1. **完全替換命名空間**：將所有 `machinenativeops.io/v2` 替換為 `machinenativeops.io/v2`
2. **統一資源類型**：將 `MachineNativeOpsGlobalBaseline` 替換為 `MachineNativeOpsGlobalBaseline`
3. **更新 URN 模式**：將 `urn:machinenativeops:` 替換為 `urn:machinenativeops:`
4. **標準化標籤**：將 `machinenativeops.io/` 前綴替換為 `machinenativeops.io/`

## 🛠️ 工具使用

```bash
# 試運行
python scripts/migration/namespace-converter.py --dry-run .

# 正式轉換
python scripts/migration/namespace-converter.py .
```

## 📁 核心檔案

- `config/axioms/global-baseline-v2.yaml` - 主要配置檔案
- `scripts/migration/namespace-converter.py` - 轉換工具
- `docs/migration/machinenativeops-namespace-migration-guide.md` - 詳細指南

## 📊 預期結果

- **轉換檔案數**：約 200+ 個檔案
- **成功率**：預期 99%+
- **處理時間**：約 5-10 分鐘

---

*最後更新：2025-12-20*
