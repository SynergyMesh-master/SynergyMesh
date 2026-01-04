#!/bin/bash

###############################################################################
# Monitoring Stack Setup Script
# Deploys Prometheus, Grafana, and AlertManager with CI/CD monitoring
###############################################################################

set -euo pipefail

# Configuration
NAMESPACE="${NAMESPACE:-monitoring}"
PROMETHEUS_VERSION="${PROMETHEUS_VERSION:-v2.45.0}"
GRAFANA_VERSION="${GRAFANA_VERSION:-10.0.0}"
ALERTMANAGER_VERSION="${ALERTMANAGER_VERSION:-v0.25.0}"

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Please install kubectl."
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_info "Creating namespace: $NAMESPACE"
        kubectl create namespace "$NAMESPACE"
    fi
    
    log_info "✅ Prerequisites check passed"
}

# Deploy Prometheus
deploy_prometheus() {
    log_info "Deploying Prometheus..."
    
    # Create ConfigMap for alerts
    kubectl apply -f monitoring/prometheus-alerts.yaml -n "$NAMESPACE"
    
    # Deploy Prometheus using Helm (simplified for demonstration)
    cat <<EOF | kubectl apply -n "$NAMESPACE" -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  labels:
    app: prometheus
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:${PROMETHEUS_VERSION}
        ports:
        - containerPort: 9090
        args:
          - '--config.file=/etc/prometheus/prometheus.yml'
          - '--storage.tsdb.path=/prometheus'
          - '--web.console.libraries=/etc/prometheus/console_libraries'
          - '--web.console.templates=/etc/prometheus/consoles'
          - '--web.enable-lifecycle'
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
        - name: alerts
          mountPath: /etc/prometheus/alerts
        - name: storage
          mountPath: /prometheus
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
      volumes:
      - name: config
        configMap:
          name: prometheus-config
      - name: alerts
        configMap:
          name: prometheus-alerts
      - name: storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus
spec:
  selector:
    app: prometheus
  ports:
  - port: 9090
    targetPort: 9090
  type: ClusterIP
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    rule_files:
      - "/etc/prometheus/alerts/*.yml"
    scrape_configs:
      - job_name: 'argo-rollouts'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_label_app]
            regex: machine-native-ops
            action: keep
          - source_labels: [__meta_kubernetes_pod_ip]
            target_label: __address__
            replacement: $1:8080
      - job_name: 'prometheus'
        static_configs:
          - targets: ['localhost:9090']
      - job_name: 'kubernetes-pods'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
            regex: true
            action: keep
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
            regex: (.+)
            target_label: __metrics_path__
            replacement: $1
          - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
            regex: ([^:]+)(?::\d+)?;(\d+)
            replacement: $1:$2
            target_label: __address__
EOF
    
    log_info "✅ Prometheus deployed"
}

# Deploy Grafana
deploy_grafana() {
    log_info "Deploying Grafana..."
    
    cat <<EOF | kubectl apply -n "$NAMESPACE" -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  labels:
    app: grafana
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:${GRAFANA_VERSION}
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          value: "admin"
        - name: GF_INSTALL_PLUGINS
          value: "grafana-piechart-panel"
        volumeMounts:
        - name: dashboards
          mountPath: /etc/grafana/provisioning/dashboards
        - name: dashboard-definitions
          mountPath: /var/lib/grafana/dashboards
        resources:
          requests:
            memory: "256Mi"
            cpu: "125m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      volumes:
      - name: dashboards
        configMap:
          name: grafana-dashboards-config
      - name: dashboard-definitions
        configMap:
          name: grafana-dashboards
---
apiVersion: v1
kind: Service
metadata:
  name: grafana
spec:
  selector:
    app: grafana
  ports:
  - port: 3000
    targetPort: 3000
  type: ClusterIP
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards-config
data:
  dashboards.yml: |
    apiVersion: 1
    providers:
      - name: 'Default'
        orgId: 1
        folder: ''
        type: file
        disableDeletion: false
        editable: true
        options:
          path: /var/lib/grafana/dashboards
EOF
    
    # Create dashboard ConfigMap
    kubectl create configmap grafana-dashboards \
        --from-file=monitoring/grafana-dashboard.json \
        -n "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -n "$NAMESPACE" -f -
    
    log_info "✅ Grafana deployed"
}

# Deploy AlertManager
deploy_alertmanager() {
    log_info "Deploying AlertManager..."
    
    cat <<EOF | kubectl apply -n "$NAMESPACE" -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alertmanager
  labels:
    app: alertmanager
spec:
  replicas: 1
  selector:
    matchLabels:
      app: alertmanager
  template:
    metadata:
      labels:
        app: alertmanager
    spec:
      containers:
      - name: alertmanager
        image: prom/alertmanager:${ALERTMANAGER_VERSION}
        ports:
        - containerPort: 9093
        args:
          - '--config.file=/etc/alertmanager/alertmanager.yml'
          - '--storage.path=/alertmanager'
        volumeMounts:
        - name: config
          mountPath: /etc/alertmanager
        - name: storage
          mountPath: /alertmanager
---
apiVersion: v1
kind: Service
metadata:
  name: alertmanager
spec:
  selector:
    app: alertmanager
  ports:
  - port: 9093
    targetPort: 9093
  type: ClusterIP
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
data:
  alertmanager.yml: |
    global:
      resolve_timeout: 5m
    route:
      group_by: ['alertname', 'severity']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 1h
      receiver: 'default'
      routes:
        - match:
            severity: critical
          receiver: 'critical-alerts'
        - match:
            severity: warning
          receiver: 'warning-alerts'
    receivers:
      - name: 'default'
      - name: 'critical-alerts'
        webhook_configs:
          - url: 'http://slack-webhook-service:8080/critical'
      - name: 'warning-alerts'
        webhook_configs:
          - url: 'http://slack-webhook-service:8080/warning'
EOF
    
    log_info "✅ AlertManager deployed"
}

# Wait for deployments to be ready
wait_for_ready() {
    log_info "Waiting for deployments to be ready..."
    
    local max_wait=300
    local waited=0
    
    while [ $waited -lt $max_wait ]; do
        local prom_ready=$(kubectl get deployment prometheus -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        local grafana_ready=$(kubectl get deployment grafana -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        local alert_ready=$(kubectl get deployment alertmanager -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        
        if [ "$prom_ready" == "1" ] && [ "$grafana_ready" == "1" ] && [ "$alert_ready" == "1" ]; then
            log_info "✅ All deployments are ready"
            return 0
        fi
        
        sleep 5
        waited=$((waited + 5))
        echo -n "."
    done
    
    log_error "Timeout waiting for deployments"
    return 1
}

# Display access information
display_access_info() {
    log_info "Monitoring stack deployed successfully!"
    echo ""
    echo "Access Information:"
    echo "==================="
    echo ""
    echo "To access the monitoring services, use port-forwarding:"
    echo ""
    echo "  Prometheus:"
    echo "    kubectl port-forward svc/prometheus 9090:9090 -n $NAMESPACE"
    echo "    URL: http://localhost:9090"
    echo ""
    echo "  Grafana:"
    echo "    kubectl port-forward svc/grafana 3000:3000 -n $NAMESPACE"
    echo "    URL: http://localhost:3000"
    echo "    Username: admin"
    echo "    Password: admin"
    echo ""
    echo "  AlertManager:"
    echo "    kubectl port-forward svc/alertmanager 9093:9093 -n $NAMESPACE"
    echo "    URL: http://localhost:9093"
    echo ""
    echo "To verify monitoring:"
    echo "  kubectl get pods -n $NAMESPACE"
    echo "  kubectl get services -n $NAMESPACE"
    echo ""
}

# Main execution
main() {
    log_info "Starting monitoring stack deployment..."
    echo ""
    
    check_prerequisites
    deploy_prometheus
    deploy_grafana
    deploy_alertmanager
    wait_for_ready
    display_access_info
    
    log_info "✅ Monitoring stack deployment completed!"
}

main "$@"