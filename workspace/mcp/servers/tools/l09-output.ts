/**
 * Layer L09: Output Optimization Tools
 * Quality scoring, format optimization, grammar checking
 * @module tools/l09-output
 */

import type { ToolDefinition } from "./types.js";

export const L09_TOOLS: ToolDefinition[] = [
  {
    name: "output_quality",
    description: "Quantum-enhanced output scoring and optimization",
    source_module: "AXM-L09-OUTQ-001",
    input_schema: {
      type: "object",
      properties: {
        output: { type: "object" },
        quality_dimensions: { type: "array", items: { type: "string" } },
        optimization_enabled: { type: "boolean", default: true },
        target_quality: { type: "number", default: 0.95 },
      },
      required: ["output"],
    },
    quantum_enabled: true,
    priority: 30,
  },
  {
    name: "format_optimizer",
    description: "Multi-format optimization with compression",
    source_module: "AXM-L09-FORM-002",
    input_schema: {
      type: "object",
      properties: {
        content: { type: "object" },
        source_format: { type: "string" },
        target_format: { type: "string" },
        compression: { type: "object" },
      },
      required: ["content", "target_format"],
    },
    quantum_enabled: true,
    priority: 31,
  },
  {
    name: "grammar_checker",
    description: "Multi-language grammar validation",
    source_module: "AXM-L09-GRAM-003",
    input_schema: {
      type: "object",
      properties: {
        text: { type: "string" },
        language: { type: "string", default: "auto" },
        check_types: { type: "array", items: { type: "string" } },
        auto_correct: { type: "boolean", default: false },
      },
      required: ["text"],
    },
    quantum_enabled: true,
    priority: 32,
  },
];
