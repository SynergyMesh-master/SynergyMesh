#!/bin/bash
# .git/hooks/post-commit
# 自動同步所有子目錄到遠程倉庫

set -e

echo "ðŸ"„ [Island AI] 開始自動同步所有子目錄..."

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
SYNC_LOG=".git/sync-log.txt"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 記錄日誌
log() {
    echo -e "${GREEN}[${TIMESTAMP}]${NC} $1" | tee -a "$SYNC_LOG"
}

error() {
    echo -e "${RED}[ERROR ${TIMESTAMP}]${NC} $1" | tee -a "$SYNC_LOG"
}

warn() {
    echo -e "${YELLOW}[WARN ${TIMESTAMP}]${NC} $1" | tee -a "$SYNC_LOG"
}

# 獲取當前分支
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
log "當前分支: $CURRENT_BRANCH"

# 獲取最後一次提交的信息
LAST_COMMIT=$(git log -1 --pretty=format:"%H - %s")
log "最後提交: $LAST_COMMIT"

# 檢測所有變更的目錄（包括子子子...目錄）
CHANGED_DIRS=$(git diff-tree --no-commit-id --name-only -r HEAD | \
    sed 's|/[^/]*$||' | \
    sort -u)

if [ -z "$CHANGED_DIRS" ]; then
    warn "沒有檢測到目錄變更，跳過同步"
    exit 0
fi

log "檢測到以下目錄有變更:"
echo "$CHANGED_DIRS" | while read -r dir; do
    log "  - $dir"
done

# 同步函數
sync_directory() {
    local dir=$1
    local depth=$(echo "$dir" | tr -cd '/' | wc -c)
    
    log "正在同步: $dir (深度: $depth)"
    
    # 檢查目錄是否存在
    if [ ! -d "$dir" ]; then
        warn "目錄不存在，跳過: $dir"
        return
    fi
    
    # 檢查是否有 .gitignore 阻止同步
    if git check-ignore -q "$dir"; then
        warn "目錄被 .gitignore 忽略: $dir"
        return
    fi
    
    # 遞歸處理子目錄
    if [ -d "$dir" ]; then
        find "$dir" -type d -not -path '*/\.*' | while read -r subdir; do
            if [ "$subdir" != "$dir" ]; then
                log "  ↳ 發現子目錄: $subdir"
            fi
        done
    fi
}

# 執行同步
echo "$CHANGED_DIRS" | while read -r dir; do
    if [ -n "$dir" ]; then
        sync_directory "$dir"
    fi
done

# Push 到遠程
log "準備推送到遠程倉庫..."

# 檢查是否有遠程倉庫
if ! git remote get-url origin > /dev/null 2>&1; then
    error "未配置遠程倉庫 origin"
    exit 1
fi

# 拉取最新更改以避免衝突
log "拉取遠程最新更改..."
if git pull --rebase origin "$CURRENT_BRANCH"; then
    log "✅ 成功拉取遠程更改"
else
    error "拉取失敗，請手動解決衝突"
    exit 1
fi

# 推送到遠程
log "推送到 origin/$CURRENT_BRANCH..."
if git push origin "$CURRENT_BRANCH"; then
    log "✅ 成功推送到遠程倉庫"
else
    error "推送失敗，請檢查網絡連接或權限"
    exit 1
fi

# 統計信息
TOTAL_FILES=$(git diff-tree --no-commit-id --name-only -r HEAD | wc -l)
TOTAL_DIRS=$(echo "$CHANGED_DIRS" | wc -l)

log "================================================"
log "同步完成統計:"
log "  - 變更文件數: $TOTAL_FILES"
log "  - 影響目錄數: $TOTAL_DIRS"
log "  - 當前分支: $CURRENT_BRANCH"
log "  - 提交 SHA: $(git rev-parse HEAD)"
log "================================================"

echo ""
echo -e "${GREEN}✅ 自動同步完成！${NC}"
echo ""
