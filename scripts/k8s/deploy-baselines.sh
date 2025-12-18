#!/bin/bash
# ==============================================================================
# SynergyMesh Baseline Deployment Script
# ==============================================================================
# Purpose: Deploy SynergyMesh baseline configurations to Kubernetes cluster
# Extracted from legacy deploy-baselines.v1.0.sh and adapted for SynergyMesh
# ==============================================================================

set -euo pipefail

# Configuration
NAMESPACE="${NAMESPACE:-synergymesh-system}"
BASELINE_DIR="${BASELINE_DIR:-./config/baselines}"
LOG_FILE="/tmp/synergymesh-deployment-$(date +%Y%m%d-%H%M%S).log"
ROLLBACK_STACK=()
DRY_RUN="${DRY_RUN:-false}"
SKIP_VALIDATION="${SKIP_VALIDATION:-false}"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $*${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $*${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $*${NC}" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${CYAN}[$(date +'%Y-%m-%d %H:%M:%S')] ℹ️  $*${NC}" | tee -a "$LOG_FILE"
}

print_banner() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                                ║${NC}"
    echo -e "${CYAN}║    ${GREEN}SynergyMesh Baseline Deployment System${CYAN}                  ║${NC}"
    echo -e "${CYAN}║    ${YELLOW}Intelligent Automation Platform${CYAN}                        ║${NC}"
    echo -e "${CYAN}║                                                                ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

check_prerequisites() {
    log "Checking prerequisites..."
    
    local missing_tools=()
    
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi
    
    if ! command -v jq &> /dev/null; then
        log_warning "jq not found. JSON validation will be skipped."
    fi
    
    if ! command -v yq &> /dev/null; then
        log_warning "yq not found. YAML validation will be limited."
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_error "Please install missing tools and try again."
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster."
        log_error "Please check your kubeconfig and cluster availability."
        exit 1
    fi
    
    local k8s_version=$(kubectl version --short 2>/dev/null | grep "Server Version" | awk '{print $3}' | sed 's/v//' || echo "unknown")
    log_info "Connected to Kubernetes cluster version: $k8s_version"
    
    log_success "Prerequisites check passed"
}

create_namespace() {
    log "Creating namespace: $NAMESPACE"
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace already exists: $NAMESPACE"
        return 0
    fi
    
    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY-RUN] Would create namespace: $NAMESPACE"
    else
        kubectl create namespace "$NAMESPACE"
        log_success "Namespace created: $NAMESPACE"
        
        # Apply namespace labels
        kubectl label namespace "$NAMESPACE" \
            app.kubernetes.io/name=synergymesh \
            app.kubernetes.io/component=baseline \
            app.kubernetes.io/managed-by=kubectl \
            --overwrite
        
        kubectl annotate namespace "$NAMESPACE" \
            synergymesh.io/deployed-at="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
            synergymesh.io/deployed-by="$(whoami)@$(hostname)" \
            --overwrite
        
        log_success "Namespace labels and annotations applied"
    fi
}

validate_yaml_file() {
    local file=$1
    
    if [ ! -f "$file" ]; then
        log_error "File not found: $file"
        return 1
    fi
    
    if ! kubectl apply --dry-run=client -f "$file" &> /dev/null; then
        log_error "YAML validation failed for: $file"
        kubectl apply --dry-run=client -f "$file" 2>&1 | tee -a "$LOG_FILE"
        return 1
    fi
    
    return 0
}

deploy_baseline() {
    local baseline_file=$1
    local wait_resources=${2:-""}
    
    log ""
    log "=================================================="
    log "Deploying baseline: $(basename $baseline_file)"
    log "=================================================="
    
    if [ ! -f "$baseline_file" ]; then
        log_error "Baseline file not found: $baseline_file"
        return 1
    fi
    
    log_info "Validating YAML file..."
    if ! validate_yaml_file "$baseline_file"; then
        return 1
    fi
    log_success "YAML validation passed"
    
    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY-RUN] Would deploy: $baseline_file"
        kubectl apply --dry-run=client -f "$baseline_file" | tee -a "$LOG_FILE"
        return 0
    fi
    
    log_info "Applying baseline configuration..."
    if kubectl apply -f "$baseline_file" -n "$NAMESPACE"; then
        log_success "Baseline deployed successfully"
        ROLLBACK_STACK+=("$baseline_file")
    else
        log_error "Failed to deploy baseline"
        return 1
    fi
    
    if [ -n "$wait_resources" ]; then
        log_info "Waiting for resources to be ready..."
        IFS=',' read -ra RESOURCES <<< "$wait_resources"
        for resource in "${RESOURCES[@]}"; do
            log_info "  Waiting for $resource..."
            if kubectl wait --for=condition=ready \
                --timeout=300s \
                -n "$NAMESPACE" \
                "$resource" &> /dev/null; then
                log_success "  $resource is ready"
            else
                log_warning "  Timeout waiting for $resource"
            fi
        done
    fi
    
    log_success "Baseline deployment completed"
    return 0
}

rollback_deployment() {
    log_error "Deployment failed. Initiating rollback..."
    
    local rollback_count=${#ROLLBACK_STACK[@]}
    if [ $rollback_count -eq 0 ]; then
        log_warning "Nothing to rollback"
        return
    fi
    
    log_warning "Rolling back $rollback_count baseline(s)..."
    
    for ((i=${#ROLLBACK_STACK[@]}-1; i>=0; i--)); do
        local file="${ROLLBACK_STACK[$i]}"
        log_info "  Rolling back: $file"
        
        if kubectl delete -f "$file" -n "$NAMESPACE" --ignore-not-found=true; then
            log_success "  Rolled back: $file"
        else
            log_error "  Failed to rollback: $file"
        fi
    done
    
    log_warning "Rollback completed"
}

show_usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Deploy SynergyMesh baseline configurations to Kubernetes cluster.

Options:
    --dry-run              Perform a dry-run without applying changes
    --skip-validation      Skip health validation checks
    --baseline-dir DIR     Directory containing baseline files (default: $BASELINE_DIR)
    --namespace NS         Target namespace (default: $NAMESPACE)
    --help                 Show this help message

Environment Variables:
    DRY_RUN                Set to 'true' for dry-run mode
    SKIP_VALIDATION        Set to 'true' to skip validation
    BASELINE_DIR           Directory containing baseline files

Examples:
    # Normal deployment
    $0

    # Dry-run mode
    $0 --dry-run

    # Custom baseline directory
    $0 --baseline-dir /path/to/baselines

EOF
}

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            --skip-validation)
                SKIP_VALIDATION="true"
                shift
                ;;
            --baseline-dir)
                BASELINE_DIR="$2"
                shift 2
                ;;
            --namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

main() {
    parse_arguments "$@"
    
    print_banner
    
    log "Deployment Configuration:"
    log "  Namespace: $NAMESPACE"
    log "  Baseline Directory: $BASELINE_DIR"
    log "  Dry Run: $DRY_RUN"
    log "  Skip Validation: $SKIP_VALIDATION"
    log "  Log File: $LOG_FILE"
    log ""
    
    check_prerequisites
    create_namespace
    
    # Deploy all baseline files in the directory
    if [ -d "$BASELINE_DIR" ]; then
        for baseline_file in "$BASELINE_DIR"/*.yaml; do
            if [ -f "$baseline_file" ]; then
                if ! deploy_baseline "$baseline_file"; then
                    log_error "Failed to deploy $baseline_file"
                    rollback_deployment
                    exit 1
                fi
                sleep 2
            fi
        done
    else
        log_warning "Baseline directory not found: $BASELINE_DIR"
    fi
    
    if [ "$DRY_RUN" = "false" ]; then
        log_success "All baselines deployed successfully!"
        log "Log file: $LOG_FILE"
    else
        log_info "[DRY-RUN] Deployment simulation completed"
    fi
}

trap 'log_error "Deployment interrupted. Rolling back..."; rollback_deployment; exit 1' INT TERM

main "$@"
