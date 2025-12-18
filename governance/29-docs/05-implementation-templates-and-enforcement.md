# Canonical Naming: Implementation Templates and Enforcement | 實施模板與強制執行

## 📋 Overview 概述

This document provides ready-to-use templates and enforcement tools for implementing the Canonical Naming Governance v1.0 framework across the SynergyMesh ecosystem.

本文檔提供即用型模板和強制執行工具，用於在 SynergyMesh 生態系統中實施單一權威命名治理 v1.0 框架。

## 🎯 Purpose 目的

- Provide concrete implementation templates for Kubernetes resources
- Enable automated enforcement via Gatekeeper and Conftest
- Support both minimal and strict governance modes
- Facilitate migration from legacy naming patterns

## 📚 Table of Contents 目錄

1. [Namespace Templates](#namespace-templates)
2. [Label Injection Templates](#label-injection-templates)
3. [RBAC Templates](#rbac-templates)
4. [ResourceQuota Templates](#resourcequota-templates)
5. [NetworkPolicy Templates](#networkpolicy-templates)
6. [Helm and Kustomize Helpers](#helm-and-kustomize-helpers)
7. [Gatekeeper ConstraintTemplates](#gatekeeper-constrainttemplates)
8. [Conftest Rego Policies](#conftest-rego-policies)
9. [CI/CD Integration](#cicd-integration)
10. [Migration Guide](#migration-guide)

---

## 1. Namespace Templates

### Minimal Mode Namespace

**File**: `governance/27-templates/k8s/namespace-minimal.yaml`

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dev-myapp-service
  labels:
    environment: dev
    tenant: platform
    app.kubernetes.io/managed-by: axiom-naming-controller
  annotations:
    axiom.io/canonical-urn: "urn:axiom:platform:myapp:env:dev:v1"
    axiom.io/governance-mode: minimal
```

### Strict Mode Namespace

**File**: `governance/27-templates/k8s/namespace-strict.yaml`

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: prod-myapp-service
  labels:
    environment: prod
    tenant: platform
    app.kubernetes.io/name: myapp
    app.kubernetes.io/component: service
    app.kubernetes.io/part-of: synergymesh
    app.kubernetes.io/managed-by: axiom-naming-controller
    app.kubernetes.io/version: v1.0.0
    team: platform-team
    cost-center: engineering
  annotations:
    axiom.io/canonical-urn: "urn:axiom:platform:myapp:env:prod:v1"
    axiom.io/qualifiers: "region=us-west-2,zone=a,cluster=prod-cluster-01"
    axiom.io/governance-mode: strict
    axiom.io/description: "Production service namespace for MyApp"
    axiom.io/owner: platform-team@example.com
    axiom.io/documentation: https://docs.example.com/myapp
```

### Multi-Environment Template

**File**: `governance/27-templates/k8s/namespace-template.yaml`

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: {{ .Values.environment }}-{{ .Values.component }}-{{ .Values.suffix }}
  labels:
    environment: {{ .Values.environment }}
    tenant: {{ .Values.tenant | default "platform" }}
    app.kubernetes.io/name: {{ .Values.component }}
    app.kubernetes.io/managed-by: {{ .Values.managedBy | default "axiom-naming-controller" }}
    {{- range $key, $value := .Values.extraLabels }}
    {{ $key }}: {{ $value }}
    {{- end }}
  annotations:
    axiom.io/canonical-urn: "urn:axiom:{{ .Values.domain }}:{{ .Values.component }}:env:{{ .Values.environment }}:{{ .Values.version }}"
    axiom.io/governance-mode: {{ .Values.governanceMode | default "minimal" }}
    {{- range $key, $value := .Values.extraAnnotations }}
    {{ $key }}: {{ $value }}
    {{- end }}
```

---

## 2. Label Injection Templates

### Deployment with Canonical Labels

**File**: `governance/27-templates/k8s/deployment-canonical.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dev-myapp-deployment
  namespace: dev-myapp-service
  labels:
    environment: dev
    tenant: platform
    app.kubernetes.io/name: myapp
    app.kubernetes.io/component: backend
    app.kubernetes.io/part-of: synergymesh
    app.kubernetes.io/managed-by: axiom-naming-controller
    app.kubernetes.io/version: "1.0.0"
  annotations:
    axiom.io/canonical-urn: "urn:axiom:platform:myapp:env:dev:v1"
    axiom.io/qualifiers: "tier=backend,layer=application"
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: myapp
      app.kubernetes.io/component: backend
  template:
    metadata:
      labels:
        environment: dev
        tenant: platform
        app.kubernetes.io/name: myapp
        app.kubernetes.io/component: backend
        app.kubernetes.io/part-of: synergymesh
        app.kubernetes.io/version: "1.0.0"
    spec:
      containers:
      - name: myapp
        image: myapp:1.0.0
        ports:
        - containerPort: 8080
          name: http
```

### Service with Canonical Labels

**File**: `governance/27-templates/k8s/service-canonical.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: dev-myapp-svc
  namespace: dev-myapp-service
  labels:
    environment: dev
    tenant: platform
    app.kubernetes.io/name: myapp
    app.kubernetes.io/component: backend
    app.kubernetes.io/managed-by: axiom-naming-controller
  annotations:
    axiom.io/canonical-urn: "urn:axiom:platform:myapp:env:dev:v1"
spec:
  selector:
    app.kubernetes.io/name: myapp
    app.kubernetes.io/component: backend
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
  type: ClusterIP
```

---

## 3. RBAC Templates

### Minimal RBAC

**File**: `governance/27-templates/k8s/rbac-minimal.yaml`

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: dev-myapp-role
  namespace: dev-myapp-service
  labels:
    environment: dev
    tenant: platform
    app.kubernetes.io/managed-by: axiom-naming-controller
  annotations:
    axiom.io/canonical-urn: "urn:axiom:platform:myapp:env:dev:v1"
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dev-myapp-binding
  namespace: dev-myapp-service
  labels:
    environment: dev
    tenant: platform
    app.kubernetes.io/managed-by: axiom-naming-controller
subjects:
- kind: ServiceAccount
  name: dev-myapp-sa
  namespace: dev-myapp-service
roleRef:
  kind: Role
  name: dev-myapp-role
  apiGroup: rbac.authorization.k8s.io
```

### Strict RBAC

**File**: `governance/27-templates/k8s/rbac-strict.yaml`

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: prod-myapp-role
  namespace: prod-myapp-service
  labels:
    environment: prod
    tenant: platform
    app.kubernetes.io/name: myapp
    app.kubernetes.io/managed-by: axiom-naming-controller
    security-tier: restricted
  annotations:
    axiom.io/canonical-urn: "urn:axiom:platform:myapp:env:prod:v1"
    axiom.io/governance-mode: strict
    axiom.io/security-review: "2025-12-17"
    axiom.io/principle: least-privilege
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["services"]
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: prod-myapp-binding
  namespace: prod-myapp-service
  labels:
    environment: prod
    tenant: platform
    app.kubernetes.io/managed-by: axiom-naming-controller
  annotations:
    axiom.io/canonical-urn: "urn:axiom:platform:myapp:env:prod:v1"
subjects:
- kind: ServiceAccount
  name: prod-myapp-sa
  namespace: prod-myapp-service
roleRef:
  kind: Role
  name: prod-myapp-role
  apiGroup: rbac.authorization.k8s.io
```

---

## 4. ResourceQuota Templates

### Minimal ResourceQuota

**File**: `governance/27-templates/k8s/resourcequota-minimal.yaml`

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: dev-myapp-quota
  namespace: dev-myapp-service
  labels:
    environment: dev
    tenant: platform
    app.kubernetes.io/managed-by: axiom-naming-controller
  annotations:
    axiom.io/canonical-urn: "urn:axiom:platform:myapp:env:dev:v1"
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "20"
```

### Strict ResourceQuota

**File**: `governance/27-templates/k8s/resourcequota-strict.yaml`

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: prod-myapp-quota
  namespace: prod-myapp-service
  labels:
    environment: prod
    tenant: platform
    app.kubernetes.io/name: myapp
    app.kubernetes.io/managed-by: axiom-naming-controller
    cost-center: engineering
  annotations:
    axiom.io/canonical-urn: "urn:axiom:platform:myapp:env:prod:v1"
    axiom.io/governance-mode: strict
    axiom.io/budget: "monthly-limit-500-usd"
spec:
  hard:
    requests.cpu: "16"
    requests.memory: 32Gi
    limits.cpu: "32"
    limits.memory: 64Gi
    requests.storage: 100Gi
    persistentvolumeclaims: "10"
    pods: "50"
    services: "10"
    configmaps: "20"
    secrets: "20"
  scopeSelector:
    matchExpressions:
    - operator: In
      scopeName: PriorityClass
      values: ["high", "medium"]
```

---

## 5. NetworkPolicy Templates

### Minimal NetworkPolicy

**File**: `governance/27-templates/k8s/networkpolicy-minimal.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: dev-myapp-netpol
  namespace: dev-myapp-service
  labels:
    environment: dev
    tenant: platform
    app.kubernetes.io/managed-by: axiom-naming-controller
  annotations:
    axiom.io/canonical-urn: "urn:axiom:platform:myapp:env:dev:v1"
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: myapp
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          environment: dev
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443
```

### Strict NetworkPolicy (Zero-Trust)

**File**: `governance/27-templates/k8s/networkpolicy-strict.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: prod-myapp-netpol
  namespace: prod-myapp-service
  labels:
    environment: prod
    tenant: platform
    app.kubernetes.io/name: myapp
    app.kubernetes.io/managed-by: axiom-naming-controller
    security-tier: zero-trust
  annotations:
    axiom.io/canonical-urn: "urn:axiom:platform:myapp:env:prod:v1"
    axiom.io/governance-mode: strict
    axiom.io/security-policy: zero-trust
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: myapp
      environment: prod
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: frontend
          environment: prod
    - namespaceSelector:
        matchLabels:
          tenant: platform
          environment: prod
    ports:
    - protocol: TCP
      port: 8080
      endPort: 8080
  egress:
  # Allow DNS
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
    ports:
    - protocol: UDP
      port: 53
  # Allow external HTTPS
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443
  # Deny all other egress by default
```

---

## 6. Helm and Kustomize Helpers

### Helm Helper (_helpers.tpl)

**File**: `governance/27-templates/helm/_helpers.tpl`

```yaml
{{/*
Generate canonical name following the governance spec
*/}}
{{- define "canonical.name" -}}
{{- $env := .Values.environment | default "dev" -}}
{{- $component := .Values.component | required "component is required" -}}
{{- $suffix := .Values.suffix | default "service" -}}
{{- printf "%s-%s-%s" $env $component $suffix | lower | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Generate canonical URN
*/}}
{{- define "canonical.urn" -}}
{{- $domain := .Values.domain | default "platform" -}}
{{- $component := .Values.component | required "component is required" -}}
{{- $environment := .Values.environment | default "dev" -}}
{{- $version := .Values.version | default "v1" -}}
{{- printf "urn:axiom:%s:%s:env:%s:%s" $domain $component $environment $version -}}
{{- end -}}

{{/*
Generate required labels
*/}}
{{- define "canonical.labels" -}}
environment: {{ .Values.environment | default "dev" }}
tenant: {{ .Values.tenant | default "platform" }}
app.kubernetes.io/name: {{ .Values.component }}
app.kubernetes.io/managed-by: {{ .Values.managedBy | default "axiom-naming-controller" }}
{{- if .Values.appVersion }}
app.kubernetes.io/version: {{ .Values.appVersion | quote }}
{{- end }}
{{- end -}}

{{/*
Generate canonical annotations
*/}}
{{- define "canonical.annotations" -}}
axiom.io/canonical-urn: {{ include "canonical.urn" . | quote }}
{{- if .Values.qualifiers }}
axiom.io/qualifiers: {{ .Values.qualifiers | quote }}
{{- end }}
axiom.io/governance-mode: {{ .Values.governanceMode | default "minimal" }}
{{- end -}}

{{/*
Validate naming pattern
*/}}
{{- define "canonical.validate" -}}
{{- $name := include "canonical.name" . -}}
{{- if not (regexMatch "^(?!.*--)(team|tenant|dev|test|staging|prod|learn|sandbox)-[a-z0-9]+(?:-[a-z0-9]+)*$" $name) -}}
{{- fail (printf "Name '%s' does not match canonical naming pattern" $name) -}}
{{- end -}}
{{- if gt (len $name) 63 -}}
{{- fail (printf "Name '%s' exceeds maximum length of 63 characters" $name) -}}
{{- end -}}
{{- end -}}
```

### Kustomize Component

**File**: `governance/27-templates/kustomize/canonical-labels/kustomization.yaml`

```yaml
apiVersion: kustomize.config.k8s.io/v1alpha1
kind: Component
metadata:
  name: canonical-labels
  annotations:
    config.kubernetes.io/local-config: "true"

commonLabels:
  app.kubernetes.io/managed-by: axiom-naming-controller

labels:
- pairs:
    environment: dev
    tenant: platform
  includeSelectors: true
  includeTemplates: true

commonAnnotations:
  axiom.io/governance-mode: minimal

patches:
- patch: |-
    - op: add
      path: /metadata/annotations/axiom.io~1canonical-urn
      value: urn:axiom:platform:component:env:dev:v1
  target:
    kind: Namespace

configurations:
- kustomizeconfig.yaml
```

**File**: `governance/27-templates/kustomize/canonical-labels/kustomizeconfig.yaml`

```yaml
nameReference:
- kind: ConfigMap
  fieldSpecs:
  - path: spec/volumes/configMap/name
    kind: Pod

commonLabels:
- path: spec/selector/matchLabels
  create: true
  kind: Deployment
- path: spec/template/metadata/labels
  create: true
  kind: Deployment

labels:
- path: metadata/labels
  create: true
- path: spec/template/metadata/labels
  create: true
```

---

## 7. Gatekeeper ConstraintTemplates

### K8sRequiredLabels

**File**: `governance/23-policies/gatekeeper/constraint-templates/k8srequiredlabels.yaml`

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
  annotations:
    metadata.gatekeeper.sh/title: "Required Labels"
    metadata.gatekeeper.sh/version: 1.0.0
    description: "Requires resources to contain specified labels as per canonical naming governance"
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLabels
      validation:
        openAPIV3Schema:
          type: object
          properties:
            labels:
              type: array
              description: "List of required labels"
              items:
                type: string
            message:
              type: string
              description: "Custom violation message"
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredlabels

        violation[{"msg": msg, "details": {"missing_labels": missing}}] {
          provided := {label | input.review.object.metadata.labels[label]}
          required := {label | label := input.parameters.labels[_]}
          missing := required - provided
          count(missing) > 0
          def_msg := sprintf("Missing required labels: %v", [missing])
          msg := object.get(input.parameters, "message", def_msg)
        }
```

### K8sNamingPattern

**File**: `governance/23-policies/gatekeeper/constraint-templates/k8snamingpattern.yaml`

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8snamingpattern
  annotations:
    metadata.gatekeeper.sh/title: "Naming Pattern"
    metadata.gatekeeper.sh/version: 1.0.0
    description: "Enforces canonical naming pattern on resources"
spec:
  crd:
    spec:
      names:
        kind: K8sNamingPattern
      validation:
        openAPIV3Schema:
          type: object
          properties:
            pattern:
              type: string
              description: "Regex pattern for valid names"
            maxLength:
              type: integer
              description: "Maximum name length"
              default: 63
            message:
              type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8snamingpattern

        violation[{"msg": msg}] {
          name := input.review.object.metadata.name
          pattern := input.parameters.pattern
          not re_match(pattern, name)
          def_msg := sprintf("Resource name '%v' does not match required pattern '%v'", [name, pattern])
          msg := object.get(input.parameters, "message", def_msg)
        }

        violation[{"msg": msg}] {
          name := input.review.object.metadata.name
          max_length := object.get(input.parameters, "maxLength", 63)
          count(name) > max_length
          msg := sprintf("Resource name '%v' exceeds maximum length of %v characters", [name, max_length])
        }

        violation[{"msg": msg}] {
          name := input.review.object.metadata.name
          contains(name, "--")
          msg := sprintf("Resource name '%v' contains forbidden consecutive hyphens '--'", [name])
        }
```

### Constraint Instances

**File**: `governance/23-policies/gatekeeper/constraints/require-canonical-labels.yaml`

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: require-canonical-labels
spec:
  enforcementAction: deny
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Namespace", "Service", "Pod"]
      - apiGroups: ["apps"]
        kinds: ["Deployment", "StatefulSet", "DaemonSet"]
  parameters:
    labels:
      - environment
      - tenant
      - app.kubernetes.io/managed-by
    message: "Resources must have canonical governance labels: environment, tenant, app.kubernetes.io/managed-by"
```

**File**: `governance/23-policies/gatekeeper/constraints/enforce-naming-pattern.yaml`

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sNamingPattern
metadata:
  name: enforce-canonical-naming
spec:
  enforcementAction: deny
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Namespace", "Service"]
      - apiGroups: ["apps"]
        kinds: ["Deployment", "StatefulSet"]
  parameters:
    pattern: "^(?!.*--)(team|tenant|dev|test|staging|prod|learn|sandbox)-[a-z0-9]+(?:-[a-z0-9]+)*$"
    maxLength: 63
    message: "Resource name must follow canonical naming pattern: {env}-{component}-{suffix}, lowercase, no consecutive hyphens, max 63 chars"
```

---

## 8. Conftest Rego Policies

### Naming Policy

**File**: `governance/23-policies/conftest/naming_policy.rego`

```rego
package main

import future.keywords.in

# Canonical naming pattern
canonical_pattern := "^(?!.*--)(team|tenant|dev|test|staging|prod|learn|sandbox)-[a-z0-9]+(?:-[a-z0-9]+)*$"
max_name_length := 63

# Required labels
required_labels := ["environment", "tenant", "app.kubernetes.io/managed-by"]

# Allowed environments
allowed_environments := ["dev", "test", "staging", "prod", "learn", "sandbox"]

# Deny if name doesn't match canonical pattern
deny[msg] {
    input.kind in ["Namespace", "Deployment", "Service", "StatefulSet"]
    name := input.metadata.name
    not regex.match(canonical_pattern, name)
    msg := sprintf("Resource name '%v' does not match canonical pattern. Expected: {env}-{component}-{suffix}", [name])
}

# Deny if name contains consecutive hyphens
deny[msg] {
    input.kind in ["Namespace", "Deployment", "Service", "StatefulSet"]
    name := input.metadata.name
    contains(name, "--")
    msg := sprintf("Resource name '%v' contains forbidden consecutive hyphens '--'", [name])
}

# Deny if name exceeds maximum length
deny[msg] {
    input.kind in ["Namespace", "Deployment", "Service", "StatefulSet"]
    name := input.metadata.name
    count(name) > max_name_length
    msg := sprintf("Resource name '%v' exceeds maximum length of %v characters", [name, max_name_length])
}

# Deny if required labels are missing
deny[msg] {
    input.metadata
    missing_labels := [label | label := required_labels[_]; not input.metadata.labels[label]]
    count(missing_labels) > 0
    msg := sprintf("Missing required labels: %v", [missing_labels])
}

# Deny if environment label value is not allowed
deny[msg] {
    input.metadata.labels.environment
    env := input.metadata.labels.environment
    not env in allowed_environments
    msg := sprintf("Invalid environment label '%v'. Allowed: %v", [env, allowed_environments])
}

# Deny if name prefix doesn't match environment label
deny[msg] {
    input.metadata.labels.environment
    name := input.metadata.name
    env := input.metadata.labels.environment
    startswith(name, sprintf("%v-", [env]))
    not startswith(name, sprintf("%v-", [env]))
    msg := sprintf("Name prefix must match environment label. Expected prefix: %v-", [env])
}

# Warn if canonical URN annotation is missing
warn[msg] {
    input.metadata
    not input.metadata.annotations["axiom.io/canonical-urn"]
    msg := "Missing recommended annotation: axiom.io/canonical-urn"
}

# Warn if governance mode annotation is missing
warn[msg] {
    input.metadata
    not input.metadata.annotations["axiom.io/governance-mode"]
    msg := "Missing recommended annotation: axiom.io/governance-mode"
}
```

### URN Validation Policy

**File**: `governance/23-policies/conftest/urn_validation.rego`

```rego
package main

import future.keywords.in

# URN pattern: urn:axiom:{domain}:{component}:env:{environment}:{version}
urn_pattern := "^urn:axiom:[a-z0-9-]+:[a-z0-9-]+:env:(dev|test|staging|prod|learn|sandbox):(v[0-9]+|v[0-9]+\\.[0-9]+\\.[0-9]+)$"

# Deny if URN annotation is malformed
deny[msg] {
    input.metadata.annotations["axiom.io/canonical-urn"]
    urn := input.metadata.annotations["axiom.io/canonical-urn"]
    not regex.match(urn_pattern, urn)
    msg := sprintf("Malformed canonical URN: '%v'. Expected format: urn:axiom:{domain}:{component}:env:{environment}:{version}", [urn])
}

# Deny if URN environment doesn't match label
deny[msg] {
    input.metadata.annotations["axiom.io/canonical-urn"]
    input.metadata.labels.environment
    urn := input.metadata.annotations["axiom.io/canonical-urn"]
    env_label := input.metadata.labels.environment

    # Extract environment from URN
    urn_parts := split(urn, ":")
    urn_env := urn_parts[4]  # env:{environment}

    urn_env != env_label
    msg := sprintf("URN environment '%v' does not match environment label '%v'", [urn_env, env_label])
}
```

---

## 9. CI/CD Integration

### GitHub Actions Workflow

**File**: `governance/35-scripts/ci/github-actions-naming-validation.yaml`

```yaml
name: Canonical Naming Validation

on:
  pull_request:
    paths:
      - '**.yaml'
      - '**.yml'
  push:
    branches:
      - main
      - develop

jobs:
  validate-naming:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Conftest
        run: |
          wget https://github.com/open-policy-agent/conftest/releases/download/v0.49.1/conftest_0.49.1_Linux_x86_64.tar.gz
          tar xzf conftest_0.49.1_Linux_x86_64.tar.gz
          sudo mv conftest /usr/local/bin/
          conftest --version

      - name: Validate K8s manifests against naming policy
        run: |
          find . -name "*.yaml" -o -name "*.yml" | \
          xargs conftest test \
            --policy governance/23-policies/conftest/naming_policy.rego \
            --policy governance/23-policies/conftest/urn_validation.rego \
            --namespace main \
            --output table

      - name: Generate compliance report
        if: always()
        run: |
          conftest test \
            --policy governance/23-policies/conftest/naming_policy.rego \
            --namespace main \
            --output json \
            $(find . -name "*.yaml" -o -name "*.yml") \
            > naming-compliance-report.json

      - name: Upload compliance report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: naming-compliance-report
          path: naming-compliance-report.json
```

### GitLab CI Pipeline

**File**: `governance/35-scripts/ci/gitlab-ci-naming-validation.yaml`

```yaml
stages:
  - validate

variables:
  CONFTEST_VERSION: "0.49.1"

validate-canonical-naming:
  stage: validate
  image: alpine:latest
  before_script:
    - apk add --no-cache wget tar
    - wget https://github.com/open-policy-agent/conftest/releases/download/v${CONFTEST_VERSION}/conftest_${CONFTEST_VERSION}_Linux_x86_64.tar.gz
    - tar xzf conftest_${CONFTEST_VERSION}_Linux_x86_64.tar.gz
    - mv conftest /usr/local/bin/
  script:
    - |
      find . -name "*.yaml" -o -name "*.yml" | \
      xargs conftest test \
        --policy governance/23-policies/conftest/naming_policy.rego \
        --policy governance/23-policies/conftest/urn_validation.rego \
        --namespace main \
        --fail-on-warn
  artifacts:
    when: always
    reports:
      junit: conftest-report.xml
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'
```

### Pre-commit Hook

**File**: `governance/35-scripts/hooks/pre-commit-naming-check.sh`

```bash
#!/bin/bash
# Pre-commit hook for canonical naming validation

set -e

echo "🔍 Validating canonical naming compliance..."

# Check if conftest is installed
if ! command -v conftest &> /dev/null; then
    echo "❌ conftest is not installed. Please install it first:"
    echo "   https://www.conftest.dev/install/"
    exit 1
fi

# Find all YAML files staged for commit
YAML_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(yaml|yml)$' || true)

if [ -z "$YAML_FILES" ]; then
    echo "✅ No YAML files to validate"
    exit 0
fi

# Validate with conftest
echo "$YAML_FILES" | xargs conftest test \
    --policy governance/23-policies/conftest/naming_policy.rego \
    --policy governance/23-policies/conftest/urn_validation.rego \
    --namespace main \
    --fail-on-warn

if [ $? -eq 0 ]; then
    echo "✅ All files pass canonical naming validation"
    exit 0
else
    echo "❌ Naming validation failed. Please fix the issues above."
    exit 1
fi
```

---

## 10. Migration Guide

### Migration Script

**File**: `governance/35-scripts/migration/migrate-to-canonical-naming.sh`

```bash
#!/bin/bash
# Migration script for canonical naming compliance

set -e

MACHINE_SPEC="governance/34-config/naming/canonical-naming-machine-spec.yaml"
MAPPING_FILE="governance/34-config/naming/namespace-mapping.yaml"
OUTPUT_DIR="reports/migration"
DRY_RUN="${DRY_RUN:-true}"

echo "🚀 Starting canonical naming migration..."
echo "📋 Dry run: $DRY_RUN"

mkdir -p "$OUTPUT_DIR"

# Generate migration plan
echo "📊 Analyzing current resources..."
kubectl get namespaces -o json | \
  jq -r '.items[] | select(.metadata.labels.environment != null) |
  {
    name: .metadata.name,
    labels: .metadata.labels,
    canonical: (.metadata.labels.environment + "-" + (.metadata.labels["app.kubernetes.io/name"] // "unknown") + "-service")
  }' > "$OUTPUT_DIR/namespace-analysis.json"

# Validate against canonical pattern
echo "🔍 Validating against canonical pattern..."
cat "$OUTPUT_DIR/namespace-analysis.json" | \
  jq -r '. | select(.name != .canonical) |
  "\(.name) -> \(.canonical)"' > "$OUTPUT_DIR/migrations-needed.txt"

MIGRATION_COUNT=$(wc -l < "$OUTPUT_DIR/migrations-needed.txt")

if [ "$MIGRATION_COUNT" -eq 0 ]; then
    echo "✅ All namespaces are already compliant!"
    exit 0
fi

echo "⚠️  Found $MIGRATION_COUNT namespaces needing migration"
echo ""
echo "📝 Migration plan saved to: $OUTPUT_DIR/migrations-needed.txt"

if [ "$DRY_RUN" = "false" ]; then
    echo "🔧 Applying migrations..."

    while IFS= read -r line; do
        OLD_NAME=$(echo "$line" | cut -d' ' -f1)
        NEW_NAME=$(echo "$line" | cut -d' ' -f3)

        echo "  Migrating: $OLD_NAME -> $NEW_NAME"

        # Export current namespace
        kubectl get namespace "$OLD_NAME" -o yaml > "$OUTPUT_DIR/${OLD_NAME}-backup.yaml"

        # Create new namespace with canonical name
        kubectl get namespace "$OLD_NAME" -o yaml | \
          sed "s/name: $OLD_NAME/name: $NEW_NAME/" | \
          kubectl create -f -

        # Migrate resources
        kubectl get all -n "$OLD_NAME" -o yaml | \
          sed "s/namespace: $OLD_NAME/namespace: $NEW_NAME/" | \
          kubectl create -f -

        echo "  ✅ Migrated $OLD_NAME to $NEW_NAME"

    done < "$OUTPUT_DIR/migrations-needed.txt"

    echo ""
    echo "🎉 Migration complete!"
    echo "⚠️  Please verify the new namespaces and delete the old ones manually"
else
    echo ""
    echo "✨ Dry run complete. Set DRY_RUN=false to apply migrations."
fi
```

### Validation Report Generator

**File**: `governance/35-scripts/validation/generate-compliance-report.sh`

```bash
#!/bin/bash
# Generate canonical naming compliance report

OUTPUT_FILE="${OUTPUT_FILE:-reports/canonical-naming-compliance-report.html}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

mkdir -p "$(dirname "$OUTPUT_FILE")"

cat > "$OUTPUT_FILE" <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Canonical Naming Compliance Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        .compliant { color: green; }
        .non-compliant { color: red; }
        .warning { color: orange; }
    </style>
</head>
<body>
    <h1>Canonical Naming Compliance Report</h1>
    <p>Generated: $TIMESTAMP</p>
    <h2>Namespace Compliance</h2>
    <table>
        <tr>
            <th>Namespace</th>
            <th>Pattern Match</th>
            <th>Required Labels</th>
            <th>URN Annotation</th>
            <th>Status</th>
        </tr>
EOF

# Get all namespaces and check compliance
kubectl get namespaces -o json | jq -r '.items[] |
  @json' | while read -r ns; do
    NAME=$(echo "$ns" | jq -r '.metadata.name')
    LABELS=$(echo "$ns" | jq -r '.metadata.labels')
    URN=$(echo "$ns" | jq -r '.metadata.annotations["axiom.io/canonical-urn"] // "missing"')

    # Check pattern
    if echo "$NAME" | grep -Eq '^(?!.*--)(team|tenant|dev|test|staging|prod|learn|sandbox)-[a-z0-9]+(?:-[a-z0-9]+)*$'; then
        PATTERN="✅"
        PATTERN_CLASS="compliant"
    else
        PATTERN="❌"
        PATTERN_CLASS="non-compliant"
    fi

    # Check required labels
    if echo "$LABELS" | jq -e '.environment and .tenant and .["app.kubernetes.io/managed-by"]' > /dev/null; then
        LABELS_CHECK="✅"
        LABELS_CLASS="compliant"
    else
        LABELS_CHECK="❌"
        LABELS_CLASS="non-compliant"
    fi

    # Check URN
    if [ "$URN" != "missing" ]; then
        URN_CHECK="✅"
        URN_CLASS="compliant"
    else
        URN_CHECK="⚠️"
        URN_CLASS="warning"
    fi

    # Overall status
    if [ "$PATTERN" = "✅" ] && [ "$LABELS_CHECK" = "✅" ]; then
        STATUS="✅ Compliant"
        STATUS_CLASS="compliant"
    else
        STATUS="❌ Non-compliant"
        STATUS_CLASS="non-compliant"
    fi

    cat >> "$OUTPUT_FILE" <<INNER_EOF
        <tr>
            <td>$NAME</td>
            <td class="$PATTERN_CLASS">$PATTERN</td>
            <td class="$LABELS_CLASS">$LABELS_CHECK</td>
            <td class="$URN_CLASS">$URN_CHECK</td>
            <td class="$STATUS_CLASS">$STATUS</td>
        </tr>
INNER_EOF
done

cat >> "$OUTPUT_FILE" <<EOF
    </table>
</body>
</html>
EOF

echo "✅ Compliance report generated: $OUTPUT_FILE"
```

---

## 📖 References 參考資料

### Related Documents

- **[Canonical Naming Governance Report](./canonical-naming-governance-report.md)** - Governance framework overview
- **[Machine Spec](../34-config/naming/canonical-naming-machine-spec.yaml)** - Single source of truth for naming rules
- **[Namespace Mapping](../34-config/naming/namespace-mapping.yaml)** - Legacy to canonical mapping
- **[Good vs Bad Examples](../../examples/governance/naming/good-vs-bad-naming.yaml)** - Naming examples

### External Resources

- [Kubernetes Naming Conventions](https://kubernetes.io/docs/concepts/overview/working-with-objects/names/)
- [Gatekeeper Documentation](https://open-policy-agent.github.io/gatekeeper/)
- [Conftest Documentation](https://www.conftest.dev/)
- [OPA Rego Guide](https://www.openpolicyagent.org/docs/latest/policy-language/)

---

## 📝 Document History

| Date       | Version | Changes                                |
|------------|---------|----------------------------------------|
| 2025-12-17 | 1.0.0   | Initial implementation templates       |

**Owner**: Platform Governance Team
**Last Updated**: 2025-12-17
