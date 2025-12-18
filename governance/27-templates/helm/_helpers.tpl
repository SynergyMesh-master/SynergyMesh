{{/*
Canonical Naming Helpers for Helm Charts
Following governance/34-config/naming/canonical-naming-machine-spec.yaml
*/}}

{{/*
Generate canonical name following the governance spec
Format: {environment}-{component}-{suffix}
*/}}
{{- define "canonical.name" -}}
{{- $env := .Values.environment | default "dev" -}}
{{- $component := .Values.component | required "component is required" -}}
{{- $suffix := .Values.suffix | default "service" -}}
{{- printf "%s-%s-%s" $env $component $suffix | lower | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Generate canonical URN
Format: urn:axiom:{domain}:{component}:env:{environment}:{version}
*/}}
{{- define "canonical.urn" -}}
{{- $domain := .Values.domain | default "platform" -}}
{{- $component := .Values.component | required "component is required" -}}
{{- $environment := .Values.environment | default "dev" -}}
{{- $version := .Values.version | default "v1" -}}
{{- printf "urn:axiom:%s:%s:env:%s:%s" $domain $component $environment $version -}}
{{- end -}}

{{/*
Generate required labels per canonical governance
*/}}
{{- define "canonical.labels" -}}
environment: {{ .Values.environment | default "dev" }}
tenant: {{ .Values.tenant | default "platform" }}
app.kubernetes.io/name: {{ .Values.component }}
app.kubernetes.io/managed-by: {{ .Values.managedBy | default "Helm" }}
{{- if .Values.appVersion }}
app.kubernetes.io/version: {{ .Values.appVersion | quote }}
{{- end }}
{{- if .Values.appComponent }}
app.kubernetes.io/component: {{ .Values.appComponent }}
{{- end }}
{{- if .Values.partOf }}
app.kubernetes.io/part-of: {{ .Values.partOf }}
{{- end }}
{{- end -}}

{{/*
Generate selector labels (subset of all labels, stable across versions)
*/}}
{{- define "canonical.selectorLabels" -}}
app.kubernetes.io/name: {{ .Values.component }}
{{- if .Values.appComponent }}
app.kubernetes.io/component: {{ .Values.appComponent }}
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
{{- if .Values.description }}
axiom.io/description: {{ .Values.description | quote }}
{{- end }}
{{- end -}}

{{/*
Validate naming pattern
Ensures name matches: ^(?!.*--)(team|tenant|dev|test|staging|prod|learn|sandbox)-[a-z0-9]+(?:-[a-z0-9]+)*$
*/}}
{{- define "canonical.validate" -}}
{{- $name := include "canonical.name" . -}}
{{- $pattern := "^(?!.*--)(team|tenant|dev|test|staging|prod|learn|sandbox)-[a-z0-9]+(?:-[a-z0-9]+)*$" -}}
{{- if not (regexMatch $pattern $name) -}}
{{- fail (printf "Name '%s' does not match canonical naming pattern. Expected: {env}-{component}-{suffix}" $name) -}}
{{- end -}}
{{- if gt (len $name) 63 -}}
{{- fail (printf "Name '%s' exceeds maximum length of 63 characters" $name) -}}
{{- end -}}
{{- if contains "--" $name -}}
{{- fail (printf "Name '%s' contains forbidden consecutive hyphens '--'" $name) -}}
{{- end -}}
{{- end -}}

{{/*
Generate full qualified app name
*/}}
{{- define "canonical.fullname" -}}
{{- include "canonical.name" . -}}
{{- end -}}

{{/*
Chart name and version
*/}}
{{- define "canonical.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Validate required values
*/}}
{{- define "canonical.validateValues" -}}
{{- if not .Values.component -}}
{{- fail "component is required" -}}
{{- end -}}
{{- $allowedEnvs := list "dev" "test" "staging" "prod" "learn" "sandbox" -}}
{{- $env := .Values.environment | default "dev" -}}
{{- if not (has $env $allowedEnvs) -}}
{{- fail (printf "Invalid environment '%s'. Allowed: %s" $env (join ", " $allowedEnvs)) -}}
{{- end -}}
{{- end -}}

{{/*
Generate namespace with canonical naming
*/}}
{{- define "canonical.namespace" -}}
{{- .Values.namespace | default (include "canonical.name" .) -}}
{{- end -}}

{{/*
Generate service account name
*/}}
{{- define "canonical.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (printf "%s-sa" (include "canonical.name" .)) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}
