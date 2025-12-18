#!/bin/bash
# /docs/ 目錄結構修復腳本
# 
# 用途: 修復 docs/ 目錄的結構性問題
# 作者: GitHub Copilot
# 日期: 2025-12-10
#
# 使用方式:
#   ./docs/_fix_structure.sh --dry-run    # 預覽變更
#   ./docs/_fix_structure.sh --execute    # 執行變更

set -euo pipefail

REPO_ROOT="/home/runner/work/SynergyMesh/SynergyMesh"
DOCS_DIR="$REPO_ROOT/docs"
DRY_RUN=true

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 解析參數
if [[ "${1:-}" == "--execute" ]]; then
    DRY_RUN=false
    echo -e "${RED}⚠️  執行模式 - 將會實際修改文件！${NC}"
elif [[ "${1:-}" == "--dry-run" || "${1:-}" == "" ]]; then
    DRY_RUN=true
    echo -e "${GREEN}✓ 預覽模式 - 不會修改文件${NC}"
else
    echo "用法: $0 [--dry-run|--execute]"
    exit 1
fi

echo ""
echo "========================================================================"
echo "  📂 /docs/ 目錄結構修復腳本"
echo "========================================================================"
echo ""

# 輔助函數
log_step() {
    echo -e "${BLUE}▸ $1${NC}"
}

log_action() {
    if $DRY_RUN; then
        echo -e "  ${YELLOW}[DRY-RUN]${NC} $1"
    else
        echo -e "  ${GREEN}[執行]${NC} $1"
    fi
}

execute_cmd() {
    if $DRY_RUN; then
        echo "    $ $1"
    else
        eval "$1"
    fi
}

# ============================================================================
# 階段 1: 治理目錄整合 (P0 - 最高優先級)
# ============================================================================
log_step "階段 1: 治理目錄整合 (P0)"

if [ -d "$DOCS_DIR/GOVERNANCE" ]; then
    log_action "將 docs/GOVERNANCE/ 遷移到 governance/29-docs/"
    
    execute_cmd "mkdir -p $REPO_ROOT/governance/29-docs"
    
    for file in "$DOCS_DIR/GOVERNANCE"/*.md; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            log_action "  移動: $filename"
            execute_cmd "mv '$file' '$REPO_ROOT/governance/29-docs/$filename'"
        fi
    done
    
    log_action "刪除舊目錄 docs/GOVERNANCE/"
    execute_cmd "rmdir '$DOCS_DIR/GOVERNANCE'"
    
    # 更新引用
    log_action "更新 tools/cli/README.md 中的引用"
    execute_cmd "sed -i 's|docs/GOVERNANCE/|governance/29-docs/|g' '$REPO_ROOT/tools/cli/README.md'"
    
    echo -e "  ${GREEN}✓ 治理目錄整合完成${NC}"
else
    echo -e "  ${YELLOW}⊘ docs/GOVERNANCE/ 不存在，跳過${NC}"
fi

echo ""

# ============================================================================
# 階段 2: 生成文件隔離 (P2)
# ============================================================================
log_step "階段 2: 生成文件隔離 (P2)"

log_action "建立 docs/generated/ 目錄"
execute_cmd "mkdir -p '$DOCS_DIR/generated'"

# 移動生成文件
GENERATED_FILES=(
    "generated-index.yaml"
    "generated-mndoc.yaml"
    "knowledge-graph.yaml"
    "superroot-entities.yaml"
    "reports-analysis.json"
)

for file in "${GENERATED_FILES[@]}"; do
    if [ -f "$DOCS_DIR/$file" ]; then
        log_action "移動生成文件: $file"
        execute_cmd "mv '$DOCS_DIR/$file' '$DOCS_DIR/generated/$file'"
    fi
done

# 建立 .gitignore
log_action "建立 docs/generated/.gitignore"
if $DRY_RUN; then
    echo "    內容:"
    echo "      # Auto-generated files - regenerate with 'make all-kg'"
    echo "      *.yaml"
    echo "      *.json"
    echo "      !.gitignore"
else
    cat > "$DOCS_DIR/generated/.gitignore" << 'EOF'
# Auto-generated files - regenerate with 'make all-kg'
*.yaml
*.json
!.gitignore
EOF
fi

echo -e "  ${GREEN}✓ 生成文件隔離完成${NC}"
echo ""

# ============================================================================
# 階段 3: UPPERCASE 目錄處理 (P1)
# ============================================================================
log_step "階段 3: UPPERCASE 目錄處理 (P1)"

# 3.1 AGENTS/ → agents/
if [ -d "$DOCS_DIR/AGENTS" ]; then
    log_action "處理 AGENTS/ 目錄"
    
    execute_cmd "mkdir -p '$DOCS_DIR/agents/cli'"
    execute_cmd "mkdir -p '$DOCS_DIR/agents/mcp'"
    execute_cmd "mkdir -p '$DOCS_DIR/agents/virtual-experts'"
    
    [ -f "$DOCS_DIR/AGENTS/CLI.md" ] && execute_cmd "mv '$DOCS_DIR/AGENTS/CLI.md' '$DOCS_DIR/agents/cli/'"
    [ -f "$DOCS_DIR/AGENTS/MCP.md" ] && execute_cmd "mv '$DOCS_DIR/AGENTS/MCP.md' '$DOCS_DIR/agents/mcp/'"
    [ -f "$DOCS_DIR/AGENTS/VIRTUAL_EXPERTS.md" ] && execute_cmd "mv '$DOCS_DIR/AGENTS/VIRTUAL_EXPERTS.md' '$DOCS_DIR/agents/virtual-experts/'"
    [ -f "$DOCS_DIR/AGENTS/LIFECYCLE.md" ] && execute_cmd "mv '$DOCS_DIR/AGENTS/LIFECYCLE.md' '$DOCS_DIR/agents/'"
    
    execute_cmd "rmdir '$DOCS_DIR/AGENTS'"
fi

# 3.2 ARCHITECTURE/ → architecture/
if [ -d "$DOCS_DIR/ARCHITECTURE" ]; then
    log_action "處理 ARCHITECTURE/ 目錄"
    
    for file in "$DOCS_DIR/ARCHITECTURE"/*.md; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            log_action "  移動: $filename"
            execute_cmd "mv '$file' '$DOCS_DIR/architecture/$filename'"
        fi
    done
    
    execute_cmd "rmdir '$DOCS_DIR/ARCHITECTURE'"
fi

# 3.3 AUTONOMY/ → automation/autonomous-docs/
if [ -d "$DOCS_DIR/AUTONOMY" ]; then
    log_action "處理 AUTONOMY/ 目錄"
    execute_cmd "mkdir -p '$DOCS_DIR/automation/autonomous-docs'"
    execute_cmd "mv '$DOCS_DIR/AUTONOMY'/* '$DOCS_DIR/automation/autonomous-docs/'"
    execute_cmd "rmdir '$DOCS_DIR/AUTONOMY'"
fi

# 3.4 COMPONENTS/ → architecture/components/
if [ -d "$DOCS_DIR/COMPONENTS" ]; then
    log_action "處理 COMPONENTS/ 目錄"
    execute_cmd "mkdir -p '$DOCS_DIR/architecture/components'"
    execute_cmd "mv '$DOCS_DIR/COMPONENTS'/* '$DOCS_DIR/architecture/components/'"
    execute_cmd "rmdir '$DOCS_DIR/COMPONENTS'"
fi

# 3.5 COPILOT/ → tools/copilot-docs/ (或新位置)
if [ -d "$DOCS_DIR/COPILOT" ]; then
    log_action "處理 COPILOT/ 目錄"
    execute_cmd "mkdir -p '$DOCS_DIR/automation/copilot'"
    execute_cmd "mv '$DOCS_DIR/COPILOT'/* '$DOCS_DIR/automation/copilot/'"
    execute_cmd "rmdir '$DOCS_DIR/COPILOT'"
fi

# 3.6 DEPLOYMENT/ → operations/deployment/
if [ -d "$DOCS_DIR/DEPLOYMENT" ]; then
    log_action "處理 DEPLOYMENT/ 目錄"
    execute_cmd "mkdir -p '$DOCS_DIR/operations/deployment'"
    execute_cmd "mv '$DOCS_DIR/DEPLOYMENT'/* '$DOCS_DIR/operations/deployment/'"
    execute_cmd "rmdir '$DOCS_DIR/DEPLOYMENT'"
fi

echo -e "  ${GREEN}✓ UPPERCASE 目錄處理完成${NC}"
echo ""

# ============================================================================
# 階段 4: 更新索引文件
# ============================================================================
log_step "階段 4: 更新文檔索引"

if ! $DRY_RUN; then
    log_action "重新生成 knowledge_index.yaml"
    echo "  ⚠️  需要手動運行: python3 tools/docs/scan_repo_generate_index.py"
    
    log_action "驗證索引"
    echo "  ⚠️  需要手動運行: python3 tools/docs/validate_index.py --verbose"
fi

echo ""

# ============================================================================
# 完成總結
# ============================================================================
echo "========================================================================"
echo "  ✅ 腳本執行完成"
echo "========================================================================"
echo ""

if $DRY_RUN; then
    echo -e "${YELLOW}這是預覽模式。要實際執行變更，請運行:${NC}"
    echo -e "  ${BLUE}$0 --execute${NC}"
    echo ""
else
    echo -e "${GREEN}結構修復已完成！${NC}"
    echo ""
    echo "後續步驟:"
    echo "  1. 檢查 git status，確認變更符合預期"
    echo "  2. 運行: python3 tools/docs/validate_index.py --verbose"
    echo "  3. 運行: make all-kg"
    echo "  4. 提交變更: git add . && git commit -m '修復 docs/ 目錄結構'"
    echo ""
fi

exit 0
