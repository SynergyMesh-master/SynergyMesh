/**
 * Layer L07: Reasoning & Knowledge Tools
 * Logical reasoning, inference engine, knowledge graphs
 * @module tools/l07-reasoning
 */

import type { ToolDefinition } from "./types.js";

export const L07_TOOLS: ToolDefinition[] = [
  {
    name: "logical_reasoning",
    description: "First-order logic with neural-symbolic reasoning",
    source_module: "AXM-L07-LOGI-001",
    input_schema: {
      type: "object",
      properties: {
        premises: { type: "array", items: { type: "string" } },
        query: { type: "string" },
        reasoning_mode: { type: "string", enum: ["deductive", "inductive", "abductive", "analogical"] },
        neural_symbolic: { type: "boolean", default: true },
      },
      required: ["premises", "query"],
    },
    quantum_enabled: true,
    priority: 24,
  },
  {
    name: "inference_engine",
    description: "Hybrid inference with theorem proving",
    source_module: "AXM-L07-INFR-002",
    input_schema: {
      type: "object",
      properties: {
        knowledge_base: { type: "object" },
        query: { type: "object" },
        inference_method: {
          type: "string",
          enum: ["forward_chaining", "backward_chaining", "hybrid", "probabilistic"],
        },
        max_inference_depth: { type: "integer", default: 10 },
      },
      required: ["knowledge_base", "query"],
    },
    quantum_enabled: true,
    priority: 25,
  },
  {
    name: "knowledge_graph",
    description: "Graph neural network with Neo4j backend",
    source_module: "AXM-L07-KNOW-003",
    input_schema: {
      type: "object",
      properties: {
        operation: { type: "string", enum: ["query", "insert", "update", "delete", "traverse", "embed"] },
        cypher_query: { type: "string" },
        entity: { type: "object" },
        traversal_config: { type: "object" },
      },
      required: ["operation"],
    },
    quantum_enabled: true,
    priority: 26,
  },
];
