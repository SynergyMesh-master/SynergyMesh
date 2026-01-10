#!/bin/bash
# Script to generate MCP Level 2 artifacts for remaining modules
# Usage: ./generate-module-artifacts.sh <module-name>

set -e

MODULE_NAME=$1
if [ -z "$MODULE_NAME" ]; then
    echo "Usage: $0 <module-name>"
    exit 1
fi

BASE_DIR="/workspace/machine-native-ops/00-namespaces/namespaces-mcp"

echo "Generating artifacts for module: $MODULE_NAME"

# Create manifest
cat > "$BASE_DIR/manifests/${MODULE_NAME}.manifest.yaml" << EOF
# ${MODULE_NAME^} Module Manifest
version: "2.0.0"
semantic_role: manifest_storage
artifact_type: manifest
semantic_root: true

module:
  name: "$MODULE_NAME"
  version: "1.0.0"
  description: "${MODULE_NAME^} module"
  author: "MCP Core Team"
  license: "MIT"
  category: "$MODULE_NAME"
  semantic_classification: "${MODULE_NAME}_layer"

metadata:
  created_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  status: "active"
EOF

echo "✅ Created manifest for $MODULE_NAME"

# Create schema
cat > "$BASE_DIR/schemas/${MODULE_NAME}.schema.yaml" << EOF
# ${MODULE_NAME^} Module Schema
version: "2.0.0"
semantic_role: schema_definitions
artifact_type: schema
semantic_root: false

schema_definitions:
  ${MODULE_NAME^}Config:
    type: "object"
    description: "Configuration for ${MODULE_NAME} module"

metadata:
  created_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  status: "active"
EOF

echo "✅ Created schema for $MODULE_NAME"

# Create spec
cat > "$BASE_DIR/specs/${MODULE_NAME}.spec.yaml" << EOF
# ${MODULE_NAME^} Module Specification
version: "2.0.0"
semantic_role: specification_definitions
artifact_type: spec
semantic_root: false

interfaces:
  ${MODULE_NAME^}Interface:
    description: "Main interface for ${MODULE_NAME} module"
    methods: []

metadata:
  created_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  status: "active"
EOF

echo "✅ Created spec for $MODULE_NAME"

# Create policy
cat > "$BASE_DIR/policies/${MODULE_NAME}.policy.yaml" << EOF
# ${MODULE_NAME^} Module Policy
version: "2.0.0"
semantic_role: policy_definitions
artifact_type: policy
semantic_root: false

access_control:
  rbac:
    roles:
      - name: "${MODULE_NAME}.admin"
        permissions: ["${MODULE_NAME}:*"]

metadata:
  created_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  status: "active"
EOF

echo "✅ Created policy for $MODULE_NAME"

# Create bundle
cat > "$BASE_DIR/bundles/${MODULE_NAME}.bundle.yaml" << EOF
# ${MODULE_NAME^} Module Bundle
version: "2.0.0"
semantic_role: artifact_bundles
artifact_type: bundle
semantic_root: false

bundle:
  name: "$MODULE_NAME"
  version: "1.0.0"
  type: "module"

artifacts:
  manifest:
    path: "manifests/${MODULE_NAME}.manifest.yaml"
    type: "manifest"
    required: true

metadata:
  created_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  status: "active"
EOF

echo "✅ Created bundle for $MODULE_NAME"

# Create graph
cat > "$BASE_DIR/graphs/${MODULE_NAME}.graph.yaml" << EOF
# ${MODULE_NAME^} Module Dependency Graph
version: "2.0.0"
semantic_role: dependency_graphs
artifact_type: graph
semantic_root: false

graph:
  name: "${MODULE_NAME}-dependencies"
  version: "1.0.0"
  type: "dag"

nodes:
  - id: "$MODULE_NAME"
    type: "module"
    artifact: "${MODULE_NAME}.manifest.yaml"
    semantic_root: true

metadata:
  created_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  status: "active"
EOF

echo "✅ Created graph for $MODULE_NAME"

echo "✅ All artifacts generated for $MODULE_NAME"
EOF

chmod +x 00-namespaces/namespaces-mcp/scripts/generate-module-artifacts.sh