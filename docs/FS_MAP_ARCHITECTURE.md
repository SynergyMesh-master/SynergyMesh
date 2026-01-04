# Filesystem Mapping Architecture (fs.map + fs.index)

## 概述

MachineNativeOps 採用**層次化自動生成**的 fs.map + fs.index 架構，實現目錄結構的全面治理，同時**100% 自動化維護 = 0% 手動負擔**。

## 架構設計

### 雙層架構：fs.map + fs.index

```
┌─────────────────────────────────────────────────────────────────┐
│                     root.fs.index (頂層聚合)                      │
│  - 聚合所有子 fs.index                                           │
│  - 聚合所有子 fs.map                                             │
│  - 定義驗證規則                                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
     ┌──────────────────────┼──────────────────────┐
     ▼                      ▼                      ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│controlplane/│      │ workspace/  │      │  chatops/   │
│  fs.index   │      │  fs.index   │      │  fs.index   │
│  fs.map     │      │  fs.map     │      │  fs.map     │
└──────┬──────┘      └──────┬──────┘      └──────┬──────┘
       │                    │                    │
       │         ┌──────────┼──────────┐         │
       │         ▼          ▼          ▼         │
       │   ┌──────────┐ ┌───────┐ ┌────────┐     │
       │   │  src/    │ │config/│ │ docs/  │     │
       │   │fs.index  │ │fs.idx │ │fs.map  │     │
       │   │ fs.map   │ │fs.map │ │        │     │
       │   └────┬─────┘ └───────┘ └────────┘     │
       │        │                                │
       ▼        ▼                                ▼
   [子模組]  [子模組]                         [子模組]
   fs.map    fs.map                          fs.map
```

### 生成的檔案結構

```
root.fs.index                    ← 頂層聚合（9個子索引）
├── controlplane/fs.index        ← 自動生成
├── workspace/fs.index           ← 自動生成
│   ├── workspace/config/fs.index
│   └── workspace/src/fs.index
├── chatops/fs.index             ← 自動生成
│   ├── chatops/deploy/fs.index
│   └── chatops/services/fs.index
└── web/fs.index                 ← 自動生成

+ 635 個 fs.map 檔案（自動生成）
+ 4,646 個目錄映射條目
```

## 核心組件

### 1. root.fs.map (手動維護 - 精簡版)

**位置**: `/root.fs.map`

**內容**:
- FHS 3.0 系統目錄定義
- 頂層模組入口（@include 指令）
- 生產環境安裝路徑
- 權限配置組

**更新頻率**: 極少（僅當系統架構變更時）

### 2. root.fs.index (自動維護)

**位置**: `/root.fs.index`

**功能**:
- 索引所有子 fs.map 檔案
- 定義生成器配置
- 指定模組邊界標記
- 設定權限模式

**更新頻率**: 由生成器自動更新

### 3. 模組 fs.map (自動生成)

**位置**: 各模組目錄下

**範例**:
- `controlplane/fs.map`
- `workspace/fs.map`
- `workspace/src/fs.map`
- `chatops/services/fs.map`

**更新頻率**: 執行生成器時自動更新

## 自動化工具

### fs-map-generator.py

**位置**: `/bin/fs-map-generator.py`

**功能**:

```bash
# 驗證現有映射
./bin/fs-map-generator.py

# 重新生成所有 fs.map
./bin/fs-map-generator.py --regenerate

# 檢查漂移（目錄結構與映射不同步）
./bin/fs-map-generator.py --check-drift

# 自動修復漂移
./bin/fs-map-generator.py --fix-drift

# 生成覆蓋報告
./bin/fs-map-generator.py --report

# 顯示詳細輸出
./bin/fs-map-generator.py --regenerate --verbose

# 乾跑模式（不實際寫入）
./bin/fs-map-generator.py --regenerate --dry-run
```

### 模組邊界檢測

生成器使用以下標記來識別模組邊界：

| 標記檔案 | 說明 |
|---------|------|
| `package.json` | Node.js 模組 |
| `pyproject.toml` | Python 專案 |
| `Cargo.toml` | Rust 專案 |
| `go.mod` | Go 模組 |
| `README.md` | 文檔目錄 |
| `fs.map` | 已存在的映射 |
| `__init__.py` | Python 套件 |

### 強制模組目錄

以下目錄無論是否有標記都會生成 fs.map：

```
controlplane/
workspace/
chatops/
web/
workspace/src/
workspace/config/
workspace/docs/
chatops/services/
chatops/deploy/
chatops/scripts/
```

## 權限配置

### 自動權限分配

生成器根據目錄名稱模式自動分配權限：

| 模式 | 權限 | 檔案系統 | 掛載選項 |
|------|------|---------|---------|
| `*secrets*` | `-rwx------` | ext4 | relatime,rw |
| `*config*` | `-rwxr-xr-x` | ext4 | relatime,rw |
| `*logs*` | `-rwxr-xr-x` | ext4 | relatime,rw |
| `*tmp*` | `-rwxrwxrwx` | tmpfs | size=1G,rw,nosuid,nodev |
| `*cache*` | `-rwxr-xr-x` | ext4 | relatime,rw |
| 預設 | `-rwxr-xr-x` | ext4 | relatime,rw |

## 工作流程

### 日常開發

```
1. 正常開發，創建/修改目錄
2. Pre-commit hook 自動檢測漂移
3. 如有漂移，顯示警告
4. 可選：執行 --regenerate 更新
```

### 定期同步

```bash
# 建議：每週或每次大型重構後執行
./bin/fs-map-generator.py --regenerate
git add -A "*.map" root.fs.index
git commit -m "chore: sync fs.map files"
```

### CI/CD 整合

```yaml
# .github/workflows/fsmap-check.yml
name: fs.map Check
on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check fs.map drift
        run: ./bin/fs-map-generator.py --check-drift
```

## 統計

執行 `--regenerate` 後的統計（2026-01-04）:

| 指標 | 數值 |
|------|------|
| 掃描目錄數 | 1,978 |
| 偵測到的模組邊界 | 628 |
| 生成的 fs.map 檔案 | ~90 |
| 總映射條目 | 4,646 |
| 覆蓋率 | ~100% |

## 排除目錄

以下目錄會被自動排除：

```
.git/
node_modules/
__pycache__/
.venv/
*.egg-info/
workspace-archive/
workspace-problematic/
.githooks/
coverage/
dist/
build/
.cache/
.pytest_cache/
```

## 故障排除

### 漂移警告

```bash
# 問題：pre-commit 顯示 "fs.map drift detected"
# 解決：
./bin/fs-map-generator.py --regenerate
git add -A "*.map"
```

### 生成器失敗

```bash
# 問題：生成器報錯
# 檢查：
python3 --version  # 需要 Python 3.8+
pip install pyyaml  # 確保依賴已安裝
```

### 覆蓋率低

```bash
# 問題：覆蓋率低於預期
# 檢查模組邊界標記：
./bin/fs-map-generator.py --report --verbose
```

## 設計原則

1. **最小手動維護**: 只有 root.fs.map 需要偶爾手動調整
2. **自動發現**: 新目錄自動被下次生成納入
3. **漂移警告而非阻擋**: 提醒但不阻止提交
4. **權限智能推斷**: 根據目錄名稱自動分配合適權限
5. **層次化結構**: 每個模組管理自己的映射

## 相關檔案

| 檔案 | 說明 |
|------|------|
| `/root.fs.map` | 根層精簡映射 |
| `/root.fs.index` | 聚合索引 |
| `/bin/fs-map-generator.py` | 自動生成腳本 |
| `/.githooks/pre-commit` | Git hook（含漂移檢查） |
| `/docs/FS_MAP_ARCHITECTURE.md` | 本文檔 |

---

**版本**: 1.0.0
**最後更新**: 2026-01-04
**維護者**: MachineNativeOps Team
