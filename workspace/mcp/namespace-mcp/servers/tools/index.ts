/**
 * AXIOM Dissolved Tools Registry
 * Central aggregation of all 59 tool definitions organized by layer
 * @module tools/index
 */

import type { ToolDefinition } from "./types.js";
import { L00_TOOLS } from "./l00-infrastructure.js";
import { L01_TOOLS } from "./l01-language.js";
import { L02_TOOLS } from "./l02-input.js";
import { L03_TOOLS } from "./l03-network.js";
import { L04_TOOLS } from "./l04-cognitive.js";
import { L05_TOOLS } from "./l05-ethics.js";
import { L06_TOOLS } from "./l06-integration.js";
import { L07_TOOLS } from "./l07-reasoning.js";
import { L08_TOOLS } from "./l08-emotion.js";
import { L09_TOOLS } from "./l09-output.js";
import { L10_TOOLS } from "./l10-governance.js";
import { L11_TOOLS } from "./l11-performance.js";
import { L12_TOOLS } from "./l12-metacognitive.js";
import { L13_TOOLS } from "./l13-quantum.js";

/**
 * All AXIOM dissolved tools aggregated by layer
 * Total: 59 tools across 14 layers
 */
export const DISSOLVED_TOOLS: ToolDefinition[] = [
  ...L00_TOOLS, // Infrastructure & Bootstrap (5 tools)
  ...L01_TOOLS, // Language Processing (2 tools)
  ...L02_TOOLS, // Input Processing (3 tools)
  ...L03_TOOLS, // Network & Routing (3 tools)
  ...L04_TOOLS, // Cognitive Processing (4 tools)
  ...L05_TOOLS, // Ethics & Governance (3 tools)
  ...L06_TOOLS, // Integration & Orchestration (3 tools)
  ...L07_TOOLS, // Reasoning & Knowledge (3 tools)
  ...L08_TOOLS, // Emotional Intelligence (3 tools)
  ...L09_TOOLS, // Output Optimization (3 tools)
  ...L10_TOOLS, // System Governance (5 tools)
  ...L11_TOOLS, // Performance Optimization (4 tools)
  ...L12_TOOLS, // Metacognitive & Strategic (3 tools)
  ...L13_TOOLS, // Quantum Specialized (15 tools)
];

/**
 * Layer-organized exports for selective imports
 */
export {
  L00_TOOLS,
  L01_TOOLS,
  L02_TOOLS,
  L03_TOOLS,
  L04_TOOLS,
  L05_TOOLS,
  L06_TOOLS,
  L07_TOOLS,
  L08_TOOLS,
  L09_TOOLS,
  L10_TOOLS,
  L11_TOOLS,
  L12_TOOLS,
  L13_TOOLS,
};

export type { ToolDefinition, ResourceDefinition, PromptDefinition } from "./types.js";
