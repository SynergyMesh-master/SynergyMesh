#!/bin/bash
# ============================================================================
# 備份腳本 (Backup Script)
# ============================================================================
# 執行完整或增量備份，支持多種備份目標
# ============================================================================

set -euo pipefail

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
BACKUP_TYPE="${1:-full}"  # full, incremental, database
BACKUP_DIR="${BACKUP_DIR:-/tmp/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="slasolve_${BACKUP_TYPE}_${TIMESTAMP}"
RETENTION_DAYS=30

# S3 配置 (如果使用)
S3_BUCKET="${S3_BUCKET:-slasolve-backups}"
S3_REGION="${S3_REGION:-us-east-1}"

# 日誌函數
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 檢查依賴
check_dependencies() {
    local deps=("tar" "gzip" "sha256sum")
    
    for cmd in "${deps[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error "Required command not found: $cmd"
            exit 1
        fi
    done
    
    # 檢查 AWS CLI (如果需要)
    if [ -n "${S3_BUCKET:-}" ]; then
        if ! command -v aws &> /dev/null; then
            warning "AWS CLI not found, skipping S3 upload"
            S3_BUCKET=""
        fi
    fi
}

# 創建備份目錄
prepare_backup_dir() {
    log "準備備份目錄: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    
    local backup_path="$BACKUP_DIR/$BACKUP_NAME"
    mkdir -p "$backup_path"
    echo "$backup_path"
}

# 備份配置文件
backup_config() {
    local backup_path="$1"
    log "備份配置文件..."
    
    local config_files=(
        "docker-compose.yml"
        "docker-compose.prod.yml"
        ".env.production"
        "auto-fix-bot.yml"
        "nginx.conf"
    )
    
    mkdir -p "$backup_path/config"
    
    for file in "${config_files[@]}"; do
        if [ -f "$file" ]; then
            cp "$file" "$backup_path/config/"
            log "  ✓ $file"
        fi
    done
    
    # 備份 Kubernetes 配置
    if [ -d "k8s" ]; then
        cp -r k8s "$backup_path/config/"
        log "  ✓ k8s/"
    fi
}

# 備份代碼
backup_code() {
    local backup_path="$1"
    log "備份代碼..."
    
    local dirs=(
        "core"
        "mcp-servers"
        "advanced-system-src"
        "scripts"
    )
    
    mkdir -p "$backup_path/code"
    
    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            tar -czf "$backup_path/code/${dir}.tar.gz" "$dir"
            log "  ✓ $dir"
        fi
    done
}

# 備份數據庫
backup_database() {
    local backup_path="$1"
    log "備份數據庫..."
    
    mkdir -p "$backup_path/database"
    
    # PostgreSQL 備份 (如果使用)
    if [ -n "${POSTGRES_HOST:-}" ]; then
        local db_file="$backup_path/database/postgres_${TIMESTAMP}.sql.gz"
        
        # 使用 .pgpass 文件以提高安全性
        # 格式: hostname:port:database:username:password
        if [ -f "$HOME/.pgpass" ]; then
            pg_dump \
                -h "${POSTGRES_HOST}" \
                -U "${POSTGRES_USER}" \
                -d "${POSTGRES_DB}" \
                | gzip > "$db_file"
        else
            # 後備方案，但會有安全警告
            warning "建議使用 .pgpass 文件以提高安全性"
            PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
                -h "${POSTGRES_HOST}" \
                -U "${POSTGRES_USER}" \
                -d "${POSTGRES_DB}" \
                | gzip > "$db_file"
        fi
        
        log "  ✓ PostgreSQL 備份完成"
    fi
    
    # Redis 備份 (如果使用)
    if [ -n "${REDIS_HOST:-}" ]; then
        local redis_file="$backup_path/database/redis_${TIMESTAMP}.rdb"
        
        redis-cli -h "${REDIS_HOST}" --rdb "$redis_file"
        log "  ✓ Redis 備份完成"
    fi
}

# 備份數據目錄
backup_data() {
    local backup_path="$1"
    log "備份數據目錄..."
    
    local data_dirs=(
        "/data/provenance"
        "/data/slsa"
        "/data/logs"
    )
    
    mkdir -p "$backup_path/data"
    
    for dir in "${data_dirs[@]}"; do
        if [ -d "$dir" ]; then
            local dir_name=$(basename "$dir")
            tar -czf "$backup_path/data/${dir_name}.tar.gz" "$dir"
            log "  ✓ $dir"
        fi
    done
}

# 生成備份清單
generate_manifest() {
    local backup_path="$1"
    log "生成備份清單..."
    
    cat > "$backup_path/manifest.json" <<EOF
{
  "backup_name": "$BACKUP_NAME",
  "backup_type": "$BACKUP_TYPE",
  "timestamp": "$TIMESTAMP",
  "hostname": "$(hostname)",
  "version": "1.0.0",
  "files": []
}
EOF
    
    # 生成文件列表和校驗和
    find "$backup_path" -type f ! -name "manifest.json" ! -name "*.sha256" -exec sha256sum {} \; > "$backup_path/checksums.sha256"
    
    log "  ✓ 清單已生成"
}

# 壓縮備份
compress_backup() {
    local backup_path="$1"
    log "壓縮備份..."
    
    local archive_path="${backup_path}.tar.gz"
    tar -czf "$archive_path" -C "$BACKUP_DIR" "$BACKUP_NAME"
    
    # 生成校驗和
    sha256sum "$archive_path" > "${archive_path}.sha256"
    
    # 刪除臨時目錄
    rm -rf "$backup_path"
    
    local size=$(du -h "$archive_path" | cut -f1)
    success "備份壓縮完成: $archive_path ($size)"
    
    echo "$archive_path"
}

# 上傳到 S3
upload_to_s3() {
    local archive_path="$1"
    
    if [ -z "${S3_BUCKET:-}" ]; then
        return 0
    fi
    
    log "上傳備份到 S3..."
    
    aws s3 cp "$archive_path" "s3://$S3_BUCKET/backups/" \
        --region "$S3_REGION" \
        --storage-class STANDARD_IA
    
    aws s3 cp "${archive_path}.sha256" "s3://$S3_BUCKET/backups/" \
        --region "$S3_REGION"
    
    success "備份已上傳到 S3: s3://$S3_BUCKET/backups/$(basename $archive_path)"
}

# 清理舊備份
cleanup_old_backups() {
    log "清理 $RETENTION_DAYS 天前的舊備份..."
    
    find "$BACKUP_DIR" -name "slasolve_*.tar.gz" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "slasolve_*.tar.gz.sha256" -mtime +$RETENTION_DAYS -delete
    
    # S3 清理 (如果使用)
    if [ -n "${S3_BUCKET:-}" ]; then
        aws s3 ls "s3://$S3_BUCKET/backups/" | while read -r line; do
            createDate=$(echo "$line" | awk '{print $1" "$2}')
            createDate=$(date -d "$createDate" +%s)
            olderThan=$(date -d "$RETENTION_DAYS days ago" +%s)
            
            if [[ $createDate -lt $olderThan ]]; then
                fileName=$(echo "$line" | awk '{print $4}')
                if [[ $fileName != "" ]]; then
                    aws s3 rm "s3://$S3_BUCKET/backups/$fileName"
                    log "  ✓ 刪除: $fileName"
                fi
            fi
        done
    fi
    
    success "舊備份清理完成"
}

# 完整備份
full_backup() {
    log "開始完整備份..."
    
    local backup_path=$(prepare_backup_dir)
    
    backup_config "$backup_path"
    backup_code "$backup_path"
    backup_database "$backup_path"
    backup_data "$backup_path"
    generate_manifest "$backup_path"
    
    local archive_path=$(compress_backup "$backup_path")
    upload_to_s3 "$archive_path"
    
    success "完整備份完成: $archive_path"
}

# 增量備份
incremental_backup() {
    log "開始增量備份..."
    
    local backup_path=$(prepare_backup_dir)
    
    # 只備份最近 24 小時內修改的文件
    backup_config "$backup_path"
    backup_database "$backup_path"
    
    # 數據目錄增量備份
    mkdir -p "$backup_path/data"
    find /data -type f -mtime -1 -exec cp --parents {} "$backup_path/data/" \;
    
    generate_manifest "$backup_path"
    
    local archive_path=$(compress_backup "$backup_path")
    upload_to_s3 "$archive_path"
    
    success "增量備份完成: $archive_path"
}

# 僅數據庫備份
database_only_backup() {
    log "開始數據庫備份..."
    
    local backup_path=$(prepare_backup_dir)
    
    backup_database "$backup_path"
    generate_manifest "$backup_path"
    
    local archive_path=$(compress_backup "$backup_path")
    upload_to_s3 "$archive_path"
    
    success "數據庫備份完成: $archive_path"
}

# 主函數
main() {
    echo "============================================================================"
    echo "SLASolve 備份系統"
    echo "============================================================================"
    echo ""
    
    log "備份類型: $BACKUP_TYPE"
    log "備份目錄: $BACKUP_DIR"
    log "時間戳: $TIMESTAMP"
    echo ""
    
    check_dependencies
    
    case "$BACKUP_TYPE" in
        full)
            full_backup
            ;;
        incremental)
            incremental_backup
            ;;
        database)
            database_only_backup
            ;;
        *)
            error "未知的備份類型: $BACKUP_TYPE"
            echo "使用方式: $0 [full|incremental|database]"
            exit 1
            ;;
    esac
    
    cleanup_old_backups
    
    echo ""
    success "🎉 備份任務完成！"
}

# 執行主函數
main
