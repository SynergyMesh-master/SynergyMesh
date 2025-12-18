#!/bin/bash
# Migration script for canonical naming compliance
# Usage: DRY_RUN=true ./migrate-to-canonical-naming.sh

set -e

MACHINE_SPEC="governance/34-config/naming/canonical-naming-machine-spec.yaml"
MAPPING_FILE="governance/34-config/naming/namespace-mapping.yaml"
OUTPUT_DIR="reports/migration"
DRY_RUN="${DRY_RUN:-true}"

echo "🚀 Starting canonical naming migration..."
echo "📋 Dry run: $DRY_RUN"
echo ""

# Check prerequisites
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "❌ jq is not installed"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

# Generate migration plan
echo "📊 Analyzing current resources..."
kubectl get namespaces -o json | \
  jq -r '.items[] | select(.metadata.labels.environment != null) |
  {
    name: .metadata.name,
    labels: .metadata.labels,
    environment: .metadata.labels.environment,
    component: (.metadata.labels["app.kubernetes.io/name"] // "unknown"),
    canonical: (.metadata.labels.environment + "-" + (.metadata.labels["app.kubernetes.io/name"] // "unknown") + "-service")
  }' > "$OUTPUT_DIR/namespace-analysis.json"

echo "✅ Analysis complete: $OUTPUT_DIR/namespace-analysis.json"
echo ""

# Validate against canonical pattern
echo "🔍 Validating against canonical pattern..."
cat "$OUTPUT_DIR/namespace-analysis.json" | \
  jq -r 'select(.name != .canonical) |
  "\(.name) -> \(.canonical)"' > "$OUTPUT_DIR/migrations-needed.txt"

MIGRATION_COUNT=$(wc -l < "$OUTPUT_DIR/migrations-needed.txt" | tr -d ' ')

if [ "$MIGRATION_COUNT" -eq 0 ]; then
    echo "✅ All namespaces are already compliant!"
    echo ""
    cat "$OUTPUT_DIR/namespace-analysis.json" | jq -r '"\(.name) ✓"'
    exit 0
fi

echo "⚠️  Found $MIGRATION_COUNT namespace(s) needing migration"
echo ""
echo "📝 Migration plan:"
cat "$OUTPUT_DIR/migrations-needed.txt" | sed 's/^/  /'
echo ""

# Generate detailed migration report
echo "📋 Generating detailed migration report..."
cat > "$OUTPUT_DIR/migration-report.md" <<EOF
# Canonical Naming Migration Report

**Generated**: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Total Namespaces Analyzed**: $(jq -s 'length' "$OUTPUT_DIR/namespace-analysis.json")
**Namespaces Requiring Migration**: $MIGRATION_COUNT

## Migration Plan

EOF

while IFS= read -r line; do
    OLD_NAME=$(echo "$line" | cut -d' ' -f1)
    NEW_NAME=$(echo "$line" | cut -d' ' -f3)

    # Get labels for this namespace
    LABELS=$(kubectl get namespace "$OLD_NAME" -o json 2>/dev/null | jq -r '.metadata.labels | to_entries | map("\(.key)=\(.value)") | join(", ")' || echo "N/A")

    cat >> "$OUTPUT_DIR/migration-report.md" <<INNER_EOF
### \`$OLD_NAME\` → \`$NEW_NAME\`

- **Current Labels**: $LABELS
- **Risk Level**: Medium
- **Action Required**: Rename namespace and migrate resources

INNER_EOF
done < "$OUTPUT_DIR/migrations-needed.txt"

cat >> "$OUTPUT_DIR/migration-report.md" <<EOF

## Migration Steps

1. **Backup**: Export current namespace configuration
2. **Create**: Create new namespace with canonical name
3. **Migrate**: Move all resources to new namespace
4. **Verify**: Ensure all resources are functioning
5. **Cleanup**: Delete old namespace (manual step)

## Notes

- This is a $DRY_RUN migration plan
- Set \`DRY_RUN=false\` to execute migrations
- Always backup before migrating

EOF

echo "✅ Migration report saved: $OUTPUT_DIR/migration-report.md"
echo ""

if [ "$DRY_RUN" = "false" ]; then
    echo "🔧 Applying migrations..."
    echo ""

    MIGRATED=0
    FAILED=0

    while IFS= read -r line; do
        OLD_NAME=$(echo "$line" | cut -d' ' -f1)
        NEW_NAME=$(echo "$line" | cut -d' ' -f3)

        echo "📦 Migrating: $OLD_NAME → $NEW_NAME"

        # Export current namespace
        echo "  1/5 Exporting namespace configuration..."
        kubectl get namespace "$OLD_NAME" -o yaml > "$OUTPUT_DIR/${OLD_NAME}-backup.yaml" 2>/dev/null || {
            echo "  ❌ Failed to export namespace $OLD_NAME"
            FAILED=$((FAILED + 1))
            continue
        }

        # Create new namespace with canonical name
        echo "  2/5 Creating new namespace: $NEW_NAME"
        kubectl get namespace "$OLD_NAME" -o yaml | \
          sed "s/name: $OLD_NAME/name: $NEW_NAME/" | \
          kubectl create -f - 2>/dev/null || {
            echo "  ⚠️  Namespace $NEW_NAME may already exist"
        }

        # Migrate resources
        echo "  3/5 Migrating resources..."
        RESOURCE_TYPES="deployment,statefulset,daemonset,service,configmap,secret,serviceaccount"
        kubectl get $RESOURCE_TYPES -n "$OLD_NAME" -o yaml 2>/dev/null | \
          sed "s/namespace: $OLD_NAME/namespace: $NEW_NAME/" | \
          kubectl create -f - 2>/dev/null || {
            echo "  ⚠️  Some resources may have failed to migrate"
        }

        # Verify migration
        echo "  4/5 Verifying migration..."
        OLD_COUNT=$(kubectl get all -n "$OLD_NAME" 2>/dev/null | wc -l || echo 0)
        NEW_COUNT=$(kubectl get all -n "$NEW_NAME" 2>/dev/null | wc -l || echo 0)

        if [ "$NEW_COUNT" -ge "$OLD_COUNT" ]; then
            echo "  ✅ Migration verified ($NEW_COUNT resources in new namespace)"
            MIGRATED=$((MIGRATED + 1))
        else
            echo "  ⚠️  Verification inconclusive (old: $OLD_COUNT, new: $NEW_COUNT)"
        }

        echo "  5/5 Complete! Review and manually delete old namespace if successful."
        echo ""

    done < "$OUTPUT_DIR/migrations-needed.txt"

    echo ""
    echo "🎉 Migration complete!"
    echo "   ✅ Migrated: $MIGRATED"
    echo "   ❌ Failed: $FAILED"
    echo ""
    echo "⚠️  IMPORTANT: Please verify the new namespaces and delete the old ones manually:"
    while IFS= read -r line; do
        OLD_NAME=$(echo "$line" | cut -d' ' -f1)
        echo "   kubectl delete namespace $OLD_NAME"
    done < "$OUTPUT_DIR/migrations-needed.txt"
else
    echo "✨ Dry run complete. Review the migration plan above."
    echo ""
    echo "📖 See detailed report: $OUTPUT_DIR/migration-report.md"
    echo ""
    echo "To execute migrations, run:"
    echo "   DRY_RUN=false $0"
fi
