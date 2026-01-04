#!/bin/bash
# MachineNativeOps 性能測試腳本
# 支持 K6 壓力測試和 Prometheus 指標監控

set -e

# 配置變量
DEFAULT_TARGET_URL="https://staging.machine-native-ops.com"
DEFAULT_CONCURRENCY=50
DEFAULT_DURATION="10m"
DEFAULT_ENVIRONMENT="staging"

# 解析命令行參數
TARGET_URL="${1:-$DEFAULT_TARGET_URL}"
CONCURRENCY="${2:-$DEFAULT_CONCURRENCY}"
DURATION="${3:-$DEFAULT_DURATION}"
ENVIRONMENT="${4:-$DEFAULT_ENVIRONMENT}"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查依賴
check_dependencies() {
    log_info "檢查依賴工具..."
    
    # 檢查 K6
    if ! command -v k6 &> /dev/null; then
        log_error "K6 未安裝，正在安裝..."
        install_k6
    else
        log_success "K6 已安裝: $(k6 version)"
    fi
    
    # 檢查 curl
    if ! command -v curl &> /dev/null; then
        log_error "curl 未安裝"
        exit 1
    fi
    
    # 檢查 jq
    if ! command -v jq &> /dev/null; then
        log_error "jq 未安裝，正在安裝..."
        apt-get update && apt-get install -y jq
    fi
}

# 安裝 K6
install_k6() {
    log_info "安裝 K6..."
    
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
        echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
        sudo apt-get update
        sudo apt-get install k6
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo rpm --import https://dl.k6.io/rpm/repo.key
        sudo dnf install -y https://dl.k6.io/rpm/k6-latest.rpm
    elif command -v brew &> /dev/null; then
        # macOS
        brew install k6
    else
        log_error "無法自動安裝 K6，請手動安裝: https://k6.io/docs/getting-started/installation/"
        exit 1
    fi
    
    log_success "K6 安裝完成"
}

# 生成 K6 測試腳本
generate_k6_script() {
    local test_file="load-test-$(date +%Y%m%d_%H%M%S).js"
    
    log_info "生成 K6 測試腳本: $test_file"
    
    cat > "$test_file" << 'EOF'
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// 自定義指標
export let errorRate = new Rate('errors');
export let responseTime = new Trend('response_time');

// 測試配置
export let options = {
    stages: [
        { duration: '2m', target: __ENV.CONCURRENCY || 50 },   // 起步階段
        { duration: '5m', target: __ENV.CONCURRENCY || 50 },   // 穩定階段
        { duration: '2m', target: Math.round((__ENV.CONCURRENCY || 50) * 1.5) },  // 增壓階段
        { duration: '5m', target: Math.round((__ENV.CONCURRENCY || 50) * 1.5) },  // 高負載階段
        { duration: '2m', target: 0 },                         // 降壓階段
    ],
    thresholds: {
        http_req_duration: ['p(99)<1500'],     // 99% 請求響應時間 < 1.5s
        http_req_failed: ['rate<0.1'],         // 錯誤率 < 10%
        errors: ['rate<0.1'],                  // 自定義錯誤率 < 10%
        response_time: ['p(95)<1000'],         // 95% 響應時間 < 1s
    },
};

const BASE_URL = __ENV.TARGET_URL || 'https://staging.machine-native-ops.com';

export default function () {
    // 1. 健康檢查端點測試
    let healthResponse = http.get(`${BASE_URL}/health`);
    let healthOk = check(healthResponse, {
        'health status is 200': (r) => r.status === 200,
        'health response time < 500ms': (r) => r.timings.duration < 500,
    });
    errorRate.add(!healthOk);
    responseTime.add(healthResponse.timings.duration);
    
    // 2. API 功能測試
    let apiResponse = http.post(`${BASE_URL}/api/v1/process`, 
        JSON.stringify({ 
            data: 'test-data',
            timestamp: new Date().toISOString()
        }), 
        { 
            headers: { 
                'Content-Type': 'application/json',
                'User-Agent': 'k6-performance-test'
            }
        }
    );
    
    let apiOk = check(apiResponse, {
        'api status is 200': (r) => r.status === 200,
        'api response time < 1500ms': (r) => r.timings.duration < 1500,
        'api response contains data': (r) => r.json().hasOwnProperty('result'),
    });
    errorRate.add(!apiOk);
    responseTime.add(apiResponse.timings.duration);
    
    // 3. 數據查詢端點測試
    let queryResponse = http.get(`${BASE_URL}/api/v1/data?limit=100`);
    let queryOk = check(queryResponse, {
        'query status is 200': (r) => r.status === 200,
        'query response time < 1000ms': (r) => r.timings.duration < 1000,
        'query returns data': (r) => r.json().data.length > 0,
    });
    errorRate.add(!queryOk);
    responseTime.add(queryResponse.timings.duration);
    
    // 4. 文件上傳測試（模擬）
    let uploadData = {
        filename: 'test-file.txt',
        content: 'This is a test file for performance testing',
        size: 1024
    };
    
    let uploadResponse = http.post(`${BASE_URL}/api/v1/upload`, 
        JSON.stringify(uploadData),
        { headers: { 'Content-Type': 'application/json' } }
    );
    
    let uploadOk = check(uploadResponse, {
        'upload status is 200 or 201': (r) => r.status === 200 || r.status === 201,
        'upload response time < 3000ms': (r) => r.timings.duration < 3000,
    });
    errorRate.add(!uploadOk);
    responseTime.add(uploadResponse.timings.duration);
    
    sleep(1);
}

// 測試結束後的處理
export function handleSummary(data) {
    return {
        'performance-report.json': JSON.stringify(data, null, 2),
        stdout: textSummary(data, { indent: ' ', enableColors: true }),
    };
}

function textSummary(data, options) {
    return `
    Performance Test Results:
    ========================
    
    Total Requests: ${data.metrics.http_reqs.count}
    Failed Requests: ${data.metrics.http_req_failed.count}
    Error Rate: ${(data.metrics.http_req_failed.rate * 100).toFixed(2)}%
    
    Response Time:
    - Average: ${data.metrics.http_req_duration.avg.toFixed(2)}ms
    - Median: ${data.metrics.http_req_duration.med.toFixed(2)}ms
    - 95th Percentile: ${data.metrics.http_req_duration['p(95)'].toFixed(2)}ms
    - 99th Percentile: ${data.metrics.http_req_duration['p(99)'].toFixed(2)}ms
    
    Throughput: ${data.metrics.http_reqs.rate.toFixed(2)} requests/second
    
    ${data.metrics.http_req_failed.rate > 0.1 ? '❌ PERFORMANCE TEST FAILED' : '✅ PERFORMANCE TEST PASSED'}
    `;
}
EOF
    
    echo "$test_file"
}

# 執行性能測試
run_performance_test() {
    log_info "開始執行性能測試..."
    log_info "目標 URL: $TARGET_URL"
    log_info "併發數: $CONCURRENCY"
    log_info "持續時間: $DURATION"
    log_info "環境: $ENVIRONMENT"
    
    # 生成測試腳本
    local test_file
    test_file=$(generate_k6_script)
    
    # 設置環境變量
    export TARGET_URL="$TARGET_URL"
    export CONCURRENCY="$CONCURRENCY"
    
    # 執行測試
    log_info "執行 K6 性能測試..."
    
    local start_time=$(date +%s)
    
    k6 run \
        --out json=performance-results.json \
        --out csv=performance-results.csv \
        --vus $CONCURRENCY \
        --duration "$DURATION" \
        "$test_file" || {
        local exit_code=$?
        log_error "性能測試失敗，退出碼: $exit_code"
        
        # 即使測試失敗，也繼續生成報告
        generate_report "$start_time" "$test_file"
        exit $exit_code
    }
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_success "性能測試完成，耗時: ${duration} 秒"
    
    # 生成測試報告
    generate_report "$start_time" "$test_file"
}

# 生成測試報告
generate_report() {
    local start_time=$1
    local test_file=$2
    local report_file="performance-report-$(date +%Y%m%d_%H%M%S).html"
    
    log_info "生成性能測試報告..."
    
    # 解析 JSON 結果
    if [ -f "performance-results.json" ]; then
        local total_requests
        local failed_requests
        local error_rate
        local avg_response_time
        local p95_response_time
        local throughput
        
        total_requests=$(jq -r '.metrics.http_reqs.count' performance-results.json)
        failed_requests=$(jq -r '.metrics.http_req_failed.count' performance-results.json)
        error_rate=$(jq -r '.metrics.http_req_failed.rate * 100' performance-results.json)
        avg_response_time=$(jq -r '.metrics.http_req_duration.avg' performance-results.json)
        p95_response_time=$(jq -r '.metrics.http_req_duration["p(95)"]' performance-results.json)
        throughput=$(jq -r '.metrics.http_reqs.rate' performance-results.json)
        
        # 生成 HTML 報告
        cat > "$report_file" << EOF
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MachineNativeOps 性能測試報告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #007bff; }
        .metric-value { font-size: 2em; font-weight: bold; color: #007bff; }
        .metric-label { color: #666; margin-top: 5px; }
        .status-pass { border-left-color: #28a745; }
        .status-pass .metric-value { color: #28a745; }
        .status-fail { border-left-color: #dc3545; }
        .status-fail .metric-value { color: #dc3545; }
        .details { background: #f8f9fa; padding: 20px; border-radius: 8px; }
        .details h3 { margin-top: 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>MachineNativeOps 性能測試報告</h1>
            <p>測試時間: $(date '+%Y-%m-%d %H:%M:%S')</p>
            <p>目標環境: $ENVIRONMENT ($TARGET_URL)</p>
        </div>
        
        <div class="metrics">
            <div class="metric-card $([ "$(echo "$error_rate < 10" | bc)" -eq 1 ] && echo "status-pass" || echo "status-fail")">
                <div class="metric-value">$(printf "%.1f" $error_rate)%</div>
                <div class="metric-label">錯誤率</div>
            </div>
            <div class="metric-card $([ "$(echo "$avg_response_time < 1000" | bc)" -eq 1 ] && echo "status-pass" || echo "status-fail")">
                <div class="metric-value">$(printf "%.0f" $avg_response_time)ms</div>
                <div class="metric-label">平均響應時間</div>
            </div>
            <div class="metric-card $([ "$(echo "$p95_response_time < 1500" | bc)" -eq 1 ] && echo "status-pass" || echo "status-fail")">
                <div class="metric-value">$(printf "%.0f" $p95_response_time)ms</div>
                <div class="metric-label">95th 響應時間</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">$(printf "%.1f" $throughput)</div>
                <div class="metric-label">吞吐量 (req/s)</div>
            </div>
        </div>
        
        <div class="details">
            <h3>測試詳情</h3>
            <table>
                <tr><th>指標</th><th>數值</th><th>狀態</th></tr>
                <tr><td>總請求數</td><td>$total_requests</td><td>✅</td></tr>
                <tr><td>失敗請求數</td><td>$failed_requests</td><td>$([ "$failed_requests" -eq 0 ] && echo "✅" || echo "❌")</td></tr>
                <tr><td>錯誤率 (< 10%)</td><td>$(printf "%.2f" $error_rate)%</td><td>$([ "$(echo "$error_rate < 10" | bc)" -eq 1 ] && echo "✅" || echo "❌")</td></tr>
                <tr><td>平均響應時間 (< 1000ms)</td><td>$(printf "%.0f" $avg_response_time)ms</td><td>$([ "$(echo "$avg_response_time < 1000" | bc)" -eq 1 ] && echo "✅" || echo "❌")</td></tr>
                <tr><td>95th 響應時間 (< 1500ms)</td><td>$(printf "%.0f" $p95_response_time)ms</td><td>$([ "$(echo "$p95_response_time < 1500" | bc)" -eq 1 ] && echo "✅" || echo "❌")</td></tr>
                <tr><td>併發數</td><td>$CONCURRENCY</td><td>-</td></tr>
                <tr><td>測試持續時間</td><td>$DURATION</td><td>-</td></tr>
            </table>
        </div>
        
        <div class="details">
            <h3>測試配置</h3>
            <ul>
                <li>目標 URL: $TARGET_URL</li>
                <li>併發用戶數: $CONCURRENCY</li>
                <li>測試持續時間: $DURATION</li>
                <li>測試腳本: $test_file</li>
            </ul>
        </div>
    </div>
</body>
</html>
EOF
        
        log_success "測試報告已生成: $report_file"
        
        # 判斷測試是否通過
        local test_passed=true
        if [ "$(echo "$error_rate >= 10" | bc)" -eq 1 ]; then
            test_passed=false
        fi
        if [ "$(echo "$avg_response_time >= 1000" | bc)" -eq 1 ]; then
            test_passed=false
        fi
        if [ "$(echo "$p95_response_time >= 1500" | bc)" -eq 1 ]; then
            test_passed=false
        fi
        
        if [ "$test_passed" = true ]; then
            log_success "性能測試通過！"
        else
            log_error "性能測試未通過，請查看報告詳情"
        fi
        
        return $([ "$test_passed" = true ] && echo 0 || echo 1)
    else
        log_error "無法找到測試結果文件"
        return 1
    fi
}

# 監控系統資源
monitor_system_resources() {
    log_info "監控系統資源使用情況..."
    
    # 檢查 CPU 使用率
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    log_info "CPU 使用率: ${cpu_usage}%"
    
    # 檢查內存使用率
    local memory_usage=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')
    log_info "內存使用率: ${memory_usage}%"
    
    # 檢查磁盤使用率
    local disk_usage=$(df -h / | awk 'NR==2 {print $5}' | cut -d'%' -f1)
    log_info "磁盤使用率: ${disk_usage}%"
    
    # 檢查網絡連接數
    local connections=$(netstat -an | grep ESTABLISHED | wc -l)
    log_info "當前網絡連接數: $connections"
    
    # 資源告警
    if [ "$(echo "$cpu_usage > 80" | bc)" -eq 1 ]; then
        log_warning "CPU 使用率過高: ${cpu_usage}%"
    fi
    
    if [ "$(echo "$memory_usage > 80" | bc)" -eq 1 ]; then
        log_warning "內存使用率過高: ${memory_usage}%"
    fi
    
    if [ "$(echo "$disk_usage > 80" | bc)" -eq 1 ]; then
        log_warning "磁盤使用率過高: ${disk_usage}%"
    fi
}

# 清理函數
cleanup() {
    log_info "清理臨時文件..."
    rm -f *.js
    log_info "清理完成"
}

# 發送通知
send_notification() {
    local test_result=$1
    local report_file=$2
    
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        local color="good"
        local message="✅ 性能測試通過"
        
        if [ "$test_result" -ne 0 ]; then
            color="danger"
            message="❌ 性能測試失敗"
        fi
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                &quot;attachments&quot;: [{
                    &quot;color&quot;: &quot;$color&quot;,
                    &quot;title&quot;: &quot;$message&quot;,
                    &quot;fields&quot;: [
                        {&quot;title&quot;: &quot;目標環境&quot;, &quot;value&quot;: &quot;$ENVIRONMENT&quot;, &quot;short&quot;: true},
                        {&quot;title&quot;: &quot;目標 URL&quot;, &quot;value&quot;: &quot;$TARGET_URL&quot;, &quot;short&quot;: true},
                        {&quot;title&quot;: &quot;併發數&quot;, &quot;value&quot;: &quot;$CONCURRENCY&quot;, &quot;short&quot;: true},
                        {&quot;title&quot;: &quot;持續時間&quot;, &quot;value&quot;: &quot;$DURATION&quot;, &quot;short&quot;: true}
                    ],
                    &quot;footer&quot;: &quot;MachineNativeOps 性能測試&quot;,
                    &quot;ts&quot;: $(date +%s)
                }]
            }" \
            "$SLACK_WEBHOOK_URL" || true
    fi
}

# 主函數
main() {
    log_info "MachineNativeOps 性能測試開始..."
    log_info "配置: $TARGET_URL | $CONCURRENCY | $DURATION | $ENVIRONMENT"
    
    # 檢查系統資源
    monitor_system_resources
    
    # 檢查依賴
    check_dependencies
    
    # 執行性能測試
    local test_result=0
    run_performance_test || test_result=$?
    
    # 發送通知
    send_notification "$test_result" "$report_file"
    
    # 清理
    cleanup
    
    log_info "性能測試完成，退出碼: $test_result"
    exit $test_result
}

# 信號處理
trap cleanup EXIT

# 執行主函數
main "$@"