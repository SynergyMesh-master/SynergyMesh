"""
SynergyMesh Core Package
========================

Core modules for the SynergyMesh autonomous coordination grid system.

Governance Namespace: governance.core
Reference: governance/00-governance-mapping-matrix.yaml

This package contains modules mapped to governance dimensions:
- modules/: Various functional modules (AI, monitoring, execution, etc.)
  - mind_matrix → governance.30-agents.mind_matrix
  - training_system → governance.73-learning.training_system
  - virtual_experts → governance.30-agents.virtual_experts
  - ci_error_handler → governance.40-self-healing.ci_error_handler
  - cloud_agent_delegation → governance.30-agents.cloud_agent_delegation
  - main_system → governance.39-automation.main_system
  - mcp_servers_enhanced → governance.11-tools-systems.mcp_servers_enhanced
  - execution_architecture → governance.01-architecture.execution_architecture
  - execution_engine → governance.41-orchestration.execution_engine
  - monitoring_system → governance.50-monitoring.monitoring_system

- safety_mechanisms/ → governance.06-security.safety_mechanisms
  Safety and resilience components for security controls

- slsa_provenance/ → governance.62-provenance.slsa_provenance
  SLSA supply chain security and build attestation

- unified_integration/ → governance.41-orchestration.unified_integration
  System integration and orchestration

- ai_constitution/ → governance.10-policy.ai_constitution
  AI governance policies and ethical guidelines

- hlp_executor/ → governance.41-orchestration.hlp_executor
  Hard Logic Plugin async DAG orchestration engine

Namespace Conventions:
- Format: governance.[dimension-id].[module-name].[component]
- Python imports: Replace hyphens with underscores for module names
- Reference: governance/25-principles/namespace-conventions.yaml

Usage:
    from core import modules
    from core import safety_mechanisms
    
    # With governance namespace awareness:
    # from governance.41_orchestration.unified_integration import SystemBootstrap
    # from governance.06_security.safety_mechanisms import CircuitBreaker
"""

__version__ = "1.0.0"
__author__ = "SynergyMesh Team"

__governance_namespace__ = "governance.core"
__governance_reference__ = "governance/00-governance-mapping-matrix.yaml"
