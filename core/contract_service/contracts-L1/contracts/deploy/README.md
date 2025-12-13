# Contracts L1 Service - Deployment Configurations

此目錄包含 Contracts L1 Service 的所有部署配置檔案，支援多種部署環境與平台。

## 📁 目錄結構

```
deploy/
├── README.md                       # 本文件
├── .env.example                    # 環境變數範本
├── docker-compose.production.yml   # Docker Compose 生產配置
├── nginx.conf                      # Nginx 負載平衡器配置
├── grafana-dashboard.json         # Grafana 儀表板定義
├── k8s/                           # Kubernetes 配置
│   ├── namespace.yaml             # 命名空間
│   ├── configmap.yaml             # 配置映射
│   ├── secret.yaml                # 密鑰
│   ├── deployment-production.yaml # 生產部署
│   ├── service-production.yaml    # 服務定義
│   ├── ingress.yaml               # 流量入口
│   ├── servicemonitor.yaml        # Prometheus 監控
│   ├── prometheusrule.yaml        # 告警規則
│   └── kustomization.yaml         # Kustomize 配置
└── (existing files...)
```

## 🚀 快速開始

### 使用 Docker Compose

1. **複製環境變數範本**

   ```bash
   cp .env.example .env.production
   # 編輯 .env.production，設定實際的值
   ```

2. **啟動服務**

   ```bash
   docker-compose -f docker-compose.production.yml up -d
   ```

3. **驗證服務**

   ```bash
   curl http://localhost:3000/healthz
   ```

### 使用 Kubernetes

1. **安裝前提條件**
   - Kubernetes 集群 (v1.24+)
   - kubectl 已配置
   - Kustomize (可選，kubectl 內建)

2. **創建命名空間與密鑰**

   ```bash
   kubectl apply -f k8s/namespace.yaml

   # 創建實際的密鑰（不要使用範例值！）
   kubectl create secret generic contracts-l1-secrets \
     --from-literal=API_KEY_SECRET=your-strong-secret-here \
     -n synergymesh
   ```

3. **部署服務**

   ```bash
   # 使用 kubectl
   kubectl apply -f k8s/

   # 或使用 Kustomize
   kubectl apply -k k8s/
   ```

4. **驗證部署**

   ```bash
   kubectl get pods -n synergymesh -l app=contracts-l1
   kubectl get svc -n synergymesh contracts-l1
   ```

## 📋 配置檔案說明

### .env.example

環境變數範本，包含：

- 應用程式配置（PORT, NODE_ENV）
- 資料庫配置（可選）
- Sigstore 配置
- 安全設定
- 監控配置
- **Redis 配置（速率限制）** - 生產環境多實例部署必須啟用

### docker-compose.production.yml

Docker Compose 生產配置，包含：

- Contracts L1 服務（3 個副本）
- Nginx 負載平衡器（可選）
- 健康檢查
- 資源限制

### K8s 配置

#### namespace.yaml

定義 `synergymesh` 命名空間。

#### configmap.yaml

應用程式配置（非敏感資料）：

- 環境設定
- 功能開關
- Sigstore URL

#### secret.yaml

敏感資料（**生產環境必須替換！**）：

- API 密鑰
- 資料庫憑證
- 第三方服務令牌

#### deployment-production.yaml

生產部署配置：

- 3 個副本（高可用）
- 滾動更新策略
- 健康檢查（liveness, readiness, startup）
- 資源限制（CPU: 250m-500m, Memory: 256Mi-512Mi）
- 安全上下文（非 root 使用者，只讀根檔案系統）
- Pod 反親和性（避免單點故障）

#### service-production.yaml

兩個服務定義：

1. **contracts-l1**: ClusterIP 服務（內部訪問）
2. **contracts-l1-headless**: Headless 服務（直接 Pod 訪問）

#### ingress.yaml

流量入口配置：

- HTTPS 自動憑證（Let's Encrypt）
- 速率限制
- CORS 支援
- 多域名支援

#### servicemonitor.yaml

Prometheus 監控配置：

- 指標收集端點
- 收集間隔：30 秒

#### prometheusrule.yaml

告警規則：

- 高錯誤率（>5%）
- 慢回應時間（p95 > 100ms）
- 服務停止
- 高記憶體使用（>90%）
- Pod 重啟
- 低副本數（<2）

#### kustomization.yaml

Kustomize 配置：

- 統一命名空間
- 共同標籤
- 映像標籤管理
- 配置生成器

### nginx.conf

Nginx 負載平衡器配置：

- HTTP 到 HTTPS 重定向
- SSL/TLS 配置
- 速率限制
- 安全標頭
- 健康檢查路由
- 指標端點（內部網路限制）

### grafana-dashboard.json

Grafana 儀表板定義：

- 請求速率
- 回應時間（p95）
- 錯誤率
- CPU 使用
- 記憶體使用
- Pod 狀態

## 🔧 常見操作

### 擴展副本數

```bash
# Docker Compose
docker-compose -f docker-compose.production.yml up -d --scale contracts-l1=5

# Kubernetes
kubectl scale deployment contracts-l1 -n synergymesh --replicas=5
```

### 查看日誌

```bash
# Docker Compose
docker-compose -f docker-compose.production.yml logs -f contracts-l1

# Kubernetes
kubectl logs -n synergymesh -l app=contracts-l1 -f
```

### 更新映像

```bash
# Docker Compose
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d

# Kubernetes
kubectl set image deployment/contracts-l1 \
  contracts-l1=ghcr.io/we-can-fix/synergymesh/contracts-l1:v1.1.0 \
  -n synergymesh
```

### 回滾部署

```bash
# Kubernetes
kubectl rollout undo deployment/contracts-l1 -n synergymesh
kubectl rollout status deployment/contracts-l1 -n synergymesh
```

## 🔧 Redis 配置（速率限制）

**重要：生產環境多實例部署必須配置 Redis！**

### 為什麼需要 Redis？

速率限制需要在所有服務實例間共享狀態。預設的記憶體儲存 (in-memory store) 只能在單一實例內運作，無法在多個 Pod 或容器間同步限制計數器。

### 配置步驟

1. **部署 Redis 實例**

   ```bash
   # Kubernetes - 使用 Bitnami Helm Chart
   helm repo add bitnami https://charts.bitnami.com/bitnami
   helm install redis bitnami/redis \
     --namespace synergymesh \
     --set auth.password=your-redis-password \
     --set master.persistence.enabled=true \
     --set replica.replicaCount=2

   # 或使用 Docker Compose（已包含在 docker-compose.production.yml）
   docker-compose -f docker-compose.production.yml up -d redis
   ```

2. **設定環境變數**

   在 `.env.production` 或 Kubernetes ConfigMap/Secret 中設定：

   ```bash
   REDIS_RATE_LIMIT_ENABLED=true
   REDIS_HOST=redis-master.synergymesh.svc.cluster.local  # K8s 服務名稱
   REDIS_PORT=6379
   REDIS_PASSWORD=your-redis-password                      # 建議使用 Secret
   REDIS_DB=0
   REDIS_TLS_ENABLED=false                                 # AWS ElastiCache/Azure Cache 需設為 true
   ```

3. **驗證連線**

   查看服務日誌，確認 Redis 連線成功：

   ```bash
   # Kubernetes
   kubectl logs -n synergymesh -l app=contracts-l1 | grep -i redis

   # 應該看到:
   # Redis client connected for rate limiting
   # Redis client ready for rate limiting
   ```

### 管理式 Redis 服務

生產環境建議使用管理式 Redis 服務：

- **AWS ElastiCache for Redis**: 自動備份、高可用、自動故障轉移
- **Azure Cache for Redis**: 企業級 SLA、進階安全功能
- **Google Cloud Memorystore**: 完全管理、高效能

使用管理式服務時，記得：
- 設定 `REDIS_TLS_ENABLED=true`
- 配置 VPC/VNet 網路訪問
- 使用密鑰管理服務儲存 Redis 密碼

### 監控 Redis

```bash
# 連線到 Redis 查看速率限制鍵
kubectl exec -it redis-master-0 -n synergymesh -- redis-cli
> AUTH your-redis-password
> KEYS rl:*                    # 查看所有速率限制鍵
> TTL rl:127.0.0.1              # 查看某個 IP 的限制剩餘時間
> GET rl:127.0.0.1              # 查看當前請求計數
```

## 🔒 安全最佳實踐

1. **密鑰管理**
   - ❌ 不要將密鑰提交到 Git
   - ✅ 使用外部密鑰管理（AWS Secrets Manager, Azure Key Vault）
   - ✅ 定期輪換密鑰
   - ✅ Redis 密碼必須使用 Kubernetes Secret

2. **網路安全**
   - ✅ 使用 NetworkPolicy 限制 Pod 間通訊
   - ✅ 僅暴露必要的端口
   - ✅ 啟用 HTTPS/TLS
   - ✅ Redis 應只允許服務 Pod 訪問（不對外暴露）

3. **容器安全**
   - ✅ 使用非 root 使用者運行
   - ✅ 只讀根檔案系統
   - ✅ Drop 所有 capabilities
   - ✅ 定期掃描映像漏洞（Trivy）

4. **訪問控制**
   - ✅ 使用 RBAC 限制權限
   - ✅ 不要自動掛載 ServiceAccount Token
   - ✅ 啟用 Pod Security Standards

5. **速率限制 (Rate Limiting)**
   - ✅ 生產環境必須啟用 Redis 儲存
   - ✅ 配置適當的速率限制閾值
   - ✅ 監控速率限制觸發次數

## 📊 監控與告警

### Prometheus 指標

```bash
# 查看指標
curl http://contracts-l1.synergymesh.com:9090/metrics
```

### Grafana 儀表板

1. 匯入 `grafana-dashboard.json`
2. 配置 Prometheus 資料來源
3. 查看即時指標

### 告警通知

配置 Alertmanager 接收告警：

- Slack
- Email
- PagerDuty
- Webhook

## 🐛 故障排除

### Pod 無法啟動

```bash
# 查看 Pod 狀態
kubectl describe pod -n synergymesh -l app=contracts-l1

# 查看事件
kubectl get events -n synergymesh --sort-by='.lastTimestamp'
```

### 健康檢查失敗

```bash
# 進入 Pod
kubectl exec -it -n synergymesh <pod-name> -- sh

# 手動測試健康檢查
curl http://localhost:3000/healthz
```

### 效能問題

```bash
# 查看資源使用
kubectl top pods -n synergymesh -l app=contracts-l1

# 查看 HPA 狀態
kubectl get hpa -n synergymesh
```

### Redis 連線問題

```bash
# 檢查服務日誌中的 Redis 錯誤
kubectl logs -n synergymesh -l app=contracts-l1 | grep -i "redis\|rate limit"

# 常見錯誤訊息:
# "Redis client error: connect ECONNREFUSED"
#   -> 檢查 REDIS_HOST 和 REDIS_PORT 是否正確
#   -> 確認 Redis Pod 是否正在運行

# "Redis client error: NOAUTH Authentication required"
#   -> 確認 REDIS_PASSWORD 設定正確

# "Rate limiting will fail open if Redis is unavailable"
#   -> 正常警告，當 Redis 暫時不可用時，速率限制會允許請求通過

# 測試 Redis 連線
kubectl run redis-client --rm -it --restart=Never \
  --image=redis:7-alpine \
  --namespace=synergymesh \
  -- redis-cli -h redis-master -a your-redis-password ping
# 應該返回: PONG

# 檢查 Redis Pod 狀態
kubectl get pods -n synergymesh -l app.kubernetes.io/name=redis
kubectl describe pod -n synergymesh redis-master-0
```

## 📚 相關文件

- [部署計劃](/docs/TIER1_CONTRACTS_L1_DEPLOYMENT_PLAN.md)
- [CI/CD Workflow](/.github/workflows/deploy-contracts-l1.yml)
- [部署評估](/docs/DEPLOYMENT_ASSESSMENT.md)
- [Dockerfile](../Dockerfile)
- [SLSA 整合報告](../SLSA_INTEGRATION_REPORT.md)

## 📞 支援

- **平台團隊**: <platform@isynergymesh.com>
- **DevOps 團隊**: <devops@isynergymesh.com>
- **緊急聯絡**: <incident@isynergymesh.com>
- **Slack**: #contracts-l1-support

---

**最後更新**: 2025-11-24  
**維護者**: Platform Governance Team
