#!/bin/bash

###############################################################################
# ArgoCD Automated Rollback Mechanism
# Implements intelligent failure detection and automatic rollback
###############################################################################

set -euo pipefail

# Configuration
APP_NAME="${APP_NAME:-machine-native-ops}"
NAMESPACE="${NAMESPACE:-default}"
MAX_RETRIES="${MAX_RETRIES:-3}"
RETRY_DELAY="${RETRY_DELAY:-30}"
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-300}"
SNAPSHOT_RETENTION="${SNAPSHOT_RETENTION:-7}"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Health check function
health_check() {
    local pod_name=$1
    local timeout=$2
    local elapsed=0
    
    log_info "Checking health for pod: $pod_name"
    
    while [ $elapsed -lt $timeout ]; do
        local status=$(kubectl get pod "$pod_name" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
        
        if [ "$status" == "Running" ]; then
            local ready=$(kubectl get pod "$pod_name" -n "$NAMESPACE" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
            
            if [ "$ready" == "True" ]; then
                log_info "Pod $pod_name is healthy"
                return 0
            fi
        fi
        
        sleep 5
        elapsed=$((elapsed + 5))
    done
    
    log_error "Health check failed for pod $pod_name after ${timeout}s"
    return 1
}

# Get current rollout status
get_rollout_status() {
    local phase
    phase=$(kubectl get argo rollouts "$APP_NAME" -n "$NAMESPACE" -o jsonpath='{.status.phase}' 2>/dev/null || echo "Unknown")
    echo "$phase"
}

# Create application snapshot
create_snapshot() {
    local snapshot_name="${APP_NAME}-snapshot-$(date +%Y%m%d-%H%M%S)"
    
    log_info "Creating application snapshot: $snapshot_name"
    
    # Save current configuration
    kubectl get argo rollouts "$APP_NAME" -n "$NAMESPACE" -o yaml > "/tmp/${snapshot_name}.yaml"
    
    # Save current replica count
    local replicas=$(kubectl get argo rollouts "$APP_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
    echo "$replicas" > "/tmp/${snapshot_name}.replicas"
    
    # Save current image version
    local image=$(kubectl get argo rollouts "$APP_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].image}')
    echo "$image" > "/tmp/${snapshot_name}.image"
    
    log_info "Snapshot created: /tmp/${snapshot_name}.yaml"
    echo "$snapshot_name"
}

# Perform rollback
perform_rollback() {
    local reason=$1
    local snapshot_name=$(create_snapshot)
    
    log_warn "Initiating rollback due to: $reason"
    log_info "Snapshot saved: $snapshot_name"
    
    # Get current revision
    local current_rev
    current_rev=$(kubectl get argo rollouts "$APP_NAME" -n "$NAMESPACE" -o jsonpath='{.status.currentPodHash}' 2>/dev/null || echo "")
    
    # Rollback to previous stable revision
    log_info "Rolling back to previous stable version..."
    
    if kubectl argo rollouts undo "$APP_NAME" -n "$NAMESPACE"; then
        log_info "Rollback command executed successfully"
    else
        log_error "Rollback command failed"
        return 1
    fi
    
    # Wait for rollback to complete
    log_info "Waiting for rollback to complete..."
    local retry_count=0
    
    while [ $retry_count -lt $MAX_RETRIES ]; do
        sleep $RETRY_DELAY
        
        local status=$(get_rollout_status)
        
        if [ "$status" == "Healthy" ]; then
            log_info "✅ Rollback completed successfully"
            
            # Send notification (integrations can be added here)
            send_notification "rollback_success" "$snapshot_name"
            
            return 0
        elif [ "$status" == "Degraded" ]; then
            log_error "❌ Rollback resulted in degraded state"
            send_notification "rollback_failed" "$snapshot_name"
            return 1
        fi
        
        retry_count=$((retry_count + 1))
        log_info "Waiting for rollback... (attempt $retry_count/$MAX_RETRIES)"
    done
    
    log_error "❌ Rollback timeout after $MAX_RETRIES attempts"
    return 1
}

# Send notifications
send_notification() {
    local event_type=$1
    local snapshot_name=$2
    
    log_info "Sending notification: $event_type"
    
    # Slack notification example
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        local message="Rollback event: $event_type for $APP_NAME. Snapshot: $snapshot_name"
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{&quot;text&quot;:&quot;$message&quot;}" \
            "$SLACK_WEBHOOK_URL" || log_warn "Failed to send Slack notification"
    fi
    
    # Email notification example
    if [ -n "${ALERT_EMAIL:-}" ]; then
        echo "Rollback event: $event_type for $APP_NAME. Snapshot: $snapshot_name" | \
            mail -s "Rollback Alert: $APP_NAME" "$ALERT_EMAIL" || \
            log_warn "Failed to send email notification"
    fi
}

# Monitor deployment and trigger rollback if needed
monitor_deployment() {
    local initial_status=$(get_rollout_status)
    log_info "Starting deployment monitoring. Initial status: $initial_status"
    
    local check_interval=10
    local total_checks=0
    local max_checks=$((HEALTH_CHECK_TIMEOUT / check_interval))
    
    while [ $total_checks -lt $max_checks ]; do
        sleep $check_interval
        total_checks=$((total_checks + 1))
        
        local current_status=$(get_rollout_status)
        log_info "Current status: $current_status (check $total_checks/$max_checks)"
        
        # Check for error conditions
        case "$current_status" in
            "Degraded")
                log_error "Deployment is in degraded state"
                perform_rollback "Deployment degraded"
                return $?
                ;;
            "Invalid")
                log_error "Deployment is invalid"
                perform_rollback "Invalid configuration"
                return $?
                ;;
            "Healthy")
                log_info "✅ Deployment completed successfully"
                return 0
                ;;
        esac
        
        # Check for unhealthy pods
        local unhealthy_pods
        unhealthy_pods=$(kubectl get pods -n "$NAMESPACE" -l app="$APP_NAME" \
            -o jsonpath='{.items[?(@.status.phase!="Running" || @.status.conditions[?(@.type=="Ready")].status!="True")].metadata.name}')
        
        if [ -n "$unhealthy_pods" ]; then
            log_warn "Unhealthy pods detected: $unhealthy_pods"
            
            for pod in $unhealthy_pods; do
                if ! health_check "$pod" "$RETRY_DELAY"; then
                    perform_rollback "Unhealthy pod: $pod"
                    return $?
                fi
            done
        fi
    done
    
    log_error "Deployment monitoring timeout"
    perform_rollback "Deployment timeout"
    return 1
}

# Manual rollback to specific revision
manual_rollback() {
    local revision=$1
    
    log_info "Manual rollback to revision: $revision"
    
    local snapshot_name=$(create_snapshot)
    
    if kubectl argo rollouts undo "$APP_NAME" -n "$NAMESPACE" --to-revision="$revision"; then
        log_info "✅ Manual rollback initiated"
        send_notification "manual_rollback" "$snapshot_name"
        return 0
    else
        log_error "❌ Manual rollback failed"
        return 1
    fi
}

# List available rollback points
list_rollback_points() {
    log_info "Available rollback points:"
    
    kubectl argo rollouts history "$APP_NAME" -n "$NAMESPACE"
}

# Cleanup old snapshots
cleanup_snapshots() {
    log_info "Cleaning up snapshots older than $SNAPSHOT_RETENTION days"
    
    find /tmp -name "${APP_NAME}-snapshot-*" -mtime +$SNAPSHOT_RETENTION -delete
    
    log_info "Snapshot cleanup completed"
}

# Main execution
main() {
    case "${1:-monitor}" in
        monitor)
            monitor_deployment
            ;;
        rollback)
            perform_rollback "${2:-Manual rollback requested}"
            ;;
        manual-rollback)
            if [ -z "${2:-}" ]; then
                log_error "Revision number required for manual rollback"
                list_rollback_points
                exit 1
            fi
            manual_rollback "$2"
            ;;
        list)
            list_rollback_points
            ;;
        status)
            get_rollout_status
            ;;
        cleanup)
            cleanup_snapshots
            ;;
        *)
            echo "Usage: $0 {monitor|rollback|manual-rollback|list|status|cleanup}"
            echo ""
            echo "Commands:"
            echo "  monitor              Monitor deployment and auto-rollback on failure"
            echo "  rollback [reason]    Trigger rollback with optional reason"
            echo "  manual-rollback REV  Rollback to specific revision"
            echo "  list                 List available rollback points"
            echo "  status               Show current rollout status"
            echo "  cleanup              Clean up old snapshots"
            exit 1
            ;;
    esac
}

main "$@"