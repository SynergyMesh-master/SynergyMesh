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
    sourceModule: "AXM-L03-PROT-001",
    inputSchema: {
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
    quantumEnabled: true,
    priority: 11,
  },
  {
    name: "load_balancer",
    description: "Adaptive load balancing with circuit breaker patterns",
    sourceModule: "AXM-L03-LOAD-002",
    inputSchema: {
      type: "object",
      properties: {
        service: { type: "string" },
        request: { type: "object" },
        strategy: { type: "string", enum: ["round_robin", "least_connections", "weighted", "adaptive"] },
        circuit_breaker: { type: "object" },
      },
      required: ["service", "request"],
    },
    quantumEnabled: true,
    priority: 12,
  },
  {
    name: "adaptive_router",
    description: "Reinforcement learning-based routing optimization",
    sourceModule: "AXM-L03-ADPT-003",
    inputSchema: {
      type: "object",
      properties: {
        network_state: { type: "object" },
        optimization_objective: { type: "string", enum: ["latency", "throughput", "cost", "reliability"] },
        learning_mode: { type: "string", enum: ["online", "offline", "hybrid"] },
        exploration_rate: { type: "number", default: 0.1 },
      },
      required: ["network_state"],
    },
    quantumEnabled: true,
    priority: 13,
  },
];
