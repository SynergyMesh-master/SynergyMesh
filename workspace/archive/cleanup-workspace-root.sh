#!/bin/bash
# Workspace Root Directory Cleanup Script
# Cleans up /workspace to follow minimal system skeleton principle

set -e

echo "🧹 Workspace Root Directory Cleanup"
echo "===================================="
echo ""
echo "Current directory: $(pwd)"
echo ""

# Directories/files to KEEP in /workspace
KEEP_ITEMS=(
    ".git"
    ".github"
    ".gitignore"
    ".gitignore.prod"
    ".env.example"
    ".replit"
    "controlplane"
    "workspace"
    "README.md"
    "root.bootstrap.yaml"
    "root.env.sh"
    "root.fs.map"
    "todo.md"
    "CNAME"
    "wrangler.toml"
    "FINAL_COMPLETION_SUMMARY.md"
    "PROJECT_REORGANIZATION_REPORT.md"
    "PR_REVIEW_REPORT.md"
    "PR_REVIEW_COMPLETION_REPORT.md"
    "CLOUDFLARE_DEPLOYMENT_FIX.md"
)

# Directories to REMOVE (move to workspace/archive/)
REMOVE_DIRS=(
    ".github-private"
    ".local"
    ".vscode"
    "MachineNativeOps"
    "archive"
    "axm-tools"
    "bin"
    "cloudflare"
    "config"
    "current-repo"
    "deploy"
    "docs"
    "engine"
    "etc"
    "examples"
    "governance"
    "home"
    "init.d"
    "lib"
    "machine-native-ops"
    "machine-native-ops-fresh"
    "machine-native-ops-new"
    "ops"
    "opt"
    "outputs"
    "reference-repo"
    "root"
    "sbin"
    "schemas"
    "scripts"
    "src"
    "srv"
    "summarized_conversations"
    "teams"
    "templates"
    "tests"
    "tools"
    "usr"
    "var"
)

echo "📋 Items to keep in /workspace:"
for item in "${KEEP_ITEMS[@]}"; do
    if [ -e "$item" ]; then
        echo "  ✅ $item (exists)"
    else
        echo "  ⚪ $item (not found)"
    fi
done

echo ""
echo "🗑️  Directories to remove from /workspace:"
removed_count=0
for dir in "${REMOVE_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ❌ $dir (will be archived)"
        ((removed_count++))
    fi
done

echo ""
echo "📊 Summary:"
echo "  - Directories to remove: $removed_count"
echo ""

if [ $removed_count -eq 0 ]; then
    echo "✅ No cleanup needed! Directory is already clean."
    exit 0
fi

read -p "⚠️  Proceed with cleanup? This will move $removed_count directories to workspace/archive/ (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Cleanup cancelled"
    exit 0
fi

echo ""
echo "🧹 Starting cleanup..."
echo ""

# Create archive directory
ARCHIVE_DIR="workspace/archive/workspace-root-cleanup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$ARCHIVE_DIR"
echo "📦 Archive directory: $ARCHIVE_DIR"
echo ""

# Move directories to archive
moved_count=0
failed_count=0

for dir in "${REMOVE_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "📦 Moving $dir to archive..."
        if mv "$dir" "$ARCHIVE_DIR/" 2>/dev/null; then
            ((moved_count++))
        else
            echo "  ⚠️  Failed to move $dir"
            ((failed_count++))
        fi
    fi
done

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Results:"
echo "  - Directories moved: $moved_count"
echo "  - Failed moves: $failed_count"
echo "  - Archive location: $ARCHIVE_DIR"
echo ""

echo "📁 Current /workspace structure:"
ls -la | grep "^d" | awk '{print "  " $9}' | grep -v "^\s*\.$" | grep -v "^\s*\.\.$"

echo ""
echo "🎯 Next steps:"
echo "1. Verify the workspace structure looks correct"
echo "2. Test that everything still works"
echo "3. Run validation: python3 controlplane/baseline/validation/validate-root-specs.py"
echo "4. If satisfied, commit changes: git add -A && git commit -m 'chore: Clean up workspace root directory'"
echo "5. Optional: Delete archive if no longer needed"