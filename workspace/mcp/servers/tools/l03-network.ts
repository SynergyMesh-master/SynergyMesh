/**
 * Layer L03: Network & Routing Tools
 * Protocol routing, load balancing, adaptive routing
 * @module tools/l03-network
 */

import type { ToolDefinition } from "./types.js";

export const L03_TOOLS: ToolDefinition[] = [
  {
    name: "protocol_routing",
    description: "ML-based intelligent routing with quantum optimization",
    source_module: "AXM-L03-PROT-001",
    input_schema: {
      type: "object",
      properties: {
        source: { type: "string" },
        destination: { type: "string" },
        payload_size_bytes: { type: "integer" },
        routing_algorithm: {
          type: "string",
          enum: ["shortest_path", "ml_optimized", "quantum_optimized", "adaptive"],
        },
      },
      required: ["source", "destination"],
    },
    quantum_enabled: true,
    priority: 11,
  },
  {
    name: "load_balancer",
    description: "Adaptive load balancing with circuit breaker patterns",
    source_module: "AXM-L03-LOAD-002",
    input_schema: {
      type: "object",
      properties: {
        service: { type: "string" },
        request: { type: "object" },
        strategy: { type: "string", enum: ["round_robin", "least_connections", "weighted", "adaptive"] },
        circuit_breaker: { type: "object" },
      },
      required: ["service", "request"],
    },
    quantum_enabled: true,
    priority: 12,
  },
  {
    name: "adaptive_router",
    description: "Reinforcement learning-based routing optimization",
    source_module: "AXM-L03-ADPT-003",
    input_schema: {
      type: "object",
      properties: {
        network_state: { type: "object" },
        optimization_objective: { type: "string", enum: ["latency", "throughput", "cost", "reliability"] },
        learning_mode: { type: "string", enum: ["online", "offline", "hybrid"] },
        exploration_rate: { type: "number", default: 0.1 },
      },
      required: ["network_state"],
    },
    quantum_enabled: true,
    priority: 13,
  },
];
