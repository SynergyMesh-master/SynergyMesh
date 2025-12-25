#!/bin/bash
# Root Directory Cleanup Script
# Removes all non-FHS and non-essential directories from root

set -e

echo "🧹 Root Directory Cleanup Script"
echo "================================"
echo ""

# Define directories to KEEP
KEEP_DIRS=(
    "bin"
    "sbin"
    "lib"
    "etc"
    "usr"
    "var"
    "opt"
    "srv"
    "home"
    "root"
    "tmp"
    "controlplane"
    "workspace"
    ".github"
    ".git"
)

# Define directories to REMOVE
REMOVE_DIRS=(
    ".local"
    ".vscode"
    "MachineNativeOps"
    "archive"
    "axm-tools"
    "cloudflare"
    "config"
    "current-repo"
    "deploy"
    "docs"
    "engine"
    "examples"
    "governance"
    "init.d"
    "machine-native-ops"
    "machine-native-ops-fresh"
    "machine-native-ops-new"
    "ops"
    "outputs"
    "reference-repo"
    "schemas"
    "scripts"
    "src"
    "summarized_conversations"
    "teams"
    "templates"
    "tests"
    "tools"
)

echo "📋 Directories to keep:"
for dir in "${KEEP_DIRS[@]}"; do
    echo "  ✅ $dir"
done

echo ""
echo "🗑️  Directories to remove:"
for dir in "${REMOVE_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ❌ $dir (exists)"
    else
        echo "  ⚪ $dir (not found)"
    fi
done

echo ""
read -p "⚠️  Do you want to proceed with cleanup? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Cleanup cancelled"
    exit 0
fi

echo ""
echo "🧹 Starting cleanup..."
echo ""

# Create archive directory in workspace
mkdir -p workspace/archive/root-cleanup-$(date +%Y%m%d-%H%M%S)
ARCHIVE_DIR="workspace/archive/root-cleanup-$(date +%Y%m%d-%H%M%S)"

# Remove directories
for dir in "${REMOVE_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "📦 Archiving $dir to $ARCHIVE_DIR/"
        mv "$dir" "$ARCHIVE_DIR/" 2>/dev/null || echo "  ⚠️  Failed to move $dir"
    fi
done

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Final root directory structure:"
ls -la / | grep "^d" | awk '{print $9}' | grep -v "^\.$" | grep -v "^\.\.$"

echo ""
echo "📦 Archived directories are in: $ARCHIVE_DIR"
echo ""
echo "🎯 Next steps:"
echo "1. Verify the root directory structure"
echo "2. Test that everything still works"
echo "3. If satisfied, you can delete the archive"
echo "4. Commit the changes to Git"