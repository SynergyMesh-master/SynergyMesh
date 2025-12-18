#!/bin/bash
# SLASolve 快速部署腳本
# 用於本地開發或生產環境快速啟動

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函數：打印彩色訊息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 函數：檢查 Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安裝。請先安裝 Docker。"
        exit 1
    fi
    print_info "Docker 已安裝 ✓"
}

# 函數：檢查 Docker Compose
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安裝。請先安裝 Docker Compose。"
        exit 1
    fi
    print_info "Docker Compose 已安裝 ✓"
}

# 函數：部署所有服務
deploy_all() {
    print_info "開始部署所有 SLASolve 服務..."
    
    # 檢查環境
    check_docker
    check_docker_compose
    
    # 建置並啟動
    print_info "建置 Docker images..."
    docker-compose build
    
    print_info "啟動服務..."
    docker-compose up -d
    
    # 等待服務啟動
    print_info "等待服務啟動..."
    sleep 10
    
    # 檢查服務狀態
    print_info "檢查服務狀態..."
    docker-compose ps
    
    print_info ""
    print_info "=========================================="
    print_info "✅ 部署完成！"
    print_info "=========================================="
    print_info ""
    print_info "服務端點："
    print_info "  - Contracts L1 API: http://localhost:3000"
    print_info "  - MCP Servers:       http://localhost:3001"
    print_info "  - Dashboard:         http://localhost:8080"
    print_info ""
    print_info "查看日誌："
    print_info "  docker-compose logs -f"
    print_info ""
    print_info "停止服務："
    print_info "  docker-compose down"
    print_info ""
}

# 函數：部署單一服務
deploy_service() {
    local service=$1
    print_info "部署 $service 服務..."
    
    check_docker
    check_docker_compose
    
    docker-compose build "$service"
    docker-compose up -d "$service"
    
    print_info "✅ $service 服務已啟動"
}

# 函數：停止所有服務
stop_all() {
    print_info "停止所有服務..."
    docker-compose down
    print_info "✅ 所有服務已停止"
}

# 函數：查看服務狀態
status() {
    print_info "服務狀態："
    docker-compose ps
}

# 函數：查看日誌
logs() {
    local service=$1
    if [ -z "$service" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$service"
    fi
}

# 函數：驗證配置
validate() {
    print_info "驗證 Auto-Fix Bot 配置..."
    
    if ! command -v python3 &> /dev/null; then
        print_warn "Python3 未安裝，跳過驗證"
        return
    fi
    
    python3 tools/validate_yaml.py
    python3 scripts/validate_auto_fix_bot_config.py
    
    print_info "✅ 配置驗證通過"
}

# 函數：顯示幫助
show_help() {
    cat << EOF
SLASolve 部署腳本

用法: $0 [命令] [選項]

命令:
  deploy              部署所有服務 (預設)
  deploy <service>    部署特定服務 (contracts-l1, mcp-servers, dashboard)
  stop                停止所有服務
  restart             重啟所有服務
  status              顯示服務狀態
  logs [service]      查看日誌
  validate            驗證配置
  help                顯示此幫助訊息

範例:
  $0                          # 部署所有服務
  $0 deploy contracts-l1      # 僅部署 Contracts L1
  $0 logs                     # 查看所有服務日誌
  $0 logs mcp-servers         # 查看 MCP Servers 日誌
  $0 stop                     # 停止所有服務

EOF
}

# 主程式
main() {
    local command=${1:-deploy}
    
    case $command in
        deploy)
            if [ -n "$2" ]; then
                deploy_service "$2"
            else
                deploy_all
            fi
            ;;
        stop)
            stop_all
            ;;
        restart)
            stop_all
            sleep 2
            deploy_all
            ;;
        status)
            status
            ;;
        logs)
            logs "$2"
            ;;
        validate)
            validate
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 執行主程式
main "$@"
