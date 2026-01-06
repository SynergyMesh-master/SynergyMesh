/**
 * Shared type definitions for AXIOM dissolved tools
 * @module tools/types
 */

export interface ToolDefinition {
  name: string;
  description: string;
  source_module: string;
  input_schema: object;
  quantum_enabled: boolean;
  fallback_enabled?: boolean;
  priority: number;
}

export interface ResourceDefinition {
  uri: string;
  name: string;
  description: string;
  mime_type: string;
  metadata: object;
}

export interface PromptDefinition {
  name: string;
  description: string;
  arguments: Array<{ name: string; description: string; required: boolean }>;
}
