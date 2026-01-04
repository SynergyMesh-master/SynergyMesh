#!/usr/bin/env python3
"""
Naming Conventions Validator
Validates file names, directory names, identifiers, versions, and URNs against naming specifications.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any

_compiled_patterns: Dict[str, re.Pattern] = {}

def load_naming_spec() -> Dict[str, Any]:
    """Load naming specification from baseline."""
    spec_path = Path(__file__).parent.parent.parent / "specifications" / "root.specs.naming.yaml"
    with open(spec_path, 'r') as f:
        return yaml.safe_load(f)

def _get_compiled_pattern(pattern: str) -> re.Pattern:
    """Return a cached compiled regex pattern."""
    if pattern not in _compiled_patterns:
        _compiled_patterns[pattern] = re.compile(pattern)
    return _compiled_patterns[pattern]

def validate_naming(target: str, target_type: str) -> Tuple[bool, List[str], List[str]]:
    """
    Validate naming conventions.
    
    Args:
        target: The name to validate (file, directory, identifier, etc.)
        target_type: Type of target ('file', 'directory', 'identifier', 'version', 'urn')
    
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    spec = load_naming_spec()
    errors = []
    warnings = []
    
    if target_type == 'file':
        errors, warnings = validate_file_name(target, spec)
    elif target_type == 'directory':
        errors, warnings = validate_directory_name(target, spec)
    elif target_type == 'identifier':
        errors, warnings = validate_identifier(target, spec)
    elif target_type == 'version':
        errors, warnings = validate_version(target, spec)
    elif target_type == 'urn':
        errors, warnings = validate_urn_format(target, spec)
    else:
        errors.append(f"Unknown target type: {target_type}")
    
    is_valid = len(errors) == 0
    return is_valid, errors, warnings

def validate_file_name(filename: str, spec: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Validate file name against naming conventions."""
    errors = []
    warnings = []
    
    # Get validation rules
    rules = spec['spec']['validation']['rules']
    file_conventions = spec['spec'].get('conventions', {}).get('files', {})
    
    # Allow root-prefixed files that follow the documented root pattern (e.g., root.config.yaml)
    root_pattern = file_conventions.get('root', {}).get('pattern')
    root_match = False
    if root_pattern:
        try:
            compiled_root = _get_compiled_pattern(root_pattern)
            if compiled_root.match(filename):
                root_match = True
        except re.error as exc:
            errors.append(f"Invalid root pattern '{root_pattern}' for '{filename}': {exc}")
    
    # Check for double extensions
    if filename.count('.') > 1 and not root_match:
        errors.append(f"File '{filename}' has double extension (rule: no-double-extensions)")
    
    # Check for lowercase only
    if not re.match(r'^[a-z0-9.-]+$', filename):
        errors.append(f"File '{filename}' must use lowercase letters, numbers, dots, hyphens only (rule: lowercase-only)")
    
    # Check for spaces
    if ' ' in filename:
        errors.append(f"File '{filename}' contains spaces (rule: no-spaces)")
    
    # Check for underscores (warning)
    if '_' in filename:
        warnings.append(f"File '{filename}' contains underscores; use hyphens instead (rule: no-underscores)")
    
    # Check kebab-case format (excluding extension)
    name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
    if not root_match and not re.match(r'^[a-z][a-z0-9-]*$', name_without_ext):
        errors.append(f"File name '{name_without_ext}' must follow kebab-case format (rule: kebab-case-format)")
    
    # Check for consecutive hyphens
    if '--' in filename:
        errors.append(f"File '{filename}' contains consecutive hyphens (rule: no-consecutive-hyphens)")
    
    # Check for leading/trailing hyphens
    if name_without_ext.startswith('-') or name_without_ext.endswith('-'):
        errors.append(f"File name '{name_without_ext}' cannot start or end with hyphen (rule: no-leading-trailing-hyphens)")
    
    return errors, warnings

def validate_directory_name(dirname: str, spec: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Validate directory name against naming conventions."""
    errors = []
    warnings = []
    
    # Check for lowercase only
    if not re.match(r'^[a-z0-9-]+$', dirname):
        errors.append(f"Directory '{dirname}' must use lowercase letters, numbers, hyphens only")
    
    # Check for spaces
    if ' ' in dirname:
        errors.append(f"Directory '{dirname}' contains spaces")
    
    # Check for underscores (warning)
    if '_' in dirname:
        warnings.append(f"Directory '{dirname}' contains underscores; use hyphens instead")
    
    # Check kebab-case format
    if not re.match(r'^[a-z][a-z0-9-]*$', dirname):
        errors.append(f"Directory '{dirname}' must follow kebab-case format")
    
    # Check for consecutive hyphens
    if '--' in dirname:
        errors.append(f"Directory '{dirname}' contains consecutive hyphens")
    
    # Check for leading/trailing hyphens
    if dirname.startswith('-') or dirname.endswith('-'):
        errors.append(f"Directory '{dirname}' cannot start or end with hyphen")
    
    # Check if it looks like a file extension
    if '.' in dirname:
        warnings.append(f"Directory '{dirname}' contains dot; avoid file extension-like names")
    
    return errors, warnings

def validate_identifier(identifier: str, spec: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Validate identifier against naming conventions."""
    errors = []
    warnings = []
    
    # Get identifier conventions
    id_spec = spec['spec']['conventions']['identifiers']
    pattern = id_spec['pattern']
    min_length = id_spec['minLength']
    max_length = id_spec['maxLength']
    
    # Check pattern
    if not re.match(pattern, identifier):
        errors.append(f"Identifier '{identifier}' must match pattern: {pattern}")
    
    # Check length
    if len(identifier) < min_length:
        errors.append(f"Identifier '{identifier}' is too short (minimum: {min_length})")
    
    if len(identifier) > max_length:
        errors.append(f"Identifier '{identifier}' is too long (maximum: {max_length})")
    
    return errors, warnings

def validate_version(version: str, spec: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Validate version against naming conventions."""
    errors = []
    warnings = []
    
    # Get version conventions
    version_spec = spec['spec']['conventions']['versions']
    pattern = version_spec['pattern']
    
    # Check pattern
    if not re.match(pattern, version):
        errors.append(f"Version '{version}' must match pattern: {pattern} (e.g., v1.0.0)")
    
    # Check for 'v' prefix
    if not version.startswith('v'):
        errors.append(f"Version '{version}' must start with 'v' prefix")
    
    # Check for three components
    if version.startswith('v'):
        version_parts = version[1:].split('.')
        if len(version_parts) != 3:
            errors.append(f"Version '{version}' must have three components: v{{major}}.{{minor}}.{{patch}}")
        else:
            # Check for leading zeros
            for part in version_parts:
                if len(part) > 1 and part.startswith('0'):
                    errors.append(f"Version '{version}' contains leading zeros")
                    break
    
    return errors, warnings

def validate_urn_format(urn: str, spec: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Validate URN format against naming conventions."""
    errors = []
    warnings = []
    
    # Get URN conventions
    urn_spec = spec['spec']['conventions']['urns']
    pattern = urn_spec['pattern']
    
    # Check pattern
    if not re.match(pattern, urn):
        errors.append(f"URN '{urn}' must match pattern: {pattern}")
    
    # Check scheme
    if not urn.startswith('urn:'):
        errors.append(f"URN '{urn}' must start with 'urn:' scheme")
        return errors, warnings
    
    # Parse URN components
    parts = urn.split(':')
    if len(parts) < 4:
        errors.append(f"URN '{urn}' must have at least 4 components: urn:namespace:type:identifier")
        return errors, warnings
    
    scheme, namespace, resource_type, identifier = parts[0], parts[1], parts[2], parts[3]
    version = parts[4] if len(parts) > 4 else None
    
    # Validate namespace (kebab-case)
    if not re.match(r'^[a-z][a-z0-9-]*$', namespace):
        errors.append(f"URN namespace '{namespace}' must follow kebab-case format")
    
    # Validate resource type (kebab-case)
    if not re.match(r'^[a-z][a-z0-9-]*$', resource_type):
        errors.append(f"URN resource type '{resource_type}' must follow kebab-case format")
    
    # Check if resource type is allowed
    allowed_types = urn_spec['types']
    if resource_type not in allowed_types:
        errors.append(f"URN resource type '{resource_type}' not in allowed types: {allowed_types}")
    
    # Validate identifier (kebab-case)
    if not re.match(r'^[a-z0-9][a-z0-9-]*$', identifier):
        errors.append(f"URN identifier '{identifier}' must follow kebab-case format")
    
    # Validate version if present
    if version:
        version_errors, version_warnings = validate_version(version, spec)
        errors.extend(version_errors)
        warnings.extend(version_warnings)
    
    return errors, warnings

def validate_reserved_names(name: str, spec: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Check if name is reserved."""
    errors = []
    warnings = []
    
    reserved = spec['spec']['reserved']
    
    # Check reserved keywords
    if name in reserved.get('keywords', []):
        errors.append(f"Name '{name}' is a reserved keyword")
    
    # Check reserved prefixes
    for prefix in reserved.get('prefixes', []):
        if name.startswith(prefix):
            errors.append(f"Name '{name}' uses reserved prefix '{prefix}'")
    
    return errors, warnings

if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("root.config.yaml", "file"),
        ("validate-root-specs.py", "file"),
        ("controlplane", "directory"),
        ("workspace", "directory"),
        ("core-validator", "identifier"),
        ("v1.0.0", "version"),
        ("urn:machinenativeops:module:core-validator:v1.0.0", "urn"),
    ]
    
    print("=== Naming Validation Test ===\n")
    for target, target_type in test_cases:
        is_valid, errors, warnings = validate_naming(target, target_type)
        status = "✓ PASS" if is_valid else "✗ FAIL"
        print(f"{status} | {target_type}: {target}")
        if errors:
            for error in errors:
                print(f"  ERROR: {error}")
        if warnings:
            for warning in warnings:
                print(f"  WARNING: {warning}")
        print()
