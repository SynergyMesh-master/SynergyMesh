/**
 * Layer L11: Performance Optimization Tools
 * System optimization, performance tuning, resource optimization, energy management
 * @module tools/l11-performance
 */

import type { ToolDefinition } from "./types.js";

export const L11_TOOLS: ToolDefinition[] = [
  {
    name: "system_optimization",
    description: "Genetic algorithms with simulated annealing",
    sourceModule: "AXM-L11-SOPT-001",
    inputSchema: {
      type: "object",
      properties: {
        objective_function: { type: "object" },
        constraints: { type: "array" },
        optimization_method: {
          type: "string",
          enum: ["genetic", "simulated_annealing", "particle_swarm", "bayesian", "multi_objective"],
        },
        max_iterations: { type: "integer", default: 1000 },
      },
      required: ["objective_function"],
    },
    quantumEnabled: true,
    priority: 38,
  },
  {
    name: "performance_tuner",
    description: "JVM and kernel parameter optimization",
    sourceModule: "AXM-L11-PERF-002",
    inputSchema: {
      type: "object",
      properties: {
        target_system: { type: "string" },
        tuning_domain: { type: "string", enum: ["jvm", "kernel", "database", "network", "application"] },
        workload_profile: { type: "object" },
        auto_apply: { type: "boolean", default: false },
      },
      required: ["target_system", "tuning_domain"],
    },
    quantumEnabled: false,
    priority: 39,
  },
  {
    name: "resource_optimizer",
    description: "Bin packing with genetic algorithms",
    sourceModule: "AXM-L11-RSRC-003",
    inputSchema: {
      type: "object",
      properties: {
        resources: { type: "array", items: { type: "object" } },
        nodes: { type: "array", items: { type: "object" } },
        optimization_goal: { type: "string", enum: ["utilization", "cost", "balance", "latency"] },
      },
      required: ["resources", "nodes"],
    },
    quantumEnabled: true,
    priority: 40,
  },
  {
    name: "energy_optimizer",
    description: "DVFS control with power monitoring",
    sourceModule: "AXM-L11-ENRG-004",
    inputSchema: {
      type: "object",
      properties: {
        target_nodes: { type: "array", items: { type: "string" } },
        optimization_mode: { type: "string", enum: ["performance", "balanced", "power_save", "adaptive"] },
        power_budget_watts: { type: "number" },
        thermal_limit_celsius: { type: "number", default: 85 },
      },
      required: ["target_nodes"],
    },
    quantumEnabled: false,
    priority: 41,
  },
];
