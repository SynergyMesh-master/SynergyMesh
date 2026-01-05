---
# MachineNativeOps 治理框架 - 快速參考指南
# Quick Reference Guide

## 🚀 30 秒快速開始

### 1. 讀取 Manifest（所有知識的入口）
```bash
cat governance-manifest.yaml
```

### 2. 驗證名稱
```bash
python3 tools/python/governance_agent.py validate "prod-platform-api-deploy-1.0.0" "k8s-deployment" "prod"
```

### 3. 生成名稱
```bash
python3 tools/python/governance_agent.py generate "k8s-deployment" "prod" "platform" "api" "v1.0.0"
# 結果: prod-platform-api-deploy-1.0.0
```

### 4. 獲取系統信息
```bash
python3 tools/python/governance_agent.py info
```

---

## 📋 AI 接口速查

### 驗證接口
```
命令: validate <name> <type> <env>
請求: schemas/validation-request.schema.yaml
響應: schemas/validation-response.schema.yaml
```

### 生成接口
```
命令: generate <type> <env> [team] [service] [version]
請求: schemas/generation-request.schema.yaml
響應: schemas/generation-response.schema.yaml
```

### 變更請求接口
```
命令: create-change <json-data>
請求: schemas/change-request.schema.yaml
響應: schemas/change-response.schema.yaml
```

### 例外請求接口
```
命令: create-exception <json-data>
請求: schemas/exception-request.schema.yaml
響應: schemas/exception-response.schema.yaml
```

---

## 📁 關鍵文件位置

### 入口點
```
governance-manifest.yaml          # 系統總覽和地圖
README-MACHINE.md                 # AI 專用文檔
```

### 工具
```
tools/python/governance_agent.py   # 主要治理代理
tools/git-hooks/pre-commit         # Git pre-commit hook
```

### Schema
```
schemas/*.schema.yaml              # 所有驗證模式
```

### 模板
```
templates/ci/github-actions-*.yml  # CI/CD 模板
templates/monitoring/*.yaml        # 監控配置
```

### 初始化
```
init-governance.sh                 # 系統初始化腳本
```

---

## 🤖 Python API 速查

```python
from governance_agent import GovernanceAgent

# 初始化
agent = GovernanceAgent()

# 驗證名稱
result = agent.validate_name(name, type, env, team=None, service=None)

# 生成名稱
result = agent.generate_name(type, env, team=None, service=None, version=None)

# 創建變更請求
result = agent.create_change_request(change_data)

# 創建例外請求
result = agent.create_exception_request(exception_data)

# 獲取信息
info = agent.get_manifest_info()
modules = agent.list_modules()
module = agent.get_module_info(module_id)
```

---

## 🔧 常見任務

### 驗證 Kubernetes Deployment 名稱
```bash
python3 tools/python/governance_agent.py validate \
  "prod-payment-deploy-1.0.0" \
  "k8s-deployment" \
  "prod"
```

### 生成服務名稱
```bash
python3 tools/python/governance_agent.py generate \
  "k8s-service" \
  "prod" \
  "platform" \
  "api"
```

### 批量驗證
```bash
# 驗證多個名稱
for name in "prod-api-deploy-1.0.0" "staging-db-deploy-2.0.0"; do
  python3 tools/python/governance_agent.py validate "$name" "k8s-deployment" "prod"
done
```

### 列出所有模組
```bash
python3 tools/python/governance_agent.py modules
```

---

## 📊 資源類型

### Kubernetes
```
k8s-deployment     # Deployment
k8s-service        # Service
k8s-ingress        # Ingress
k8s-configmap      # ConfigMap
k8s-secret         # Secret
k8s-pvc            # PersistentVolumeClaim
k8s-pv             # PersistentVolume
```

### AWS
```
aws-s3-bucket      # S3 Bucket
aws-lambda         # Lambda Function
```

### Azure
```
azure-storage-account  # Storage Account
```

### GCP
```
gcp-storage-bucket  # Storage Bucket
```

### 其他
```
docker-image        # Docker Image
git-branch          # Git Branch
environment-variable    # Environment Variable
config-file         # Configuration File
```

---

## 🎯 環境前綴

```
dev         # Development
staging     # Staging
prod        # Production
```

---

## 🔍 驗證規則

### 長度
- 最小: 3 字符
- 最大: 63 字符

### 格式
- 只允許: 小寫字母、數字、連字符、點號
- 不能以連字符或點號開頭或結束

### 模式
```
^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$
```

### 必須包含
- 環境前綴（dev/staging/prod）

---

## 📈 監控警報

### 關鍵警報
```
NamingAdoptionRateLow          # 採用率 < 75%
NamingComplianceRateCritical   # 合規率 < 85%
NamingViolationsSpike          # 違規激增
SecurityNamingViolation         # 安全違規
ProdConfigDriftDetected        # 生產配置漂移
```

---

## 🔄 工作流

### Pre-commit 驗證
```bash
# 自動觸發
git commit

# 手動運行
bash tools/git-hooks/pre-commit
```

### CI Pipeline
```yaml
# 添加到 .github/workflows/
name: Naming Validation
on: [push, pull_request]
jobs:
  validate:
    steps:
      - run: python3 tools/python/governance_agent.py validate-all
```

---

## 📞 獲取幫助

### 查看所有命令
```bash
python3 tools/python/governance_agent.py
```

### 查看模組信息
```bash
python3 tools/python/governance_agent.py modules
```

### 閱讀文檔
```bash
cat README-MACHINE.md
cat MACHINE_NATIVE_GOVERNANCE_COMPLETE.md
```

---

## ✅ 快速檢查清單

- [ ] governance-manifest.yaml 存在
- [ ] tools/python/governance_agent.py 可執行
- [ ] 已安裝依賴（pyyaml, jsonschema）
- [ ] Git hooks 已安裝
- [ ] CI/CD 已配置

---

**版本**: 2.0.0  
**最後更新**: 2025-01-05