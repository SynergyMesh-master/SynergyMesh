/**
 * Layer L04: Cognitive Processing Tools
 * Deep cognitive analysis, pattern recognition, semantic processing
 * @module tools/l04-cognitive
 */

import type { ToolDefinition } from "./types.js";

export const L04_TOOLS: ToolDefinition[] = [
  {
    name: "cognitive_analysis",
    description: "Deep cognitive processing with transformer architectures",
    sourceModule: "AXM-L04-COGN-001",
    inputSchema: {
      type: "object",
      properties: {
        input: { type: "object" },
        analysis_depth: { type: "string", enum: ["surface", "deep", "comprehensive"] },
        attention_config: { type: "object" },
        reasoning_mode: { type: "string", enum: ["deductive", "inductive", "abductive", "analogical"] },
      },
      required: ["input"],
    },
    quantumEnabled: true,
    priority: 14,
  },
  {
    name: "pattern_recognition",
    description: "Multi-architecture pattern detection with ensemble methods",
    sourceModule: "AXM-L04-PATT-002",
    inputSchema: {
      type: "object",
      properties: {
        data: { type: "object" },
        pattern_types: { type: "array", items: { type: "string" } },
        detection_method: { type: "string", enum: ["cnn", "gnn", "transformer", "ensemble"] },
        anomaly_detection: { type: "boolean", default: true },
      },
      required: ["data"],
    },
    quantumEnabled: true,
    priority: 15,
  },
  {
    name: "semantic_processor",
    description: "Deep semantic understanding with BERT and GPT integration",
    sourceModule: "AXM-L04-SEMA-003",
    inputSchema: {
      type: "object",
      properties: {
        content: { type: "string" },
        processing_mode: { type: "string", enum: ["parse", "understand", "reason", "synthesize"] },
        knowledge_base_query: { type: "boolean", default: true },
        context: { type: "array", items: { type: "string" } },
      },
      required: ["content"],
    },
    quantumEnabled: true,
    priority: 16,
  },
  {
    name: "metacognitive_monitor",
    description: "Self-awareness engine with performance tracking",
    sourceModule: "AXM-L04-META-004",
    inputSchema: {
      type: "object",
      properties: {
        target_system: { type: "string" },
        monitoring_aspects: { type: "array", items: { type: "string" } },
        introspection_depth: { type: "string", enum: ["shallow", "medium", "deep"] },
      },
      required: ["target_system"],
    },
    quantumEnabled: true,
    priority: 17,
  },
];
