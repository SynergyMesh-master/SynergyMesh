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
    sourceModule: "AXM-L06-COLL-001",
    inputSchema: {
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
    quantumEnabled: true,
    priority: 21,
  },
  {
    name: "api_orchestrator",
    description: "API gateway with rate limiting and authentication",
    sourceModule: "AXM-L06-APIS-002",
    inputSchema: {
      type: "object",
      properties: {
        endpoint: { type: "string" },
        method: { type: "string", enum: ["GET", "POST", "PUT", "DELETE", "PATCH"] },
        payload: { type: "object" },
        auth_context: { type: "object" },
      },
      required: ["endpoint", "method"],
    },
    quantumEnabled: false,
    priority: 22,
  },
  {
    name: "workflow_engine",
    description: "Temporal-based workflow orchestration",
    sourceModule: "AXM-L06-WORK-003",
    inputSchema: {
      type: "object",
      properties: {
        workflow_definition: { type: "object" },
        input_data: { type: "object" },
        execution_mode: { type: "string", enum: ["sync", "async", "distributed"] },
      },
      required: ["workflow_definition"],
    },
    quantumEnabled: true,
    priority: 23,
  },
];
