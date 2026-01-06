/**
 * Layer L05: Ethics & Governance Tools
 * Policy evaluation, bias detection, fairness optimization
 * @module tools/l05-ethics
 */

import type { ToolDefinition } from "./types.js";

export const L05_TOOLS: ToolDefinition[] = [
  {
    name: "ethics_governance",
    description: "Policy evaluation framework with audit logging",
    sourceModule: "AXM-L05-ETHG-001",
    inputSchema: {
      type: "object",
      properties: {
        action: { type: "object" },
        policy_frameworks: { type: "array", items: { type: "string" } },
        audit_required: { type: "boolean", default: true },
      },
      required: ["action"],
    },
    quantumEnabled: false,
    priority: 18,
  },
  {
    name: "bias_detector",
    description: "Multi-algorithm bias detection system",
    sourceModule: "AXM-L05-BIAS-002",
    inputSchema: {
      type: "object",
      properties: {
        model_or_data: { type: "object" },
        protected_attributes: { type: "array", items: { type: "string" } },
        detection_algorithms: { type: "array", items: { type: "string" } },
      },
      required: ["model_or_data", "protected_attributes"],
    },
    quantumEnabled: false,
    priority: 19,
  },
  {
    name: "fairness_optimizer",
    description: "Adversarial debiasing with dual network architecture",
    sourceModule: "AXM-L05-FAIR-003",
    inputSchema: {
      type: "object",
      properties: {
        model: { type: "object" },
        fairness_constraints: { type: "array" },
        optimization_method: { type: "string", enum: ["adversarial", "reweighting", "calibration"] },
      },
      required: ["model", "fairness_constraints"],
    },
    quantumEnabled: false,
    priority: 20,
  },
];
