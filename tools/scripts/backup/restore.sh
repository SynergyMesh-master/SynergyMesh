#!/bin/bash
# ============================================================================
# 恢復腳本 (Restore Script)
# ============================================================================
# 從備份恢復系統
# ============================================================================

set -euo pipefail

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
BACKUP_FILE="${1:-}"
RESTORE_DIR="/tmp/restore"
DRY_RUN="${DRY_RUN:-false}"

# 日誌函數
log() { echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# 使用說明
usage() {
    cat <<EOF
使用方式: $0 <backup_file> [options]

參數:
    backup_file     備份文件路徑或 S3 URI

選項:
    --dry-run       僅驗證，不實際恢復
    --help          顯示此幫助信息

環境變數:
    S3_BUCKET       S3 桶名稱
    S3_REGION       S3 區域

範例:
    $0 /tmp/backups/slasolve_full_20251125.tar.gz
    $0 s3://slasolve-backups/slasolve_full_20251125.tar.gz
    DRY_RUN=true $0 backup.tar.gz
EOF
    exit 0
}

# 驗證備份文件
validate_backup() {
    local backup_file="$1"
    log "驗證備份文件..."
    
    # 檢查校驗和
    if [ -f "${backup_file}.sha256" ]; then
        if sha256sum -c "${backup_file}.sha256"; then
            success "備份文件校驗通過"
        else
            error "備份文件校驗失敗"
            exit 1
        fi
    else
        warning "未找到校驗和文件，跳過驗證"
    fi
}

# 解壓備份
extract_backup() {
    local backup_file="$1"
    log "解壓備份文件..."
    
    mkdir -p "$RESTORE_DIR"
    tar -xzf "$backup_file" -C "$RESTORE_DIR"
    
    success "備份文件已解壓到: $RESTORE_DIR"
}

# 恢復配置
restore_config() {
    local restore_path="$1"
    log "恢復配置文件..."
    
    if [ "$DRY_RUN" = "true" ]; then
        log "[DRY RUN] 將恢復配置文件"
        return 0
    fi
    
    if [ -d "$restore_path/config" ]; then
        cp -r "$restore_path/config"/* ./
        success "配置文件已恢復"
    fi
}

# 恢復代碼
restore_code() {
    local restore_path="$1"
    log "恢復代碼..."
    
    if [ "$DRY_RUN" = "true" ]; then
        log "[DRY RUN] 將恢復代碼"
        return 0
    fi
    
    if [ -d "$restore_path/code" ]; then
        for archive in "$restore_path/code"/*.tar.gz; do
            tar -xzf "$archive" -C ./
            log "  ✓ $(basename $archive)"
        done
        success "代碼已恢復"
    fi
}

# 恢復數據庫
restore_database() {
    local restore_path="$1"
    log "恢復數據庫..."
    
    if [ "$DRY_RUN" = "true" ]; then
        log "[DRY RUN] 將恢復數據庫"
        return 0
    fi
    
    if [ -d "$restore_path/database" ]; then
        # PostgreSQL
        if ls "$restore_path/database"/postgres_*.sql.gz >/dev/null 2>&1; then
            local db_file=$(ls -t "$restore_path/database"/postgres_*.sql.gz | head -1)
            PGPASSWORD="${POSTGRES_PASSWORD}" gunzip -c "$db_file" | \
                psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"
            success "PostgreSQL 數據庫已恢復"
        fi
        
        # Redis
        if ls "$restore_path/database"/redis_*.rdb >/dev/null 2>&1; then
            local redis_file=$(ls -t "$restore_path/database"/redis_*.rdb | head -1)
            redis-cli -h "${REDIS_HOST}" --rdb "$redis_file"
            success "Redis 數據已恢復"
        fi
    fi
}

# 恢復數據
restore_data() {
    local restore_path="$1"
    log "恢復數據目錄..."
    
    if [ "$DRY_RUN" = "true" ]; then
        log "[DRY RUN] 將恢復數據目錄"
        return 0
    fi
    
    if [ -d "$restore_path/data" ]; then
        for archive in "$restore_path/data"/*.tar.gz; do
            tar -xzf "$archive" -C /
            log "  ✓ $(basename $archive)"
        done
        success "數據目錄已恢復"
    fi
}

# 主函數
main() {
    [ -z "$BACKUP_FILE" ] && usage
    [ "$BACKUP_FILE" = "--help" ] && usage
    
    echo "============================================================================"
    echo "SLASolve 恢復系統"
    echo "============================================================================"
    echo ""
    
    log "備份文件: $BACKUP_FILE"
    log "恢復目錄: $RESTORE_DIR"
    [ "$DRY_RUN" = "true" ] && warning "DRY RUN 模式 - 不會實際恢復"
    echo ""
    
    # 從 S3 下載 (如果需要)
    if [[ "$BACKUP_FILE" == s3://* ]]; then
        log "從 S3 下載備份..."
        local local_file="/tmp/$(basename $BACKUP_FILE)"
        aws s3 cp "$BACKUP_FILE" "$local_file"
        aws s3 cp "${BACKUP_FILE}.sha256" "${local_file}.sha256" || true
        BACKUP_FILE="$local_file"
    fi
    
    validate_backup "$BACKUP_FILE"
    extract_backup "$BACKUP_FILE"
    
    local restore_path="$RESTORE_DIR/$(ls -t $RESTORE_DIR | head -1)"
    
    restore_config "$restore_path"
    restore_code "$restore_path"
    restore_database "$restore_path"
    restore_data "$restore_path"
    
    # 清理
    rm -rf "$RESTORE_DIR"
    
    echo ""
    success "🎉 恢復任務完成！"
    
    if [ "$DRY_RUN" != "true" ]; then
        warning "請重新啟動服務以應用恢復的配置"
    fi
}

main
