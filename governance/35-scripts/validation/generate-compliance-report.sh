#!/bin/bash
# Generate canonical naming compliance report

OUTPUT_FILE="${OUTPUT_FILE:-reports/canonical-naming-compliance-report.html}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

mkdir -p "$(dirname "$OUTPUT_FILE")"

echo "📊 Generating canonical naming compliance report..."

# Check prerequisites
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "❌ jq is not installed"
    exit 1
fi

cat > "$OUTPUT_FILE" <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Canonical Naming Compliance Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        .timestamp {
            color: #666;
            font-size: 14px;
            margin-bottom: 30px;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .summary-card {
            padding: 20px;
            border-radius: 6px;
            text-align: center;
        }
        .summary-card.compliant {
            background: #d4edda;
            border: 1px solid #c3e6cb;
        }
        .summary-card.non-compliant {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
        }
        .summary-card.warning {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
        }
        .summary-card h2 {
            margin: 0;
            font-size: 36px;
            font-weight: bold;
        }
        .summary-card p {
            margin: 5px 0 0 0;
            color: #666;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #4CAF50;
            color: white;
            font-weight: 600;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .status-icon {
            font-size: 18px;
        }
        .compliant { color: #28a745; }
        .non-compliant { color: #dc3545; }
        .warning { color: #ffc107; }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge.compliant {
            background: #28a745;
            color: white;
        }
        .badge.non-compliant {
            background: #dc3545;
            color: white;
        }
        .badge.warning {
            background: #ffc107;
            color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Canonical Naming Compliance Report</h1>
        <p class="timestamp">Generated: $TIMESTAMP</p>

        <div class="summary">
EOF

# Get namespace statistics
TOTAL_NS=$(kubectl get namespaces -o json | jq '.items | length')
COMPLIANT_NS=0
NON_COMPLIANT_NS=0
WARNING_NS=0

# Pattern for validation
PATTERN="^(?!.*--)(team|tenant|dev|test|staging|prod|learn|sandbox)-[a-z0-9]+(?:-[a-z0-9]+)*$"

# Analyze namespaces
kubectl get namespaces -o json | jq -r '.items[] | @json' | while read -r ns; do
    NAME=$(echo "$ns" | jq -r '.metadata.name')
    LABELS=$(echo "$ns" | jq -r '.metadata.labels')
    URN=$(echo "$ns" | jq -r '.metadata.annotations["axiom.io/canonical-urn"] // "missing"')

    # Skip system namespaces
    if [[ "$NAME" =~ ^kube- ]] || [ "$NAME" = "default" ]; then
        continue
    fi

    # Check pattern match
    if echo "$NAME" | grep -Eq "$PATTERN"; then
        PATTERN_OK=true
    else
        PATTERN_OK=false
        NON_COMPLIANT_NS=$((NON_COMPLIANT_NS + 1))
        continue
    fi

    # Check required labels
    if echo "$LABELS" | jq -e '.environment and .tenant and .["app.kubernetes.io/managed-by"]' > /dev/null 2>&1; then
        LABELS_OK=true
    else
        LABELS_OK=false
        NON_COMPLIANT_NS=$((NON_COMPLIANT_NS + 1))
        continue
    fi

    # Check URN
    if [ "$URN" != "missing" ]; then
        URN_OK=true
        COMPLIANT_NS=$((COMPLIANT_NS + 1))
    else
        URN_OK=false
        WARNING_NS=$((WARNING_NS + 1))
    fi
done

cat >> "$OUTPUT_FILE" <<INNER_EOF
            <div class="summary-card compliant">
                <h2>$COMPLIANT_NS</h2>
                <p>Compliant</p>
            </div>
            <div class="summary-card non-compliant">
                <h2>$NON_COMPLIANT_NS</h2>
                <p>Non-Compliant</p>
            </div>
            <div class="summary-card warning">
                <h2>$WARNING_NS</h2>
                <p>Warnings</p>
            </div>
            <div class="summary-card">
                <h2>$TOTAL_NS</h2>
                <p>Total Namespaces</p>
            </div>
        </div>

        <h2>Namespace Compliance Details</h2>
        <table>
            <tr>
                <th>Namespace</th>
                <th>Pattern Match</th>
                <th>Required Labels</th>
                <th>URN Annotation</th>
                <th>Status</th>
            </tr>
INNER_EOF

# Generate detailed table
kubectl get namespaces -o json | jq -r '.items[] | @json' | while read -r ns; do
    NAME=$(echo "$ns" | jq -r '.metadata.name')
    LABELS=$(echo "$ns" | jq -r '.metadata.labels')
    URN=$(echo "$ns" | jq -r '.metadata.annotations["axiom.io/canonical-urn"] // "missing"')

    # Skip system namespaces
    if [[ "$NAME" =~ ^kube- ]] || [ "$NAME" = "default" ]; then
        continue
    fi

    # Check pattern
    if echo "$NAME" | grep -Eq "$PATTERN"; then
        PATTERN='<span class="status-icon compliant">✅</span>'
        PATTERN_CLASS="compliant"
    else
        PATTERN='<span class="status-icon non-compliant">❌</span>'
        PATTERN_CLASS="non-compliant"
    fi

    # Check required labels
    if echo "$LABELS" | jq -e '.environment and .tenant and .["app.kubernetes.io/managed-by"]' > /dev/null 2>&1; then
        LABELS_CHECK='<span class="status-icon compliant">✅</span>'
        LABELS_CLASS="compliant"
    else
        LABELS_CHECK='<span class="status-icon non-compliant">❌</span>'
        LABELS_CLASS="non-compliant"
    fi

    # Check URN
    if [ "$URN" != "missing" ]; then
        URN_CHECK='<span class="status-icon compliant">✅</span>'
        URN_CLASS="compliant"
    else
        URN_CHECK='<span class="status-icon warning">⚠️</span>'
        URN_CLASS="warning"
    fi

    # Overall status
    if [ "$PATTERN_CLASS" = "compliant" ] && [ "$LABELS_CLASS" = "compliant" ]; then
        STATUS='<span class="badge compliant">Compliant</span>'
    else
        STATUS='<span class="badge non-compliant">Non-Compliant</span>'
    fi

    cat >> "$OUTPUT_FILE" <<INNER2_EOF
            <tr>
                <td><code>$NAME</code></td>
                <td>$PATTERN</td>
                <td>$LABELS_CHECK</td>
                <td>$URN_CHECK</td>
                <td>$STATUS</td>
            </tr>
INNER2_EOF
done

cat >> "$OUTPUT_FILE" <<EOF
        </table>

        <h2>Governance Documentation</h2>
        <ul>
            <li><a href="../governance/29-docs/canonical-naming-governance-report.md">Canonical Naming Governance Report</a></li>
            <li><a href="../governance/34-config/naming/canonical-naming-machine-spec.yaml">Machine Specification</a></li>
            <li><a href="../governance/29-docs/05-implementation-templates-and-enforcement.md">Implementation Templates</a></li>
        </ul>
    </div>
</body>
</html>
EOF

echo "✅ Compliance report generated: $OUTPUT_FILE"
