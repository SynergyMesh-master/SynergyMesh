# namespace-mcp 結構速覽（深度研究預備）

本文件對 `workspace/mcp/namespace-mcp` 的實際目錄、關鍵檔案與入口進行快速盤點，作為後續架構協助的事前準備。

## 目錄實況（近期同步）
- `config/`：`conversion.yaml`、`mcp-rules.yaml`、`governance.yaml` 三個主要配置。
- `src/`：`converter.py` 單一核心轉換器。
- `scripts/`：`convert.sh`（轉換入口）、`test.sh`（測試入口）。
- `docs/`：`architecture.md`、`usage.md`（架構與使用說明）。
- `tests/`：`test_converter.py` 單元測試。
- `examples/`：`README.md` 與 `example-project/` 範例來源。
- 根目錄：`README.md`、`CHANGELOG.md`、`CONTRIBUTING.md`、`LICENSE`、`PROJECT-SUMMARY.md`、`INSTANT-COMPLIANCE.md`、`KNOWLEDGE_INDEX.yaml` 等說明與索引文件。

## 核心組件與責任
- **converter.py**：負責六層治理（namespace/dependency/reference/structure/semantic/governance）規則的構建與應用，讀取 `config/` 內 YAML 規則並生成轉換結果。
- **config/**：定義企業前綴、依賴映射、檔案類型與治理規則；為轉換器提供唯一配置來源。
- **scripts/convert.sh**：封裝執行流程，包含乾跑模式與日誌輸出。  
- **tests/test_converter.py**：覆蓋命名空間、依賴與報告輸出等核心路徑（pytest）。

## 測試與執行觀察
- 測試命令：`python -m pytest tests`（已在本次檢視中通過）。
- 轉換入口：`./scripts/convert.sh <source> <target>`；測試入口：`./scripts/test.sh`。

## 更新紀錄
- 補齊 README 提及的結構：`.instant-manifest.yaml`、`src/advanced_converter.py`、`scripts/advanced-convert.sh`、`examples/converted-example/`、`reports/` 目錄。
- `.instant-manifest.yaml` 用於列舉關鍵工件（含新增佔位項），保持 INSTANT 兼容。

以上盤點可作為後續架構調整與治理校驗的即時基線。
