/**
 * Layer L02: Input Processing Tools
 * Quantum state preparation, validation, multimodal processing
 * @module tools/l02-input
 */

import type { ToolDefinition } from "./types.js";

export const L02_TOOLS: ToolDefinition[] = [
  {
    name: "input_quantum",
    description: "Quantum state preparation and multimodal input processing",
    sourceModule: "AXM-L02-INPQ-001",
    inputSchema: {
      type: "object",
      properties: {
        data: { type: "object" },
        encoding_method: { type: "string", enum: ["amplitude", "angle", "basis", "superposition"] },
        modalities: { type: "array", items: { type: "string" } },
        noise_modeling: { type: "boolean", default: true },
      },
      required: ["data"],
    },
    quantumEnabled: true,
    priority: 8,
  },
  {
    name: "data_validator",
    description: "Comprehensive validation with quality scoring",
    sourceModule: "AXM-L02-VALD-002",
    inputSchema: {
      type: "object",
      properties: {
        data: { type: "object" },
        schema: { type: "object" },
        quality_metrics: { type: "array", items: { type: "string" } },
        strict_mode: { type: "boolean", default: true },
      },
      required: ["data"],
    },
    quantumEnabled: false,
    priority: 9,
  },
  {
    name: "multimodal_processor",
    description: "Cross-modal fusion with attention mechanisms",
    sourceModule: "AXM-L02-MULT-003",
    inputSchema: {
      type: "object",
      properties: {
        inputs: { type: "object" },
        fusion_method: {
          type: "string",
          enum: ["cross_attention", "early_fusion", "late_fusion", "hierarchical"],
        },
        output_modality: { type: "string", enum: ["text", "embedding", "classification"] },
      },
      required: ["inputs"],
    },
    quantumEnabled: true,
    priority: 10,
  },
];
