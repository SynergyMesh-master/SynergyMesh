/**
 * GRAIL Protocols Types
 * @module grail::types::protocols
 * @description Type definitions for GRAIL communication protocols
 * @version 1.0.0
 */

import type { NamespacePath } from './namespaces.js';

// ============================================================================
// STANDARD PROTOCOL
// ============================================================================

/**
 * Standard Protocol Message
 */
export interface ProtocolMessage {
  readonly type: string;
  readonly payload: unknown;
  readonly signature: Uint8Array;
  readonly timestamp: Date;
}

/**
 * Standard Protocol Interface (no divinity required)
 */
export interface StandardProtocol {
  send(message: ProtocolMessage): Promise<void>;
  receive(): AsyncGenerator<ProtocolMessage>;
  verify(message: ProtocolMessage): Promise<boolean>;
  seal(message: ProtocolMessage): Promise<ProtocolMessage>;
}

// ============================================================================
// MCP EXTENSIONS
// ============================================================================

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

// ============================================================================
// INTER-PROTOCOL BRIDGE
// ============================================================================

/**
 * Protocol Adapter for bridging between protocols
 */
export interface ProtocolAdapter<T, U> {
  readonly sourceProtocol: string;
  readonly targetProtocol: string;
  adapt(message: T): U;
  reverse(message: U): T;
}

/**
 * Inter-Protocol Bridge Interface
 */
export interface InterProtocolBridge {
  registerAdapter<T, U>(adapter: ProtocolAdapter<T, U>): void;
  bridge<T, U>(message: T, sourceProtocol: string, targetProtocol: string): U;
  getSupportedBridges(): Array<[string, string]>;
}
