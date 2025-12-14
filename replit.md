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

### Directory Structure

```
apps/
  web/                         # React frontend (esbuild + Tailwind) - UI 組件唯一來源

core/
  modules/                     # Python AI/automation modules - 模組唯一來源
    ai_constitution/           # AI 憲法與護欄
    ci_error_handler/          # CI 錯誤處理
    cloud_agent_delegation/    # 雲端代理委派
    drone_system/              # 無人機系統
    execution_architecture/    # 執行架構
    execution_engine/          # 執行引擎
    main_system/               # 主系統
    mcp_servers_enhanced/      # MCP 服務器增強
    mind_matrix/               # 心智矩陣
    monitoring_system/         # 監控系統
    tech_stack/                # 技術棧
    training_system/           # 訓練系統
    virtual_experts/           # 虛擬專家
    yaml_module_system/        # YAML 模組系統
  advisory-database/           # 諮詢資料庫
  contract_service/            # 合約服務
  hlp_executor/                # HLP 執行器
  island_ai_runtime/           # Island AI 運行時
  project_factory/             # 專案工廠
  safety_mechanisms/           # 安全機制
  slsa_provenance/             # SLSA 來源驗證
  unified_integration/         # 統一整合
  validators/                  # 驗證器

governance/                    # 治理中心 (00-80 維度)
  00-governance-mapping-matrix.yaml
  25-principles/               # 命名空間慣例
  29-docs/                     # 治理文檔
  30-agents/                   # 代理治理
  39-automation/               # 自動化引擎

services/
  agents/                      # 代理服務
  mcp/                         # MCP 服務
  watchdog/                    # 看門狗服務

automation/                    # 自動化管線
infrastructure/                # Kubernetes 與監控
mcp-servers/                   # MCP 服務器實作
island-ai/                     # Island AI 組件
tools/                         # 開發工具
tests/                         # 測試套件
```

### Key Principles

1. **Python 模組單一來源**: 所有 Python 模組位於 `core/modules/`
2. **UI 組件單一來源**: 所有 UI 組件位於 `apps/web/src/components/`
3. **Import 路徑規範**: 使用 `from core.modules.X import Y` 格式

### Module Registry

```python
from core.modules import get_module_info, list_modules

# 列出所有可用模組
modules = list_modules()

# 取得模組資訊
info = get_module_info('mind_matrix')
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

- **Frontend**: `cd apps/web && npm run dev` - React development server on port 5000

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

## Notes

- Governance-centric architecture with 80+ dimensions
- Module auto-selection via capability-based registry
- Namespace format: `governance.[dimension-id].[module-name]`
- Frontend binds to 0.0.0.0:5000 for Replit compatibility
