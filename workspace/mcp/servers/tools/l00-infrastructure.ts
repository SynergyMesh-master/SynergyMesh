/**
 * Layer L00: Infrastructure & Bootstrap Tools
 * Platform initialization, kernel compute, emergency systems
 * @module tools/l00-infrastructure
 */

import type { ToolDefinition } from "./types.js";

export const L00_TOOLS: ToolDefinition[] = [
  {
    name: "bootstrap_core",
    description: "Platform initialization and quantum backend discovery",
    source_module: "AXM-L00-BOOT-001",
    input_schema: {
      type: "object",
      properties: {
        backend_type: {
          type: "string",
          enum: ["ibm_quantum", "aws_braket", "azure_quantum", "local_simulator"],
          description: "Quantum backend type to discover and initialize",
        },
        calibration_required: { type: "boolean", default: true },
        timeout_seconds: { type: "integer", default: 30 },
      },
      required: ["backend_type"],
    },
    quantum_enabled: true,
    priority: 1,
  },
  {
    name: "kernel_compute",
    description: "High-performance quantum-classical compute orchestration",
    source_module: "AXM-L00-KERN-002",
    input_schema: {
      type: "object",
      properties: {
        circuit: { type: "object", description: "Quantum circuit to execute" },
        optimization_level: { type: "integer", enum: [0, 1, 2, 3], default: 3 },
        parallel_execution: { type: "boolean", default: true },
      },
      required: ["circuit"],
    },
    quantum_enabled: true,
    priority: 2,
  },
  {
    name: "emergency_override",
    description: "Multi-level emergency shutdown and recovery system",
    source_module: "AXM-L00-EMER-003",
    input_schema: {
      type: "object",
      properties: {
        action: { type: "string", enum: ["initiate_shutdown", "trigger_recovery", "check_status"] },
        level: { type: "string", enum: ["component", "layer", "system", "full"], default: "component" },
        target: { type: "string" },
        force: { type: "boolean", default: false },
      },
      required: ["action"],
    },
    quantum_enabled: false,
    priority: 3,
  },
  {
    name: "resource_scheduler",
    description: "Quantum-aware resource scheduling with deadline priorities",
    source_module: "AXM-L00-SCHD-004",
    input_schema: {
      type: "object",
      properties: {
        jobs: { type: "array", items: { type: "object" } },
        scheduling_algorithm: {
          type: "string",
          enum: ["fifo", "priority", "deadline", "quantum_aware"],
          default: "quantum_aware",
        },
      },
      required: ["jobs"],
    },
    quantum_enabled: true,
    priority: 4,
  },
  {
    name: "memory_allocator",
    description: "Quantum coherence-aware memory management",
    source_module: "AXM-L00-MEML-005",
    input_schema: {
      type: "object",
      properties: {
        action: { type: "string", enum: ["allocate", "deallocate", "query", "optimize"] },
        size_bytes: { type: "integer" },
        memory_type: { type: "string", enum: ["standard", "quantum_coherent", "gpu", "hugepages"] },
      },
      required: ["action"],
    },
    quantum_enabled: true,
    priority: 5,
  },
];
