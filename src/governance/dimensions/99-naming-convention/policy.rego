# =============================================================================
# SynergyMesh Governance - 99-naming-convention Policy
# Unified Naming Convention Enforcement via OPA/Rego
# =============================================================================
# URN: urn:machinenativeops:governance:99-naming-convention:v1
# =============================================================================

package governance.naming_convention

import future.keywords.in
import future.keywords.if
import future.keywords.contains

# =============================================================================
# METADATA
# =============================================================================
metadata := {
    "id": "99-naming-convention",
    "name": "統一命名規範治理",
    "version": "1.0.0",
    "urn": "urn:machinenativeops:governance:naming-convention:v1"
}

# =============================================================================
# PATTERNS
# =============================================================================

# kebab-case pattern
kebab_case_pattern := `^[a-z0-9]+(-[a-z0-9]+)*$`

# snake_case pattern
snake_case_pattern := `^[a-z][a-z0-9]*(_[a-z0-9]+)*$`

# camelCase pattern
camel_case_pattern := `^[a-z][a-zA-Z0-9]*$`

# SemVer pattern
semver_pattern := `^v?[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+)?(\+[a-zA-Z0-9]+)?$`

# Canonical URN pattern
canonical_urn_pattern := `^urn:machinenativeops:[a-z0-9-]+:[a-z0-9-]+(:v[0-9]+)?$`

# API URI pattern
api_uri_pattern := `^/api/v[0-9]+/[a-z0-9-]+(/[a-z0-9-]+)*$`

# =============================================================================
# STANDARD ROOT DIRECTORIES
# =============================================================================
standard_root_directories := {
    "src",
    "config",
    "scripts",
    "docs",
    "tests"
}

# =============================================================================
# RESERVED KEYWORDS
# =============================================================================
reserved_keywords := {
    "apiVersion",
    "kind",
    "metadata",
    "spec",
    "status",
    "id",
    "name",
    "version"
}

# =============================================================================
# FORBIDDEN SYNONYM PAIRS
# =============================================================================
forbidden_synonym_pairs := [
    ["infra", "infrastructure"],
    ["config", "configuration"],
    ["script", "scripts"],
    ["doc", "docs"],
    ["test", "tests"]
]

# =============================================================================
# REGISTERED URN DOMAINS
# =============================================================================
registered_urn_domains := {
    "governance",
    "ai",
    "core",
    "autonomous",
    "config",
    "dimension"
}

# =============================================================================
# ENVIRONMENT ABBREVIATIONS
# =============================================================================
environment_abbreviations := {
    "dev",
    "staging",
    "prod",
    "test",
    "learn"
}

# =============================================================================
# FORBIDDEN EXTENSIONS
# =============================================================================
forbidden_extensions := {
    ".bak",
    ".tmp",
    ".old",
    ".orig"
}

# =============================================================================
# SPECIAL UPPERCASE FILES
# =============================================================================
special_uppercase_files := {
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md"
}

# =============================================================================
# VALIDATION RULES
# =============================================================================

# DIR-001: Directory names must use kebab-case
deny_directory_naming contains msg if {
    input.type == "directory"
    not regex.match(kebab_case_pattern, input.name)
    msg := sprintf("DIR-001: Directory '%s' must use kebab-case (lowercase with hyphens)", [input.name])
}

# DIR-002: Root directories must use standard names
deny_root_directory contains msg if {
    input.type == "directory"
    input.is_root == true
    not input.name in standard_root_directories
    msg := sprintf("DIR-002: Root directory '%s' is not a standard name. Use: %v", [input.name, standard_root_directories])
}

# DIR-003: Synonym elimination - check for forbidden pairs
deny_synonym_pair contains msg if {
    input.type == "directory"
    some pair in forbidden_synonym_pairs
    input.name == pair[0]
    msg := sprintf("DIR-003: Directory '%s' conflicts with synonym '%s'. Use only one standard name.", [input.name, pair[1]])
}

# FILE-001: File names must use kebab-case (except special files)
deny_file_naming contains msg if {
    input.type == "file"
    not input.name in special_uppercase_files
    filename := split(input.name, ".")[0]
    not regex.match(kebab_case_pattern, filename)
    msg := sprintf("FILE-001: File '%s' must use kebab-case", [input.name])
}

# EXT-003: Forbidden extensions
deny_extension contains msg if {
    input.type == "file"
    some ext in forbidden_extensions
    endswith(input.name, ext)
    msg := sprintf("EXT-003: Extension '%s' is forbidden in file '%s'", [ext, input.name])
}

# KEY-001: YAML keys must use snake_case
deny_yaml_key contains msg if {
    input.type == "yaml_key"
    not regex.match(snake_case_pattern, input.key)
    not input.key in reserved_keywords
    msg := sprintf("KEY-001: YAML key '%s' must use snake_case", [input.key])
}

# KEY-003: Reserved keywords cannot be custom keys
deny_reserved_keyword contains msg if {
    input.type == "custom_key"
    input.key in reserved_keywords
    msg := sprintf("KEY-003: '%s' is a reserved keyword and cannot be used as custom key", [input.key])
}

# VAL-001: Enum values must use kebab-case
deny_enum_value contains msg if {
    input.type == "enum_value"
    not regex.match(kebab_case_pattern, input.value)
    msg := sprintf("VAL-001: Enum value '%s' must use kebab-case", [input.value])
}

# VAL-002: Boolean values must be canonical
deny_boolean_value contains msg if {
    input.type == "boolean_value"
    forbidden_booleans := {"yes", "no", "on", "off", "1", "0"}
    lower(input.value) in forbidden_booleans
    msg := sprintf("VAL-002: Boolean value '%s' must use 'true' or 'false'", [input.value])
}

# VAL-003: Version must follow SemVer
deny_version contains msg if {
    input.type == "version"
    not regex.match(semver_pattern, input.value)
    msg := sprintf("VAL-003: Version '%s' must follow semantic versioning (e.g., 1.0.0)", [input.value])
}

# VAL-004: Environment must use standard abbreviation
deny_environment contains msg if {
    input.type == "environment"
    not input.value in environment_abbreviations
    msg := sprintf("VAL-004: Environment '%s' must use standard abbreviation: %v", [input.value, environment_abbreviations])
}

# URN-001: URN must follow canonical format
deny_urn_format contains msg if {
    input.type == "urn"
    not regex.match(canonical_urn_pattern, input.value)
    msg := sprintf("URN-001: URN '%s' must follow format 'urn:machinenativeops:{domain}:{resource}:{version}'", [input.value])
}

# URN-002: URN domain must be registered
deny_urn_domain contains msg if {
    input.type == "urn"
    urn_parts := split(input.value, ":")
    count(urn_parts) >= 3
    domain := urn_parts[2]
    not domain in registered_urn_domains
    msg := sprintf("URN-002: URN domain '%s' is not registered. Valid domains: %v", [domain, registered_urn_domains])
}

# URI-001: API URI must follow pattern
deny_api_uri contains msg if {
    input.type == "api_uri"
    not regex.match(api_uri_pattern, input.value)
    msg := sprintf("URI-001: API URI '%s' must follow pattern '/api/v{version}/{resource}'", [input.value])
}

# DEP-003: Circular dependency check
deny_circular_dependency contains msg if {
    input.type == "dependency_graph"
    has_cycle(input.dependencies)
    msg := "DEP-003: Circular dependency detected in dependency graph"
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# Check if dependency graph has cycles (simplified)
has_cycle(deps) if {
    some dep in deps
    reachable(deps, dep.from, dep.to)
}

# Check if target is reachable from source
reachable(deps, source, target) if {
    some dep in deps
    dep.from == source
    dep.to == target
}

reachable(deps, source, target) if {
    some dep in deps
    dep.from == source
    reachable(deps, dep.to, target)
}

# =============================================================================
# AGGREGATED VIOLATIONS
# =============================================================================
all_violations := deny_directory_naming | 
                  deny_root_directory | 
                  deny_synonym_pair |
                  deny_file_naming | 
                  deny_extension |
                  deny_yaml_key |
                  deny_reserved_keyword |
                  deny_enum_value |
                  deny_boolean_value |
                  deny_version |
                  deny_environment |
                  deny_urn_format |
                  deny_urn_domain |
                  deny_api_uri |
                  deny_circular_dependency

# =============================================================================
# MAIN VALIDATION
# =============================================================================
default allow := false

allow if {
    count(all_violations) == 0
}

# Validation result
result := {
    "valid": allow,
    "violations": all_violations,
    "metadata": metadata
}
