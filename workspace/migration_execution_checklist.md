# refactor_playbooks Migration Execution Checklist

**Migration Type**: Full Integration (Option 1)  
**Estimated Duration**: 4 days  
**Risk Level**: Medium  
**Rollback Time**: < 30 minutes

---

## Pre-Migration Phase (Day 0)

### Stakeholder Approval
- [ ] Review assessment report with stakeholders
- [ ] Obtain approval for migration strategy
- [ ] Schedule migration window
- [ ] Notify team of upcoming changes
- [ ] Set up communication channels for migration updates

### Environment Preparation
- [ ] Verify git repository is clean
- [ ] Create feature branch: `migration/refactor-playbooks-to-namespace-mcp`
- [ ] Document current git commit hash: `________________`
- [ ] Set up staging environment for testing
- [ ] Prepare rollback scripts

---

## Phase 1: Preparation (Day 1 - Morning)

### Backup & Documentation
- [ ] Create full backup of `workspace/docs/refactor_playbooks/`
  ```bash
  tar -czf refactor_playbooks_backup_$(date +%Y%m%d).tar.gz \
    machine-native-ops/workspace/docs/refactor_playbooks/
  ```
- [ ] Verify backup integrity
- [ ] Document backup location: `________________`
- [ ] Create backup of `workspace/mcp/namespace-mcp/`
- [ ] Commit all current changes to git

### Dependency Audit
- [ ] Search entire codebase for references to `docs/refactor_playbooks`
  ```bash
  grep -r "docs/refactor_playbooks" machine-native-ops/ \
    --exclude-dir=.git --exclude-dir=node_modules
  ```
- [ ] Document all found references in spreadsheet
- [ ] Identify CI/CD workflow dependencies
- [ ] Identify automation script dependencies
- [ ] Identify documentation link dependencies
- [ ] Create dependency update plan

### Path Reference Analysis
- [ ] List all files with relative path references
  ```bash
  find machine-native-ops/workspace/docs/refactor_playbooks/ \
    -type f \( -name "*.yaml" -o -name "*.yml" -o -name "*.md" \) \
    -exec grep -l "\.\./\.\." {} \;
  ```
- [ ] Document current path patterns
- [ ] Calculate new path patterns (add one `../`)
- [ ] Prepare path update script

---

## Phase 1: Preparation (Day 1 - Afternoon)

### Target Directory Setup
- [ ] Create target directory structure
  ```bash
  mkdir -p machine-native-ops/workspace/mcp/namespace-mcp/refactor_playbooks
  ```
- [ ] Verify directory permissions
- [ ] Test write access
- [ ] Create `.gitkeep` files if needed

### Migration Script Preparation
- [ ] Create file copy script
- [ ] Create path update script
- [ ] Create validation script
- [ ] Test scripts in staging environment
- [ ] Document script usage

### Staging Environment Test
- [ ] Copy files to staging namespace-mcp
- [ ] Update paths in staging
- [ ] Run validation in staging
- [ ] Test CI/CD in staging
- [ ] Document any issues found
- [ ] Adjust scripts based on findings

---

## Phase 2: Migration Execution (Day 2 - Morning)

### File Migration
- [ ] Execute file copy to target location
  ```bash
  cp -r machine-native-ops/workspace/docs/refactor_playbooks/* \
    machine-native-ops/workspace/mcp/namespace-mcp/refactor_playbooks/
  ```
- [ ] Verify all 107 files copied
  ```bash
  find machine-native-ops/workspace/mcp/namespace-mcp/refactor_playbooks/ \
    -type f | wc -l
  # Expected: 107
  ```
- [ ] Verify file sizes match
- [ ] Verify file permissions preserved
- [ ] Check for any copy errors

### Internal Path Updates
- [ ] Update `config/refactor-engine-config.yaml`
  - [ ] Change `../../` to `../../../` in integrations section
  - [ ] Verify YAML syntax
- [ ] Update `config/integration-processor.yaml`
  - [ ] Update all relative paths
  - [ ] Verify YAML syntax
- [ ] Update `config/legacy-scratch-processor.yaml`
  - [ ] Update all relative paths
  - [ ] Verify YAML syntax
- [ ] Update `03_refactor/index.yaml`
  - [ ] Update file paths if needed
  - [ ] Verify YAML syntax
- [ ] Update all README.md files
  - [ ] Update relative links
  - [ ] Verify markdown rendering

### Configuration Updates
- [ ] Update main README.md
  - [ ] Update location references
  - [ ] Add migration notice
- [ ] Update ARCHITECTURE.md
  - [ ] Update path references
  - [ ] Update diagrams if needed
- [ ] Update INTEGRATION_REPORT.md
  - [ ] Update integration paths
- [ ] Update HLP_EXECUTOR_CORE_INDEX.md
  - [ ] Update index paths

---

## Phase 2: Integration (Day 2 - Afternoon)

### NAMESPACE_INDEX.yaml Update
- [ ] Open `workspace/mcp/namespace-mcp/NAMESPACE_INDEX.yaml`
- [ ] Update statistics section
  ```yaml
  statistics:
    totalScatteredFiles: 166  # Was 59, now 59 + 107
    categoryBreakdown:
      namingPolicies: 25
      namespaceConfigs: 18
      namingSchemas: 8
      namingTools: 8
      refactorPlaybooks: 107  # NEW
  ```
- [ ] Add refactorPlaybooks section (see migration_visual_comparison.md)
- [ ] Verify YAML syntax
- [ ] Commit changes

### INTEGRATION_INDEX.yaml Update
- [ ] Open `workspace/mcp/namespace-mcp/INTEGRATION_INDEX.yaml`
- [ ] Add refactor_playbooks integration section
  ```yaml
  refactor_playbooks:
    location: workspace/mcp/namespace-mcp/refactor_playbooks/
    type: refactor-system
    status: integrated
    integration_date: "2026-01-08"
    methodology: three-phase-refactor
    execution_mode: INSTANT-Autonomous
  ```
- [ ] Verify YAML syntax
- [ ] Commit changes

### Cross-Reference Documentation
- [ ] Update namespace-mcp README.md
  - [ ] Add refactor_playbooks section
  - [ ] Add link to refactor_playbooks README
- [ ] Update refactor_playbooks README.md
  - [ ] Add namespace-mcp context
  - [ ] Add integration notes
- [ ] Create MIGRATION_NOTES.md in refactor_playbooks
  - [ ] Document migration date
  - [ ] Document old location
  - [ ] Document reason for migration

---

## Phase 3: External Updates (Day 3 - Morning)

### CI/CD Workflow Updates
- [ ] Identify all workflows referencing refactor_playbooks
- [ ] Update workflow paths
  ```yaml
  # Before
  - uses: docs/refactor_playbooks/config/
  # After
  - uses: mcp/namespace-mcp/refactor_playbooks/config/
  ```
- [ ] Test workflows in staging
- [ ] Commit workflow changes

### Automation Script Updates
- [ ] Update governance validation scripts
- [ ] Update refactor engine scripts
- [ ] Update documentation generation scripts
- [ ] Test all updated scripts
- [ ] Commit script changes

### Documentation Link Updates
- [ ] Search for all documentation links
  ```bash
  grep -r "docs/refactor_playbooks" machine-native-ops/docs/ \
    --include="*.md"
  ```
- [ ] Update all found links
- [ ] Verify links work
- [ ] Commit documentation changes

---

## Phase 3: Validation (Day 3 - Afternoon)

### File Integrity Validation
- [ ] Verify file count matches
  ```bash
  # Source
  find machine-native-ops/workspace/docs/refactor_playbooks/ -type f | wc -l
  # Target
  find machine-native-ops/workspace/mcp/namespace-mcp/refactor_playbooks/ -type f | wc -l
  # Should match: 107
  ```
- [ ] Verify total size matches
  ```bash
  du -sh machine-native-ops/workspace/docs/refactor_playbooks/
  du -sh machine-native-ops/workspace/mcp/namespace-mcp/refactor_playbooks/
  # Should both be ~1.9M
  ```
- [ ] Run file checksum comparison
- [ ] Verify no files were corrupted

### Path Reference Validation
- [ ] Test all relative paths in config files
- [ ] Verify YAML files parse correctly
  ```bash
  yamllint machine-native-ops/workspace/mcp/namespace-mcp/refactor_playbooks/config/*.yaml
  ```
- [ ] Verify markdown links work
- [ ] Check for broken references
  ```bash
  # Look for old path references
  grep -r "docs/refactor_playbooks" \
    machine-native-ops/workspace/mcp/namespace-mcp/refactor_playbooks/
  # Should return 0 results
  ```

### Governance Compliance Validation
- [ ] Run namespace governance validation
- [ ] Verify naming conventions compliance
- [ ] Check directory structure compliance
- [ ] Validate YAML schema compliance
- [ ] Review validation reports

### CI/CD Pipeline Testing
- [ ] Trigger test CI/CD run
- [ ] Verify all stages pass
- [ ] Check for any warnings
- [ ] Verify deployment works
- [ ] Monitor for errors

### Integration Testing
- [ ] Test refactor engine functionality
- [ ] Test playbook generation
- [ ] Test three-phase workflow
- [ ] Verify all tools work
- [ ] Document any issues

---

## Phase 4: Cleanup (Day 3 - Evening)

### Redirect Documentation
- [ ] Create `MOVED.md` in old location
  ```bash
  cat > machine-native-ops/workspace/docs/refactor_playbooks/MOVED.md << 'EOF'
  # ⚠️ LOCATION CHANGED
  
  This directory has been migrated to:
  **New Location**: `workspace/mcp/namespace-mcp/refactor_playbooks/`
  
  See: [Migration Assessment](../../mcp/namespace-mcp/refactor_playbooks/MIGRATION_ASSESSMENT.md)
  EOF
  ```
- [ ] Add redirect in old README.md
- [ ] Create symlink (optional)
  ```bash
  ln -s ../../mcp/namespace-mcp/refactor_playbooks \
    machine-native-ops/workspace/docs/refactor_playbooks_new
  ```

### Archive Old Location (Optional)
- [ ] Discuss with team: archive or keep?
- [ ] If archiving:
  - [ ] Move to `_archived/refactor_playbooks/`
  - [ ] Update .gitignore if needed
  - [ ] Document archive location
- [ ] If keeping:
  - [ ] Add prominent MOVED.md
  - [ ] Keep for 30 days before archiving

### Team Documentation
- [ ] Update team wiki/documentation
- [ ] Update onboarding documentation
- [ ] Update development guides
- [ ] Create migration announcement
- [ ] Schedule team meeting to discuss changes

---

## Phase 5: Monitoring (Day 4)

### Post-Migration Monitoring
- [ ] Monitor CI/CD pipelines for 24 hours
- [ ] Watch for error reports
- [ ] Monitor team feedback
- [ ] Track any issues in issue tracker
- [ ] Respond to questions promptly

### Issue Resolution
- [ ] Document any issues found
- [ ] Prioritize issues (P0/P1/P2)
- [ ] Fix critical issues immediately
- [ ] Schedule fixes for non-critical issues
- [ ] Update migration documentation with lessons learned

### Success Validation
- [ ] Verify all success criteria met
- [ ] Collect team feedback
- [ ] Measure migration metrics
- [ ] Document actual vs. estimated effort
- [ ] Create lessons learned document

---

## Rollback Procedure (If Needed)

### Rollback Decision Criteria
- [ ] Critical CI/CD failure
- [ ] Data loss or corruption
- [ ] Widespread team disruption
- [ ] Unforeseen technical issues
- [ ] Stakeholder decision

### Rollback Steps (< 30 minutes)
1. [ ] Announce rollback decision
2. [ ] Restore from backup
   ```bash
   tar -xzf refactor_playbooks_backup_YYYYMMDD.tar.gz
   ```
3. [ ] Revert git commits
   ```bash
   git revert <migration-commit-hash>
   ```
4. [ ] Restore old CI/CD workflows
5. [ ] Restore old automation scripts
6. [ ] Verify old structure works
7. [ ] Notify team of rollback completion
8. [ ] Schedule post-mortem meeting

---

## Post-Migration Tasks

### Documentation Finalization
- [ ] Finalize migration assessment report
- [ ] Create migration completion report
- [ ] Update project documentation
- [ ] Archive migration artifacts
- [ ] Share lessons learned

### Process Improvement
- [ ] Review migration process
- [ ] Identify improvement opportunities
- [ ] Update migration playbook
- [ ] Document best practices
- [ ] Share knowledge with team

### Celebration
- [ ] Announce successful migration
- [ ] Thank team members
- [ ] Document success metrics
- [ ] Share migration story
- [ ] Plan next consolidation effort

---

## Sign-Off

### Migration Team Sign-Off
- [ ] Migration Lead: _________________ Date: _______
- [ ] Technical Lead: _________________ Date: _______
- [ ] QA Lead: _______________________ Date: _______
- [ ] DevOps Lead: ___________________ Date: _______

### Stakeholder Sign-Off
- [ ] Product Owner: _________________ Date: _______
- [ ] Engineering Manager: ___________ Date: _______
- [ ] Architecture Lead: _____________ Date: _______

---

## Appendix

### Key Contacts
- Migration Lead: ________________
- Technical Support: ________________
- Emergency Contact: ________________

### Important Links
- Assessment Report: `refactor_playbooks_assessment.md`
- Visual Comparison: `migration_visual_comparison.md`
- Backup Location: ________________
- Issue Tracker: ________________

### Migration Metrics
- Start Date: ________________
- End Date: ________________
- Actual Duration: ________ days
- Files Migrated: 107
- Issues Found: ________
- Rollbacks: ________

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-08  
**Status**: Ready for Execution  
**Next Review**: After Migration Completion