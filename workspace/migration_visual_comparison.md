# refactor_playbooks Migration Visual Comparison

## Current State vs. Target State

### Current Structure (Before Migration)

```
machine-native-ops/
└── workspace/
    ├── docs/
    │   └── refactor_playbooks/              ← CURRENT LOCATION
    │       ├── 01_deconstruction/           (10 files)
    │       ├── 02_integration/              (15 files)
    │       ├── 03_refactor/                 (50 files)
    │       ├── config/                      (10 files)
    │       ├── templates/                   (12 files)
    │       ├── _legacy_scratch/
    │       └── [19 root MD files]
    │       Total: 107 files, 1.9 MB
    │
    └── mcp/
        └── namespace-mcp/                   ← TARGET PARENT
            ├── NAMESPACE_INDEX.yaml         (59 files indexed)
            ├── INTEGRATION_INDEX.yaml
            ├── policies/
            ├── pipelines/
            ├── schemas/
            ├── servers/
            └── tools/
```

### Target Structure (After Migration - Option 1)

```
machine-native-ops/
└── workspace/
    └── mcp/
        └── namespace-mcp/                   ← CONSOLIDATED LOCATION
            ├── refactor_playbooks/          ← MIGRATED HERE
            │   ├── 01_deconstruction/
            │   ├── 02_integration/
            │   ├── 03_refactor/
            │   ├── config/
            │   ├── templates/
            │   ├── _legacy_scratch/
            │   └── [root files]
            │
            ├── NAMESPACE_INDEX.yaml         (UPDATED: +107 files)
            ├── INTEGRATION_INDEX.yaml       (UPDATED)
            ├── policies/
            ├── pipelines/
            ├── schemas/
            ├── servers/
            └── tools/
```

---

## Path Reference Changes

### Before Migration

```yaml
# refactor-engine-config.yaml
integrations:
  machinenativeops_config: "../../machinenativeops.yaml"
  module_map: "../../config/system-module-map.yaml"
  language_governance: "../../governance/language-governance-report.md"
  ci_workflows: "../../.github/workflows/"
```

### After Migration

```yaml
# refactor-engine-config.yaml
integrations:
  machinenativeops_config: "../../../machinenativeops.yaml"
  module_map: "../../../config/system-module-map.yaml"
  language_governance: "../../../governance/language-governance-report.md"
  ci_workflows: "../../../.github/workflows/"
```

**Change**: Add one more `../` to all relative paths

---

## Integration Points

### NAMESPACE_INDEX.yaml Update

```yaml
# BEFORE (Current)
statistics:
  totalScatteredFiles: 59
  categoryBreakdown:
    namingPolicies: 25
    namespaceConfigs: 18
    namingSchemas: 8
    namingTools: 8

# AFTER (Updated)
statistics:
  totalScatteredFiles: 166  # 59 + 107
  categoryBreakdown:
    namingPolicies: 25
    namespaceConfigs: 18
    namingSchemas: 8
    namingTools: 8
    refactorPlaybooks: 107  # NEW CATEGORY
```

### New Section in NAMESPACE_INDEX.yaml

```yaml
# Add to NAMESPACE_INDEX.yaml
refactorPlaybooks:
  canonicalLocation: workspace/mcp/namespace-mcp/refactor_playbooks/
  
  description: |
    Three-phase refactor system for legacy asset analysis, integration design,
    and executable refactor plans. Supports INSTANT execution architecture.
  
  components:
    - name: 01_deconstruction
      path: workspace/mcp/namespace-mcp/refactor_playbooks/01_deconstruction/
      purpose: "Legacy asset analysis and deconstruction"
      fileCount: 10
      
    - name: 02_integration
      path: workspace/mcp/namespace-mcp/refactor_playbooks/02_integration/
      purpose: "Integration design and architecture planning"
      fileCount: 15
      
    - name: 03_refactor
      path: workspace/mcp/namespace-mcp/refactor_playbooks/03_refactor/
      purpose: "Executable refactor plans with P0/P1/P2 priorities"
      fileCount: 50
      
    - name: config
      path: workspace/mcp/namespace-mcp/refactor_playbooks/config/
      purpose: "Refactor engine and governance configurations"
      fileCount: 10
      
    - name: templates
      path: workspace/mcp/namespace-mcp/refactor_playbooks/templates/
      purpose: "Document generation templates"
      fileCount: 12
  
  methodology: "三階段重構系統 (Three-Phase Refactor System)"
  executionMode: "INSTANT-Autonomous"
  status: "migrated"
  migratedFrom: "workspace/docs/refactor_playbooks/"
  migrationDate: "2026-01-08"
```

---

## File Movement Matrix

| Source Path | Target Path | File Count | Status |
|-------------|-------------|------------|--------|
| `docs/refactor_playbooks/01_deconstruction/` | `mcp/namespace-mcp/refactor_playbooks/01_deconstruction/` | 10 | Pending |
| `docs/refactor_playbooks/02_integration/` | `mcp/namespace-mcp/refactor_playbooks/02_integration/` | 15 | Pending |
| `docs/refactor_playbooks/03_refactor/` | `mcp/namespace-mcp/refactor_playbooks/03_refactor/` | 50 | Pending |
| `docs/refactor_playbooks/config/` | `mcp/namespace-mcp/refactor_playbooks/config/` | 10 | Pending |
| `docs/refactor_playbooks/templates/` | `mcp/namespace-mcp/refactor_playbooks/templates/` | 12 | Pending |
| `docs/refactor_playbooks/_legacy_scratch/` | `mcp/namespace-mcp/refactor_playbooks/_legacy_scratch/` | 1 | Pending |
| `docs/refactor_playbooks/*.md` | `mcp/namespace-mcp/refactor_playbooks/*.md` | 19 | Pending |

**Total Files to Move**: 107

---

## Redirect Documentation

### Create in Old Location

```markdown
# docs/refactor_playbooks/MOVED.md

# ⚠️ LOCATION CHANGED

This directory has been migrated to:

**New Location**: `workspace/mcp/namespace-mcp/refactor_playbooks/`

**Migration Date**: 2026-01-08

**Reason**: Consolidation under namespace-mcp as single source of truth for naming and refactoring governance.

## Quick Links

- [New Location](../mcp/namespace-mcp/refactor_playbooks/)
- [Migration Assessment](../mcp/namespace-mcp/refactor_playbooks/MIGRATION_ASSESSMENT.md)
- [NAMESPACE_INDEX.yaml](../mcp/namespace-mcp/NAMESPACE_INDEX.yaml)

## For Developers

Update your bookmarks and scripts to use the new path:

```bash
# Old path (deprecated)
cd workspace/docs/refactor_playbooks

# New path (current)
cd workspace/mcp/namespace-mcp/refactor_playbooks
```

## Rollback

If you need to access the old structure, see the git history:
```bash
git log --follow -- workspace/docs/refactor_playbooks/
```
```

---

## Dependency Update Checklist

### Internal References (within refactor_playbooks)

- [ ] Update all `../../` paths to `../../../`
- [ ] Update config/refactor-engine-config.yaml integrations
- [ ] Update config/integration-processor.yaml paths
- [ ] Update config/legacy-scratch-processor.yaml paths
- [ ] Update 03_refactor/index.yaml references
- [ ] Update all README.md relative links

### External References (from other parts of codebase)

- [ ] Search for `docs/refactor_playbooks` in entire codebase
- [ ] Update CI/CD workflow references
- [ ] Update governance script references
- [ ] Update documentation links
- [ ] Update automation tool configurations

### Documentation Updates

- [ ] Update main README.md
- [ ] Update ARCHITECTURE.md
- [ ] Update INTEGRATION_REPORT.md
- [ ] Update HLP_EXECUTOR_CORE_INDEX.md
- [ ] Add migration notice to old location

---

## Validation Checklist

### Pre-Migration Validation

- [ ] Backup current refactor_playbooks directory
- [ ] Verify all files are committed to git
- [ ] Document current git commit hash
- [ ] Test current functionality
- [ ] Identify all external dependencies

### Post-Migration Validation

- [ ] Verify all 107 files copied successfully
- [ ] Verify file permissions preserved
- [ ] Test all relative path references
- [ ] Validate YAML syntax in all config files
- [ ] Run governance validation scripts
- [ ] Test CI/CD pipelines
- [ ] Verify documentation links work
- [ ] Check for broken references

### Rollback Validation

- [ ] Document rollback procedure
- [ ] Test rollback in staging environment
- [ ] Verify rollback time < 30 minutes
- [ ] Document rollback decision criteria

---

## Timeline Visualization

```
Day 1: Preparation
├── Morning: Backup & Audit
│   ├── Create full backup
│   ├── Audit all path references
│   └── Identify dependencies
└── Afternoon: Setup
    ├── Create target directory
    ├── Prepare update scripts
    └── Test in staging

Day 2: Migration
├── Morning: Execute Migration
│   ├── Copy all files
│   ├── Update internal paths
│   └── Update configurations
└── Afternoon: Integration
    ├── Update NAMESPACE_INDEX.yaml
    ├── Update INTEGRATION_INDEX.yaml
    └── Add cross-references

Day 3: Validation
├── Morning: Testing
│   ├── Verify all paths
│   ├── Test CI/CD
│   └── Run validation scripts
└── Afternoon: Cleanup
    ├── Create redirect docs
    ├── Update team docs
    └── Announce completion

Day 4: Monitoring
└── Full Day: Monitor & Support
    ├── Monitor for issues
    ├── Support team questions
    └── Document lessons learned
```

---

## Risk Mitigation Matrix

| Risk | Probability | Impact | Mitigation | Rollback Time |
|------|-------------|--------|------------|---------------|
| Path breakage | HIGH | HIGH | Comprehensive audit + testing | 15 min |
| CI/CD failure | MEDIUM | HIGH | Staging test + gradual rollout | 30 min |
| Doc fragmentation | MEDIUM | MEDIUM | Redirect docs + clear communication | N/A |
| Team confusion | MEDIUM | LOW | Clear announcement + training | N/A |
| Data loss | LOW | CRITICAL | Git backup + verification | 5 min |

---

## Success Metrics

### Quantitative Metrics

- ✅ 100% of files migrated successfully
- ✅ 0 broken path references
- ✅ 0 CI/CD pipeline failures
- ✅ < 30 minutes rollback time (if needed)
- ✅ 100% governance compliance

### Qualitative Metrics

- ✅ Team can locate and use new structure
- ✅ Documentation is clear and accurate
- ✅ Integration with namespace-mcp is seamless
- ✅ Future maintenance is simplified
- ✅ Single source of truth achieved

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-08  
**Status**: Ready for Migration Execution