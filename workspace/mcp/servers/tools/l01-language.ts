/**
 * Layer L01: Language Processing Tools
 * NLP, semantic analysis, transformers
 * @module tools/l01-language
 */

import type { ToolDefinition } from "./types.js";

export const L01_TOOLS: ToolDefinition[] = [
  {
    name: "language_core",
    description: "Quantum-enhanced NLP with BERT and transformer models",
    source_module: "AXM-L01-LANG-001",
    input_schema: {
      type: "object",
      properties: {
        text: { type: "string" },
        operation: { type: "string", enum: ["tokenize", "embed", "encode", "classify", "generate"] },
        model: { type: "string", default: "quantum_bert_xxl" },
        context_window: { type: "integer", default: 32768 },
        quantum_attention: { type: "boolean", default: false },
      },
      required: ["text", "operation"],
    },
    quantum_enabled: true,
    priority: 6,
  },
  {
    name: "language_advanced",
    description: "Advanced semantic analysis with quantum coherence",
    source_module: "AXM-L01-LADV-002",
    input_schema: {
      type: "object",
      properties: {
        text: { type: "string" },
        analysis_type: {
          type: "string",
          enum: ["sentiment", "zero_shot_classification", "conversation", "entity_extraction"],
        },
        categories: { type: "array", items: { type: "string" } },
        streaming: { type: "boolean", default: false },
      },
      required: ["text", "analysis_type"],
    },
    quantum_enabled: true,
    priority: 7,
  },
];
