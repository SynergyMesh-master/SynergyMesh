"""
Intelligent Automation Module
智能自動化模組

High-value capabilities extracted from OJ-agent for autonomous systems.
核心商業價值能力，專為自動化系統設計。
"""

__version__ = "1.0.0"
__author__ = "SLASolve Team"

# Handle both package and standalone imports
try:
    from .pipeline_service import pipeline_service, PipelineService
except ImportError:
    # When running standalone (e.g., in tests), use absolute imports
    try:
        from pipeline_service import pipeline_service, PipelineService
    except ImportError:
        # Module not available in this context
        pipeline_service = None
        PipelineService = None

# Agent system imports (kebab-case filenames require importlib)
import importlib.util
import sys
from pathlib import Path

def _import_kebab_module(module_name: str, file_name: str):
    """Import a module with a kebab-case filename"""
    module_path = Path(__file__).parent / file_name
    if not module_path.exists():
        return None
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    return None

# Import base agent components
_base_agent = _import_kebab_module('agents.base_agent', 'base-agent.py')
if _base_agent:
    BaseAgent = _base_agent.BaseAgent
    AgentStatus = _base_agent.AgentStatus
    AgentColors = _base_agent.Colors
else:
    BaseAgent = None
    AgentStatus = None
    AgentColors = None

# Import coordinator agent
_coordinator_agent = _import_kebab_module('agents.coordinator_agent', 'coordinator-agent.py')
CoordinatorAgent = _coordinator_agent.CoordinatorAgent if _coordinator_agent else None

# Import autopilot agent
_autopilot_agent = _import_kebab_module('agents.autopilot_agent', 'autopilot-agent.py')
AutopilotAgent = _autopilot_agent.AutopilotAgent if _autopilot_agent else None

# Import deployment agent
_deployment_agent = _import_kebab_module('agents.deployment_agent', 'deployment-agent.py')
DeploymentAgent = _deployment_agent.DeploymentAgent if _deployment_agent else None

# Import utils
_agent_utils = _import_kebab_module('agents.agent_utils', 'agent-utils.py')
if _agent_utils:
    print_color = _agent_utils.print_color
    print_info = _agent_utils.print_info
    print_success = _agent_utils.print_success
    print_warn = _agent_utils.print_warn
    print_error = _agent_utils.print_error
else:
    print_color = None
    print_info = None
    print_success = None
    print_warn = None
    print_error = None

__all__ = [
    "pipeline_service",
    "PipelineService",
    "BaseAgent",
    "AgentStatus",
    "AgentColors",
    "CoordinatorAgent",
    "AutopilotAgent",
    "DeploymentAgent",
    "print_color",
    "print_info",
    "print_success",
    "print_warn",
    "print_error",
]
