#!/bin/bash
# MachineNativeOps 緊急回滾腳本
# 支持自動檢測、智能回滾和通知

set -e

# 配置變量
DEFAULT_NAMESPACE="production"
DEFAULT_APP_NAME="machine-native-ops"
DEFAULT_HEALTH_CHECK_URL="https://machine-native-ops.com/health"
DEFAULT_MAX_RETRIES=10
DEFAULT_RETRY_INTERVAL=30
DEFAULT_ROLLBACK_TIMEOUT=300

# 解析命令行參數
NAMESPACE="${1:-$DEFAULT_NAMESPACE}"
APP_NAME="${2:-$DEFAULT_APP_NAME}"
HEALTH_CHECK_URL="${3:-$DEFAULT_HEALTH_CHECK_URL}"
MAX_RETRIES="${4:-$DEFAULT_MAX_RETRIES}"
RETRY_INTERVAL="${5:-$DEFAULT_RETRY_INTERVAL}"
ROLLBACK_TIMEOUT="${6:-$DEFAULT_ROLLBACK_TIMEOUT}"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 全局變數
ROLLBACK_REASON=""
CURRENT_REVISION=""
TARGET_REVISION=""
EMERGENCY_MODE=false

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_emergency() {
    echo -e "${RED}🚨 [EMERGENCY]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 檢查依賴工具
check_dependencies() {
    log_info "檢查依賴工具..."
    
    local missing_tools=()
    
    # 檢查 kubectl
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi
    
    # 檢查 argocd
    if ! command -v argocd &> /dev/null; then
        missing_tools+=("argocd")
    fi
    
    # 檢查 curl
    if ! command -v curl &> /dev/null; then
        missing_tools+=("curl")
    fi
    
    # 檢查 jq
    if ! command -v jq &> /dev/null; then
        missing_tools+=("jq")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "缺少必要工具: ${missing_tools[*]}"
        log_info "請安裝缺少的工具後重試"
        exit 1
    fi
    
    log_success "所有依賴工具已就緒"
}

# 檢查集群連接
check_cluster_connection() {
    log_info "檢查集群連接..."
    
    # 檢查 kubectl 連接
    if ! kubectl cluster-info &> /dev/null; then
        log_error "無法連接到 Kubernetes 集群"
        exit 1
    fi
    
    # 檢查 ArgoCD 連接
    if ! argocd app list &> /dev/null; then
        log_error "無法連接到 ArgoCD"
        exit 1
    fi
    
    log_success "集群連接正常"
}

# 獲取應用當前狀態
get_app_status() {
    log_info "獲取應用 $APP_NAME 當前狀態..."
    
    # 獲取 ArgoCD 應用狀態
    local app_info
    app_info=$(argocd app get "$APP_NAME" -n "$NAMESPACE" 2>/dev/null || echo "")
    
    if [ -z "$app_info" ]; then
        log_error "無法獲取應用 $APP_NAME 的信息"
        exit 1
    fi
    
    # 解析應用信息
    CURRENT_REVISION=$(echo "$app_info" | grep "Revision:" | awk '{print $2}' || echo "unknown")
    local sync_status=$(echo "$app_info" | grep "Sync Status:" | awk '{print $3}' || echo "Unknown")
    local health_status=$(echo "$app_info" | grep "Health Status:" | awk '{print $3}' || echo "Unknown")
    local operation_state=$(echo "$app_info" | grep "Operation State:" | awk '{print $3}' || echo "Unknown")
    
    log_info "當前版本: $CURRENT_REVISION"
    log_info "同步狀態: $sync_status"
    log_info "健康狀態: $health_status"
    log_info "操作狀態: $operation_state"
    
    # 檢查是否需要緊急回滾
    if [ "$health_status" != "Healthy" ] || [ "$sync_status" != "Synced" ]; then
        log_warning "應用狀態異常，可能需要回滾"
        ROLLBACK_REASON="Health: $health_status, Sync: $sync_status"
        EMERGENCY_MODE=true
    fi
}

# 獲取健康版本列表
get_healthy_revisions() {
    log_info "獲取健康版本列表..."
    
    local history_output
    history_output=$(argocd app history "$APP_NAME" -n "$NAMESPACE" 2>/dev/null || echo "")
    
    if [ -z "$history_output" ]; then
        log_error "無法獲取應用歷史版本"
        exit 1
    fi
    
    # 提取健康版本
    local healthy_revisions
    healthy_revisions=$(echo "$history_output" | grep "Healthy" | head -5 | awk '{print $1}' | sort -nr)
    
    if [ -z "$healthy_revisions" ]; then
        log_error "沒有找到健康的歷史版本"
        exit 1
    fi
    
    log_info "可用的健康版本:"
    echo "$healthy_revisions" | while read rev; do
        local date_info=$(echo "$history_output" | grep "^$rev " | awk '{print $2, $3, $4}')
        echo "  - 版本 $rev ($date_info)"
    done
    
    # 選擇最新的健康版本
    TARGET_REVISION=$(echo "$healthy_revisions" | head -1)
    log_success "目標回滾版本: $TARGET_REVISION"
}

# 執行健康檢查
perform_health_check() {
    local url="$1"
    local timeout="${2:-30}"
    
    log_info "執行健康檢查: $url"
    
    local start_time=$(date +%s)
    local end_time=$((start_time + timeout))
    
    while [ $(date +%s) -lt $end_time ]; do
        if curl -f -s --max-time 10 "$url" > /dev/null 2>&1; then
            log_success "健康檢查通過"
            return 0
        fi
        
        sleep 5
    done
    
    log_error "健康檢查失敗（超時 ${timeout}s）"
    return 1
}

# 執行 ArgoCD 回滾
execute_argocd_rollback() {
    log_info "執行 ArgoCD 回滾到版本 $TARGET_REVISION..."
    
    # 執行回滾
    if ! argocd app rollback "$APP_NAME" -n "$NAMESPACE" "$TARGET_REVISION"; then
        log_error "ArgoCD 回滾失敗"
        return 1
    fi
    
    log_success "ArgoCD 回滾命令已發送"
}

# 等待回滾完成
wait_for_rollback() {
    log_info "等待回滾完成..."
    
    local timeout="$ROLLBACK_TIMEOUT"
    local start_time=$(date +%s)
    local end_time=$((start_time + timeout))
    
    while [ $(date +%s) -lt $end_time ]; do
        local app_info
        app_info=$(argocd app get "$APP_NAME" -n "$NAMESPACE" 2>/dev/null || echo "")
        
        if [ -n "$app_info" ]; then
            local sync_status=$(echo "$app_info" | grep "Sync Status:" | awk '{print $3}' || echo "Unknown")
            local health_status=$(echo "$app_info" | grep "Health Status:" | awk '{print $3}' || echo "Unknown")
            local current_rev=$(echo "$app_info" | grep "Revision:" | awk '{print $2}' || echo "unknown")
            
            log_info "同步狀態: $sync_status, 健康狀態: $health_status, 當前版本: $current_rev"
            
            if [ "$sync_status" = "Synced" ] && [ "$health_status" = "Healthy" ]; then
                log_success "回滾完成，應用已恢復健康"
                return 0
            fi
        fi
        
        sleep 10
    done
    
    log_error "回滾超時"
    return 1
}

# 驗證回滾結果
verify_rollback() {
    log_info "驗證回滾結果..."
    
    local verification_passed=true
    
    # 1. 檢查 ArgoCD 狀態
    local app_info
    app_info=$(argocd app get "$APP_NAME" -n "$NAMESPACE" 2>/dev/null || echo "")
    
    if [ -n "$app_info" ]; then
        local sync_status=$(echo "$app_info" | grep "Sync Status:" | awk '{print $3}' || echo "Unknown")
        local health_status=$(echo "$app_info" | grep "Health Status:" | awk '{print $3}' || echo "Unknown")
        
        if [ "$sync_status" != "Synced" ]; then
            log_error "同步狀態異常: $sync_status"
            verification_passed=false
        fi
        
        if [ "$health_status" != "Healthy" ]; then
            log_error "健康狀態異常: $health_status"
            verification_passed=false
        fi
    else
        log_error "無法獲取應用狀態"
        verification_passed=false
    fi
    
    # 2. 檢查 Pod 狀態
    log_info "檢查 Pod 狀態..."
    local pod_status
    pod_status=$(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/name=$APP_NAME" -o jsonpath='{.items[*].status.phase}' 2>/dev/null || echo "")
    
    if [ -n "$pod_status" ]; then
        local running_pods=$(echo "$pod_status" | grep -c "Running" || echo "0")
        local total_pods=$(echo "$pod_status" | wc -w)
        
        log_info "運行中的 Pod: $running_pods/$total_pods"
        
        if [ "$running_pods" -ne "$total_pods" ]; then
            log_error "不是所有 Pod 都在運行"
            verification_passed=false
        fi
    else
        log_error "無法獲取 Pod 狀態"
        verification_passed=false
    fi
    
    # 3. 執行健康檢查
    if [ -n "$HEALTH_CHECK_URL" ]; then
        log_info "執行應用健康檢查..."
        if ! perform_health_check "$HEALTH_CHECK_URL" 60; then
            log_error "應用健康檢查失敗"
            verification_passed=false
        fi
    fi
    
    if [ "$verification_passed" = true ]; then
        log_success "回滾驗證通過"
        return 0
    else
        log_error "回滾驗證失敗"
        return 1
    fi
}

# 生成回滾報告
generate_rollback_report() {
    local report_file="rollback-report-$(date +%Y%m%d_%H%M%S).json"
    
    log_info "生成回滾報告: $report_file"
    
    cat > "$report_file" << EOF
{
  "rollback_report": {
    "timestamp": "$(date -Iseconds)",
    "namespace": "$NAMESPACE",
    "app_name": "$APP_NAME",
    "health_check_url": "$HEALTH_CHECK_URL",
    "current_revision": "$CURRENT_REVISION",
    "target_revision": "$TARGET_REVISION",
    "rollback_reason": "$ROLLBACK_REASON",
    "emergency_mode": $EMERGENCY_MODE,
    "execution": {
      "rollback_completed": $([ "$?" -eq 0 ] && echo "true" || echo "false"),
      "verification_passed": $([ "$?" -eq 0 ] && echo "true" || echo "false")
    },
    "configuration": {
      "max_retries": $MAX_RETRIES,
      "retry_interval": $RETRY_INTERVAL,
      "rollback_timeout": $ROLLBACK_TIMEOUT
    }
  }
}
EOF
    
    log_success "回滾報告已生成: $report_file"
}

# 發送通知
send_notifications() {
    local rollback_result=$1
    
    log_info "發送通知..."
    
    # 發送 Slack 通知
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        local color="good"
        local title="✅ 緊急回滾成功"
        local message="應用已成功回滾到健康版本"
        
        if [ "$rollback_result" -ne 0 ]; then
            color="danger"
            title="❌ 緊急回滾失敗"
            message="回滾過程中遇到問題，需要手動介入"
        fi
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                &quot;attachments&quot;: [{
                    &quot;color&quot;: &quot;$color&quot;,
                    &quot;title&quot;: &quot;$title&quot;,
                    &quot;text&quot;: &quot;$message&quot;,
                    &quot;fields&quot;: [
                        {&quot;title&quot;: &quot;應用名稱&quot;, &quot;value&quot;: &quot;$APP_NAME&quot;, &quot;short&quot;: true},
                        {&quot;title&quot;: &quot;命名空間&quot;, &quot;value&quot;: &quot;$NAMESPACE&quot;, &quot;short&quot;: true},
                        {&quot;title&quot;: &quot;原版本&quot;, &quot;value&quot;: &quot;$CURRENT_REVISION&quot;, &quot;short&quot;: true},
                        {&quot;title&quot;: &quot;回滾到版本&quot;, &quot;value&quot;: &quot;$TARGET_REVISION&quot;, &quot;short&quot;: true},
                        {&quot;title&quot;: &quot;回滾原因&quot;, &quot;value&quot;: &quot;$ROLLBACK_REASON&quot;, &quot;short&quot;: false}
                    ],
                    &quot;footer&quot;: &quot;MachineNativeOps 緊急回滾系統&quot;,
                    &quot;ts&quot;: $(date +%s)
                }]
            }" \
            "$SLACK_WEBHOOK_URL" || true
    fi
    
    # 發送郵件通知
    if [ -n "$NOTIFICATION_EMAIL" ] && command -v mail &> /dev/null; then
        local subject="MachineNativeOps 緊急回滾通知 - $([ "$rollback_result" -eq 0 ] && echo "成功" || echo "失敗")"
        local body="緊急回滾操作已完成
        
應用: $APP_NAME
命名空間: $NAMESPACE
回滾時間: $(date '+%Y-%m-%d %H:%M:%S')
原版本: $CURRENT_REVISION
回滾到版本: $TARGET_REVISION
回滾原因: $ROLLBACK_REASON
結果: $([ "$rollback_result" -eq 0 ] && echo "成功" || echo "失敗")

詳細信息請查看回滾報告文件。"
        
        echo "$body" | mail -s "$subject" "$NOTIFICATION_EMAIL" || true
    fi
    
    log_success "通知已發送"
}

# 創建應用快照
create_snapshot() {
    log_info "創建應用快照..."
    
    local snapshot_name="snapshot-$(date +%Y%m%d_%H%M%S)"
    local snapshot_file="snapshot-$APP_NAME-$NAMESPACE-$(date +%Y%m%d_%H%M%S).yaml"
    
    # 導出當前應用配置
    kubectl get deployment,service,configmap,secret -n "$NAMESPACE" -l "app.kubernetes.io/name=$APP_NAME" -o yaml > "$snapshot_file" || {
        log_warning "無法創建快照文件"
        return 1
    }
    
    log_success "快照已創建: $snapshot_file"
}

# 主回滾流程
main_rollback() {
    log_emergency "開始緊急回滾流程..."
    log_info "應用: $APP_NAME"
    log_info "命名空間: $NAMESPACE"
    log_info "健康檢查 URL: $HEALTH_CHECK_URL"
    
    # 1. 創建快照
    create_snapshot
    
    # 2. 檢查依賴和連接
    check_dependencies
    check_cluster_connection
    
    # 3. 獲取當前狀態
    get_app_status
    
    # 4. 獲取健康版本
    get_healthy_revisions
    
    # 5. 確認回滾操作
    if [ "$EMERGENCY_MODE" = false ]; then
        log_warning "應用狀態正常，確認是否要繼續回滾？"
        read -p "繼續回滾? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "用戶取消回滾操作"
            exit 0
        fi
    fi
    
    # 6. 執行回滾
    if ! execute_argocd_rollback; then
        log_error "回滾執行失敗"
        send_notifications 1
        exit 1
    fi
    
    # 7. 等待回滾完成
    if ! wait_for_rollback; then
        log_error "回滾等待超時"
        send_notifications 1
        exit 1
    fi
    
    # 8. 驗證回滾結果
    local verification_result=0
    if ! verify_rollback; then
        log_error "回滾驗證失敗"
        verification_result=1
    fi
    
    # 9. 生成報告
    generate_rollback_report
    
    # 10. 發送通知
    send_notifications "$verification_result"
    
    # 11. 返回結果
    if [ "$verification_result" -eq 0 ]; then
        log_success "緊急回滾流程完成！"
        return 0
    else
        log_error "緊急回滾流程失敗，需要手動介入"
        return 1
    fi
}

# 顯示幫助信息
show_help() {
    cat << EOF
MachineNativeOps 緊急回滾腳本

用法: $0 [NAMESPACE] [APP_NAME] [HEALTH_CHECK_URL] [MAX_RETRIES] [RETRY_INTERVAL] [ROLLBACK_TIMEOUT]

參數說明:
  NAMESPACE        Kubernetes 命名空間 (默認: production)
  APP_NAME         ArgoCD 應用名稱 (默認: machine-native-ops)
  HEALTH_CHECK_URL 健康檢查 URL (默認: https://machine-native-ops.com/health)
  MAX_RETRIES       最大重試次數 (默認: 10)
  RETRY_INTERVAL    重試間隔，秒 (默認: 30)
  ROLLBACK_TIMEOUT  回滾超時時間，秒 (默認: 300)

環境變量:
  SLACK_WEBHOOK_URL    Slack Webhook URL
  NOTIFICATION_EMAIL   通知郵箱地址

示例:
  $0 production machine-native-ops https://machine-native-ops.com/health
  $0 staging machine-native-ops-staging https://staging.machine-native-ops.com/health

注意:
  - 請確保已安裝 kubectl, argocd, curl, jq
  - 請確保具有足夠的權限執行回滾操作
  - 建議在執行前備份重要數據

EOF
}

# 信號處理
handle_signal() {
    log_warning "收到中斷信號，正在清理..."
    exit 130
}

trap handle_signal INT TERM

# 解析命令行參數
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        # 主執行流程
        main_rollback
        ;;
esac