# =============================================================================
# 99-naming-convention Test Suite
# URN: urn:machinenativeops:governance:test:naming-convention:v1
# =============================================================================

package governance.naming_convention_test

import future.keywords.in
import data.governance.naming_convention

# =============================================================================
# DIRECTORY NAMING TESTS
# =============================================================================

test_valid_directory_kebab_case {
    not naming_convention.deny_directory_naming with input as {
        "type": "directory",
        "name": "my-awesome-module"
    }
}

test_invalid_directory_uppercase {
    count(naming_convention.deny_directory_naming) > 0 with input as {
        "type": "directory",
        "name": "MyAwesomeModule"
    }
}

test_invalid_directory_underscore {
    count(naming_convention.deny_directory_naming) > 0 with input as {
        "type": "directory",
        "name": "my_awesome_module"
    }
}

# =============================================================================
# FILE NAMING TESTS
# =============================================================================

test_valid_file_kebab_case {
    not naming_convention.deny_file_naming with input as {
        "type": "file",
        "name": "my-config.yaml"
    }
}

test_valid_special_file_readme {
    not naming_convention.deny_file_naming with input as {
        "type": "file",
        "name": "README.md"
    }
}

test_invalid_file_pascal_case {
    count(naming_convention.deny_file_naming) > 0 with input as {
        "type": "file",
        "name": "MyConfig.yaml"
    }
}

# =============================================================================
# EXTENSION TESTS
# =============================================================================

test_forbidden_extension_bak {
    count(naming_convention.deny_extension) > 0 with input as {
        "type": "file",
        "name": "config.yaml.bak"
    }
}

test_forbidden_extension_tmp {
    count(naming_convention.deny_extension) > 0 with input as {
        "type": "file",
        "name": "temp.tmp"
    }
}

# =============================================================================
# KEY NAMING TESTS
# =============================================================================

test_valid_yaml_key_snake_case {
    not naming_convention.deny_yaml_key with input as {
        "type": "yaml_key",
        "key": "api_version"
    }
}

test_invalid_yaml_key_camel_case {
    count(naming_convention.deny_yaml_key) > 0 with input as {
        "type": "yaml_key",
        "key": "apiVersion"
    }
}

# =============================================================================
# VALUE NAMING TESTS
# =============================================================================

test_valid_enum_kebab_case {
    not naming_convention.deny_enum_value with input as {
        "type": "enum_value",
        "value": "in-progress"
    }
}

test_invalid_enum_uppercase {
    count(naming_convention.deny_enum_value) > 0 with input as {
        "type": "enum_value",
        "value": "IN_PROGRESS"
    }
}

test_invalid_boolean_yes {
    count(naming_convention.deny_boolean_value) > 0 with input as {
        "type": "boolean_value",
        "value": "yes"
    }
}

test_valid_version_semver {
    not naming_convention.deny_version with input as {
        "type": "version",
        "value": "1.0.0"
    }
}

test_invalid_version_incomplete {
    count(naming_convention.deny_version) > 0 with input as {
        "type": "version",
        "value": "1.0"
    }
}

test_valid_environment_dev {
    not naming_convention.deny_environment with input as {
        "type": "environment",
        "value": "dev"
    }
}

test_invalid_environment_development {
    count(naming_convention.deny_environment) > 0 with input as {
        "type": "environment",
        "value": "development"
    }
}

# =============================================================================
# URN TESTS
# =============================================================================

test_valid_urn_format {
    not naming_convention.deny_urn_format with input as {
        "type": "urn",
        "value": "urn:machinenativeops:governance:naming-convention:v1"
    }
}

test_invalid_urn_uppercase {
    count(naming_convention.deny_urn_format) > 0 with input as {
        "type": "urn",
        "value": "urn:MachineNativeOps:Governance:NamingConvention"
    }
}

test_valid_urn_domain {
    not naming_convention.deny_urn_domain with input as {
        "type": "urn",
        "value": "urn:machinenativeops:governance:test:v1"
    }
}

test_invalid_urn_domain {
    count(naming_convention.deny_urn_domain) > 0 with input as {
        "type": "urn",
        "value": "urn:machinenativeops:unknown:test:v1"
    }
}

# =============================================================================
# URI TESTS
# =============================================================================

test_valid_api_uri {
    not naming_convention.deny_api_uri with input as {
        "type": "api_uri",
        "value": "/api/v1/dimensions/99-naming-convention"
    }
}

test_invalid_api_uri_uppercase {
    count(naming_convention.deny_api_uri) > 0 with input as {
        "type": "api_uri",
        "value": "/API/V1/Dimensions"
    }
}

# =============================================================================
# AGGREGATED TESTS
# =============================================================================

test_all_violations_empty_for_valid_input {
    result := naming_convention.result with input as {
        "type": "directory",
        "name": "valid-directory"
    }
    result.valid == true
    count(result.violations) == 0
}

test_all_violations_not_empty_for_invalid_input {
    result := naming_convention.result with input as {
        "type": "directory",
        "name": "InvalidDirectory"
    }
    result.valid == false
    count(result.violations) > 0
}
