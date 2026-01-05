#!/bin/bash
# Improved Branch Merge Script
# Merges all branches systematically with conflict resolution

set -e

echo "========================================="
echo "Comprehensive Branch Merge Script"
echo "========================================="

# Ensure we're on main
git checkout main
git pull origin main

# Get all branches except main and HEAD
BRANCHES=$(git branch -r | grep -v "main" | grep -v "HEAD" | sed 's/origin\///' | sort -u)

TOTAL=$(echo "$BRANCHES" | wc -l)
echo "Total branches to process: $TOTAL"

# Counter
MERGED=0
SKIPPED=0
FAILED=0

# Process each branch
for branch in $BRANCHES; do
    echo ""
    echo "[$((MERGED + SKIPPED + FAILED + 1))/$TOTAL] Processing: $branch"
    
    # Check if already merged
    if git merge-base --is-ancestor "origin/$branch" origin/main 2>/dev/null; then
        echo "  ✓ Already merged"
        ((SKIPPED++))
        continue
    fi
    
    # Check for unique commits
    COMMITS=$(git log origin/main..origin/$branch --oneline | wc -l)
    if [ "$COMMITS" -eq 0 ]; then
        echo "  ✓ No unique commits"
        ((SKIPPED++))
        continue
    fi
    
    echo "  → Found $COMMITS unique commits"
    
    # Try to merge with strategies
    MERGE_SUCCESS=false
    
    # Strategy 1: Normal merge
    if ! $MERGE_SUCCESS; then
        echo "  → Attempting normal merge..."
        if git merge "origin/$branch" --no-edit --no-ff 2>/dev/null; then
            echo "  ✓ Normal merge successful"
            MERGE_SUCCESS=true
        else
            git merge --abort 2>/dev/null || true
        fi
    fi
    
    # Strategy 2: Use 'ours' for conflicts
    if ! $MERGE_SUCCESS; then
        echo "  → Trying with -X ours strategy..."
        if git merge "origin/$branch" -X ours --no-edit --no-ff 2>/dev/null; then
            echo "  ✓ Merge with -X ours successful"
            MERGE_SUCCESS=true
        else
            git merge --abort 2>/dev/null || true
        fi
    fi
    
    # Strategy 3: Use 'theirs' for conflicts
    if ! $MERGE_SUCCESS; then
        echo "  → Trying with -X theirs strategy..."
        if git merge "origin/$branch" -X theirs --no-edit --no-ff 2>/dev/null; then
            echo "  ✓ Merge with -X theirs successful"
            MERGE_SUCCESS=true
        else
            git merge --abort 2>/dev/null || true
        fi
    fi
    
    # Strategy 4: Squash merge (take all commits)
    if ! $MERGE_SUCCESS; then
        echo "  → Trying squash merge..."
        if git merge --squash "origin/$branch" 2>/dev/null; then
            git commit -m "Merge branch '$branch' (squashed)" 2>/dev/null
            echo "  ✓ Squash merge successful"
            MERGE_SUCCESS=true
        else
            git merge --abort 2>/dev/null || true
        fi
    fi
    
    if $MERGE_SUCCESS; then
        ((MERGED++))
        echo "  ✓ Branch merged successfully"
    else
        ((FAILED++))
        echo "  ✗ Failed to merge branch"
    fi
done

echo ""
echo "========================================="
echo "Merge Summary"
echo "========================================="
echo "Total branches: $TOTAL"
echo "Successfully merged: $MERGED"
echo "Skipped: $SKIPPED"
echo "Failed: $FAILED"
echo "========================================="

# Push if we merged anything
if [ "$MERGED" -gt 0 ]; then
    echo ""
    echo "Pushing merged changes to origin..."
    git push origin main
    echo "✓ Pushed successfully"
fi

echo ""
echo "Branch merge process completed!"