# MCP Level 3 部署指南

## 目錄
1. [前置要求](#前置要求)
2. [快速開始](#快速開始)
3. [配置說明](#配置說明)
4. [Kubernetes 部署](#kubernetes-部署)
5. [監控與告警](#監控與告警)
6. [故障排除](#故障排除)

## 前置要求

### 系統要求
- **Kubernetes**: v1.24+
- **Node.js**: v18+
- **Docker**: v20+
- **Helm**: v3+

### 資源要求
- **最小配置**:
  - CPU: 2 cores
  - Memory: 4 GB
  - Storage: 20 GB

- **推薦配置**:
  - CPU: 4 cores
  - Memory: 8 GB
  - Storage: 100 GB

### 依賴服務
- PostgreSQL 14+ (Artifact Registry)
- Redis 7+ (Cache)
- Elasticsearch 8+ (日誌聚合)
- Prometheus (監控)
- Jaeger (追蹤)

## 快速開始

### 1. 克隆倉庫

```bash
git clone https://github.com/MachineNativeOps/machine-native-ops.git
cd machine-native-ops/00-namespaces/mcp-level3
```

### 2. 安裝依賴

```bash
npm install
```

### 3. 配置環境變量

```bash
cp .env.example .env
# 編輯 .env 文件，設置必要的環境變量
```

### 4. 本地開發運行

```bash
# 啟動所有引擎
npm run dev

# 或單獨啟動特定引擎
npm run dev:rag
npm run dev:dag
npm run dev:governance
```

### 5. 驗證部署

```bash
# 健康檢查
curl http://localhost:8080/health

# API 文檔
open http://localhost:8080/api/docs
```

## 配置說明

### Engine Map 配置

編輯 `config/engine_map.yaml`:

```yaml
engine_map:
  RAG_engine:
    semantic_role: "Contextual Retrieval and Generation"
    modules:
      - VectorRAG
      - GraphRAG
      - HybridRAG
    # ... 其他配置
```

### API Routes 配置

編輯 `endpoints/api-routes.yaml`:

```yaml
api_version: "v1"
base_path: "/api/v1"
protocol: ["REST", "JSON-RPC"]
# ... 其他配置
```

### 安全配置

編輯 `security/auth-config.yaml`:

```yaml
authentication:
  oauth2:
    enabled: true
    provider: "auth0"
    client_id: "${OAUTH_CLIENT_ID}"
    client_secret: "${OAUTH_CLIENT_SECRET}"
  
  jwt:
    enabled: true
    secret: "${JWT_SECRET}"
    expiry: "24h"
  
  api_key:
    enabled: true
    header: "X-API-Key"
```

## Kubernetes 部署

### 1. 創建 Namespace

```bash
kubectl create namespace mcp-level3
```

### 2. 部署配置 ConfigMap

```bash
kubectl create configmap engine-map \
  --from-file=config/engine_map.yaml \
  -n mcp-level3

kubectl create configmap api-routes \
  --from-file=endpoints/api-routes.yaml \
  -n mcp-level3
```

### 3. 部署 Secrets

```bash
kubectl create secret generic mcp-secrets \
  --from-literal=jwt-secret="${JWT_SECRET}" \
  --from-literal=db-password="${DB_PASSWORD}" \
  -n mcp-level3
```

### 4. 使用 Helm 部署

```bash
# 添加 Helm repository
helm repo add mcp https://charts.mcp.io
helm repo update

# 安裝 MCP Level 3
helm install mcp-level3 mcp/mcp-level3 \
  --namespace mcp-level3 \
  --values values.yaml
```

### 5. 驗證部署

```bash
# 檢查 Pods 狀態
kubectl get pods -n mcp-level3

# 檢查 Services
kubectl get svc -n mcp-level3

# 查看日誌
kubectl logs -f deployment/mcp-control-plane -n mcp-level3
```

## Helm Values 配置

創建 `values.yaml`:

```yaml
# values.yaml
replicaCount: 3

image:
  repository: mcp-level3
  tag: "1.0.0"
  pullPolicy: IfNotPresent

service:
  type: LoadBalancer
  port: 8080

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: mcp.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: mcp-tls
      hosts:
        - mcp.example.com

resources:
  limits:
    cpu: 1000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 1Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

# 引擎配置
engines:
  rag:
    enabled: true
    vectorStore:
      type: "pgvector"
      connectionString: "${VECTOR_DB_URL}"
    graphStore:
      type: "neo4j"
      uri: "${NEO4J_URI}"
  
  dag:
    enabled: true
    maxNodes: 10000
  
  governance:
    enabled: true
    auditLevel: "full"
  
  taxonomy:
    enabled: true
    ontologyPath: "/config/ontology.owl"
  
  execution:
    enabled: true
    maxConcurrency: 100
  
  validation:
    enabled: true
    strictMode: true
  
  promotion:
    enabled: true
    approvalRequired: true
  
  registry:
    enabled: true
    storageClass: "fast-ssd"

# 可觀測性配置
observability:
  tracing:
    enabled: true
    jaeger:
      endpoint: "http://jaeger-collector:14268/api/traces"
  
  metrics:
    enabled: true
    prometheus:
      port: 9090
      path: /metrics
  
  logging:
    level: "info"
    format: "json"

# 安全配置
security:
  rbac:
    enabled: true
  
  networkPolicy:
    enabled: true
  
  podSecurityPolicy:
    enabled: true
```

## 監控與告警

### 1. Prometheus 配置

```yaml
# prometheus-config.yaml
scrape_configs:
  - job_name: 'mcp-level3'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - mcp-level3
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: mcp-level3
```

### 2. Grafana Dashboard

導入預配置的 Dashboard:

```bash
# 導入 Dashboard JSON
kubectl create configmap grafana-dashboard \
  --from-file=observability/grafana-dashboard.json \
  -n monitoring
```

### 3. 告警規則

```yaml
# alerting-rules.yaml
groups:
  - name: mcp-level3
    interval: 30s
    rules:
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency detected"
      
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
```

## 故障排除

### 常見問題

#### 1. Pod 無法啟動

**症狀**: Pod 處於 CrashLoopBackOff 狀態

**解決方案**:
```bash
# 查看 Pod 日誌
kubectl logs <pod-name> -n mcp-level3

# 查看 Pod 事件
kubectl describe pod <pod-name> -n mcp-level3

# 檢查配置
kubectl get configmap engine-map -n mcp-level3 -o yaml
```

#### 2. 高延遲

**症狀**: API 響應時間過長

**解決方案**:
```bash
# 檢查資源使用
kubectl top pods -n mcp-level3

# 增加副本數
kubectl scale deployment mcp-control-plane --replicas=5 -n mcp-level3

# 檢查數據庫連接
kubectl exec -it <pod-name> -n mcp-level3 -- psql -h $DB_HOST -U $DB_USER
```

#### 3. 內存洩漏

**症狀**: 內存使用持續增長

**解決方案**:
```bash
# 查看內存使用趨勢
kubectl top pods -n mcp-level3 --containers

# 重啟 Pod
kubectl rollout restart deployment/mcp-control-plane -n mcp-level3

# 啟用內存分析
kubectl set env deployment/mcp-control-plane NODE_OPTIONS="--max-old-space-size=2048" -n mcp-level3
```

#### 4. 連接超時

**症狀**: 無法連接到外部服務

**解決方案**:
```bash
# 檢查網絡策略
kubectl get networkpolicies -n mcp-level3

# 測試連接
kubectl run -it --rm debug --image=nicolaka/netshoot -n mcp-level3 -- bash
# 在容器內: curl http://service-name:port

# 檢查 DNS
kubectl exec -it <pod-name> -n mcp-level3 -- nslookup service-name
```

### 日誌收集

```bash
# 收集所有 Pod 日誌
kubectl logs -l app=mcp-level3 -n mcp-level3 --tail=1000 > mcp-logs.txt

# 實時查看日誌
kubectl logs -f deployment/mcp-control-plane -n mcp-level3

# 查看特定引擎日誌
kubectl logs -f deployment/mcp-control-plane -n mcp-level3 | grep "RAG_engine"
```

### 性能分析

```bash
# CPU 分析
kubectl exec -it <pod-name> -n mcp-level3 -- node --prof app.js

# 內存快照
kubectl exec -it <pod-name> -n mcp-level3 -- node --heapsnapshot app.js

# 追蹤分析
kubectl port-forward svc/jaeger-query 16686:16686 -n mcp-level3
open http://localhost:16686
```

## 升級指南

### 滾動升級

```bash
# 更新鏡像
kubectl set image deployment/mcp-control-plane \
  control-plane=mcp-level3:1.1.0 \
  -n mcp-level3

# 監控升級進度
kubectl rollout status deployment/mcp-control-plane -n mcp-level3

# 回滾（如需要）
kubectl rollout undo deployment/mcp-control-plane -n mcp-level3
```

### 藍綠部署

```bash
# 部署新版本（綠）
kubectl apply -f deployment-green.yaml

# 切換流量
kubectl patch service mcp-level3 -p '{"spec":{"selector":{"version":"green"}}}'

# 驗證後刪除舊版本（藍）
kubectl delete deployment mcp-control-plane-blue
```

### 金絲雀部署

```bash
# 使用 Flagger 進行金絲雀部署
kubectl apply -f canary.yaml

# 監控金絲雀進度
kubectl get canary mcp-level3 -n mcp-level3 -w
```

## 備份與恢復

### 備份配置

```bash
# 備份所有配置
kubectl get all,configmap,secret -n mcp-level3 -o yaml > mcp-backup.yaml

# 備份 PVC
kubectl get pvc -n mcp-level3 -o yaml > pvc-backup.yaml
```

### 恢復配置

```bash
# 恢復配置
kubectl apply -f mcp-backup.yaml

# 恢復 PVC
kubectl apply -f pvc-backup.yaml
```

## 安全加固

### 1. 網絡策略

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mcp-network-policy
  namespace: mcp-level3
spec:
  podSelector:
    matchLabels:
      app: mcp-level3
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8080
  egress:
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: TCP
          port: 5432  # PostgreSQL
        - protocol: TCP
          port: 6379  # Redis
```

### 2. Pod Security Policy

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: mcp-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

## 性能調優

### 1. 資源限制優化

```yaml
resources:
  requests:
    cpu: "500m"
    memory: "1Gi"
  limits:
    cpu: "2000m"
    memory: "4Gi"
```

### 2. 連接池配置

```javascript
// database.config.js
module.exports = {
  pool: {
    min: 10,
    max: 50,
    acquireTimeoutMillis: 30000,
    idleTimeoutMillis: 30000
  }
};
```

### 3. 緩存策略

```yaml
cache:
  redis:
    enabled: true
    ttl: 3600
    maxSize: 1000
  memory:
    enabled: true
    maxSize: 500
```

## 聯繫支持

- **文檔**: https://docs.mcp.io
- **GitHub**: https://github.com/MachineNativeOps/machine-native-ops
- **Discord**: https://discord.gg/mcp
- **Email**: support@mcp.io

---

**最後更新**: 2024-01-20  
**版本**: 1.0.0