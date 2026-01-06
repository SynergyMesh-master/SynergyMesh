/**
 * Layer L12: Metacognitive & Strategic Tools
 * Strategic planning, self-optimization, emergence detection
 * @module tools/l12-metacognitive
 */

import type { ToolDefinition } from "./types.js";

export const L12_TOOLS: ToolDefinition[] = [
  {
    name: "meta_strategist",
    description: "Multi-objective optimization with Pareto analysis",
    source_module: "AXM-L12-STRT-001",
    input_schema: {
      type: "object",
      properties: {
        objectives: { type: "array", items: { type: "object" } },
        constraints: { type: "array" },
        decision_variables: { type: "array" },
        game_theory_mode: { type: "boolean", default: false },
      },
      required: ["objectives", "decision_variables"],
    },
    quantum_enabled: true,
    priority: 42,
  },
  {
    name: "self_optimizer",
    description: "Deep Q-Network reinforcement learning",
    source_module: "AXM-L12-SOPT-002",
    input_schema: {
      type: "object",
      properties: {
        environment: { type: "object" },
        learning_config: { type: "object" },
        training_episodes: { type: "integer", default: 1000 },
        target_metric: { type: "string" },
      },
      required: ["environment"],
    },
    quantum_enabled: true,
    priority: 43,
  },
  {
    name: "emergence_detector",
    description: "Complexity metrics and phase transition detection",
    source_module: "AXM-L12-EMER-003",
    input_schema: {
      type: "object",
      properties: {
        system_state: { type: "object" },
        analysis_type: { type: "string", enum: ["complexity", "phase_transition", "emergence", "all"] },
        time_window: { type: "object" },
      },
      required: ["system_state"],
    },
    quantum_enabled: true,
    priority: 44,
  },
];
