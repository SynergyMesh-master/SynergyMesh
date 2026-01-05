#!/bin/bash
# Script to systematically merge all branches into main
# This script will handle conflicts gracefully

set -e

echo "========================================="
echo "Branch Merge Automation Script"
echo "========================================="

# Ensure we're on main branch
echo "Step 1: Switching to main branch..."
git checkout main || git checkout -b main origin/main
git pull origin main

# Get list of all remote branches (excluding main and HEAD)
echo "Step 2: Getting list of branches to merge..."
BRANCHES=$(git branch -r | grep -v "main" | grep -v "HEAD" | sed 's/origin\///' | sort -u)

# Count branches
TOTAL_BRANCHES=$(echo "$BRANCHES" | wc -l)
echo "Found $TOTAL_BRANCHES branches to potentially merge"

# Filter branches that have unique commits (not already merged)
echo "Step 3: Identifying branches with unique commits..."
MERGE_COUNT=0
SKIP_COUNT=0
CONFLICT_COUNT=0

# Create a log file
LOG_FILE="merge-log-$(date +%Y%m%d-%H%M%S).txt"
echo "Merge Log - $(date)" > "$LOG_FILE"

# Process each branch
for branch in $BRANCHES; do
    echo ""
    echo "Processing branch: $branch"
    
    # Check if branch is already merged
    if git merge-base --is-ancestor "origin/$branch" origin/main 2>/dev/null; then
        echo "  ✓ Branch already merged, skipping"
        ((SKIP_COUNT++))
        echo "$branch: SKIPPED (already merged)" >> "$LOG_FILE"
        continue
    fi
    
    # Check if branch has commits ahead of main
    COMMITS_AHEAD=$(git log origin/main..origin/$branch --oneline | wc -l)
    if [ "$COMMITS_AHEAD" -eq 0 ]; then
        echo "  ✓ Branch has no unique commits, skipping"
        ((SKIP_COUNT++))
        echo "$branch: SKIPPED (no unique commits)" >> "$LOG_FILE"
        continue
    fi
    
    echo "  → Branch has $COMMITS_AHEAD unique commit(s)"
    
    # Try to merge
    echo "  → Attempting merge..."
    if git merge "origin/$branch" --no-edit --no-ff 2>/dev/null; then
        echo "  ✓ Merge successful"
        ((MERGE_COUNT++))
        echo "$branch: MERGED successfully ($COMMITS_AHEAD commits)" >> "$LOG_FILE"
    else
        echo "  ✗ Merge conflict detected"
        ((CONFLICT_COUNT++))
        echo "$branch: CONFLICT detected, using 'ours' strategy" >> "$LOG_FILE"
        
        # Abort the failed merge
        git merge --abort 2>/dev/null || true
        
        # Try with -X ours strategy (prefer main branch)
        echo "  → Retrying with -X ours strategy..."
        if git merge "origin/$branch" -X ours --no-edit --no-ff; then
            echo "  ✓ Merge with -X ours successful"
            ((MERGE_COUNT++))
            echo "$branch: MERGED with -X ours strategy" >> "$LOG_FILE"
        else
            echo "  ✗ Merge still failed, skipping"
            git merge --abort 2>/dev/null || true
            echo "$branch: FAILED (could not merge)" >> "$LOG_FILE"
        fi
    fi
done

echo ""
echo "========================================="
echo "Merge Summary"
echo "========================================="
echo "Total branches processed: $TOTAL_BRANCHES"
echo "Successfully merged: $MERGE_COUNT"
echo "Skipped (already merged/no unique commits): $SKIP_COUNT"
echo "Conflicts encountered: $CONFLICT_COUNT"
echo ""
echo "Detailed log saved to: $LOG_FILE"
echo "========================================="

# Push changes to origin
echo ""
echo "Step 4: Pushing merged changes to origin..."
if [ "$MERGE_COUNT" -gt 0 ]; then
    git push origin main
    echo "✓ Successfully pushed to origin/main"
else
    echo "No changes to push"
fi

echo ""
echo "========================================="
echo "Branch merge process completed!"
echo "========================================="