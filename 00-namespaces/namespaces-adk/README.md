# Namespace-ADK: Machine-Native AI Agent Runtime Layer

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/MachineNativeOps/namespace-adk)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-orange.svg)](LICENSE)

A comprehensive, production-ready agent runtime framework that orchestrates MCP tools, manages agent memory and context, enforces runtime governance, and supports multi-step, auditable workflows.

## 🎯 Overview

Namespace-ADK provides the foundational infrastructure for building secure, scalable, and governable AI agents. It implements best practices from leading agent frameworks while adding robust governance, observability, and security capabilities.

### Key Features

- **🔌 MCP Integration**: Full Model Context Protocol support for tool discovery and invocation
- **🧠 Memory Management**: Unified short-term (context window) and long-term (persistent) memory
- **🎭 Workflow Orchestration**: Multi-step, hierarchical, and parallel workflows with error handling
- **🛡️ Governance**: MI9 runtime governance and ARI index for autonomous agent oversight
- **📊 Observability**: Structured logging, distributed tracing, and metrics collection
- **🔐 Security**: Authentication, authorization, PII filtering, and secure sandboxing
- **🔌 Plugin System**: Extensible architecture for tools, memory, workflows, and SDK integrations
- **🤝 A2A Communication**: Agent-to-agent protocol for multi-agent systems

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/MachineNativeOps/namespace-adk.git
cd namespace-adk

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## 🚀 Quick Start

### Basic Agent Runtime

```python
import asyncio
from adk import AgentRuntime, AgentConfig

async def main():
    # Create agent configuration
    config = AgentConfig(
        name="my-agent",
        environment="production",
        enable_tracing=True,
        enable_metrics=True
    )
    
    # Initialize runtime
    runtime = AgentRuntime(config)
    await runtime.initialize()
    
    # Handle a request
    response = await runtime.handle_request({
        "action": "execute_workflow",
        "workflow_id": "example_workflow",
        "parameters": {"input": "Hello, World!"}
    })
    
    print(response)
    
    # Shutdown
    await runtime.shutdown()

asyncio.run(main())
```

### Using MCP Tools

```python
from adk.mcp import MCPClient, MCPServerConfig
from adk.mcp import ToolRouter

# Create MCP client
config = MCPServerConfig(
    url="http://localhost:8000",
    transport=MCPTransportType.HTTP
)
client = MCPClient(config)
await client.connect()

# List available tools
tools = await client.list_tools()
print(f"Available tools: {[tool.name for tool in tools]}")

# Invoke a tool
result = await client.invoke_tool(
    tool_name="search",
    arguments={"query": "Python"}
)
print(f"Result: {result}")
```

### Workflow Orchestration

```python
from adk.core import WorkflowOrchestrator, WorkflowDefinition, WorkflowStep
from adk.core import StepType

# Create a workflow
workflow = WorkflowDefinition(
    name="data_processing",
    steps=[
        WorkflowStep(
            name="fetch_data",
            type=StepType.TOOL_CALL,
            parameters={"tool": "fetch", "args": {"source": "api"}}
        ),
        WorkflowStep(
            name="process_data",
            type=StepType.TASK,
            dependencies=["fetch_data"]
        ),
        WorkflowStep(
            name="save_results",
            type=StepType.TOOL_CALL,
            dependencies=["process_data"],
            parameters={"tool": "save", "args": {"dest": "db"}}
        )
    ]
)

# Register and execute
orchestrator = WorkflowOrchestrator(event_bus, memory_manager, context_manager)
orchestrator.register_workflow(workflow)

execution = await orchestrator.execute_workflow(
    workflow.id,
    context={"input_data": "example"}
)
print(f"Execution status: {execution.state}")
```

## 🏗️ Architecture

### Core Components

```
namespace-adk/
├── adk/
│   ├── core/              # Runtime core (agent lifecycle, workflows, memory)
│   ├── mcp/               # MCP integration (client, router, schemas, A2A)
│   ├── governance/        # Governance (MI9, ARI, conformance, drift)
│   ├── observability/     # Observability (logging, tracing, metrics)
│   ├── security/          # Security (auth, permissioning, PII)
│   ├── plugins/           # Plugin system
│   ├── sdk/               # Platform SDK integrations
│   └── data/              # Data models and schemas
├── config/                # Configuration files
├── examples/              # Usage examples
├── tests/                 # Test suites
└── scripts/               # Utility scripts
```

### Module Overview

#### Core Runtime
- **AgentRuntime**: Main lifecycle manager
- **WorkflowOrchestrator**: Multi-step workflow execution
- **MemoryManager**: Unified memory operations
- **ContextManager**: Hierarchical context management
- **EventBus**: Internal event system
- **ErrorHandler**: Error handling and retry
- **PluginManager**: Plugin discovery and loading
- **Sandbox**: Secure execution environments

#### MCP Integration
- **MCPClient**: MCP protocol client
- **ToolRouter**: Tool routing with load balancing
- **ToolSchemas**: Schema validation and management
- **A2AClient**: Agent-to-agent communication
- **MCPSecurity**: MCP security controls

#### Governance
- **MI9Runtime**: Real-time governance framework
- **ARIIndex**: Agency-Risk Index calculator
- **ConformanceEngine**: Workflow conformance checking
- **DriftDetection**: Behavioral drift detection
- **Containment**: Graduated containment strategies
- **AuditTrail**: Tamper-evident audit logging

#### Observability
- **Logger**: Structured JSON logging
- **Tracer**: Distributed tracing
- **MetricsCollector**: Runtime metrics
- **EventSchemaRegistry**: Event schema definitions

#### Security
- **Authenticator**: User and agent authentication
- **A2AAuthenticator**: Agent-to-agent authentication
- **PermissionManager**: RBAC and ABAC
- **PIIFilter**: PII detection and redaction

## 🔧 Configuration

### Runtime Settings

```yaml
# config/settings.yaml
agent:
  name: "my-agent"
  version: "1.0.0"
  max_concurrent_workflows: 10

observability:
  logging:
    level: "INFO"
  tracing:
    enabled: true
  metrics:
    enabled: true

governance:
  mi9:
    enabled: true
    intervention_level: "monitor"
```

### Governance Policies

```yaml
# config/policies.yaml
containment_policies:
  - policy_id: "auto_escalate"
    trigger:
      event_type: "drift.detected"
      severity: "high"
    action:
      escalate_to: "restrict"
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/test_core.py

# Run with coverage
pytest --cov=adk --cov-report=html
```

## 📚 Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Plugin Development](docs/PLUGINS.md)
- [Governance Guide](docs/GOVERNANCE.md)
- [Security Guide](docs/SECURITY.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linter
flake8 adk/

# Run formatter
black adk/

# Run type checker
mypy adk/
```

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Google ADK](https://deepwiki.com/google/adk-docs/)
- [Amazon Bedrock AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/)
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-sdk)

## 📞 Support

- 📖 [Documentation](docs/)
- 💬 [Discussions](https://github.com/MachineNativeOps/namespace-adk/discussions)
- 🐛 [Issues](https://github.com/MachineNativeOps/namespace-adk/issues)

---

Built with ❤️ by MachineNativeOps