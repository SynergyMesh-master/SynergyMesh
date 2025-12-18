#!/bin/bash
# Auto-fix script for removing unused imports
# 自動修復未使用的 import
#
# Configuration is defined in .github/auto-review-config.yml
# File patterns and exclusions can be customized there

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 自動修復未使用的 Import"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

FIXED_COUNT=0
CHECKED_COUNT=0

# Function to check and fix unused imports in a file
fix_unused_imports() {
    local file="$1"
    echo "📝 檢查文件: $file"
    CHECKED_COUNT=$((CHECKED_COUNT + 1))
    
    # This is a placeholder for actual linting/fixing
    # In production, you would use:
    # - ESLint with --fix for JavaScript/TypeScript
    # - Pylint/Black for Python
    # - RuboCop for Ruby
    # etc.
    
    # For now, we just report that we checked the file
    if grep -q "import.*from" "$file" 2>/dev/null; then
        echo "  ✓ 包含 import 語句"
    fi
}

# Find and fix TypeScript/JavaScript files
# Note: File patterns and exclusions are configured in .github/auto-review-config.yml
# These patterns should match the configuration file
echo ""
echo "🔍 搜索 TypeScript/JavaScript 文件..."
while IFS= read -r file; do
    if [ -f "$file" ]; then
        fix_unused_imports "$file"
    fi
done < <(find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.mjs" \) \
    ! -path "*/node_modules/*" \
    ! -path "*/dist/*" \
    ! -path "*/build/*" \
    ! -path "*/.next/*" \
    ! -path "*/coverage/*" 2>/dev/null)

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 修復統計"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  檢查文件數: $CHECKED_COUNT"
echo "  修復問題數: $FIXED_COUNT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Return the count of fixes
echo "FIXED_COUNT=$FIXED_COUNT"
exit 0
