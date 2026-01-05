# Schema-Driven Governance Architecture Mapping

## Executive Summary

This document maps the 5 core JSON schemas to the governance modules, establishing a schema-first architecture where all naming governance operations are validated, generated, and managed through standardized schema contracts.

---

## Schema Overview

### 1. Validation Request Schema
**Purpose**: Validate resource names against governance policies

**Core Fields**:
- `resource_name` (required): The name to validate
- `resource_type` (required): Type of resource (k8s-deployment, aws-s3-bucket, etc.)
- `environment` (required): dev/staging/prod
- `team` (optional): Team owning the resource
- `service` (optional): Service/application name
- `context` (optional): Additional metadata (region, project, tags)

**Governance Integration**:
- Maps to: `workspace/src/governance/10-policy/naming-governance-policy.yaml`
- Validates against: `workspace/src/governance/10-policy/naming-patterns.yaml`
- Uses patterns from: `workspace/src/governance/10-policy/naming-validation-automations.yaml`

---

### 2. Validation Response Schema
**Purpose**: Return validation results with detailed violations and suggestions

**Core Fields**:
- `valid` (required): Boolean indicating validity
- `resource_name` (required): Name that was validated
- `timestamp` (required): When validation occurred
- `policy_matched` (optional): Policy that was applied
- `violations` (optional): List of violations with severity, code, message, suggestion
- `suggestions` (optional): Suggested valid names
- `metadata` (optional): Validator version, policy version, execution time

**Governance Integration**:
- Maps to: `workspace/src/governance/07-audit/naming-audit-checklist.yaml`
- Triggers alerts from: `workspace/src/governance/10-policy/naming-alert-rules.yaml`
- Reports metrics to: `workspace/src/governance/13-metrics-reporting/naming-metrics-kpi.yaml`

---

### 3. Generation Request Schema
**Purpose**: Generate compliant resource names based on governance policies

**Core Fields**:
- `resource_type` (required): Type of resource to name
- `environment` (required): Deployment environment
- `team` (optional): Team owning the resource
- `service` (optional): Service/application name
- `version` (optional): Version identifier (SemVer format)
- `options` (optional): Generation settings (timestamp, suffix, multiple)

**Governance Integration**:
- Uses templates from: `workspace/src/governance/27-templates/naming-templates.yaml`
- Applies patterns from: `workspace/src/governance/10-policy/naming-patterns.yaml`
- References policy from: `workspace/src/governance/10-policy/naming-governance-policy.yaml`

---

### 4. Change Request Schema
**Purpose**: Request governance changes through RFC process

**Core Fields**:
- `change_id` (required): Unique identifier (CHG-YYYY-NNN format)
- `type` (required): standard/normal/emergency
- `requester` (required): User or team requesting
- `title` (required): Brief title
- `description` (optional): Detailed description
- `risk_level` (required): critical/high/medium/low
- `impact_assessment` (optional): Services affected, downtime, data impact
- `approval` (optional): Method, status, approvers
- `implementation_plan` (optional): Steps, timing, owners
- `rollback_plan` (optional): Rollback steps and automation
- `metrics` (optional): KPIs and audit configuration

**Governance Integration**:
- Maps to: `workspace/src/governance/03-change/naming-rfc-workflow.yaml`
- Uses template: `workspace/src/governance/03-change/naming-change-request.yaml`
- Escalates via: `workspace/src/governance/01-architecture/naming-escalation-matrix.yaml`
- Approves through: `workspace/src/governance/01-architecture/naming-governance-structure.yaml`

---

### 5. Exception Request Schema
**Purpose**: Request temporary/permanent exceptions from naming policies

**Core Fields**:
- `exception_id` (required): Unique identifier (EXC-YYYY-NNN format)
- `type` (required): temporary/standard/permanent
- `applicant` (required): Team or user requesting
- `item` (required): Item for exception
- `reason` (required): Business/technical justification
- `risk_evaluation` (required): Risk assessment
- `duration` (optional): Start/end times with justification
- `linked_change_id` (optional): Associated change request
- `approval` (optional): Status, reviewer, conditions
- `mitigation` (optional): Measures and monitoring

**Governance Integration**:
- Maps to: `workspace/src/governance/02-decision/naming-exception-process.yaml`
- Reviewed by: `workspace/src/governance/01-architecture/naming-governance-structure.yaml`
- Incentivizes compliance: `workspace/src/governance/02-decision/naming-incentives.yaml`

---

## Schema-Driven Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Governance Manifest                        │
│              (Single Entry Point for AI)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼────┐            ┌────▼────┐
    │ schemas │            │  tools  │
    │  (5)    │            │   CLI   │
    └────┬────┘            └────┬────┘
         │                      │
    ┌────┴──────────┐           │
    │  JSON Schema  │◄──────────┘
    │   Contracts   │
    └────┬──────────┘
         │
    ┌────┴───────────────────────────────────────┐
    │      Python Governance Agent               │
    │  (enforces schema validation)              │
    └────┬───────────────────────────────────────┘
         │
    ┌────┴───────────────────────────────────────┐
    │         Governance Modules                 │
    │  (referenced by schema definitions)       │
    └────────────────────────────────────────────┘
```

---

## Schema to Module Mapping Matrix

| Schema | Primary Module | Supporting Modules |
|--------|---------------|-------------------|
| validation-request | 10-policy | 27-templates, 35-scripts |
| validation-response | 07-audit | 10-policy, 13-metrics-reporting |
| generation-request | 27-templates | 10-policy, 10-policy |
| change-request | 03-change | 01-architecture, 02-decision |
| exception-request | 02-decision | 01-architecture |

---

## Schema Dependencies

```
validation-request.schema.yaml
    │
    ├── validation-response.schema.yaml (output)
    │
    └── naming-governance-policy.yaml (policy reference)
        └── naming-patterns.yaml (patterns)

generation-request.schema.yaml
    │
    └── naming-templates.yaml (template reference)
        └── naming-governance-policy.yaml (policy)

change-request.schema.yaml
    │
    ├── naming-rfc-workflow.yaml (workflow)
    ├── naming-escalation-matrix.yaml (escalation)
    └── naming-governance-structure.yaml (approvals)

exception-request.schema.yaml
    │
    ├── naming-exception-process.yaml (process)
    ├── naming-governance-structure.yaml (approvals)
    └── naming-incentives.yaml (compliance)
```

---

## Implementation Roadmap

### Phase 2: Schema-Driven Refactoring

1. **Update governance-manifest.yaml**
   - Add schema references for each module
   - Define schema as primary source of truth
   - Map module functions to schema operations

2. **Refactor naming-governance-policy.yaml**
   - Add schema validation references
   - Link patterns to validation-request schema
   - Reference generation-request for templates

3. **Refactor naming-rfc-workflow.yaml**
   - Use change-request schema as input
   - Map workflow stages to schema fields
   - Link to escalation-matrix for approvals

4. **Refactor naming-exception-process.yaml**
   - Use exception-request schema as input
   - Map exception types to schema enums
   - Link to governance-structure for approvals

5. **Update Python Governance Agent**
   - Add schema enforcement for all operations
   - Return responses matching schema contracts
   - Generate schema-compliant names

---

## Validation and Testing

### Schema Validation Tests
- [ ] Test validation-request with all resource types
- [ ] Test validation-response with all violation severities
- [ ] Test generation-request with all options
- [ ] Test change-request with all types and risk levels
- [ ] Test exception-request with all exception types

### Integration Tests
- [ ] End-to-end validation flow (request → response)
- [ ] End-to-end generation flow (request → compliant name)
- [ ] End-to-end change flow (request → approval)
- [ ] End-to-end exception flow (request → approval)

---

## Conclusion

The 5 core schemas serve as the foundation for all naming governance operations. By making schemas the primary source of truth, we create a machine-operational system where:
1. All operations are validated against schema contracts
2. Governance modules are referenced by schema definitions
3. AI agents can understand and execute operations autonomously
4. No human documentation is required for operation

This architecture transformation aligns with the user's requirement for a pure machine-operational AI governance system.