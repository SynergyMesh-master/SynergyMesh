# Kubernetes 部署

## 需求

- Kubernetes 1.25+
- Helm 3.12+
- Ingress Controller (NGINX/Traefik)
- Cert-Manager（建議）

## 安裝

```bash
helm repo add island-ai https://charts.island-ai.dev
helm install island-platform island-ai/control-plane \
  --namespace island-ai \
  --create-namespace \
  -f deploy/values-prod.yaml
```

## 自訂值

```yaml
controlPlane:
  replicas: 3
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
observability:
  enabled: true
  grafana:
    ingress: grafana.island.local
security:
  slsaVerification: true
```

## 日常操作

```bash
kubectl get pods -n island-ai
kubectl logs deployment/island-platform -n island-ai
kubectl rollout restart deployment/island-platform -n island-ai
```

## 災難復原

- 使用 Velero 備份
- etcd 快照
- 多區域部署 + Traffic Manager
