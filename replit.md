# SynergyMesh

Next-generation cloud-native platform for intelligent business automation and
seamless data orchestration.

## Project Overview

SynergyMesh is an autonomous coordination grid system (無人化自主協同網格系統)
that combines AI agents, multi-agent orchestration, and enterprise automation
capabilities with a governance-centric architecture.

## Project Architecture

This is a polyglot monorepo with a **governance-aligned** directory structure.

### Languages & Frameworks

- **TypeScript/JavaScript**: Frontend (React) and tooling
- **Python**: Core AI/ML modules, automation, and backend services
- **Rust**: High-performance runtime components (planned)
- **Go**: Microservices (planned)

### Current Directory Structure (Governance-Aligned)

```
governance/                    # Central governance hub (00-80 dimensions)
  00-governance-mapping-matrix.yaml   # Module-to-dimension mapping
  00-directory-reorganization-plan.yaml
  25-principles/               # Namespace conventions & vocabulary
  29-docs/                     # Governance documentation
  30-agents/                   # Agent governance & skills
    skills/                    # Unified skill manifests (base44, code_analysis, etc.)
  36-modules/                  # Module specifications
  37-behavior-contracts/       # Behavior contracts
  39-automation/               # Automation engines
    registry/                  # Module registry with auto-selection

apps/
  web/                         # React frontend (esbuild + Tailwind)

core/
  modules/                     # Python AI/automation modules (MODULE_REGISTRY)
  unified_integration/         # System orchestration
  safety_mechanisms/           # Safety & resilience
  slsa_provenance/             # SLSA supply chain security
  execution_engine/            # Task execution
  monitoring_system/           # Observability

config/
  governance/                  # Governance-related configs
  platform/                    # Platform & system configs
  operations/                  # CI/CD, monitoring configs
  index.yaml                   # Config-to-dimension mapping

docs/
  reports/                     # Consolidated documentation/reports

mcp-servers/                   # MCP server implementations
island-ai/                     # Island AI components
tools/                         # Development utilities
tests/                         # Test suites
_legacy/                       # Archived legacy files
```

### Key Governance Concepts

- **Dimensions (00-80)**: Governance domains (vision, architecture, security, etc.)
- **Modules**: Functional units mapped to governance dimensions
- **Capabilities**: What modules provide (exported functionality)
- **Contracts**: Behavior specifications for modules
- **Registry**: Auto-selection system for module activation

### Module Auto-Selection

```python
from governance.automation.registry import selector

# Select modules by capability
modules = selector.select_modules_by_capability(['monitoring', 'alerting'])

# Resolve dependencies
deps = selector.resolve_dependencies('mind_matrix')

# Discover all available modules
all_modules = selector.discover_all_modules()
```

### Package Managers

- **npm**: Primary JavaScript package manager (workspaces in package.json)
- **pnpm**: Alternative JS package manager (pnpm-workspace.yaml)
- **pip/uv**: Python dependencies (pyproject.toml)

## Development

### Frontend

```bash
cd apps/web && npm run dev
```

- Runs on port 5000
- Uses esbuild for bundling
- Tailwind CSS for styling

### Python

```bash
pip install -e ".[dev]"
```

## Workflows

- **Frontend**: `cd apps/web && npm run dev` - React development server on port
  5000

## Deployment

The frontend is configured for static deployment:

- Build: `npm run build --workspace apps/web`
- Output: `apps/web/dist/`

## Configuration Files

| File                  | Purpose                           |
| --------------------- | --------------------------------- |
| `package.json`        | npm workspaces configuration      |
| `pnpm-workspace.yaml` | pnpm workspaces (synced with npm) |
| `pyproject.toml`      | Python project configuration      |
| `Cargo.toml`          | Rust workspace (members pending)  |
| `go.work`             | Go workspace (modules pending)    |
| `tsconfig.json`       | TypeScript configuration          |

## Governance References

| Document                                              | Purpose                        |
| ----------------------------------------------------- | ------------------------------ |
| `governance/00-governance-mapping-matrix.yaml`        | Module-to-dimension mapping    |
| `governance/00-directory-reorganization-plan.yaml`    | Directory consolidation plan   |
| `governance/25-principles/namespace-conventions.yaml` | Namespace format standards     |
| `governance/25-principles/vocabulary-glossary.yaml`   | Vocabulary standardization     |
| `governance/29-docs/DEDUPLICATION_REPORT.md`          | Cleanup documentation          |
| `governance/30-agents/skills/manifest.yaml`           | AI skills registry             |
| `governance/39-automation/registry/manifest.yaml`     | Module registry configuration  |

## Notes

- Governance-centric architecture with 80+ dimensions
- Module auto-selection via capability-based registry
- Namespace format: `governance.[dimension-id].[module-name]`
- Frontend binds to 0.0.0.0:5000 for Replit compatibility
