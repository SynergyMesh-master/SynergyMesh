/**
 * GRAIL MCP Extension Types
 * GRAIL MCP Protocol Extensions
 * @module grail::types::protocols::mcp
 * @description Type definitions for MCP (Model Context Protocol) extensions
 * @version 1.0.0
 */

import type { NamespacePath } from './namespaces.js';

/**
 * GRAIL Tool Definition for MCP
 */
export interface GrailToolDefinition {
  readonly name: string;
  readonly description: string;
  readonly namespace: NamespacePath;
  readonly inputSchema: unknown;
  readonly outputSchema: unknown;
}

/**
 * GRAIL Resource Definition for MCP
 */
export interface GrailResourceDefinition {
  readonly uri: string;
  readonly name: string;
  readonly namespace: NamespacePath;
  readonly mimeType: string;
}

/**
 * MCP Extension Interface
 */
export interface MCPExtension {
  registerTool(tool: GrailToolDefinition): void;
  registerResource(resource: GrailResourceDefinition): void;
  getTools(): GrailToolDefinition[];
  getResources(): GrailResourceDefinition[];
  invoke(toolName: string, params: unknown): Promise<unknown>;
}
