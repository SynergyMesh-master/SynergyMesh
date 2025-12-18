#!/bin/bash
# Island AI 品牌遷移腳本
# 將所有 Island AI 相關術語替換為 Island AI 品牌

set -e

WORKSPACE="/workspaces/unmanned-island"
cd "$WORKSPACE"

echo "🏝️ Island AI 品牌遷移腳本 v1.0"
echo "================================"

# 定義替換規則
declare -A REPLACEMENTS=(
    # 主要品牌替換
    ["Island AI"]="Island AI"
    ["Island AI"]="Island AI"
    ["island ai"]="island ai"
    ["Island Agents"]="Island Agents"
    ["Island Agents"]="Island Agents"
    ["island agents"]="island agents"
    ["Island Shell"]="Island Shell"
    ["island shell"]="island shell"
    ["Island Admin CLI"]="Island Admin CLI"
    ["island admin cli"]="island admin cli"
    ["Island Workspace"]="Island Workspace"
    ["island workspace"]="island workspace"
    ["@island"]="@island"
    # 檔案引用替換
    ["island-ai-instructions.md"]="island-ai-instructions.md"
    ["island-ai-setup-steps.yml"]="island-ai-setup-steps.yml"
    ["ISLAND_AI_SETUP.md"]="ISLAND_AI_SETUP.md"
    ["validate-island-ai-instructions"]="validate-island-ai-instructions"
    ["fix-island-ai.sh"]="fix-island-ai.sh"
    ["island-ai-diagnosis"]="island-ai-diagnosis"
    # 單獨的 Island AI (需要謹慎處理)
    ["Island AI"]="Island AI"
)

echo ""
echo "📋 替換規則："
for old in "${!REPLACEMENTS[@]}"; do
    echo "   $old → ${REPLACEMENTS[$old]}"
done

echo ""
echo "🔍 開始掃描檔案..."

# 要處理的檔案類型
FILE_TYPES=("*.md" "*.yml" "*.yaml" "*.json" "*.sh" "*.txt" "*.ts" "*.js" "*.py")

# 排除的目錄
EXCLUDE_DIRS=("node_modules" ".git" "dist" "build" "__pycache__" ".venv")

# 建立 find 排除參數
EXCLUDE_ARGS=""
for dir in "${EXCLUDE_DIRS[@]}"; do
    EXCLUDE_ARGS="$EXCLUDE_ARGS -path '*/$dir/*' -prune -o"
done

# 統計
TOTAL_FILES=0
TOTAL_REPLACEMENTS=0

# 執行替換
for pattern in "${!REPLACEMENTS[@]}"; do
    old="$pattern"
    new="${REPLACEMENTS[$pattern]}"
    
    # 使用 grep 找出包含該模式的檔案
    files=$(grep -rl "$old" --include="*.md" --include="*.yml" --include="*.yaml" --include="*.json" --include="*.sh" --include="*.txt" . 2>/dev/null | grep -v node_modules | grep -v .git || true)
    
    if [ -n "$files" ]; then
        for file in $files; do
            if [ -f "$file" ]; then
                # 執行替換
                sed -i "s|$old|$new|g" "$file"
                ((TOTAL_REPLACEMENTS++)) || true
            fi
        done
    fi
done

echo ""
echo "✅ 品牌替換完成！"
echo "   總替換操作: $TOTAL_REPLACEMENTS"

# 重命名檔案
echo ""
echo "📁 重命名檔案..."

# 重命名列表
declare -A RENAMES=(
    ["docs/ISLAND_AI_SETUP.md"]="docs/ISLAND_AI_SETUP.md"
    ["docs/troubleshooting/github-island-ai-agent-fix.md"]="docs/troubleshooting/island-ai-agent-fix.md"
    ["scripts/fix-island-ai.sh"]="scripts/fix-island-ai.sh"
    [".github/workflows/island-ai-setup-steps.yml"]=".github/workflows/island-ai-setup-steps.yml"
    [".github/workflows/validate-island-ai-instructions.yml"]=".github/workflows/validate-island-ai-instructions.yml"
)

for old_file in "${!RENAMES[@]}"; do
    new_file="${RENAMES[$old_file]}"
    if [ -f "$old_file" ]; then
        mv "$old_file" "$new_file"
        echo "   ✓ $old_file → $new_file"
    fi
done

# 刪除舊的診斷檔案
rm -f island-ai-diagnosis-*.txt 2>/dev/null || true

echo ""
echo "🏝️ Island AI 品牌遷移完成！"
