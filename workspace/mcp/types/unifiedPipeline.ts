/**
 * MachineNativeOps Unified Pipeline Types v3.0.0
 *
 * INSTANT Execution Architecture
 * - AI auto-evolution, instant delivery, zero latency
 * - Execution standard: <3 minutes full stack, 0 human intervention
 * - Competitiveness: Replit | Claude | GPT equivalent
 */

// ========================================
// Event-Driven Configuration
// ========================================
export interface EventDrivenConfig {
  mode: "trigger-event-action";
  closedLoop: boolean;
  maxConcurrentEvents: number;
  eventQueueSize: number;
}

export interface InputUnification {
  protocols: string[];
  normalization: string;
  validation: string;
  timeout: number;
  eventDriven?: EventDrivenConfig;
}

// ========================================
// Auto-Scaling Configuration
// ========================================
export interface ScalingMetric {
  name: string;
  target: number;
  scaleUpThreshold?: number;
  scaleDownThreshold?: number;
}

export interface AutoScalingConfig {
  enabled: boolean;
  scaleFactor: number;
  cooldownSeconds: number;
  metrics: ScalingMetric[];
}

export interface CoreScheduling {
  maxParallelAgents: number;
  minParallelAgents?: number;
  taskDecomposition: string;
  resourceArbitration: string;
  loadBalancing: string;
  syncBarrier: string;
  autoScaling?: AutoScalingConfig;
}

// ========================================
// Latency Thresholds
// ========================================
export interface LatencyThresholds {
  instant: number;    // <=100ms
  fast: number;       // <=500ms
  standard: number;   // <=5s
  maxStage: number;   // max per-stage latency
  maxTotal: number;   // max total pipeline latency
}

// ========================================
// Pipeline Entries
// ========================================
export type PipelineType = "validation" | "refactor" | "security" | "deployment" | "observability";
export type PipelinePriority = "critical" | "high" | "medium" | "low";

export interface PipelineEntry {
  name: string;
  type: PipelineType;
  entrypoint?: string;
  worldClassValidationRef?: string;
  policies?: string;
  manifests?: string;
  dashboards?: string;
  latency?: number;
  parallelism?: number;
  priority?: PipelinePriority;
  capabilities?: string[];
}

// ========================================
// INSTANT Pipelines
// ========================================
export interface InstantPipelineStage {
  name: string;
  agent: string;
  latency: number;
  parallelism: number;
}

export interface InstantPipeline {
  name: string;
  description?: string;
  totalLatencyTarget: number;
  humanIntervention: 0;
  successRateTarget: number;
  stages: InstantPipelineStage[];
}

// ========================================
// MCP Integration
// ========================================
export interface ToolAdapter {
  name: string;
  path: string;
  capabilities?: string[];
}

export interface McpIntegration {
  serverRef: string;
  toolAdapters: ToolAdapter[];
  realTimeSync: "enabled" | "disabled";
  crossPlatformCoordination?: "enabled" | "disabled";
}

// ========================================
// Outputs
// ========================================
export interface Outputs {
  auditLog: string;
  evidenceChain: string;
  statusReport: string;
  autoRemediation: string;
  notifications: string;
}

// ========================================
// Auto-Healing
// ========================================
export interface HealingStrategy {
  name: string;
  conditions: Record<string, unknown>;
  actions: string[];
  maxRetries?: number;
  backoffMultiplier?: number;
}

export interface AutoHealing {
  enabled: boolean;
  strategies: HealingStrategy[];
}

// ========================================
// Governance Validation
// ========================================
/**
 * Governance validation rule configuration.
 *
 * The implementationStatus field indicates whether the validator script is
 * currently implemented or planned for future development.
 */
export interface GovernanceValidationRule {
  standard: string;
  validator: string;
  checkInterval: number;
  criteria: string[];
  failureAction: string;
  /** Indicates if the validator is implemented or planned */
  implementationStatus?: "implemented" | "planned";
}

// ========================================
// Metadata
// ========================================
export type PipelineMode = "INSTANT-Autonomous" | "Standard" | "Hybrid";

export interface PipelineLabels {
  tier?: "production" | "staging" | "development";
  evolution?: string;
  humanIntervention?: string;
  [key: string]: string | undefined;
}

export interface PipelineAnnotations {
  philosophy?: string;
  competitiveness?: string;
  standard?: string;
  [key: string]: string | undefined;
}

export interface PipelineMetadata {
  name: string;
  version: string;
  mode: PipelineMode;
  labels?: PipelineLabels;
  annotations?: PipelineAnnotations;
}

// ========================================
// Unified Pipeline Spec
// ========================================
export interface UnifiedPipelineSpec {
  inputUnification: InputUnification;
  coreScheduling: CoreScheduling;
  latencyThresholds?: LatencyThresholds;
  pipelines: PipelineEntry[];
  instantPipelines?: InstantPipeline[];
  mcpIntegration: McpIntegration;
  outputs: Outputs;
  autoHealing?: AutoHealing;
  governanceValidation?: GovernanceValidationRule[];
}

// ========================================
// Main Pipeline Interface
// ========================================
export type ApiVersion = "pipeline.machinenativeops/v2" | "pipeline.machinenativeops/v3";

export interface UnifiedPipeline {
  apiVersion: ApiVersion;
  kind: "UnifiedPipeline";
  metadata: PipelineMetadata;
  spec: UnifiedPipelineSpec;
}

// ========================================
// Path Constants
// ========================================
export const unifiedPipelineManifestPath = "workspace/mcp/pipelines/unified-pipeline-config.yaml";
export const unifiedPipelineSchemaPath = "workspace/mcp/schemas/unified-pipeline.schema.json";

// ========================================
// Type Guards
// ========================================
export function isInstantMode(pipeline: UnifiedPipeline): boolean {
  return pipeline.metadata.mode === "INSTANT-Autonomous";
}

export function hasZeroHumanIntervention(pipeline: UnifiedPipeline): boolean {
  return pipeline.metadata.labels?.humanIntervention === "0";
}

export function isV3Pipeline(pipeline: UnifiedPipeline): boolean {
  return pipeline.apiVersion === "pipeline.machinenativeops/v3";
}

// ========================================
// INSTANT Execution Constants
// ========================================
/**
 * Runtime constants for INSTANT execution mode validation.
 *
 * Note on schema vs runtime constraints:
 * - The JSON schema allows maxParallelAgents up to 1024 to support future
 *   scaling and non-INSTANT pipeline modes (Standard, Hybrid).
 * - For INSTANT-Autonomous mode, the runtime maximum is 256 agents.
 * - The schema's higher maximum provides flexibility for infrastructure
 *   that may scale beyond current INSTANT requirements while maintaining
 *   backward compatibility.
 */
export const INSTANT_EXECUTION_STANDARDS = {
  MAX_LATENCY_INSTANT: 100,      // ms
  MAX_LATENCY_FAST: 500,         // ms
  MAX_LATENCY_STANDARD: 5000,    // ms
  MAX_STAGE_LATENCY: 30000,      // ms
  MAX_TOTAL_LATENCY: 180000,     // ms (3 minutes)
  MIN_PARALLEL_AGENTS: 64,
  MAX_PARALLEL_AGENTS: 256,      // Runtime max for INSTANT mode (schema allows 1024)
  HUMAN_INTERVENTION: 0,
  SUCCESS_RATE_FEATURE: 95,      // %
  SUCCESS_RATE_FIX: 90,          // %
  SUCCESS_RATE_OPTIMIZE: 85,     // %
} as const;

export const AGENT_TYPES = [
  "analyzer",
  "generator",
  "validator",
  "deployer",
  "sentinel",
  "diagnostic",
  "fixer",
  "optimizer",
  "architect",
  "tester",
] as const;

export type AgentType = typeof AGENT_TYPES[number];
