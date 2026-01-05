# Workspace Directory

## Overview

This directory contains the main workspace for the MachineNativeOps project. It serves as the primary development environment with all source code, tools, and configurations organized according to the project's governance framework.

## Structure

The workspace is organized into the following key directories:

- **src/**: Source code for all services and components
  - `core/`: Core services including contract service, advisory database
  - `mcp-servers/`: Model Context Protocol server implementations
  - `services/`: Microservices (API gateway, scheduler, etc.)
  - `apps/`: Application frontends
  - `ai/`: AI-related components
  - `governance/`: Governance framework implementation
  - `autonomous/`: Autonomous systems and drone stack

- **tools/**: Development tools and utilities
  - `docs/`: Documentation generation scripts
  - `cli/`: Command-line interface tools
  - `scripts/`: Automation scripts

- **config/**: Configuration files
  - YAML configs, wrangler.toml, etc.

- **docs/**: Documentation
  - Generated docs, knowledge graphs, reports

- **cloudflare/**: Cloudflare Workers and edge functions

- **deploy/**: Deployment configurations and scripts

- **examples/**: Example code and usage demonstrations

- **schemas/**: Schema definitions for validation

- **tests/**: Test suites

## Getting Started

### Installation

From the repository root:

```bash
# Install all dependencies
npm install

# Or use Make
make install
```

### Development

```bash
# Run linting
npm run lint --workspace=workspace

# Run tests
npm run test --workspace=workspace

# Build all packages
npm run build --workspace=workspace

# Start development stack
npm run dev:stack --workspace=workspace
```

### Documentation

```bash
# Generate knowledge graph (from repository root)
make -C workspace all-kg
# Or, if already in workspace directory:
make all-kg

# Lint documentation (from repository root)
npm run docs:lint --workspace=workspace
# Or, if already in workspace directory:
npm run docs:lint
```

## Package Management

This directory contains an npm workspace with multiple packages. The workspace packages are defined in **two places**:

1. **Root-level (`/package.json`)**: Points to actual workspace packages under `workspace/src/` directories
2. **This directory (`workspace/package.json`)**: Contains its own nested workspace definitions

The actual workspace packages (paths relative to repository root) include:

- MCP server implementations (`workspace/src/mcp-servers`)
- Core contract services (`workspace/src/core/contract_service/contracts-L1/contracts`)
- Advisory database (`workspace/src/core/advisory-database`)
- Web applications (`workspace/src/apps/web`)
- AI components (`workspace/src/ai/src/ai`)
- Other components as defined in `/package.json` and `workspace/package.json`

For the authoritative list of all workspace packages, see the root `/package.json` file.
## Guidelines

Please refer to:

- [Root README](../README.md) for project overview
- [Copilot Instructions](../.github/copilot-instructions.md) for development guidelines
- [AI Behavior Contract](../.github/AI-BEHAVIOR-CONTRACT.md) for AI interaction standards
- [Island AI Instructions](../.github/island-ai-instructions.md) for detailed technical guidelines

## Architecture

This workspace implements the three-systems view:

1. **SynergyMesh Core**: AI decision engine and registries (`src/core/`)
2. **Structural Governance**: Schema and policy loops (`governance/`, `config/`)
3. **Autonomous/Drone Stack**: ROS/C++ and automation (`src/autonomous/`)

For detailed architecture information, see the individual component READMEs.
