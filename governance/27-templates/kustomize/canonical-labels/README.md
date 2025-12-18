# Canonical Labels Kustomize Component

This Kustomize component adds canonical governance labels and annotations to all resources.

## Usage

In your `kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

components:
  - ../../governance/27-templates/kustomize/canonical-labels

resources:
  - deployment.yaml
  - service.yaml

# Override default labels
commonLabels:
  environment: prod
  tenant: myteam

commonAnnotations:
  axiom.io/governance-mode: strict
  axiom.io/canonical-urn: urn:axiom:platform:myapp:env:prod:v1
```

## What It Does

1. Adds required governance labels:
   - `environment`
   - `tenant`
   - `app.kubernetes.io/managed-by`

2. Adds governance annotations:
   - `axiom.io/governance-mode`
   - `axiom.io/canonical-urn`

3. Propagates labels to:
   - Selectors
   - Templates
   - Pods

## Customization

Create a `ConfigMap` to customize values:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: canonical-config
data:
  environment: staging
  tenant: platform
  domain: myapp
```
