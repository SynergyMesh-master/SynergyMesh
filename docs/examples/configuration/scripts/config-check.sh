#!/bin/bash
# config-check.sh - Configuration validation script

set -e

PROJECT_ROOT=$(pwd)
REPORTS_DIR="$PROJECT_ROOT/reports"
mkdir -p "$REPORTS_DIR"

echo "⚙️  Starting configuration validation..."

EXIT_CODE=0

# 檢查必需的配置文件
REQUIRED_CONFIGS=(
    "package.json"
    ".eslintrc.js"
    ".prettierrc"
    "tsconfig.json"
    "sonar-project.properties"
)

echo "📋 Checking required configuration files..."
for config in "${REQUIRED_CONFIGS[@]}"; do
    if [ -f "$config" ]; then
        echo "  ✅ $config found"
    else
        echo "  ⚠️  $config missing (optional)"
    fi
done

# 驗證JSON配置文件
echo ""
echo "🔍 Validating JSON configurations..."
while read -r json_file; do
    if jq empty "$json_file" 2>/dev/null; then
        echo "  ✅ $json_file is valid"
    else
        echo "  ❌ $json_file is invalid!"
        EXIT_CODE=1
    fi
done < <(find . -name "*.json" -not -path "*/node_modules/*" -not -path "*/.git/*")

# 驗證YAML配置文件
echo ""
echo "🔍 Validating YAML configurations..."
while read -r yaml_file; do
    if python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null; then
        echo "  ✅ $yaml_file is valid"
    else
        echo "  ❌ $yaml_file is invalid!"
        EXIT_CODE=1
    fi
done < <(find . -name "*.yml" -o -name "*.yaml" | grep -v node_modules | grep -v .git)

# 驗證TypeScript配置
if [ -f "tsconfig.json" ]; then
    echo ""
    echo "📘 Validating TypeScript configuration..."
    if npx tsc --noEmit --project tsconfig.json; then
        echo "  ✅ TypeScript configuration is valid"
    else
        echo "  ❌ TypeScript configuration has errors!"
        EXIT_CODE=1
    fi
fi

# 生成配置檢查報告
cat > "$REPORTS_DIR/config-check-summary.json" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "${EXIT_CODE}",
  "checks": {
    "required_files": "checked",
    "json_validation": "checked",
    "yaml_validation": "checked",
    "typescript_config": "checked"
  }
}
EOF

if [ ${EXIT_CODE} -eq 0 ]; then
    echo ""
    echo "✅ All configuration checks passed!"
else
    echo ""
    echo "❌ Configuration validation failed!"
fi

exit ${EXIT_CODE}
