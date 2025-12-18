# Canonical Naming Templates

This directory contains implementation templates for the Canonical Naming Governance framework.

## 📁 Directory Structure

```
27-templates/
├── k8s/                    # Kubernetes resource templates
│   ├── namespace-minimal.yaml
│   ├── namespace-strict.yaml
│   ├── namespace-template.yaml
│   ├── deployment-canonical.yaml
│   ├── service-canonical.yaml
│   ├── rbac-minimal.yaml
│   ├── rbac-strict.yaml
│   ├── resourcequota-minimal.yaml
│   ├── resourcequota-strict.yaml
│   ├── networkpolicy-minimal.yaml
│   └── networkpolicy-strict.yaml
│
├── helm/                   # Helm chart helpers
│   └── _helpers.tpl       # Template functions for canonical naming
│
└── kustomize/             # Kustomize components
    └── canonical-labels/  # Label injection component
        ├── kustomization.yaml
        ├── kustomizeconfig.yaml
        └── README.md
```

## 🚀 Quick Start

### Using Kubernetes Templates

1. **Minimal Namespace** (Development):
   ```bash
   kubectl apply -f governance/27-templates/k8s/namespace-minimal.yaml
   ```

2. **Strict Namespace** (Production):
   ```bash
   kubectl apply -f governance/27-templates/k8s/namespace-strict.yaml
   ```

### Using Helm Helpers

Add to your `Chart.yaml`:
```yaml
dependencies:
  - name: canonical-helpers
    version: "1.0.0"
    repository: "file://../../governance/27-templates/helm"
```

In your templates:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: {{ include "canonical.name" . }}
  labels:
    {{- include "canonical.labels" . | nindent 4 }}
  annotations:
    {{- include "canonical.annotations" . | nindent 4 }}
```

### Using Kustomize Component

In your `kustomization.yaml`:
```yaml
components:
  - ../../governance/27-templates/kustomize/canonical-labels

commonLabels:
  environment: prod
  tenant: platform
```

## 📖 Template Modes

### Minimal Mode
- **Use case**: Development, testing, sandbox environments
- **Required labels**: environment, tenant, app.kubernetes.io/managed-by
- **Validation**: Basic pattern matching
- **Example**: `dev-myapp-service`

### Strict Mode
- **Use case**: Production, staging environments
- **Required labels**: Extended Kubernetes recommended labels
- **Additional annotations**: URN, qualifiers, ownership, documentation
- **Security**: Enhanced RBAC, network policies, resource quotas
- **Example**: `prod-myapp-service`

## 🔍 Template Categories

### 1. Namespace Templates
- **minimal**: Basic namespace with required labels
- **strict**: Production namespace with full governance
- **template**: Parameterized for Helm/Kustomize

### 2. Workload Templates
- **deployment-canonical**: Deployment with canonical labels
- **service-canonical**: Service with canonical labels

### 3. Security Templates
- **rbac-minimal**: Basic read-only RBAC
- **rbac-strict**: Production least-privilege RBAC

### 4. Resource Management
- **resourcequota-minimal**: Basic quotas for dev
- **resourcequota-strict**: Comprehensive quotas with LimitRanges

### 5. Network Security
- **networkpolicy-minimal**: Basic namespace isolation
- **networkpolicy-strict**: Zero-trust network policies

## ✅ Validation

All templates are validated against:

1. **Naming Pattern**:
   ```
   ^(?!.*--)(team|tenant|dev|test|staging|prod|learn|sandbox)-[a-z0-9]+(?:-[a-z0-9]+)*$
   ```

2. **Required Labels**:
   - environment
   - tenant
   - app.kubernetes.io/managed-by

3. **URN Format** (recommended):
   ```
   urn:axiom:{domain}:{component}:env:{environment}:{version}
   ```

## 🛠️ Customization

### Updating Templates for Your Organization

1. **Replace namespace prefix**: Change `axiom` to your org name
2. **Update URN scheme**: Modify URN template in machine spec
3. **Adjust environments**: Update allowed environments list
4. **Configure quotas**: Modify resource limits per environment

### Example: Custom Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: prod-myorg-myapp-service
  labels:
    environment: prod
    tenant: myteam
    app.kubernetes.io/name: myapp
    app.kubernetes.io/managed-by: myorg-controller
  annotations:
    myorg.io/canonical-urn: "urn:myorg:platform:myapp:env:prod:v1"
    myorg.io/governance-mode: strict
```

## 📚 Related Documentation

- [Implementation Guide](../29-docs/05-implementation-templates-and-enforcement.md)
- [Canonical Naming Governance](../29-docs/canonical-naming-governance-report.md)
- [Machine Specification](../34-config/naming/canonical-naming-machine-spec.yaml)
- [Examples](../../examples/governance/naming/)

## 🔗 Enforcement

Templates work with:

- **Gatekeeper**: Admission control with ConstraintTemplates
- **Conftest**: CI/CD policy validation
- **Kyverno**: Policy engine (alternative to Gatekeeper)
- **OPA**: Custom policy enforcement

See [Enforcement Documentation](../29-docs/05-implementation-templates-and-enforcement.md#enforcement) for details.

## 🤝 Contributing

When adding new templates:

1. Follow the naming pattern
2. Include both minimal and strict variants
3. Add comprehensive labels and annotations
4. Document usage in this README
5. Validate against conftest policies

---

**Owner**: Platform Governance Team
**Last Updated**: 2025-12-17
**Version**: 1.0.0
