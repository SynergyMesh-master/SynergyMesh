#!/usr/bin/env python3
"""
Path Validator
Validates file paths, directory paths, and path policies against specifications.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any

def load_paths_spec() -> Dict[str, Any]:
    """Load paths specification from baseline."""
    spec_path = Path(__file__).parent.parent.parent / "specifications" / "root.specs.paths.yaml"
    with open(spec_path, 'r') as f:
        return yaml.safe_load(f)

def validate_path(path: str, check_write_policy: bool = True) -> Tuple[bool, List[str], List[str]]:
    """
    Validate path against specifications.
    
    Args:
        path: The path to validate
        check_write_policy: Whether to check write policy
    
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    spec = load_paths_spec()
    errors = []
    warnings = []
    
    # Validate path format
    format_errors, format_warnings = validate_path_format(path, spec)
    errors.extend(format_errors)
    warnings.extend(format_warnings)
    
    # Check root structure rules
    root_errors, root_warnings = check_root_structure(path, spec)
    errors.extend(root_errors)
    warnings.extend(root_warnings)
    
    # Check write policy if requested
    if check_write_policy and not errors:
        policy_errors, policy_warnings = check_path_write_policy(path, spec)
        errors.extend(policy_errors)
        warnings.extend(policy_warnings)
    
    is_valid = len(errors) == 0
    return is_valid, errors, warnings

def validate_path_format(path: str, spec: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Validate path format."""
    errors = []
    warnings = []
    
    # Get validation rules
    validation_rules = spec['spec']['validation']['rules']
    
    # Check valid path format
    for rule in validation_rules:
        if rule['name'] == 'valid-path-format':
            pattern = rule['pattern']
            if not re.match(pattern, path):
                errors.append(f"Path '{path}' must match pattern: {pattern}")
    
    # Check for spaces
    if ' ' in path:
        errors.append(f"Path '{path}' contains spaces")
    
    # Check for uppercase letters
    if any(c.isupper() for c in path):
        warnings.append(f"Path '{path}' contains uppercase letters; use lowercase")
    
    return errors, warnings

def check_root_structure(path: str, spec: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Check if path follows root structure rules."""
    errors = []
    warnings = []
    
    root_structure = spec['spec']['rootStructure']
    
    normalized_path = Path(path).as_posix().lstrip("./")
    # Check if path is in root (no directory prefix)
    if '/' not in normalized_path:
        # This is a root-level file
        allowed_in_root = root_structure['allowedInRoot']
        
        # Check if it's a boot pointer
        if normalized_path in allowed_in_root['bootPointers']:
            return errors, warnings
        
        # Check if it's a git file
        if any(normalized_path.startswith(gf.rstrip('/')) for gf in allowed_in_root['gitFiles']):
            return errors, warnings
        
        # Check if it's a project file
        if normalized_path in allowed_in_root['projectFiles']:
            return errors, warnings
        
        # Check if it's a primary directory
        if normalized_path.rstrip('/') + '/' in allowed_in_root['primaryDirectories']:
            return errors, warnings
        
        # Check if it's an FHS directory
        if '/' + normalized_path.rstrip('/') + '/' in allowed_in_root['fhsDirectories']:
            return errors, warnings
        
        # If none of the above, it's prohibited in root
        prohibited = root_structure['prohibitedInRoot']
        for item in prohibited:
            if 'governance' in item.lower() and ('config' in normalized_path or 'spec' in normalized_path or 'registry' in normalized_path):
                errors.append(f"Governance file '{path}' must be in controlplane/baseline/")
            elif 'source code' in item.lower() and normalized_path.endswith('.py'):
                errors.append(f"Source code '{path}' must be in workspace/src/")
            elif 'configuration' in item.lower() and ('config' in normalized_path or normalized_path.endswith('.yaml')):
                errors.append(f"Configuration file '{path}' must be in workspace/config/ or controlplane/baseline/config/")
    
    return errors, warnings

def check_path_write_policy(path: str, spec: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Check write policy for path."""
    errors = []
    warnings = []
    
    write_policy = spec['spec']['writePolicy']
    
    # Check if path is immutable
    for immutable_path in write_policy['immutable']['paths']:
        if match_path_pattern(path, immutable_path):
            warnings.append(f"Path '{path}' is immutable and cannot be modified")
            return errors, warnings
    
    # Check if path is restricted
    for restricted_path in write_policy['restricted']['paths']:
        if match_path_pattern(path, restricted_path):
            warnings.append(f"Path '{path}' is restricted and requires elevated permissions")
            return errors, warnings
    
    # Check if path is writable
    is_writable = False
    for writable_path in write_policy['writable']['paths']:
        if match_path_pattern(path, writable_path):
            is_writable = True
            break
    
    if not is_writable:
        warnings.append(f"Path '{path}' is not in a writable location")
    
    return errors, warnings

def match_path_pattern(path: str, pattern: str) -> bool:
    """Check if path matches pattern (supports ** wildcard)."""
    # Convert pattern to regex
    regex_pattern = pattern.replace('**', '.*').replace('*', '[^/]*')
    regex_pattern = '^' + regex_pattern + '$'
    return bool(re.match(regex_pattern, path))

def validate_controlplane_path(path: str, spec: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Validate path within controlplane directory."""
    errors = []
    warnings = []
    
    if not path.startswith('controlplane/'):
        return errors, warnings
    
    controlplane_structure = spec['spec']['controlplaneStructure']
    
    # Check if in baseline (immutable)
    if path.startswith('controlplane/baseline/'):
        baseline = controlplane_structure['baseline']
        if baseline['writable']:
            errors.append(f"Baseline path '{path}' should be immutable")
        
        # Check subdirectories
        valid_subdirs = ['config', 'specifications', 'registries', 'validation', 'integration', 'documentation']
        path_parts = path.split('/')
        if len(path_parts) > 2:
            subdir = path_parts[2]
            if subdir not in valid_subdirs:
                warnings.append(f"Subdirectory '{subdir}' not in standard baseline structure")
    
    # Check if in overlay (writable)
    elif path.startswith('controlplane/overlay/'):
        overlay = controlplane_structure['overlay']
        if not overlay['writable']:
            errors.append(f"Overlay path '{path}' should be writable")
    
    # Check if in active (read-only)
    elif path.startswith('controlplane/active/'):
        active = controlplane_structure['active']
        if active['writable']:
            errors.append(f"Active path '{path}' should be read-only")
    
    return errors, warnings

def validate_workspace_path(path: str, spec: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Validate path within workspace directory."""
    errors = []
    warnings = []
    
    if not path.startswith('workspace/'):
        return errors, warnings
    
    workspace_structure = spec['spec']['workspaceStructure']
    
    # Check if in valid subdirectory
    valid_subdirs = list(workspace_structure['subdirectories'].keys())
    path_parts = path.split('/')
    if len(path_parts) > 1:
        subdir = path_parts[1]
        if subdir not in valid_subdirs:
            warnings.append(f"Subdirectory '{subdir}' not in standard workspace structure")
    
    return errors, warnings

def get_path_write_policy(path: str) -> str:
    """Get write policy for a path."""
    try:
        spec = load_paths_spec()
        write_policy = spec['spec']['writePolicy']
        
        # Check immutable
        for immutable_path in write_policy['immutable']['paths']:
            if match_path_pattern(path, immutable_path):
                return "immutable"
        
        # Check restricted
        for restricted_path in write_policy['restricted']['paths']:
            if match_path_pattern(path, restricted_path):
                return "restricted"
        
        # Check writable
        for writable_path in write_policy['writable']['paths']:
            if match_path_pattern(path, writable_path):
                return "writable"
        
        return "unknown"
    except Exception:
        return "unknown"

if __name__ == "__main__":
    # Test cases
    test_cases = [
        "controlplane/baseline/config/root.config.yaml",
        "controlplane/baseline/specifications/root.specs.naming.yaml",
        "controlplane/baseline/validation/validate-root-specs.py",
        "controlplane/overlay/evidence/validation-2024-01-01.json",
        "workspace/src/core/validator.py",
        "workspace/src/tooling/validate.py",
        "workspace/chatops/commands/autofix.yaml",
        "workspace/runtime/logs/app.log",
        "/var/log/system.log",
        "/tmp/temp-file.txt",
        "root.governance.yaml",  # should be in controlplane/baseline/config/
        "validate.py",  # should be in workspace/src/tooling/
        "src/main.py",  # should be in workspace/src/
    ]
    
    print("=== Path Validation Test ===\n")
    for path in test_cases:
        is_valid, errors, warnings = validate_path(path, check_write_policy=True)
        status = "✓ PASS" if is_valid else "✗ FAIL"
        policy = get_path_write_policy(path)
        print(f"{status} | Path: {path} (policy: {policy})")
        if errors:
            for error in errors:
                print(f"  ERROR: {error}")
        if warnings:
            for warning in warnings:
                print(f"  WARNING: {warning}")
        print()
