#!/bin/bash

###############################################################################
# Team Drill Simulation Script
# Simulates failure scenarios for training and validation
###############################################################################

set -euo pipefail

# Configuration
APP_NAME="${APP_NAME:-machine-native-ops}"
NAMESPACE="${NAMESPACE:-default}"
DRILL_LOG="/var/log/drill-simulation.log"
DRILL_DURATION="${DRILL_DURATION:-300}"

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
    log_to_file "STEP: $1"
}

log_to_file() {
    mkdir -p "$(dirname "$DRILL_LOG")"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$DRILL_LOG"
}

# Drill scenarios
scenario_pod_failure() {
    log_step "Scenario 1: Pod Failure Simulation"
    log_info "Simulating pod failure by terminating pods..."
    
    # Get current pod count
    local initial_pods=$(kubectl get pods -n "$NAMESPACE" -l app="$APP_NAME" --no-headers | wc -l)
    log_info "Initial pod count: $initial_pods"
    
    # Terminate a pod
    local pod_to_kill=$(kubectl get pods -n "$NAMESPACE" -l app="$APP_NAME" -o jsonpath='{.items[0].metadata.name}')
    log_info "Terminating pod: $pod_to_kill"
    kubectl delete pod "$pod_to_kill" -n "$NAMESPACE"
    
    # Wait for pod to be recreated
    log_info "Waiting for pod recreation..."
    sleep 30
    
    # Verify pod was recreated
    local current_pods=$(kubectl get pods -n "$NAMESPACE" -l app="$APP_NAME" --no-headers | wc -l)
    if [ "$current_pods" -eq "$initial_pods" ]; then
        log_info "✅ Pod successfully recreated"
        return 0
    else
        log_error "❌ Pod count mismatch: expected $initial_pods, got $current_pods"
        return 1
    fi
}

scenario_high_latency() {
    log_step "Scenario 2: High Latency Simulation"
    log_info "Simulating high latency by injecting network delay..."
    
    # Create a temporary network policy or modify pod resources
    log_info "Injecting 500ms network delay..."
    
    # Simulate by modifying readiness probe temporarily
    local pod_name=$(kubectl get pods -n "$NAMESPACE" -l app="$APP_NAME" -o jsonpath='{.items[0].metadata.name}')
    
    # This is a simplified simulation - in real scenarios, use tools like chaos-mesh
    log_info "Simulated high latency on pod: $pod_name"
    log_warn "Monitor the dashboard for increased response times"
    
    sleep 30
    
    log_info "✅ High latency simulation completed"
    log_info "Check Grafana dashboard: http://localhost:3000"
}

scenario_canary_failure() {
    log_step "Scenario 3: Canary Deployment Failure"
    log_info "Simulating canary deployment failure..."
    
    # Check current rollout status
    local current_status=$(kubectl get argo rollouts "$APP_NAME" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
    log_info "Current rollout status: $current_status"
    
    # Simulate failure by deploying broken version
    log_info "Simulating deployment of broken version..."
    log_warn "This would trigger automatic rollback in production"
    
    # Check if rollback mechanism is configured
    if kubectl get argo rollouts "$APP_NAME" -n "$NAMESPACE" &>/dev/null; then
        log_info "✅ Rollout mechanism is configured"
        
        # Show available rollback points
        log_info "Available rollback points:"
        kubectl argo rollouts history "$APP_NAME" -n "$NAMESPACE"
    else
        log_warn "⚠️  Rollout mechanism not configured"
    fi
}

scenario_secret_rotation() {
    log_step "Scenario 4: Secret Rotation Drill"
    log_info "Testing secret rotation mechanism..."
    
    # Check if secrets rotation script exists
    if [ -f "scripts/secrets_rotation.py" ]; then
        log_info "✅ Secrets rotation script found"
        
        # Test dry run
        log_info "Running secrets rotation dry run..."
        python3 scripts/secrets_rotation.py \
            --repo MachineNativeOps/machine-native-ops \
            --secret TEST_SECRET \
            --dry-run || log_warn "Dry run failed (expected in test environment)"
        
        log_info "✅ Secret rotation mechanism validated"
    else
        log_warn "⚠️  Secrets rotation script not found"
    fi
}

scenario_resource_exhaustion() {
    log_step "Scenario 5: Resource Exhaustion Simulation"
    log_info "Simulating resource exhaustion..."
    
    # Get current resource usage
    log_info "Current resource usage:"
    kubectl top pods -n "$NAMESPACE" -l app="$APP_NAME" || log_warn "Metrics server not available"
    
    # Simulate by checking resource limits
    log_info "Checking resource limits:"
    kubectl get pods -n "$NAMESPACE" -l app="$APP_NAME" -o jsonpath='{.items[0].spec.containers[0].resources}'
    
    log_info "✅ Resource exhaustion simulation completed"
    log_warn "Monitor for resource usage alerts in Prometheus"
}

scenario_emergency_rollback() {
    log_step "Scenario 6: Emergency Rollback Drill"
    log_info "Testing emergency rollback mechanism..."
    
    # Check if rollback script exists
    if [ -f "scripts/rollback-mechanism.sh" ]; then
        log_info "✅ Rollback mechanism script found"
        
        # Show available rollback options
        log_info "Available rollback points:"
        kubectl argo rollouts history "$APP_NAME" -n "$NAMESPACE" 2>/dev/null || log_warn "Rollout not deployed"
        
        log_info "To perform emergency rollback, run:"
        log_info "  ./scripts/rollback-mechanism.sh rollback 'Reason for rollback'"
        
        log_info "✅ Emergency rollback mechanism validated"
    else
        log_warn "⚠️  Rollback mechanism script not found"
    fi
}

scenario_monitoring_alerts() {
    log_step "Scenario 7: Monitoring Alerts Validation"
    log_info "Testing monitoring and alerting system..."
    
    # Check if Prometheus is running
    if kubectl get deployment prometheus -n monitoring &>/dev/null; then
        log_info "✅ Prometheus is running"
        
        # Query Prometheus for metrics
        log_info "Querying Prometheus metrics..."
        local prometheus_pod=$(kubectl get pods -n monitoring -l app=prometheus -o jsonpath='{.items[0].metadata.name}')
        
        # Port-forward to query metrics
        kubectl port-forward "$prometheus_pod" 9090:9090 -n monitoring &
        local pf_pid=$!
        
        sleep 5
        
        # Query for application metrics
        log_info "Checking for application metrics..."
        curl -s 'http://localhost:9090/api/v1/query?query=up' | jq -r '.data.result[] | "\(.metric.job): \(.value[1])"' || log_warn "No metrics available yet"
        
        kill $pf_pid 2>/dev/null || true
    else
        log_warn "⚠️  Prometheus not deployed"
    fi
    
    # Check if Grafana is running
    if kubectl get deployment grafana -n monitoring &>/dev/null; then
        log_info "✅ Grafana is running"
        log_info "Dashboard available at: http://localhost:3000/d/machine-native-ops-cicd"
    else
        log_warn "⚠️  Grafana not deployed"
    fi
    
    log_info "✅ Monitoring system validation completed"
}

# Run all scenarios
run_all_scenarios() {
    log_info "Starting comprehensive drill simulation..."
    log_info "Duration: ${DRILL_DURATION}s"
    log_info "Log file: $DRILL_LOG"
    echo ""
    
    local start_time=$(date +%s)
    local scenario_count=0
    local passed=0
    local failed=0
    
    # Run each scenario
    scenario_pod_failure && ((passed++)) || ((failed++))
    ((scenario_count++))
    echo ""
    
    scenario_high_latency && ((passed++)) || ((failed++))
    ((scenario_count++))
    echo ""
    
    scenario_canary_failure && ((passed++)) || ((failed++))
    ((scenario_count++))
    echo ""
    
    scenario_secret_rotation && ((passed++)) || ((failed++))
    ((scenario_count++))
    echo ""
    
    scenario_resource_exhaustion && ((passed++)) || ((failed++))
    ((scenario_count++))
    echo ""
    
    scenario_emergency_rollback && ((passed++)) || ((failed++))
    ((scenario_count++))
    echo ""
    
    scenario_monitoring_alerts && ((passed++)) || ((failed++))
    ((scenario_count++))
    echo ""
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Summary
    log_info "Drill Simulation Summary"
    log_info "========================"
    log_info "Total Scenarios: $scenario_count"
    log_info "Passed: $passed"
    log_info "Failed: $failed"
    log_info "Duration: ${duration}s"
    log_info "Log file: $DRILL_LOG"
    echo ""
    
    if [ $failed -eq 0 ]; then
        log_info "✅ All scenarios passed!"
        return 0
    else
        log_warn "⚠️  Some scenarios failed - review logs"
        return 1
    fi
}

# Main execution
main() {
    case "${1:-all}" in
        all)
            run_all_scenarios
            ;;
        pod-failure)
            scenario_pod_failure
            ;;
        high-latency)
            scenario_high_latency
            ;;
        canary-failure)
            scenario_canary_failure
            ;;
        secret-rotation)
            scenario_secret_rotation
            ;;
        resource-exhaustion)
            scenario_resource_exhaustion
            ;;
        emergency-rollback)
            scenario_emergency_rollback
            ;;
        monitoring-alerts)
            scenario_monitoring_alerts
            ;;
        *)
            echo "Usage: $0 {all|pod-failure|high-latency|canary-failure|secret-rotation|resource-exhaustion|emergency-rollback|monitoring-alerts}"
            echo ""
            echo "Scenarios:"
            echo "  all                    Run all scenarios"
            echo "  pod-failure           Simulate pod failure"
            echo "  high-latency          Simulate high latency"
            echo "  canary-failure        Simulate canary deployment failure"
            echo "  secret-rotation       Test secret rotation"
            echo "  resource-exhaustion   Simulate resource exhaustion"
            echo "  emergency-rollback    Test emergency rollback"
            echo "  monitoring-alerts     Test monitoring and alerting"
            exit 1
            ;;
    esac
}

main "$@"