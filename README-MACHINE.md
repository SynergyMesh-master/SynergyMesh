---
# MachineNativeOps Governance Framework

**Machine-Readable, Executable Governance for AI Agents and Automation**

## Quick Start for AI Agents

### 1. Read the Manifest
```bash
# Primary entry point - all governance knowledge
governance-manifest.yaml
```

The manifest contains:
- All module locations and schemas
- AI operation interfaces
- Workflow definitions
- Tool references

### 2. Use the Governance Agent
```bash
# Validate a name
python tools/python/governance_agent.py validate <name> <type> <env>

# Generate a compliant name
python tools/python/governance_agent.py generate <type> <env> [team] [service] [version]

# Create a change request
python tools/python/governance_agent.py create-change <data>

# Get manifest info
python tools/python/governance_agent.py info

# List modules
python tools/python/governance_agent.py modules
```

### 3. Validate Requests Against Schemas
```python
from governance_agent import GovernanceAgent

agent = GovernanceAgent()
result = agent.validate_request(request_data, "validation")
```

## AI Interfaces

### Validation Endpoint
```
Request:  schemas/validation-request.schema.yaml
Response: schemas/validation-response.schema.yaml
Tool:     tools/python/governance_agent.py
Command:  validate <name> <type> <env>
```

### Generation Endpoint
```
Request:  schemas/generation-request.schema.yaml
Response: schemas/generation-response.schema.yaml
Tool:     tools/python/governance_agent.py
Command:  generate <type> <env> [team] [service] [version]
```

### Change Management Endpoint
```
Request:  schemas/change-request.schema.yaml
Response: schemas/change-response.schema.yaml
Tool:     tools/python/governance_agent.py
Command:  create-change <data>
```

### Exception Request Endpoint
```
Request:  schemas/exception-request.schema.yaml
Response: schemas/exception-response.schema.yaml
Tool:     tools/python/governance_agent.py
Command:  create-exception <data>
```

## Module Structure

| Module ID | Name | Location | Functions |
|-----------|------|----------|-----------|
| vision-strategy | Vision and Strategy | workspace/src/governance/00-vision-strategy | generate_adoption_roadmap, get_strategic_objectives |
| architecture | Governance Architecture | workspace/src/governance/01-architecture | get_organizational_structure, resolve_escalation |
| decision | Decision Management | workspace/src/governance/02-decision | get_stakeholder_map, process_exception_request |
| change | Change Management | workspace/src/governance/03-change | create_change_request, validate_rfc |
| policy | Governance Policies | workspace/src/governance/10-policy | validate_naming, check_compliance |
| culture | Culture and Capability | workspace/src/governance/12-culture-capability | get_training_plan, assign_roles |
| metrics | Metrics and Reporting | workspace/src/governance/13-metrics-reporting | calculate_kpi, generate_reports |
| audit | Audit and Compliance | workspace/src/governance/07-audit | run_audit, generate_compliance_report |
| improvement | Continuous Improvement | workspace/src/governance/14-improvement | execute_pdca_cycle, log_improvement |
| templates | Templates | workspace/src/governance/27-templates | generate_template, get_examples |
| tools | Automation Tools | workspace/src/governance/35-scripts | generate_name, validate_name |

## Workflows

### Pre-commit Validation
```
Trigger: git_pre_commit
Steps:
  1. Load governance-manifest.yaml
  2. Validate file with naming-validator.sh
  3. Check alerts from naming-alert-rules.yaml
On Failure: Block commit
```

### CI Pipeline Check
```
Trigger: ci_pipeline
Steps:
  1. Load governance-manifest.yaml
  2. Batch validate with naming-cli-tool.sh
  3. Generate report from naming-metrics-kpi.yaml
  4. Check compliance from naming-audit-checklist.yaml
On Failure: Fail build
```

## CI/CD Integration

### GitHub Actions
Template: `templates/ci/github-actions-naming-check.yml`

```yaml
# Add to .github/workflows/
- uses: ./templates/ci/github-actions-naming-check.yml
```

### Git Hooks
Pre-commit hook: `tools/git-hooks/pre-commit`

```bash
# Install
cp tools/git-hooks/pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit
```

## Monitoring

### Prometheus Rules
File: `templates/monitoring/prometheus-rules.yaml`

Alerts:
- naming_governance.compliance
- naming_governance.quality
- naming_governance.operations
- naming_governance.security

## Example Usage

### Validate a Kubernetes Deployment Name
```python
from governance_agent import GovernanceAgent

agent = GovernanceAgent()
result = agent.validate_name(
    name="prod-payment-deploy-v1.0.0",
    resource_type="k8s-deployment",
    environment="prod",
    team="platform",
    service="payment"
)
```

### Generate a Compliant Name
```python
result = agent.generate_name(
    resource_type="k8s-deployment",
    environment="prod",
    team="platform",
    service="payment",
    version="v1.0.0"
)
# Result: "prod-platform-payment-deploy-1.0.0"
```

### Create a Change Request
```python
change_data = {
    "type": "standard",
    "requester": "platform-team",
    "title": "Update naming standards",
    "risk_level": "medium",
    "description": "Update naming standards for new service types"
}
result = agent.create_change_request(change_data)
```

## API Version
```
governance.machinenativeops.io/v1
```

## Supported Data Formats
- YAML
- JSON

## Execution Environments
- Bash (Shell scripts)
- Python 3.11+
- Node.js (optional)

## Maintenance

### Adding New Policies
1. Create YAML policy in `workspace/src/governance/10-policy/`
2. Update `governance-manifest.yaml` to reference new policy
3. Add schema validation in `schemas/`

### Adding New Validation Rules
1. Update `workspace/src/governance/35-scripts/naming-patterns.yaml`
2. Add validation logic in `tools/python/governance_agent.py`

### Updating Workflows
1. Modify workflow definitions in `governance-manifest.yaml`
2. Update corresponding templates in `templates/`

## For AI Agents

The entire governance framework is designed for:
- ✅ Automated reading of all policies and rules
- ✅ Programmatic validation and generation
- ✅ Self-documenting through manifest
- ✅ No manual intervention required
- ✅ Full CI/CD integration

**Start here**: `governance-manifest.yaml`

---

**Version**: 2.0.0  
**Owner**: MachineNativeOps  
**License**: MIT  
**Created**: 2025-01-05