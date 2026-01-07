/**
 * GRAIL Inter-Protocol Bridge Types
 * @module grail::types::protocols::bridge
 * @description Type definitions for inter-protocol bridging and adaptation
 * @description Type definitions for inter-protocol bridging
 * @version 1.0.0
 */

/**
 * Protocol Adapter for converting between protocol message types
 * Protocol Adapter Interface
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
