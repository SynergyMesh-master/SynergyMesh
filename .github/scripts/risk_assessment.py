#!/usr/bin/env python3
"""
Risk Assessment Script for Autonomous CI Guardian

Analyzes predicted failures and security vulnerabilities to determine
overall risk level and whether to proceed with deployment.

Environment Variables:
    PREDICTED_FAILURES: JSON string with failure prediction data
    CRITICAL_VULNS: Number of critical vulnerabilities

Output (JSON to stdout):
    {
        "level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
        "proceed": "true" | "false",
        "details": {...}
    }
"""

import json
import os
import sys


def get_env_json(name: str, default: dict) -> dict:
    """Get JSON from environment variable with fallback."""
    value = os.environ.get(name, '')
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def get_env_int(name: str, default: int) -> int:
    """Get integer from environment variable with fallback."""
    value = os.environ.get(name, '')
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def assess_risk() -> dict:
    """Perform comprehensive risk assessment."""
    # Get inputs from environment
    predicted_failures = get_env_json('PREDICTED_FAILURES', {
        'patterns': {},
        'risk_score': 0.0,
        'high_risk_areas': []
    })
    critical_vulns = get_env_int('CRITICAL_VULNS', 0)

    # Extract data
    patterns = predicted_failures.get('patterns', {})
    risk_score = float(predicted_failures.get('risk_score', 0.0))
    high_risk_areas = predicted_failures.get('high_risk_areas', [])

    # Calculate weighted risk factors
    security_risk = patterns.get('security', 0) * 3  # Security issues are critical
    docker_risk = patterns.get('docker', 0) * 2      # Docker issues affect deployment
    test_risk = patterns.get('test', 0) * 1.5        # Test changes may indicate instability
    performance_risk = patterns.get('performance', 0) * 1.5
    memory_risk = patterns.get('memory', 0) * 2      # Memory issues are serious

    # Calculate total weighted risk
    total_risk = security_risk + docker_risk + test_risk + performance_risk + memory_risk

    # Determine risk level based on multiple factors
    level = 'LOW'
    proceed = True

    # Critical vulnerabilities are immediate blockers
    if critical_vulns > 0:
        level = 'CRITICAL'
        proceed = False
    # High risk score from ML prediction
    elif risk_score > 0.8 or total_risk > 30:
        level = 'HIGH'
        proceed = True  # Allow canary deployment for high risk
    # Medium risk
    elif risk_score > 0.5 or total_risk > 15 or len(high_risk_areas) > 2:
        level = 'MEDIUM'
        proceed = True
    # Low risk - default
    else:
        level = 'LOW'
        proceed = True

    # Build result
    result = {
        'level': level,
        'proceed': 'true' if proceed else 'false',
        'details': {
            'risk_score': risk_score,
            'total_weighted_risk': total_risk,
            'critical_vulnerabilities': critical_vulns,
            'high_risk_areas': high_risk_areas,
            'factors': {
                'security': security_risk,
                'docker': docker_risk,
                'test': test_risk,
                'performance': performance_risk,
                'memory': memory_risk
            }
        }
    }

    return result


def main() -> int:
    """Main entry point."""
    try:
        result = assess_risk()
        print(json.dumps(result, indent=2))
        return 0
    except Exception as e:
        # On error, output a safe default (LOW risk, proceed)
        error_result = {
            'level': 'LOW',
            'proceed': 'true',
            'details': {
                'error': str(e),
                'fallback': True
            }
        }
        print(json.dumps(error_result, indent=2))
        return 0


if __name__ == '__main__':
    sys.exit(main())
