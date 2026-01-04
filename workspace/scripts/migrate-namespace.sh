#!/bin/bash
set -e

echo "=== MachineNativeOps Namespace Migration Script ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Handle chatops/.github directory
echo -e "${YELLOW}Step 1: Moving chatops/.github to correct location${NC}"
if [ -d "chatops/.github" ]; then
    echo "Found chatops/.github directory"
    
    # Check if .github/workflows exists at root
    if [ ! -d ".github/workflows" ]; then
        mkdir -p .github/workflows
    fi
    
    # Move chatops workflows to .github/workflows/chatops/
    if [ -d "chatops/.github/workflows" ]; then
        mkdir -p .github/workflows/chatops
        cp -r chatops/.github/workflows/* .github/workflows/chatops/ 2>/dev/null || true
        echo -e "${GREEN}✓ Moved chatops workflows to .github/workflows/chatops/${NC}"
    fi
    
    # Remove the old directory
    rm -rf chatops/.github
    echo -e "${GREEN}✓ Removed chatops/.github${NC}"
else
    echo "chatops/.github not found, skipping"
fi

echo ""

# Step 2: Handle chatops/root directory
echo -e "${YELLOW}Step 2: Analyzing chatops/root directory${NC}"
if [ -d "chatops/root" ]; then
    echo "Found chatops/root directory"
    echo "This directory contains legacy root configuration files"
    echo "These files use old API versions (root.platform.io/v1)"
    echo "Current root files use: machinenativeops.io/v1"
    
    # Archive the old root directory
    mkdir -p workspace-archive/archive/legacy-chatops-root
    cp -r chatops/root/* workspace-archive/archive/legacy-chatops-root/ 2>/dev/null || true
    echo -e "${GREEN}✓ Archived chatops/root to workspace-archive/archive/legacy-chatops-root/${NC}"
    
    # Remove the old directory
    rm -rf chatops/root
    echo -e "${GREEN}✓ Removed chatops/root${NC}"
else
    echo "chatops/root not found, skipping"
fi

echo ""

# Step 3: Replace AAPS namespace references
echo -e "${YELLOW}Step 3: Replacing AAPS namespace references${NC}"

# Find all files with AAPS references (excluding archived files)
FILES_TO_UPDATE=$(find . -type f \
    \( -name "*.yaml" -o -name "*.yml" -o -name "*.md" -o -name "*.json" \) \
    ! -path "./workspace-archive/*" \
    ! -path "./.git/*" \
    ! -path "./node_modules/*" \
    -exec grep -l "aaps\|AAPS" {} \; 2>/dev/null || true)

if [ -n "$FILES_TO_UPDATE" ]; then
    echo "Found files with AAPS references:"
    echo "$FILES_TO_UPDATE"
    echo ""
    
    for file in $FILES_TO_UPDATE; do
        echo "Processing: $file"
        
        # Create backup
        cp "$file" "$file.bak"
        
        # Replace AAPS references
        sed -i 's/aaps\.io/machinenativeops.io/g' "$file"
        sed -i 's/AAPS/MachineNativeOps/g' "$file"
        sed -i 's/aaps-/machine-native-ops-/g' "$file"
        sed -i 's/aaps_/machinenativeops_/g' "$file"
        sed -i 's/"aaps"/"machinenativeops"/g' "$file"
        sed -i "s/'aaps'/'machinenativeops'/g" "$file"
        
        # Check if file changed
        if ! diff -q "$file" "$file.bak" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Updated: $file${NC}"
            rm "$file.bak"
        else
            echo "  No changes needed"
            rm "$file.bak"
        fi
    done
else
    echo "No files with AAPS references found (excluding archived files)"
fi

echo ""

# Step 4: Rename files with AAPS in filename
echo -e "${YELLOW}Step 4: Renaming files with AAPS in filename${NC}"

FILES_TO_RENAME=$(find . -type f \
    \( -name "*aaps*" -o -name "*AAPS*" \) \
    ! -path "./workspace-archive/*" \
    ! -path "./.git/*" \
    ! -path "./node_modules/*" 2>/dev/null || true)

if [ -n "$FILES_TO_RENAME" ]; then
    echo "Found files to rename:"
    echo "$FILES_TO_RENAME"
    echo ""
    
    for file in $FILES_TO_RENAME; do
        dir=$(dirname "$file")
        filename=$(basename "$file")
        
        # Replace AAPS in filename
        new_filename=$(echo "$filename" | sed 's/AAPS/MachineNativeOps/g' | sed 's/aaps/machine-native-ops/g')
        
        if [ "$filename" != "$new_filename" ]; then
            new_path="$dir/$new_filename"
            mv "$file" "$new_path"
            echo -e "${GREEN}✓ Renamed: $filename → $new_filename${NC}"
        fi
    done
else
    echo "No files with AAPS in filename found (excluding archived files)"
fi

echo ""
echo -e "${GREEN}=== Migration Complete ===${NC}"
echo ""
echo "Next steps:"
echo "1. Review the changes: git diff"
echo "2. Regenerate fs.map and fs.index: ./bin/fs-map-generator.py --regenerate"
echo "3. Check for drift: ./bin/fs-map-generator.py --check-drift"
echo "4. Commit changes: git add . && git commit -m 'fix: migrate namespace from AAPS to MachineNativeOps'"