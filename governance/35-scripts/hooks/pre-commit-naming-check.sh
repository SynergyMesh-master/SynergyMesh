#!/bin/bash
# Pre-commit hook for canonical naming validation
# Install: ln -s ../../governance/35-scripts/hooks/pre-commit-naming-check.sh .git/hooks/pre-commit

set -e

echo "🔍 Validating canonical naming compliance..."

# Check if conftest is installed
if ! command -v conftest &> /dev/null; then
    echo "❌ conftest is not installed. Please install it first:"
    echo "   https://www.conftest.dev/install/"
    echo ""
    echo "   On macOS: brew install conftest"
    echo "   On Linux: wget https://github.com/open-policy-agent/conftest/releases/download/v0.49.1/conftest_0.49.1_Linux_x86_64.tar.gz && tar xzf conftest_*.tar.gz && sudo mv conftest /usr/local/bin/"
    exit 1
fi

# Find all YAML files staged for commit
YAML_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(yaml|yml)$' || true)

if [ -z "$YAML_FILES" ]; then
    echo "✅ No YAML files to validate"
    exit 0
fi

echo "📝 Found $(echo "$YAML_FILES" | wc -l) YAML file(s) to validate"

# Validate with conftest
POLICY_DIR="governance/23-policies/conftest"
VIOLATIONS=0

for file in $YAML_FILES; do
    if [ ! -f "$file" ]; then
        continue
    fi

    echo "  Checking: $file"

    if ! conftest test "$file" \
        --policy "$POLICY_DIR/naming_policy.rego" \
        --policy "$POLICY_DIR/urn_validation.rego" \
        --namespace main \
        --fail-on-warn=false; then
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done

echo ""

if [ $VIOLATIONS -eq 0 ]; then
    echo "✅ All files pass canonical naming validation"
    exit 0
else
    echo "❌ Found $VIOLATIONS file(s) with naming violations"
    echo ""
    echo "📖 Please review the violations above and update your files according to:"
    echo "   governance/29-docs/canonical-naming-governance-report.md"
    echo ""
    echo "💡 To skip this check (not recommended): git commit --no-verify"
    exit 1
fi
