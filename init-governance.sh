#!/bin/bash
#
# Machine-Native Governance Framework Initialization Script
# Run this to set up the complete governance system
#

set -e

echo "========================================"
echo "Machine-Native Governance Framework"
echo "Initialization Script"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Verify manifest exists
echo "[1/6] Verifying governance manifest..."
if [ ! -f "governance-manifest.yaml" ]; then
    echo "❌ ERROR: governance-manifest.yaml not found!"
    exit 1
fi
echo -e "${GREEN}✓${NC} Governance manifest found"
echo ""

# Step 2: Set up Python environment
echo "[2/6] Setting up Python environment..."
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 not found!"
    exit 1
fi

echo "Installing Python dependencies..."
pip3 install pyyaml jsonschema --quiet 2>/dev/null || pip install pyyaml jsonschema
echo -e "${GREEN}✓${NC} Python dependencies installed"
echo ""

# Step 3: Validate schemas
echo "[3/6] Validating governance schemas..."
python3 tools/python/governance_agent.py info > /dev/null 2>&1
echo -e "${GREEN}✓${NC} Schemas validated"
echo ""

# Step 4: Install Git hooks
echo "[4/6] Installing Git hooks..."
if [ -f ".git/hooks/pre-commit" ]; then
    echo "⚠ Pre-commit hook already exists, skipping..."
else
    cp tools/git-hooks/pre-commit .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    echo -e "${GREEN}✓${NC} Git hooks installed"
fi
echo ""

# Step 5: Test governance agent
echo "[5/6] Testing governance agent..."
echo "Testing name validation..."
RESULT=$(python3 tools/python/governance_agent.py validate "prod-payment-deploy-v1.0.0" "k8s-deployment" "prod" 2>&1)
if echo "$RESULT" | grep -q '"valid": true'; then
    echo -e "${GREEN}✓${NC} Name validation working"
else
    echo "⚠ Name validation returned unexpected result"
fi

echo "Testing name generation..."
RESULT=$(python3 tools/python/governance_agent.py generate "k8s-deployment" "prod" "platform" "payment" "v1.0.0" 2>&1)
if echo "$RESULT" | grep -q '"success": true'; then
    echo -e "${GREEN}✓${NC} Name generation working"
else
    echo "⚠ Name generation returned unexpected result"
fi
echo ""

# Step 6: Generate initialization report
echo "[6/6] Generating initialization report..."
python3 tools/python/governance_agent.py info > governance-init-report.json
echo -e "${GREEN}✓${NC} Initialization report generated"
echo ""

# Summary
echo "========================================"
echo "✅ Initialization Complete!"
echo "========================================"
echo ""
echo "Governance Framework is ready for use."
echo ""
echo "Next Steps:"
echo "  1. Review governance-manifest.yaml for module locations"
echo "  2. Test validation: python3 tools/python/governance_agent.py validate <name> <type> <env>"
echo "  3. Test generation: python3 tools/python/governance_agent.py generate <type> <env> [team] [service] [version]"
echo "  4. Review README-MACHINE.md for AI agent integration"
echo ""
echo "Key Files:"
echo "  - governance-manifest.yaml (primary entry point)"
echo "  - tools/python/governance_agent.py (main tool)"
echo "  - schemas/ (validation schemas)"
echo "  - README-MACHINE.md (machine-readable documentation)"
echo ""
echo -e "${YELLOW}Note:${NC} For human-readable documentation, see workspace/src/governance/"
echo ""

# Display manifest info
echo "Manifest Information:"
echo "--------------------"
python3 tools/python/governance_agent.py info | head -20