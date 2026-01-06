# Workspace Validation

## Overview

This directory contains validation scripts to ensure workspace files and configurations are correctly set up.

## Scripts

### validate-workspace.js

Validates npm workspace configuration by checking:

- ✅ Root package.json workspace paths exist
- ✅ Each workspace has a valid package.json
- ✅ Workspace package names are unique
- ✅ Workspace dependencies are valid
- ✅ No circular dependencies between workspaces

**Usage:**

```bash
# Run via npm script (recommended)
npm run validate:workspace

# Or run directly with node
node scripts/validate-workspace.js

# Or make executable and run directly (requires chmod +x first)
chmod +x scripts/validate-workspace.js
./scripts/validate-workspace.js
```

**Exit Codes:**

- `0` - All validations passed
- `1` - Validation errors found

**Output:**

The script provides colored output showing:
- ✅ Green checkmarks for successful validations
- ❌ Red X marks for errors
- ⚠️ Yellow warnings for non-critical issues

## Workspace Structure

The repository uses npm workspaces to manage multiple packages:

```
machine-native-ops/
├── package.json                     # Root workspace configuration
└── workspace/
    ├── package.json                 # Workspace-specific configuration
    └── src/
        ├── mcp-servers/            # MCP server implementations
        ├── core/
        │   ├── advisory-database/  # Security advisory database
        │   └── contract_service/
        │       └── contracts-L1/
        │           └── contracts/  # Contract service
        └── archive/
            └── unmanned-engineer-ceo/
                └── 80-skeleton-configs/  # Skeleton configurations
```

## Common Issues

### Invalid Workspace Paths

**Problem:** Workspace path in package.json doesn't exist

**Solution:** Update the workspace path or create the missing directory with a valid package.json

### Duplicate Package Names

**Problem:** Two workspaces have the same package name

**Solution:** Rename one of the packages to ensure uniqueness

### Missing package.json Fields

**Problem:** A workspace package.json is missing required fields like "name" or "version"

**Solution:** Add the missing fields to the package.json

## CI Integration

The workspace validation script can be integrated into CI pipelines:

```yaml
- name: Validate Workspaces
  run: npm run validate:workspace
```

## Maintenance

When adding a new workspace:

1. Create the workspace directory
2. Add a valid package.json with at least `name` and `version` fields
3. Add the workspace path to the root package.json `workspaces` array
4. Run `npm run validate:workspace` to verify the configuration
5. Run `npm install` to update workspace dependencies
