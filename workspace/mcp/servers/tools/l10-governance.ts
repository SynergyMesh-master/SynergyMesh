/**
 * Layer L10: System Governance Tools
 * Policy enforcement, architecture planning, audit logging, compliance
 * @module tools/l10-governance
 */

import type { ToolDefinition } from "./types.js";

export const L10_TOOLS: ToolDefinition[] = [
  {
    name: "system_governance",
    description: "System-wide policy enforcement with OPA",
    source_module: "AXM-L10-GOVN-001",
    input_schema: {
      type: "object",
      properties: {
        resource: { type: "object" },
        action: { type: "string" },
        policy_bundle: { type: "string", default: "default" },
        dry_run: { type: "boolean", default: false },
      },
      required: ["resource", "action"],
    },
    quantum_enabled: false,
    priority: 33,
  },
  {
    name: "architecture_plan",
    description: "Execute and validate architectural blueprints",
    source_module: "AXM-L10-ARCH-002",
    input_schema: {
      type: "object",
      properties: {
        blueprint: { type: "object" },
        validation_mode: { type: "string", enum: ["syntax", "semantic", "full"] },
        gitops_check: { type: "boolean", default: true },
        deployment_trigger: { type: "boolean", default: false },
      },
      required: ["blueprint"],
    },
    quantum_enabled: false,
    priority: 34,
  },
  {
    name: "audit_logger",
    description: "Immutable audit logging with cryptographic signatures",
    source_module: "AXM-L10-AUDT-003",
    input_schema: {
      type: "object",
      properties: {
        event: { type: "object" },
        sign: { type: "boolean", default: true },
        retention_policy: { type: "string", default: "standard" },
      },
      required: ["event"],
    },
    quantum_enabled: false,
    priority: 35,
  },
  {
    name: "policy_engine",
    description: "Rego-based policy evaluation",
    source_module: "AXM-L10-POLY-004",
    input_schema: {
      type: "object",
      properties: {
        policy: { type: "string" },
        input_data: { type: "object" },
        policy_path: { type: "string" },
        explain_mode: { type: "boolean", default: false },
      },
      required: ["input_data"],
    },
    quantum_enabled: false,
    priority: 36,
  },
  {
    name: "compliance_monitor",
    description: "Real-time compliance violation detection",
    source_module: "AXM-L10-COMP-005",
    input_schema: {
      type: "object",
      properties: {
        target: { type: "string" },
        compliance_standards: { type: "array", items: { type: "string" } },
        monitoring_mode: { type: "string", enum: ["continuous", "periodic", "on_demand"] },
      },
      required: ["target"],
    },
    quantum_enabled: false,
    priority: 37,
  },
];
