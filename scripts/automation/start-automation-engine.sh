#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
#                     自动化引擎启动脚本
#                     Automation Engine Startup Script
# ═══════════════════════════════════════════════════════════════════════════════
#
# 用途：启动 SynergyMesh 自动化引擎并提供监控功能
#
# 使用方式：
#   bash scripts/start-automation-engine.sh [start|stop|status|restart]
#
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LAUNCHER_SCRIPT="$PROJECT_ROOT/automation_launcher.py"
PID_FILE="$PROJECT_ROOT/.automation_engine.pid"
LOG_FILE="$PROJECT_ROOT/.automation_logs/engine.log"

# ============================================================================
# 函数
# ============================================================================

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# ============================================================================
# 启动引擎
# ============================================================================
start_engine() {
    print_info "启动自动化引擎..."
    
    # 检查是否已经运行
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            print_warning "自动化引擎已经在运行 (PID: $pid)"
            return 0
        else
            print_warning "删除过期的 PID 文件"
            rm -f "$PID_FILE"
        fi
    fi
    
    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # 启动引擎（后台运行）
    cd "$PROJECT_ROOT"
    nohup python3 "$LAUNCHER_SCRIPT" start > "$LOG_FILE" 2>&1 &
    local pid=$!
    
    # 保存 PID
    echo "$pid" > "$PID_FILE"
    
    # 等待启动
    sleep 2
    
    # 验证运行状态
    if ps -p "$pid" > /dev/null 2>&1; then
        print_success "自动化引擎已启动 (PID: $pid)"
        print_info "日志文件: $LOG_FILE"
        print_info "查看状态: bash $0 status"
    else
        print_error "启动失败，请查看日志: $LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

# ============================================================================
# 停止引擎
# ============================================================================
stop_engine() {
    print_info "停止自动化引擎..."
    
    if [ ! -f "$PID_FILE" ]; then
        print_warning "引擎未运行（PID 文件不存在）"
        return 0
    fi
    
    local pid=$(cat "$PID_FILE")
    
    if ps -p "$pid" > /dev/null 2>&1; then
        # 尝试优雅停止
        print_info "发送 SIGTERM 信号..."
        kill -TERM "$pid" 2>/dev/null || true
        
        # 等待停止
        local count=0
        while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # 如果仍在运行，强制停止
        if ps -p "$pid" > /dev/null 2>&1; then
            print_warning "优雅停止失败，强制终止..."
            kill -KILL "$pid" 2>/dev/null || true
            sleep 1
        fi
        
        print_success "引擎已停止"
    else
        print_warning "引擎未运行（PID: $pid）"
    fi
    
    rm -f "$PID_FILE"
}

# ============================================================================
# 查看状态
# ============================================================================
show_status() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}        SynergyMesh 自动化引擎状态${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        
        if ps -p "$pid" > /dev/null 2>&1; then
            print_success "运行中 (PID: $pid)"
            echo ""
            echo "进程信息:"
            ps -p "$pid" -o pid,ppid,cmd,%cpu,%mem,etime
            echo ""
            
            # 显示最近的日志
            if [ -f "$LOG_FILE" ]; then
                echo "最近日志 (最后 10 行):"
                echo "────────────────────────────────────────────────────────────"
                tail -n 10 "$LOG_FILE"
                echo "────────────────────────────────────────────────────────────"
            fi
        else
            print_warning "未运行（PID 文件存在但进程不存在）"
        fi
    else
        print_warning "未运行（PID 文件不存在）"
    fi
    
    echo ""
    echo "配置信息:"
    echo "  启动脚本: $LAUNCHER_SCRIPT"
    echo "  PID 文件:  $PID_FILE"
    echo "  日志文件:  $LOG_FILE"
    echo ""
}

# ============================================================================
# 重启引擎
# ============================================================================
restart_engine() {
    print_info "重启自动化引擎..."
    stop_engine
    sleep 2
    start_engine
}

# ============================================================================
# 查看日志
# ============================================================================
show_logs() {
    local lines=${1:-50}
    
    if [ ! -f "$LOG_FILE" ]; then
        print_warning "日志文件不存在: $LOG_FILE"
        return 1
    fi
    
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}        自动化引擎日志 (最后 $lines 行)${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    tail -n "$lines" "$LOG_FILE"
    
    echo ""
    print_info "实时查看日志: tail -f $LOG_FILE"
    echo ""
}

# ============================================================================
# 主函数
# ============================================================================
main() {
    local command=${1:-status}
    
    case $command in
        start)
            start_engine
            ;;
        stop)
            stop_engine
            ;;
        status)
            show_status
            ;;
        restart)
            restart_engine
            ;;
        logs)
            show_logs "${2:-50}"
            ;;
        help|--help|-h)
            echo ""
            echo "使用方式: $0 [command] [options]"
            echo ""
            echo "命令:"
            echo "  start        启动自动化引擎"
            echo "  stop         停止自动化引擎"
            echo "  status       查看运行状态（默认）"
            echo "  restart      重启自动化引擎"
            echo "  logs [n]     查看最近 n 行日志（默认 50）"
            echo "  help         显示此帮助信息"
            echo ""
            echo "示例:"
            echo "  $0 start          # 启动引擎"
            echo "  $0 status         # 查看状态"
            echo "  $0 logs 100       # 查看最近 100 行日志"
            echo "  $0 restart        # 重启引擎"
            echo ""
            ;;
        *)
            print_error "未知命令: $command"
            echo "使用 '$0 help' 查看帮助"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
