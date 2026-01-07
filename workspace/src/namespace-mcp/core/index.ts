/**
 * GRAIL Core Module
 * @module grail::core
 * @description The Sacred Heart of GRAIL - Core engine and protocols
 * @valuation $2.5M foundational IP
 */

export * from '../registry/index.js';

// Re-export core types
export type {
  DivineProtocol,
  DivineConfig,
  ProtocolState,
  ValueStream,
  StreamProcessor,
  StreamConfig
} from '../types/index.js';
