/**
 * GRAIL Registry Module
 * @module grail::registry
 * @description Namespace registration and component management
 */

export {
  GrailRegistry,
  GrailRegistryError,
  getGlobalRegistry,
  createRegistry
} from './grail-registry.js';

export type {
  GrailRegistryOptions,
  RegistryEventType,
  RegistryEventData,
  RegistryEventHandler,
  RegistryStats,
  RegistryExport,
  RegistryErrorCode
} from './grail-registry.js';
