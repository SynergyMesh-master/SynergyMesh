# 🔀 Namespace/Naming Files Redirect Notice

> **All namespace and naming convention files have been consolidated into `namespace-mcp`**

## Single Source of Truth

As of v3.0.0, **`namespace-mcp`** is the single source of truth for ALL:
- Naming policies
- Namespace configurations  
- Naming schemas
- Naming tools
- Naming documentation

## Key Files

| Purpose | Location |
|---------|----------|
| **Central Index** | `workspace/mcp/namespace-mcp/NAMESPACE_INDEX.yaml` |
| **Unified Governance Spec** | `workspace/mcp/namespace-mcp/policies/unified-naming-governance-spec.yaml` |
| **MCP Integration** | `workspace/mcp/namespace-mcp/INTEGRATION_INDEX.yaml` |

## Original Locations (Now Redirected)

The following scattered locations are now consolidated:

### Naming Policies (25 files)
- `workspace/src/governance/10-policy/naming-*.yaml` → `namespace-mcp/policies/`
- `workspace/src/governance/00-vision-strategy/naming-*.yaml` → `namespace-mcp/policies/`
- `workspace/governance/policies/naming/*.yaml` → `namespace-mcp/policies/`

### Namespace Configs (18 files)
- `workspace/**/namespace*.yaml` → `namespace-mcp/namespaces/`
- `workspace/mno-namespace.yaml` → `namespace-mcp/namespaces/`

### Naming Schemas (8 files)
- `workspace/src/shared/types/naming-*.schema.yaml` → `namespace-mcp/schemas/`
- `workspace/src/schemas/naming-*.schema.yaml` → `namespace-mcp/schemas/`

### Naming Tools (8 files)
- `workspace/tools/namespace-*.py` → `namespace-mcp/tools/`
- `workspace/scripts/*/namespace-*.py` → `namespace-mcp/tools/`

## Methodology

This consolidation follows the **validation-mcp 硫酸溶解法** methodology:
1. **解構 (Deconstruction)** - Index all scattered naming files
2. **集成 (Integration)** - Consolidate into unified structure
3. **重構 (Refactoring)** - Align with namespace-mcp as single source

## Questions?

See the main documentation:
- [`NAMESPACE_INDEX.yaml`](./NAMESPACE_INDEX.yaml) - Complete file index
- [`README.md`](./README.md) - Architecture overview
