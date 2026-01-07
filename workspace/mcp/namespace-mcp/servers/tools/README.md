# AXIOM Dissolved Tools - Layer-Based Modules

This directory contains the refactored AXIOM tool definitions, organized by architectural layer for improved maintainability and testability.

## Structure

- **types.ts** - Shared TypeScript type definitions
- **index.ts** - Central registry that aggregates all tools
- **l00-infrastructure.ts** - Layer L00: Infrastructure & Bootstrap (5 tools)
- **l01-language.ts** - Layer L01: Language Processing (2 tools)
- **l02-input.ts** - Layer L02: Input Processing (3 tools)
- **l03-network.ts** - Layer L03: Network & Routing (3 tools)
- **l04-cognitive.ts** - Layer L04: Cognitive Processing (4 tools)
- **l05-ethics.ts** - Layer L05: Ethics & Governance (3 tools)
- **l06-integration.ts** - Layer L06: Integration & Orchestration (3 tools)
- **l07-reasoning.ts** - Layer L07: Reasoning & Knowledge (3 tools)
- **l08-emotion.ts** - Layer L08: Emotional Intelligence (3 tools)
- **l09-output.ts** - Layer L09: Output Optimization (3 tools)
- **l10-governance.ts** - Layer L10: System Governance (5 tools)
- **l11-performance.ts** - Layer L11: Performance Optimization (4 tools)
- **l12-metacognitive.ts** - Layer L12: Metacognitive & Strategic (3 tools)
- **l13-quantum.ts** - Layer L13: Quantum Specialized (15 tools)

## Total

**59 tools** across **14 layers**

## Usage

Import all tools:
```typescript
import { DISSOLVED_TOOLS } from "./tools/index.js";
```

Import specific layer:
```typescript
import { L00_TOOLS } from "./tools/l00-infrastructure.js";
```

Import types:
```typescript
import type { ToolDefinition } from "./tools/types.js";
```

## Benefits

1. **Maintainability** - Each layer is in its own file, easier to find and update
2. **Testability** - Individual layers can be unit tested in isolation
3. **Modularity** - Tools can be imported selectively by layer
4. **Readability** - Much smaller files (2-9KB vs 60KB monolithic file)
5. **Scalability** - Easy to add new tools to specific layers

## Architecture Alignment

This structure follows the AXIOM dissolved architecture pattern, maintaining the 14-layer hierarchy while providing better code organization according to MCP standards.
