/**
 * Layer L06: Integration & Orchestration Tools
 * Multi-agent coordination, API orchestration, workflow engine
 * @module tools/l06-integration
 */

import type { ToolDefinition } from "./types.js";

export const L06_TOOLS: ToolDefinition[] = [
  {
    name: "collaboration_integration",
    description: "Multi-agent orchestration with circuit breaker patterns",
    source_module: "AXM-L06-COLL-001",
    input_schema: {
      type: "object",
      properties: {
        agents: { type: "array", items: { type: "object" } },
        coordination_protocol: {
          type: "string",
          enum: ["consensus", "leader_election", "distributed", "hierarchical"],
        },
        task: { type: "object" },
      },
      required: ["agents", "task"],
    },
    quantum_enabled: true,
    priority: 21,
  },
  {
    name: "api_orchestrator",
    description: "API gateway with rate limiting and authentication",
    source_module: "AXM-L06-APIS-002",
    input_schema: {
      type: "object",
      properties: {
        endpoint: { type: "string" },
        method: { type: "string", enum: ["GET", "POST", "PUT", "DELETE", "PATCH"] },
        payload: { type: "object" },
        auth_context: { type: "object" },
      },
      required: ["endpoint", "method"],
    },
    quantum_enabled: false,
    priority: 22,
  },
  {
    name: "workflow_engine",
    description: "Temporal-based workflow orchestration",
    source_module: "AXM-L06-WORK-003",
    input_schema: {
      type: "object",
      properties: {
        workflow_definition: { type: "object" },
        input_data: { type: "object" },
        execution_mode: { type: "string", enum: ["sync", "async", "distributed"] },
      },
      required: ["workflow_definition"],
    },
    quantum_enabled: true,
    priority: 23,
  },
];
