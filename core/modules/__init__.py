"""
Core Modules - Unified Module Management
統一模組管理入口

Governance Namespace Reference: governance/00-governance-mapping-matrix.yaml
Namespace Conventions: governance/25-principles/namespace-conventions.yaml

整合的模組列表 (Integrated Module List):
- mind_matrix: 心智矩陣 (執行系統、多代理超圖) → governance.30-agents.mind_matrix
- training_system: 訓練系統 (知識庫、技能訓練) → governance.73-learning.training_system
- virtual_experts: 虛擬專家 (領域專家、專家團隊) → governance.30-agents.virtual_experts
- ci_error_handler: CI 錯誤處理 (自動修復、狀態追蹤) → governance.40-self-healing.ci_error_handler
- cloud_agent_delegation: 雲端代理委派 (負載均衡、任務路由) → governance.30-agents.cloud_agent_delegation
- main_system: 主系統 (自動化管線、階段編排) → governance.39-automation.main_system
- mcp_servers_enhanced: 增強型 MCP 服務器 → governance.11-tools-systems.mcp_servers_enhanced
- tech_stack: 技術棧 (框架整合、多代理協調) → governance.11-tools-systems.tech_stack
- ai_constitution: AI 憲法 (基本法則、護欄) → governance.10-policy.ai_constitution
- execution_architecture: 執行架構 (代理編排、工具系統) → governance.01-architecture.execution_architecture
- monitoring_system: 監控系統 (自動診斷、智能監控) → governance.50-monitoring.monitoring_system
- yaml_module_system: YAML 模組系統 → governance.34-config.yaml_module_system
- execution_engine: 執行引擎 → governance.41-orchestration.execution_engine
"""

from typing import Any

__governance_namespace__ = "governance.core.modules"
__governance_reference__ = "governance/00-governance-mapping-matrix.yaml"

# 模組註冊表 (Module Registry)
# entry_point: Actual Python import path (for runtime)
# canonical_namespace: Governance namespace (for documentation/mapping)
MODULE_REGISTRY: dict[str, dict[str, Any]] = {
    "mind_matrix": {
        "description": "心智矩陣 - 執行系統與多代理超圖",
        "entry_point": "core.modules.mind_matrix.executive_auto",
        "canonical_namespace": "governance.30-agents.mind_matrix",
        "governance_dimension": "30-agents",
        "dependencies": ["training_system", "virtual_experts"],
        "provides": ["CognitiveStack", "ExecutiveSystem", "MultiAgentHypergraph"],
    },
    "training_system": {
        "description": "訓練系統 - 知識庫與技能訓練",
        "entry_point": "core.training_system.knowledge_base",
        "canonical_namespace": "governance.73-learning.training_system",
        "governance_dimension": "73-learning",
        "dependencies": [],
        "provides": ["KnowledgeTraining", "SkillDevelopment", "KnowledgeBase"],
    },
    "virtual_experts": {
        "description": "虛擬專家 - 領域專家與專家團隊",
        "entry_point": "core.virtual_experts.expert_team",
        "canonical_namespace": "governance.30-agents.virtual_experts",
        "governance_dimension": "30-agents",
        "dependencies": ["training_system"],
        "provides": ["ExpertKnowledge", "DomainAnalysis", "ExpertTeamCoordination"],
    },
    "ci_error_handler": {
        "description": "CI 錯誤處理 - 自動修復與狀態追蹤",
        "entry_point": "core.ci_error_handler.auto_fix_engine",
        "canonical_namespace": "governance.40-self-healing.ci_error_handler",
        "governance_dimension": "40-self-healing",
        "dependencies": ["monitoring_system"],
        "provides": ["ErrorDetection", "AutoRemediation", "StateTracking"],
    },
    "cloud_agent_delegation": {
        "description": "雲端代理委派 - 負載均衡與任務路由",
        "entry_point": "core.cloud_agent_delegation.delegation_manager",
        "canonical_namespace": "governance.30-agents.cloud_agent_delegation",
        "governance_dimension": "30-agents",
        "dependencies": ["execution_architecture"],
        "provides": ["AgentDelegation", "LoadBalancing", "TaskRouting"],
    },
    "main_system": {
        "description": "主系統 - 自動化管線與階段編排",
        "entry_point": "core.main_system.synergymesh_core",
        "canonical_namespace": "governance.39-automation.main_system",
        "governance_dimension": "39-automation",
        "dependencies": ["mind_matrix", "ai_constitution"],
        "provides": ["AutomationPipeline", "PhaseOrchestration", "SystemCoordination"],
    },
    "mcp_servers_enhanced": {
        "description": "增強型 MCP 服務器 - 工具註冊與工作流編排",
        "entry_point": "core.mcp_servers_enhanced.mcp_server_manager",
        "canonical_namespace": "governance.11-tools-systems.mcp_servers_enhanced",
        "governance_dimension": "11-tools-systems",
        "dependencies": ["execution_architecture"],
        "provides": ["MCPProtocol", "ServerCapabilities", "ToolRegistration", "WorkflowOrchestration"],
    },
    "tech_stack": {
        "description": "技術棧 - 框架整合與多代理協調",
        "entry_point": "core.tech_stack.framework_integrations",
        "canonical_namespace": "governance.11-tools-systems.tech_stack",
        "governance_dimension": "11-tools-systems",
        "dependencies": [],
        "provides": ["StackConfiguration", "ToolIntegration", "FrameworkCoordination"],
    },
    "ai_constitution": {
        "description": "AI 憲法 - 基本法則、護欄與策略提示",
        "entry_point": "core.ai_constitution.constitution_engine",
        "canonical_namespace": "governance.10-policy.ai_constitution",
        "governance_dimension": "10-policy",
        "dependencies": [],
        "provides": ["GovernancePolicies", "EthicalGuidelines", "AIGuardrails", "ConstitutionalRules"],
    },
    "execution_architecture": {
        "description": "執行架構 - 代理編排、工具系統與 MCP 整合",
        "entry_point": "core.execution_architecture.agent_orchestration",
        "canonical_namespace": "governance.01-architecture.execution_architecture",
        "governance_dimension": "01-architecture",
        "dependencies": ["tech_stack"],
        "provides": ["FullExecutionPipeline", "AgentOrchestration", "ToolSystemIntegration"],
    },
    "monitoring_system": {
        "description": "監控系統 - 自動診斷、智能監控與異常檢測",
        "entry_point": "core.monitoring_system.observability_platform",
        "canonical_namespace": "governance.50-monitoring.monitoring_system",
        "governance_dimension": "50-monitoring",
        "dependencies": [],
        "provides": ["MetricsCollection", "AlertManagement", "AutoDiagnostics", "AnomalyDetection"],
    },
    "yaml_module_system": {
        "description": "YAML 模組系統 - 配置驅動的模組載入",
        "entry_point": "core.yaml_module_system",
        "canonical_namespace": "governance.34-config.yaml_module_system",
        "governance_dimension": "34-config",
        "dependencies": [],
        "provides": ["YAMLValidation", "SchemaEnforcement", "ConfigDrivenLoading"],
    },
    "execution_engine": {
        "description": "執行引擎 - 任務執行與結果處理",
        "entry_point": "core.execution_engine.execution_engine",
        "canonical_namespace": "governance.41-orchestration.execution_engine",
        "governance_dimension": "41-orchestration",
        "dependencies": ["execution_architecture"],
        "provides": ["ActionExecution", "Rollback", "ResultProcessing"],
    },
}


def get_module_info(module_name: str) -> dict[str, Any] | None:
    """取得模組資訊 (Get module information)"""
    return MODULE_REGISTRY.get(module_name)


def list_modules() -> list[str]:
    """列出所有可用模組 (List all available modules)"""
    return list(MODULE_REGISTRY.keys())


def get_module_dependencies(module_name: str) -> list[str]:
    """取得模組依賴 (Get module dependencies)"""
    info = get_module_info(module_name)
    return info.get("dependencies", []) if info else []


def get_module_namespace(module_name: str) -> str | None:
    """取得模組的治理命名空間 (Get module governance namespace)"""
    info = get_module_info(module_name)
    return info.get("canonical_namespace") if info else None


def get_modules_by_dimension(dimension: str) -> list[str]:
    """依治理維度取得模組列表 (Get modules by governance dimension)"""
    return [
        name for name, info in MODULE_REGISTRY.items()
        if info.get("governance_dimension") == dimension
    ]


__all__ = [
    "MODULE_REGISTRY",
    "get_module_info",
    "list_modules",
    "get_module_dependencies",
    "get_module_namespace",
    "get_modules_by_dimension",
]
