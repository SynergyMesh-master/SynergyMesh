#!/usr/bin/env python3
"""
Namespace Validator
Validates namespace syntax, hierarchy, boundaries, and registration against specifications.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any

def load_namespace_spec() -> Dict[str, Any]:
    """Load namespace specification from baseline."""
    spec_path = Path(__file__).parent.parent.parent / "specifications" / "root.specs.namespace.yaml"
    with open(spec_path, 'r') as f:
        return yaml.safe_load(f)

def load_namespace_registry() -> Dict[str, Any]:
    """Load namespace registry from baseline."""
    registry_path = Path(__file__).parent.parent.parent / "registries" / "root.registry.namespaces.yaml"
    with open(registry_path, 'r') as f:
        return yaml.safe_load(f)

def validate_namespace(namespace: str, check_registration: bool = True) -> Tuple[bool, List[str], List[str]]:
    """
    Validate namespace against specifications.
    
    Args:
        namespace: The namespace to validate
        check_registration: Whether to check if namespace is registered
    
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    spec = load_namespace_spec()
    errors = []
    warnings = []
    
    # Validate syntax
    syntax_errors, syntax_warnings = validate_namespace_syntax(namespace, spec)
    errors.extend(syntax_errors)
    warnings.extend(syntax_warnings)
    
    # Validate hierarchy
    hierarchy_errors, hierarchy_warnings = validate_namespace_hierarchy(namespace, spec)
    errors.extend(hierarchy_errors)
    warnings.extend(hierarchy_warnings)
    
    # Check reserved namespaces
    reserved_errors, reserved_warnings = check_reserved_namespace(namespace, spec)
    errors.extend(reserved_errors)
    warnings.extend(reserved_warnings)
    
    # Check registration if requested
    if check_registration and not errors:
        reg_errors, reg_warnings = check_namespace_registration(namespace)
        errors.extend(reg_errors)
        warnings.extend(reg_warnings)
    
    is_valid = len(errors) == 0
    return is_valid, errors, warnings

def validate_namespace_syntax(namespace: str, spec: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Validate namespace syntax rules."""
    errors = []
    warnings = []
    
    syntax = spec['spec']['syntax']
    pattern = syntax['pattern']
    min_length = syntax['minLength']
    max_length = syntax['maxLength']
    hierarchy = spec['spec'].get('hierarchy', {})
    separator = hierarchy.get('separator', '.')
    
    # Allow hierarchical namespaces using the configured separator
    hierarchical_pattern = None
    if separator.strip():
        sep_escaped = re.escape(separator)
        hierarchical_pattern = rf"^[a-z][a-z0-9-]*(?:{sep_escaped}[a-z][a-z0-9-]*)*$"
    
    # Check pattern
    effective_pattern = hierarchical_pattern if hierarchical_pattern else pattern
    if not re.match(effective_pattern, namespace):
        errors.append(f"Namespace '{namespace}' must match pattern: {effective_pattern}")
    
    # Check length
    if len(namespace) < min_length:
        errors.append(f"Namespace '{namespace}' is too short (minimum: {min_length})")
    
    if len(namespace) > max_length:
        errors.append(f"Namespace '{namespace}' is too long (maximum: {max_length})")
    
    # Check must start with lowercase letter
    if not namespace[0].islower() or not namespace[0].isalpha():
        errors.append(f"Namespace '{namespace}' must start with lowercase letter")
    
    # Check must end with lowercase letter or number
    if not (namespace[-1].islower() or namespace[-1].isdigit()):
        errors.append(f"Namespace '{namespace}' must end with lowercase letter or number")
    
    # Check for consecutive hyphens
    if '--' in namespace:
        errors.append(f"Namespace '{namespace}' cannot contain consecutive hyphens")
    
    # Check for prohibited characters
    prohibited = syntax['prohibitedCharacters']
    for char_type in prohibited:
        if char_type == "uppercase letters (A-Z)":
            if any(c.isupper() for c in namespace):
                errors.append(f"Namespace '{namespace}' contains uppercase letters")
        elif char_type == "underscores (_)":
            if '_' in namespace:
                errors.append(f"Namespace '{namespace}' contains underscores")
        elif char_type == "dots (.)":
            if '.' in namespace and separator != '.':
                errors.append(f"Namespace '{namespace}' contains dots but separator is '{separator}' (use configured separator)")
        elif char_type == "spaces":
            if ' ' in namespace:
                errors.append(f"Namespace '{namespace}' contains spaces")
    
    return errors, warnings

def validate_namespace_hierarchy(namespace: str, spec: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Validate namespace hierarchy rules."""
    errors = []
    warnings = []
    
    hierarchy = spec['spec']['hierarchy']
    max_depth = hierarchy['maxDepth']
    separator = hierarchy['separator']
    
    # Count depth (number of separators + 1)
    depth = namespace.count(separator) + 1
    
    if depth > max_depth:
        errors.append(f"Namespace '{namespace}' exceeds maximum depth of {max_depth} (current: {depth})")
    
    # Validate each level
    levels = namespace.split(separator)
    for i, level in enumerate(levels):
        level_errors, level_warnings = validate_namespace_level(level, i, hierarchy)
        errors.extend(level_errors)
        warnings.extend(level_warnings)
    
    return errors, warnings

def validate_namespace_level(level: str, level_index: int, hierarchy: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Validate individual namespace level."""
    errors = []
    warnings = []
    
    # Each level must follow namespace syntax
    if not re.match(r'^[a-z][a-z0-9-]*$', level):
        errors.append(f"Namespace level '{level}' must follow pattern: ^[a-z][a-z0-9-]*$")
    
    # Check length constraints
    if len(level) < 2:
        errors.append(f"Namespace level '{level}' is too short (minimum: 2)")
    
    if len(level) > 31:
        errors.append(f"Namespace level '{level}' is too long (maximum: 31)")
    
    return errors, warnings

def check_reserved_namespace(namespace: str, spec: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Check if namespace is reserved."""
    errors = []
    warnings = []
    
    boundaries = spec['spec']['boundaries']
    
    # Check if 'reserved' key exists
    if 'reserved' not in boundaries:
        return errors, warnings
    
    reserved_data = boundaries['reserved']
    if 'namespaces' not in reserved_data:
        return errors, warnings
    
    reserved = reserved_data['namespaces']
    
    if namespace in reserved:
        errors.append(f"Namespace '{namespace}' is reserved and cannot be used")
    
    # Check if starts with reserved prefix
    for reserved_ns in reserved:
        if namespace.startswith(reserved_ns + '.'):
            warnings.append(f"Namespace '{namespace}' uses reserved prefix '{reserved_ns}'")
    
    return errors, warnings

def check_namespace_registration(namespace: str) -> Tuple[List[str], List[str]]:
    """Check if namespace is registered."""
    errors = []
    warnings = []
    
    try:
        registry = load_namespace_registry()
        registered_namespaces = [ns['name'] for ns in registry['spec']['namespaces']]
        
        if namespace not in registered_namespaces:
            errors.append(f"Namespace '{namespace}' is not registered in root.registry.namespaces.yaml")
        else:
            # Find namespace entry
            ns_entry = next((ns for ns in registry['spec']['namespaces'] if ns['name'] == namespace), None)
            if ns_entry:
                # Check status
                if ns_entry.get('status') != 'active':
                    warnings.append(f"Namespace '{namespace}' is registered but not active (status: {ns_entry.get('status')})")
    except FileNotFoundError:
        warnings.append("Namespace registry file not found; skipping registration check")
    except Exception as e:
        warnings.append(f"Error checking namespace registration: {str(e)}")
    
    return errors, warnings

def validate_namespace_boundaries(namespace: str, spec: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Validate namespace boundaries and isolation."""
    errors = []
    warnings = []
    
    boundaries = spec['spec']['boundaries']
    
    # Check visibility
    visibility = boundaries['visibility']
    is_public = re.match(visibility['public']['pattern'], namespace)
    is_internal = re.match(visibility['internal']['pattern'], namespace)
    
    if not is_public and not is_internal:
        warnings.append(f"Namespace '{namespace}' does not match public or internal visibility patterns")
    
    # Check write policy
    write_policy = boundaries['writePolicy']
    
    # Check if immutable
    if namespace in write_policy['immutable']['namespaces']:
        warnings.append(f"Namespace '{namespace}' is immutable and cannot be modified")
    
    # Check if restricted
    if namespace in write_policy['restricted']['namespaces']:
        warnings.append(f"Namespace '{namespace}' is restricted and requires elevated permissions")
    
    return errors, warnings

def get_namespace_info(namespace: str) -> Dict[str, Any]:
    """Get information about a registered namespace."""
    try:
        registry = load_namespace_registry()
        ns_entry = next((ns for ns in registry['spec']['namespaces'] if ns['name'] == namespace), None)
        return ns_entry if ns_entry else {}
    except Exception:
        return {}

if __name__ == "__main__":
    # Test cases
    test_cases = [
        "machinenativeops",
        "machinenativeops.core",
        "chatops",
        "workspace",
        "workspace.src",
        "invalid-Namespace",  # uppercase
        "invalid_namespace",  # underscore
        "root",  # reserved
        "-invalid",  # starts with hyphen
        "a",  # too short
    ]
    
    print("=== Namespace Validation Test ===\n")
    for namespace in test_cases:
        is_valid, errors, warnings = validate_namespace(namespace, check_registration=False)
        status = "✓ PASS" if is_valid else "✗ FAIL"
        print(f"{status} | Namespace: {namespace}")
        if errors:
            for error in errors:
                print(f"  ERROR: {error}")
        if warnings:
            for warning in warnings:
                print(f"  WARNING: {warning}")
        print()
