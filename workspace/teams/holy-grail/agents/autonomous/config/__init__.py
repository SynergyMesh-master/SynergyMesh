"""
Agent Configuration Module
代理配置模組

Contains configuration management for the agent system.
"""

import importlib.util
import sys
from pathlib import Path

# Import AgentConfig from kebab-case filename
def _import_agent_config():
    """Import AgentConfig from agent-config.py"""
    module_path = Path(__file__).parent / 'agent-config.py'
    if not module_path.exists():
        return None
    module_name = 'autonomous.agents.config.agent_config'
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    return None

_agent_config_module = _import_agent_config()
if _agent_config_module:
    AgentConfig = _agent_config_module.AgentConfig
else:
    AgentConfig = None

__all__ = [
    'AgentConfig',
]
