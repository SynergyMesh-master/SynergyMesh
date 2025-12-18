package main

import future.keywords.in

# URN pattern: urn:axiom:{domain}:{component}:env:{environment}:{version}
# Per governance/34-config/naming/canonical-naming-machine-spec.yaml
urn_pattern := "^urn:axiom:[a-z0-9-]+:[a-z0-9-]+:env:(dev|test|staging|prod|learn|sandbox):(v[0-9]+|v[0-9]+\\.[0-9]+\\.[0-9]+)$"

# ==========================================
# URN Format Violations
# ==========================================

# Deny if URN annotation exists but is malformed
deny[msg] {
    input.metadata.annotations["axiom.io/canonical-urn"]
    urn := input.metadata.annotations["axiom.io/canonical-urn"]
    not regex.match(urn_pattern, urn)
    msg := sprintf("❌ Malformed canonical URN: '%v'. Expected format: urn:axiom:{domain}:{component}:env:{environment}:{version}", [urn])
}

# Deny if URN has too many segments
deny[msg] {
    input.metadata.annotations["axiom.io/canonical-urn"]
    urn := input.metadata.annotations["axiom.io/canonical-urn"]
    parts := split(urn, ":")
    count(parts) != 6
    msg := sprintf("❌ URN '%v' has %v segments, expected 6 (urn:axiom:domain:component:env:environment:version)", [urn, count(parts)])
}

# Deny if URN doesn't start with 'urn:axiom:'
deny[msg] {
    input.metadata.annotations["axiom.io/canonical-urn"]
    urn := input.metadata.annotations["axiom.io/canonical-urn"]
    not startswith(urn, "urn:axiom:")
    msg := sprintf("❌ URN '%v' must start with 'urn:axiom:'", [urn])
}

# ==========================================
# URN-Label Consistency Violations
# ==========================================

# Deny if URN environment doesn't match environment label
deny[msg] {
    input.metadata.annotations["axiom.io/canonical-urn"]
    input.metadata.labels.environment
    urn := input.metadata.annotations["axiom.io/canonical-urn"]
    env_label := input.metadata.labels.environment

    # Extract environment from URN (5th segment after splitting)
    urn_parts := split(urn, ":")
    count(urn_parts) == 6
    urn_env := urn_parts[4]  # Should be the environment value after "env:"

    urn_env != env_label
    msg := sprintf("❌ URN environment '%v' does not match environment label '%v' for %v/%v", [urn_env, env_label, input.kind, input.metadata.name])
}

# Deny if URN component doesn't match app.kubernetes.io/name label
deny[msg] {
    input.metadata.annotations["axiom.io/canonical-urn"]
    input.metadata.labels["app.kubernetes.io/name"]
    urn := input.metadata.annotations["axiom.io/canonical-urn"]
    app_name := input.metadata.labels["app.kubernetes.io/name"]

    # Extract component from URN (4th segment)
    urn_parts := split(urn, ":")
    count(urn_parts) == 6
    urn_component := urn_parts[3]

    urn_component != app_name
    msg := sprintf("❌ URN component '%v' does not match app.kubernetes.io/name label '%v' for %v/%v", [urn_component, app_name, input.kind, input.metadata.name])
}

# ==========================================
# Qualifiers Validation
# ==========================================

# Warn if qualifiers annotation format is invalid
warn[msg] {
    input.metadata.annotations["axiom.io/qualifiers"]
    qualifiers := input.metadata.annotations["axiom.io/qualifiers"]

    # Qualifiers should be in format: key1=value1,key2=value2
    not regex.match("^[a-z0-9-]+=.+(,[a-z0-9-]+=.+)*$", qualifiers)
    msg := sprintf("⚠️  Qualifiers annotation has invalid format: '%v'. Expected: key1=value1,key2=value2", [qualifiers])
}

# Warn if qualifiers exceed maximum count (12 per spec)
warn[msg] {
    input.metadata.annotations["axiom.io/qualifiers"]
    qualifiers := input.metadata.annotations["axiom.io/qualifiers"]
    pairs := split(qualifiers, ",")
    count(pairs) > 12
    msg := sprintf("⚠️  Qualifiers count %v exceeds maximum of 12. Consider consolidating.", [count(pairs)])
}

# ==========================================
# Version Format Validation
# ==========================================

# Warn if version doesn't follow semantic versioning
warn[msg] {
    input.metadata.annotations["axiom.io/canonical-urn"]
    urn := input.metadata.annotations["axiom.io/canonical-urn"]
    urn_parts := split(urn, ":")
    count(urn_parts) == 6
    version := urn_parts[5]

    # Check if version is just 'v1' format or full semver
    not regex.match("^v[0-9]+$", version)
    not regex.match("^v[0-9]+\\.[0-9]+\\.[0-9]+$", version)
    msg := sprintf("⚠️  Version '%v' should use format 'v1' or 'v1.2.3' (semantic versioning)", [version])
}
