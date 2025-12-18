#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
#                    Install Git Hooks
#                    安裝 Git Hooks
# ═══════════════════════════════════════════════════════════════════════════════
#
# 使用方式 / Usage:
#   ./scripts/hooks/install-hooks.sh
#
# ═══════════════════════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GIT_HOOKS_DIR="$(git rev-parse --git-dir)/hooks"

echo "🔧 Installing Git hooks..."

# Install pre-commit hook
if [ -f "$SCRIPT_DIR/pre-commit" ]; then
    cp "$SCRIPT_DIR/pre-commit" "$GIT_HOOKS_DIR/pre-commit"
    chmod +x "$GIT_HOOKS_DIR/pre-commit"
    echo "✅ Installed pre-commit hook"
else
    echo "⚠️ pre-commit hook not found"
fi

# Install pre-push hook
if [ -f "$SCRIPT_DIR/pre-push" ]; then
    cp "$SCRIPT_DIR/pre-push" "$GIT_HOOKS_DIR/pre-push"
    chmod +x "$GIT_HOOKS_DIR/pre-push"
    echo "✅ Installed pre-push hook"
else
    echo "⚠️ pre-push hook not found"
fi

echo ""
echo "✅ Git hooks installed successfully!"
echo ""
echo "Hooks installed:"
echo "  - pre-commit: Validates YAML, workflows, and scans for sensitive data"
echo "  - pre-push: Validates Stage 0 requirements and runs tests"
echo ""
echo "To skip hooks temporarily, use:"
echo "  git commit --no-verify"
echo "  git push --no-verify"
echo ""
