# AXIOM 到 MachineNativeOps 命名空間遷移操作指南
# AXIOM to MachineNativeOps Namespace Migration Operation Guide

## 📖 概述 | Overview

本指南提供詳細的操作步驟，幫助開發者和運維人員順利完成 AXIOM 到 MachineNativeOps 的命名空間遷移。

This guide provides detailed step-by-step instructions to help developers and operations teams successfully complete the AXIOM to MachineNativeOps namespace migration.

---

## 🚀 快速開始 | Quick Start

### 最小步驟 | Minimum Steps

```bash
# Step 1: 創建分支
git checkout -b feature/axiom-to-mno-migration

# Step 2: 試運行驗證
python scripts/migration/axiom-namespace-migrator.py --dry-run .

# Step 3: 正式轉換
python scripts/migration/axiom-namespace-migrator.py --backup .

# Step 4: 提交變更
git add .
git commit -m "feat: migrate AXIOM namespace to MachineNativeOps"
```

---

## 📋 詳細操作步驟 | Detailed Operation Steps

### 步驟 1: 環境準備 | Step 1: Environment Preparation

#### 1.1 確認 Python 環境

```bash
# 確認 Python 版本 (需要 3.8+)
python --version

# 安裝可選依賴
pip install PyYAML
```

#### 1.2 創建工作分支

```bash
# 從 main 分支創建
git checkout main
git pull origin main
git checkout -b feature/axiom-to-mno-migration

# 確認當前狀態
git status
```

#### 1.3 確認遷移工具

```bash
# 確認遷移工具存在
ls -la scripts/migration/axiom-namespace-migrator.py

# 查看工具幫助
python scripts/migration/axiom-namespace-migrator.py --help
```

---

### 步驟 2: 試運行驗證 | Step 2: Dry Run Verification

#### 2.1 執行試運行

```bash
# 基本試運行
python scripts/migration/axiom-namespace-migrator.py --dry-run .

# 詳細試運行 (顯示所有匹配)
python scripts/migration/axiom-namespace-migrator.py --dry-run --verbose .

# 試運行並生成報告
python scripts/migration/axiom-namespace-migrator.py --dry-run --report --output dry-run-report.txt .
```

#### 2.2 審查試運行報告

檢查報告中的以下項目:

| 檢查項目 | 預期結果 | 實際結果 |
|----------|----------|----------|
| 檔案掃描數量 | ~200+ | _____ |
| 預計轉換數量 | ~100+ | _____ |
| 錯誤數量 | 0 | _____ |
| 警告數量 | 可接受 | _____ |

#### 2.3 驗證關鍵檔案

```bash
# 檢查關鍵 YAML 檔案
grep -l "axiom" config/**/*.yaml workspace/**/*.yaml

# 檢查關鍵 Python 檔案
grep -l "Axiom" workspace/src/**/*.py

# 檢查關鍵 Markdown 檔案
grep -l "axiom.io" docs/**/*.md
```

---

### 步驟 3: 正式轉換 | Step 3: Actual Conversion

#### 3.1 創建備份

```bash
# 遷移工具會自動創建備份
# 備份位置: .axiom-migration-backup/

# 或手動創建完整備份
tar -czf axiom-migration-backup-$(date +%Y%m%d).tar.gz .
```

#### 3.2 執行轉換

```bash
# 執行轉換 (包含備份)
python scripts/migration/axiom-namespace-migrator.py --backup .

# 查看轉換結果
echo "轉換完成，檢查結果..."
```

#### 3.3 生成轉換報告

```bash
# 生成詳細報告
python scripts/migration/axiom-namespace-migrator.py --validate --report --json --output conversion-report.json .

# 查看報告
cat conversion-report.json | python -m json.tool
```

---

### 步驟 4: 驗證轉換結果 | Step 4: Verify Conversion Results

#### 4.1 語法驗證

```bash
# 驗證 YAML 語法
echo "驗證 YAML 檔案..."
find . -name "*.yaml" -not -path "./.git/*" -not -path "./node_modules/*" | while read file; do
    python -c "import yaml; yaml.safe_load(open('$file'))" 2>&1 || echo "Error in: $file"
done

# 驗證 JSON 語法
echo "驗證 JSON 檔案..."
find . -name "*.json" -not -path "./.git/*" -not -path "./node_modules/*" | while read file; do
    python -c "import json; json.load(open('$file'))" 2>&1 || echo "Error in: $file"
done

# 驗證 Python 語法
echo "驗證 Python 檔案..."
find . -name "*.py" -not -path "./.git/*" -not -path "./__pycache__/*" | while read file; do
    python -m py_compile "$file" 2>&1 || echo "Error in: $file"
done
```

#### 4.2 遺留引用檢查

```bash
# 搜索遺留 API 版本
echo "檢查遺留 API 版本..."
grep -r "axiom\.io/v" --include="*.yaml" --include="*.json" . || echo "✓ 無遺留 API 版本"

# 搜索遺留類型名稱
echo "檢查遺留類型名稱..."
grep -r "Axiom[A-Z]" --include="*.py" --include="*.yaml" . || echo "✓ 無遺留類型名稱"

# 搜索遺留 URN
echo "檢查遺留 URN..."
grep -r "urn:axiom:" --include="*.yaml" --include="*.json" . || echo "✓ 無遺留 URN"

# 搜索遺留路徑
echo "檢查遺留路徑..."
grep -r "/etc/axiom\|/opt/axiom" --include="*.yaml" --include="*.sh" . || echo "✓ 無遺留路徑"
```

#### 4.3 功能測試

```bash
# 運行單元測試 (如果有)
npm test 2>/dev/null || echo "No npm tests"
python -m pytest 2>/dev/null || echo "No pytest tests"

# 運行 lint 檢查
npm run lint 2>/dev/null || echo "No npm lint"
```

---

### 步驟 5: 提交變更 | Step 5: Commit Changes

#### 5.1 檢查變更

```bash
# 查看變更狀態
git status

# 查看變更詳情
git diff --stat

# 查看具體變更 (前 50 行)
git diff | head -100
```

#### 5.2 提交變更

```bash
# 添加所有變更
git add .

# 提交 (使用規範的提交訊息)
git commit -m "feat(namespace): migrate AXIOM to MachineNativeOps namespace

- Convert API versions from axiom.io/v* to machinenativeops.io/v*
- Update resource types from Axiom* to MachineNativeOps*
- Update URN patterns from urn:axiom: to urn:machinenativeops:
- Update label prefixes from axiom.io/ to machinenativeops.io/
- Update filesystem paths from /etc/axiom to /etc/machinenativeops
- Update registry references to registry.machinenativeops.io

Refs: #ISSUE_NUMBER"
```

#### 5.3 推送變更

```bash
# 推送到遠端
git push origin feature/axiom-to-mno-migration

# 創建 Pull Request
echo "請在 GitHub 上創建 Pull Request"
```

---

## 🔧 故障排除 | Troubleshooting

### 常見問題 | Common Issues

#### 問題 1: 轉換工具執行失敗

**症狀**: `ModuleNotFoundError: No module named 'yaml'`

**解決方案**:
```bash
pip install PyYAML
```

#### 問題 2: YAML 語法錯誤

**症狀**: `yaml.scanner.ScannerError`

**解決方案**:
```bash
# 找出有問題的檔案
python -c "import yaml; yaml.safe_load(open('problem-file.yaml'))"

# 使用 yamllint 檢查
pip install yamllint
yamllint problem-file.yaml
```

#### 問題 3: 轉換不完整

**症狀**: 部分引用未被轉換

**解決方案**:
```bash
# 執行驗證模式找出遺漏
python scripts/migration/axiom-namespace-migrator.py --validate --verbose .

# 手動補充轉換
```

#### 問題 4: 備份恢復

**症狀**: 需要恢復到轉換前狀態

**解決方案**:
```bash
# 查看備份
ls -la .axiom-migration-backup/

# 恢復特定備份
cp -r .axiom-migration-backup/<timestamp>/* .

# 或使用 git 恢復
git checkout .
```

---

## 🔄 回滾方案 | Rollback Plan

### 快速回滾 | Quick Rollback

```bash
# 方法 1: Git 回滾
git checkout .
git clean -fd

# 方法 2: 從備份恢復
BACKUP_DIR=$(ls -td .axiom-migration-backup/*/ | head -1)
cp -r "$BACKUP_DIR"/* .

# 方法 3: 重新拉取
git fetch origin
git reset --hard origin/main
```

### 部分回滾 | Partial Rollback

```bash
# 回滾特定檔案
git checkout HEAD -- path/to/file.yaml

# 回滾特定目錄
git checkout HEAD -- config/
```

---

## ✅ 驗證清單 | Verification Checklist

### 遷移前 | Pre-Migration

- [ ] Python 3.8+ 已安裝
- [ ] 工作分支已創建
- [ ] 試運行已執行
- [ ] 報告已審查
- [ ] 備份已確認

### 遷移中 | During Migration

- [ ] 轉換工具執行無錯誤
- [ ] YAML 語法驗證通過
- [ ] JSON 語法驗證通過
- [ ] Python 語法驗證通過
- [ ] 無遺留引用

### 遷移後 | Post-Migration

- [ ] 所有測試通過
- [ ] Lint 檢查通過
- [ ] 變更已提交
- [ ] PR 已創建
- [ ] 審查已完成

---

## 📊 預期結果 | Expected Results

### 轉換統計 | Conversion Statistics

| 指標 | 預期值 |
|------|--------|
| 處理檔案數量 | ~200+ |
| 轉換引用數量 | ~100+ |
| 錯誤數量 | 0 |
| 處理時間 | <5 分鐘 |
| 成功率 | 99%+ |

### 轉換範例 | Conversion Examples

**Before:**
```yaml
apiVersion: axiom.io/v2
kind: AxiomGlobalBaseline
metadata:
  labels:
    axiom.io/tier: "core"
```

**After:**
```yaml
apiVersion: machinenativeops.io/v2
kind: MachineNativeOpsGlobalBaseline
metadata:
  labels:
    machinenativeops.io/tier: "core"
```

---

## 📞 支援資源 | Support Resources

### 文檔連結 | Documentation Links

- [遷移計劃](./axiom-namespace-migration-plan.md)
- [命名空間配置](../../workspace/mno-namespace.yaml)
- [遷移工具源碼](../../scripts/migration/axiom-namespace-migrator.py)

### 聯繫方式 | Contact

- **問題報告**: GitHub Issues
- **技術支援**: Slack #migration-support
- **緊急情況**: PagerDuty

---

*文檔版本: 1.0.0*
*最後更新: 2025-12-20*
*狀態: 已審核並準備發布*
