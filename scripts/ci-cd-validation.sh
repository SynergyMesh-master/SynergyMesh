#!/bin/bash

###############################################################################
# CI/CD System Validation Script
# Comprehensive testing and validation of all CI/CD components
###############################################################################

set -euo pipefail

# Configuration
APP_NAME="${APP_NAME:-machine-native-ops}"
NAMESPACE="${NAMESPACE:-default}"
MONITORING_NAMESPACE="${MONITORING_NAMESPACE:-monitoring}"
VALIDATION_LOG="/var/log/ci-cd-validation.log"
TEST_RESULTS_DIR="/tmp/ci-cd-validation-results"
MAX_RETRIES=3
RETRY_DELAY=10

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
    log_to_file "INFO: $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    log_to_file "WARN: $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    log_to_file "ERROR: $1"
}

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
    log_to_file "TEST: $1"
}

log_to_file() {
    mkdir -p "$(dirname "$VALIDATION_LOG")"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$VALIDATION_LOG"
}

# Test result recording
record_test_result() {
    local test_name=$1
    local result=$2
    local message=$3
    
    ((TOTAL_TESTS++))
    
    if [ "$result" == "PASS" ]; then
        ((PASSED_TESTS++))
        echo "✅ $test_name: $result"
    else
        ((FAILED_TESTS++))
        echo "❌ $test_name: $result - $message"
    fi
    
    # Save to results file
    mkdir -p "$TEST_RESULTS_DIR"
    echo "$test_name,$result,$message" >> "$TEST_RESULTS_DIR/results.csv"
}

# Helper functions
check_kubernetes_connection() {
    log_test "Checking Kubernetes connection..."
    if kubectl cluster-info &> /dev/null; then
        record_test_result "Kubernetes Connection" "PASS" "Cluster is accessible"
        return 0
    else
        record_test_result "Kubernetes Connection" "FAIL" "Cannot connect to cluster"
        return 1
    fi
}

check_namespace_exists() {
    local namespace=$1
    log_test "Checking if namespace $namespace exists..."
    
    if kubectl get namespace "$namespace" &> /dev/null; then
        record_test_result "Namespace $namespace" "PASS" "Namespace exists"
        return 0
    else
        record_test_result "Namespace $namespace" "FAIL" "Namespace does not exist"
        return 1
    fi
}

check_deployment_exists() {
    local deployment=$1
    local namespace=$2
    log_test "Checking if deployment $deployment exists in $namespace..."
    
    if kubectl get deployment "$deployment" -n "$namespace" &> /dev/null; then
        record_test_result "Deployment $deployment" "PASS" "Deployment exists"
        return 0
    else
        record_test_result "Deployment $deployment" "FAIL" "Deployment does not exist"
        return 1
    fi
}

check_deployment_ready() {
    local deployment=$1
    local namespace=$2
    log_test "Checking if deployment $deployment is ready in $namespace..."
    
    local ready_replicas=$(kubectl get deployment "$deployment" -n "$namespace" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    local desired_replicas=$(kubectl get deployment "$deployment" -n "$namespace" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
    
    if [ "$ready_replicas" == "$desired_replicas" ] && [ "$ready_replicas" != "0" ]; then
        record_test_result "Deployment $deployment Ready" "PASS" "$ready_replicas/$desired_replicas replicas ready"
        return 0
    else
        record_test_result "Deployment $deployment Ready" "FAIL" "$ready_replicas/$desired_replicas replicas ready"
        return 1
    fi
}

check_pod_health() {
    local app_label=$1
    local namespace=$2
    log_test "Checking pod health for $app_label in $namespace..."
    
    local unhealthy_pods=$(kubectl get pods -n "$namespace" -l app="$app_label" \
        -o jsonpath='{.items[?(@.status.phase!="Running" || @.status.conditions[?(@.type=="Ready")].status!="True")].metadata.name}')
    
    if [ -z "$unhealthy_pods" ]; then
        record_test_result "Pod Health $app_label" "PASS" "All pods are healthy"
        return 0
    else
        record_test_result "Pod Health $app_label" "FAIL" "Unhealthy pods: $unhealthy_pods"
        return 1
    fi
}

check_service_exists() {
    local service=$1
    local namespace=$2
    log_test "Checking if service $service exists in $namespace..."
    
    if kubectl get service "$service" -n "$namespace" &> /dev/null; then
        record_test_result "Service $service" "PASS" "Service exists"
        return 0
    else
        record_test_result "Service $service" "FAIL" "Service does not exist"
        return 1
    fi
}

check_argo_rollouts() {
    log_test "Checking Argo Rollouts installation..."
    
    if kubectl argo rollouts version &> /dev/null; then
        record_test_result "Argo Rollouts CLI" "PASS" "CLI is installed"
        
        # Check if rollout exists
        if kubectl get argo rollouts "$APP_NAME" -n "$NAMESPACE" &> /dev/null; then
            record_test_result "Argo Rollout $APP_NAME" "PASS" "Rollout exists"
            return 0
        else
            record_test_result "Argo Rollout $APP_NAME" "FAIL" "Rollout does not exist"
            return 1
        fi
    else
        record_test_result "Argo Rollouts CLI" "FAIL" "CLI is not installed"
        return 1
    fi
}

check_rollout_status() {
    log_test "Checking rollout status for $APP_NAME..."
    
    local status=$(kubectl get argo rollouts "$APP_NAME" -n "$NAMESPACE" -o jsonpath='{.status.phase}' 2>/dev/null || echo "Unknown")
    
    if [ "$status" == "Healthy" ]; then
        record_test_result "Rollout Status" "PASS" "Rollout is healthy"
        return 0
    else
        record_test_result "Rollout Status" "FAIL" "Rollout status: $status"
        return 1
    fi
}

check_prometheus() {
    log_test "Checking Prometheus deployment..."
    
    if check_deployment_exists "prometheus" "$MONITORING_NAMESPACE"; then
        if check_deployment_ready "prometheus" "$MONITORING_NAMESPACE"; then
            # Test Prometheus query
            local prometheus_pod=$(kubectl get pods -n "$MONITORING_NAMESPACE" -l app=prometheus -o jsonpath='{.items[0].metadata.name}')
            
            if [ -n "$prometheus_pod" ]; then
                # Port-forward to query Prometheus
                kubectl port-forward "$prometheus_pod" 9090:9090 -n "$MONITORING_NAMESPACE" &
                local pf_pid=$!
                sleep 5
                
                # Query Prometheus
                if curl -s 'http://localhost:9090/api/v1/query?query=up' | grep -q "success"; then
                    record_test_result "Prometheus Query" "PASS" "Prometheus is responding"
                    kill $pf_pid 2>/dev/null || true
                    return 0
                else
                    record_test_result "Prometheus Query" "FAIL" "Prometheus is not responding"
                    kill $pf_pid 2>/dev/null || true
                    return 1
                fi
            fi
        fi
    fi
    
    return 1
}

check_grafana() {
    log_test "Checking Grafana deployment..."
    
    if check_deployment_exists "grafana" "$MONITORING_NAMESPACE"; then
        if check_deployment_ready "grafana" "$MONITORING_NAMESPACE"; then
            # Test Grafana accessibility
            local grafana_pod=$(kubectl get pods -n "$MONITORING_NAMESPACE" -l app=grafana -o jsonpath='{.items[0].metadata.name}')
            
            if [ -n "$grafana_pod" ]; then
                # Port-forward to test Grafana
                kubectl port-forward "$grafana_pod" 3000:3000 -n "$MONITORING_NAMESPACE" &
                local pf_pid=$!
                sleep 5
                
                # Test Grafana HTTP endpoint
                if curl -s -f 'http://localhost:3000/api/health' > /dev/null 2>&1; then
                    record_test_result "Grafana Health" "PASS" "Grafana is accessible"
                    kill $pf_pid 2>/dev/null || true
                    return 0
                else
                    record_test_result "Grafana Health" "FAIL" "Grafana is not accessible"
                    kill $pf_pid 2>/dev/null || true
                    return 1
                fi
            fi
        fi
    fi
    
    return 1
}

check_alerts_config() {
    log_test "Checking Prometheus alerts configuration..."
    
    if kubectl get configmap prometheus-alerts -n "$MONITORING_NAMESPACE" &> /dev/null; then
        local alert_count=$(kubectl get configmap prometheus-alerts -n "$MONITORING_NAMESPACE" \
            -o jsonpath='{.data.alerts\.yml}' | grep -c "alert:" || echo "0")
        
        if [ "$alert_count" -gt 0 ]; then
            record_test_result "Alerts Configuration" "PASS" "$alert_count alerts configured"
            return 0
        else
            record_test_result "Alerts Configuration" "FAIL" "No alerts configured"
            return 1
        fi
    else
        record_test_result "Alerts Configuration" "FAIL" "Alerts configmap not found"
        return 1
    fi
}

check_secrets_rotation_script() {
    log_test "Checking secrets rotation script..."
    
    if [ -f "scripts/secrets_rotation.py" ]; then
        if python3 -m py_compile "scripts/secrets_rotation.py" 2>/dev/null; then
            record_test_result "Secrets Rotation Script" "PASS" "Script is valid Python"
            return 0
        else
            record_test_result "Secrets Rotation Script" "FAIL" "Script has syntax errors"
            return 1
        fi
    else
        record_test_result "Secrets Rotation Script" "FAIL" "Script not found"
        return 1
    fi
}

check_rollback_mechanism() {
    log_test "Checking rollback mechanism script..."
    
    if [ -f "scripts/rollback-mechanism.sh" ]; then
        if bash -n "scripts/rollback-mechanism.sh" 2>/dev/null; then
            record_test_result "Rollback Mechanism Script" "PASS" "Script is valid Bash"
            return 0
        else
            record_test_result "Rollback Mechanism Script" "FAIL" "Script has syntax errors"
            return 1
        fi
    else
        record_test_result "Rollback Mechanism Script" "FAIL" "Script not found"
        return 1
    fi
}

check_drill_simulation() {
    log_test "Checking drill simulation script..."
    
    if [ -f "scripts/drill-simulation.sh" ]; then
        if bash -n "scripts/drill-simulation.sh" 2>/dev/null; then
            record_test_result "Drill Simulation Script" "PASS" "Script is valid Bash"
            return 0
        else
            record_test_result "Drill Simulation Script" "FAIL" "Script has syntax errors"
            return 1
        fi
    else
        record_test_result "Drill Simulation Script" "FAIL" "Script not found"
        return 1
    fi
}

check_documentation() {
    log_test "Checking documentation files..."
    
    local missing_docs=0
    
    if [ ! -f "docs/github-secrets-setup-guide.md" ]; then
        ((missing_docs++))
    fi
    
    if [ ! -f "docs/team-training-guide.md" ]; then
        ((missing_docs++))
    fi
    
    if [ $missing_docs -eq 0 ]; then
        record_test_result "Documentation" "PASS" "All documentation files exist"
        return 0
    else
        record_test_result "Documentation" "FAIL" "$missing_docs documentation files missing"
        return 1
    fi
}

check_config_files() {
    log_test "Checking configuration files..."
    
    local missing_configs=0
    
    if [ ! -f "charts/argo-rollout.yaml" ]; then
        ((missing_configs++))
    fi
    
    if [ ! -f "monitoring/grafana-dashboard.json" ]; then
        ((missing_configs++))
    fi
    
    if [ ! -f "monitoring/prometheus-alerts.yaml" ]; then
        ((missing_configs++))
    fi
    
    if $missing_configs -eq 0 ]; then
        record_test_result "Configuration Files" "PASS" "All configuration files exist"
        return 0
    else
        record_test_result "Configuration Files" "FAIL" "$missing_configs configuration files missing"
        return 1
    fi
}

# Run all validation tests
run_all_tests() {
    log_info "Starting CI/CD System Validation..."
    log_info "Validation log: $VALIDATION_LOG"
    log_info "Test results: $TEST_RESULTS_DIR/results.csv"
    echo ""
    
    # Clear previous results
    rm -rf "$TEST_RESULTS_DIR"
    mkdir -p "$TEST_RESULTS_DIR"
    echo "Test Name,Result,Message" > "$TEST_RESULTS_DIR/results.csv"
    
    # Infrastructure tests
    log_info "=== Infrastructure Tests ==="
    check_kubernetes_connection
    check_namespace_exists "$NAMESPACE"
    check_namespace_exists "$MONITORING_NAMESPACE"
    echo ""
    
    # Application deployment tests
    log_info "=== Application Deployment Tests ==="
    check_deployment_exists "$APP_NAME" "$NAMESPACE"
    check_deployment_ready "$APP_NAME" "$NAMESPACE"
    check_pod_health "$APP_NAME" "$NAMESPACE"
    check_service_exists "$APP_NAME" "$NAMESPACE"
    echo ""
    
    # Argo Rollouts tests
    log_info "=== Argo Rollouts Tests ==="
    check_argo_rollouts
    check_rollout_status
    echo ""
    
    # Monitoring tests
    log_info "=== Monitoring Tests ==="
    check_deployment_exists "prometheus" "$MONITORING_NAMESPACE"
    check_deployment_ready "prometheus" "$MONITORING_NAMESPACE"
    check_deployment_exists "grafana" "$MONITORING_NAMESPACE"
    check_deployment_ready "grafana" "$MONITORING_NAMESPACE"
    check_prometheus
    check_grafana
    check_alerts_config
    echo ""
    
    # Automation scripts tests
    log_info "=== Automation Scripts Tests ==="
    check_secrets_rotation_script
    check_rollback_mechanism
    check_drill_simulation
    echo ""
    
    # Documentation tests
    log_info "=== Documentation Tests ==="
    check_documentation
    check_config_files
    echo ""
    
    # Print summary
    print_summary
}

# Print test summary
print_summary() {
    log_info "Validation Summary"
    log_info "=================="
    log_info "Total Tests: $TOTAL_TESTS"
    log_info "Passed: $PASSED_TESTS"
    log_info "Failed: $FAILED_TESTS"
    
    local success_rate=0
    if [ $TOTAL_TESTS -gt 0 ]; then
        success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    fi
    
    log_info "Success Rate: ${success_rate}%"
    log_info "Log file: $VALIDATION_LOG"
    log_info "Results: $TEST_RESULTS_DIR/results.csv"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        log_info "✅ All tests passed!"
        return 0
    else
        log_warn "⚠️  Some tests failed - review logs"
        return 1
    fi
}

# Main execution
main() {
    case "${1:-all}" in
        all)
            run_all_tests
            ;;
        infrastructure)
            check_kubernetes_connection
            check_namespace_exists "$NAMESPACE"
            check_namespace_exists "$MONITORING_NAMESPACE"
            ;;
        deployment)
            check_deployment_exists "$APP_NAME" "$NAMESPACE"
            check_deployment_ready "$APP_NAME" "$NAMESPACE"
            check_pod_health "$APP_NAME" "$NAMESPACE"
            ;;
        rollouts)
            check_argo_rollouts
            check_rollout_status
            ;;
        monitoring)
            check_prometheus
            check_grafana
            check_alerts_config
            ;;
        scripts)
            check_secrets_rotation_script
            check_rollback_mechanism
            check_drill_simulation
            ;;
        docs)
            check_documentation
            check_config_files
            ;;
        *)
            echo "Usage: $0 {all|infrastructure|deployment|rollouts|monitoring|scripts|docs}"
            echo ""
            echo "Test Categories:"
            echo "  all            Run all validation tests"
            echo "  infrastructure  Test Kubernetes infrastructure"
            echo "  deployment     Test application deployment"
            echo "  rollouts       Test Argo Rollouts configuration"
            echo "  monitoring     Test monitoring stack"
            echo "  scripts        Test automation scripts"
            echo "  docs           Test documentation and configs"
            exit 1
            ;;
    esac
}

main "$@"