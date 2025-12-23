# 🚀 Step-2: 建立 Controlplane (Baseline+Overlay) 架構

## 🎯 任務目標
建立完整的 controlplane 架構，採用 Baseline(不可變) + Overlay(可寫) 設計，支援 self-heal 但不污染治理真相。

---

## 📋 任務清單

### Phase 1: 目錄結構建立
- [x] 創建 controlplane/baseline/ 完整目錄結構
- [x] 創建 controlplane/overlay/ 完整目錄結構
- [x] 創建 controlplane/active/ 空目錄（合成視圖）

### Phase 2: Baseline 配置文件
- [x] 創建 baseline/config/ 所有配置文件 (10 個)
- [x] 創建 baseline/specifications/ 所有規格文件 (5 個)
- [x] 創建 baseline/registries/ 註冊文件 (2 個)
- [x] 創建 baseline/integration/ 集成配置 (1 個)
- [x] 創建 baseline/documentation/ 文檔 (1 個)

### Phase 3: Baseline 驗證系統
- [x] 創建 baseline/validation/gate-root-specs.yml
- [x] 創建 baseline/validation/validate-root-specs.py（核心驗證器）
- [x] 創建 baseline/validation/vectors/root.validation.vectors.yaml

### Phase 4: Root 引導文件更新
- [x] 更新 root.bootstrap.yaml 指向 controlplane/baseline
- [x] 更新 root.fs.map 包含 baseline/overlay/active 映射
- [x] 驗證 root.env.sh 環境變數

### Phase 5: 驗證與測試
- [x] 運行 validate-root-specs.py
- [x] 驗證 evidence 產出到 overlay/evidence/
- [x] 檢查 controlplane.manifest.json
- [x] 檢查 validation.report.json
- [x] 確認 report 顯示 pass=true

### Phase 6: 文檔與提交
- [ ] 創建 controlplane 使用文檔
- [ ] 創建驗證報告
- [ ] Git 提交所有變更
- [ ] 推送到遠端倉庫

---

## 🎯 驗收標準

### 必須通過的檢查
1. ✅ 目錄結構完整：baseline/, overlay/, active/
2. ✅ 所有必需文件存在（19 個 baseline 文件）
3. ✅ validate-root-specs.py 可執行
4. ✅ Evidence 正確產出到 overlay/evidence/
5. ✅ validation.report.json 顯示 pass=true

### 寫入規則驗證
1. ✅ Self-heal 只能寫入 overlay/**
2. ✅ Baseline/** 不可被 runtime 修改
3. ✅ Active/** 不可被 runtime 修改

---

## 📊 進度追蹤

**當前階段**: Phase 4 - Root 引導文件更新  
**完成度**: 60%  
**預計完成時間**: 15-20 分鐘

---

*繼續執行 Phase 4 任務...*