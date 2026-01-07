/**
 * GRAIL Namespace Registry
 * @module grail::core::registry
 * @description The sacred registry that holds all namespace components
 * @version 1.0.0
 * @valuation Core foundation for $10M+ system
 */

import type {
  NamespacePath,
  GrailDomain,
  RegistryEntry,
  ComponentMetadata,
  NamespaceRegistry
} from '../types/index.js';

import {
  parseNamespacePath,
  isValidNamespacePath,
  createNamespacePath
} from '../types/namespaces.js';

// ============================================================================
// REGISTRY IMPLEMENTATION
// ============================================================================

/**
 * The Holy Grail Registry - Central component registration system
 *
 * This registry is the heart of the GRAIL namespace system, providing:
 * - Type-safe component registration
 * - Dependency resolution
 * - Namespace validation
 * - Component lifecycle management
 */
export class GrailRegistry implements NamespaceRegistry {
  private readonly components: Map<NamespacePath, RegistryEntry<unknown>> = new Map();
  private readonly dependencies: Map<NamespacePath, Set<NamespacePath>> = new Map();
  private readonly listeners: Map<string, Set<RegistryEventHandler>> = new Map();

  /**
   * Create a new GrailRegistry instance
   */
  constructor(private readonly options: GrailRegistryOptions = {}) {
    if (options.autoRegisterCore) {
      this.registerCoreComponents();
    }
  }

  /**
   * Register a component in the namespace
   */
  register<T>(
    namespace: NamespacePath,
    component: T,
    metadata: ComponentMetadata
  ): void {
    // Validate namespace path
    if (!isValidNamespacePath(namespace)) {
      throw new GrailRegistryError(
        `Invalid namespace path: ${namespace}`,
        'INVALID_NAMESPACE'
      );
    }

    // Check for existing registration
    if (this.components.has(namespace) && !this.options.allowOverwrite) {
      throw new GrailRegistryError(
        `Namespace ${namespace} is already registered`,
        'ALREADY_REGISTERED'
      );
    }

    // Validate dependencies
    if (metadata.dependencies) {
      for (const dep of metadata.dependencies) {
        if (!this.components.has(dep)) {
          throw new GrailRegistryError(
            `Missing dependency: ${dep} required by ${namespace}`,
            'MISSING_DEPENDENCY'
          );
        }
      }
      this.dependencies.set(namespace, new Set(metadata.dependencies));
    }

    // Create registry entry
    const entry: RegistryEntry<T> = {
      namespace,
      component,
      metadata,
      registeredAt: new Date()
    };

    this.components.set(namespace, entry as RegistryEntry<unknown>);
    this.emit('registered', { namespace, metadata });
  }

  /**
   * Resolve a component from the namespace
   */
  resolve<T>(namespace: NamespacePath): T | undefined {
    const entry = this.components.get(namespace);
    if (!entry) {
      return undefined;
    }
    return entry.component as T;
  }

  /**
   * Resolve a component with type checking
   */
  resolveRequired<T>(namespace: NamespacePath): T {
    const component = this.resolve<T>(namespace);
    if (component === undefined) {
      throw new GrailRegistryError(
        `Required namespace not found: ${namespace}`,
        'NOT_FOUND'
      );
    }
    return component;
  }

  /**
   * List all registered components
   */
  list(domain?: GrailDomain): RegistryEntry<unknown>[] {
    const entries = Array.from(this.components.values());

    if (domain) {
      return entries.filter(entry => {
        const parsed = parseNamespacePath(entry.namespace);
        return parsed.domain === domain;
      });
    }

    return entries;
  }

  /**
   * Unregister a component
   */
  unregister(namespace: NamespacePath): boolean {
    // Check for dependents
    const dependents = this.findDependents(namespace);
    if (dependents.length > 0 && !this.options.cascadeUnregister) {
      throw new GrailRegistryError(
        `Cannot unregister ${namespace}: has dependents: ${dependents.join(', ')}`,
        'HAS_DEPENDENTS'
      );
    }

    // Cascade unregister if enabled
    if (this.options.cascadeUnregister) {
      for (const dependent of dependents) {
        this.unregister(dependent);
      }
    }

    const deleted = this.components.delete(namespace);
    this.dependencies.delete(namespace);

    if (deleted) {
      this.emit('unregistered', { namespace });
    }

    return deleted;
  }

  /**
   * Check if a namespace is registered
   */
  has(namespace: NamespacePath): boolean {
    return this.components.has(namespace);
  }

  /**
   * Get all namespaces in a specific domain
   */
  getNamespaces(domain?: GrailDomain): NamespacePath[] {
    return this.list(domain).map(entry => entry.namespace);
  }

  /**
   * Get dependencies for a namespace
   */
  getDependencies(namespace: NamespacePath): NamespacePath[] {
    const deps = this.dependencies.get(namespace);
    return deps ? Array.from(deps) : [];
  }

  /**
   * Find all namespaces that depend on the given namespace
   */
  findDependents(namespace: NamespacePath): NamespacePath[] {
    const dependents: NamespacePath[] = [];

    for (const [ns, deps] of this.dependencies) {
      if (deps.has(namespace)) {
        dependents.push(ns);
      }
    }

    return dependents;
  }

  /**
   * Get total valuation contribution from all registered components
   */
  getTotalValuation(): string {
    const entries = this.list();
    let total = 0;

    for (const entry of entries) {
      const contribution = entry.metadata.valuationContribution;
      if (contribution) {
        // Parse valuation string like "$2.5M"
        const match = contribution.match(/\$?([\d.]+)([MK])?/);
        if (match) {
          let value = parseFloat(match[1]);
          if (match[2] === 'M') value *= 1_000_000;
          if (match[2] === 'K') value *= 1_000;
          total += value;
        }
      }
    }

    if (total >= 1_000_000) {
      return `$${(total / 1_000_000).toFixed(1)}M`;
    }
    return `$${total.toLocaleString()}`;
  }

  /**
   * Subscribe to registry events
   */
  on(event: RegistryEventType, handler: RegistryEventHandler): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(handler);

    return () => {
      this.listeners.get(event)?.delete(handler);
    };
  }

  /**
   * Get registry statistics
   */
  getStats(): RegistryStats {
    const entries = this.list();
    const byDomain: Record<GrailDomain, number> = {
      core: 0,
      quantum: 0,
      nexus: 0,
      market: 0,
      converters: 0,
      protocols: 0
    };

    for (const entry of entries) {
      const parsed = parseNamespacePath(entry.namespace);
      byDomain[parsed.domain]++;
    }

    return {
      totalComponents: entries.length,
      byDomain,
      totalValuation: this.getTotalValuation(),
      oldestRegistration: entries.length > 0
        ? entries.reduce((a, b) =>
            a.registeredAt < b.registeredAt ? a : b
          ).registeredAt
        : undefined,
      newestRegistration: entries.length > 0
        ? entries.reduce((a, b) =>
            a.registeredAt > b.registeredAt ? a : b
          ).registeredAt
        : undefined
    };
  }

  /**
   * Export registry state for persistence
   */
  export(): RegistryExport {
    const entries: Array<{
      namespace: NamespacePath;
      metadata: ComponentMetadata;
      registeredAt: string;
    }> = [];

    for (const entry of this.components.values()) {
      entries.push({
        namespace: entry.namespace,
        metadata: entry.metadata,
        registeredAt: entry.registeredAt.toISOString()
      });
    }

    return {
      version: '1.0.0',
      exportedAt: new Date().toISOString(),
      entries
    };
  }

  /**
   * Clear all registrations
   */
  clear(): void {
    this.components.clear();
    this.dependencies.clear();
    this.emit('cleared', {});
  }

  // ============================================================================
  // PRIVATE METHODS
  // ============================================================================

  private emit(event: RegistryEventType, data: RegistryEventData): void {
    const handlers = this.listeners.get(event);
    if (handlers) {
      for (const handler of handlers) {
        try {
          handler(data);
        } catch (error) {
          console.error(`Registry event handler error for ${event}:`, error);
        }
      }
    }
  }

  private registerCoreComponents(): void {
    // Register core namespace markers
    const coreNamespaces: Array<{
      namespace: NamespacePath;
      metadata: ComponentMetadata;
    }> = [
      {
        namespace: createNamespacePath('core', 'protocol'),
        metadata: {
          name: 'Divine Protocol',
          version: '1.0.0',
          description: 'Sacred protocol initialization',
          valuationContribution: '$0.5M'
        }
      },
      {
        namespace: createNamespacePath('core', 'registry'),
        metadata: {
          name: 'Namespace Registry',
          version: '1.0.0',
          description: 'Component registration system',
          valuationContribution: '$0.5M'
        }
      },
      {
        namespace: createNamespacePath('core', 'stream'),
        metadata: {
          name: 'Value Stream',
          version: '1.0.0',
          description: 'Value stream processing',
          valuationContribution: '$0.5M'
        }
      }
    ];

    for (const { namespace, metadata } of coreNamespaces) {
      this.register(namespace, { initialized: true }, metadata);
    }
  }
}

// ============================================================================
// TYPES
// ============================================================================

/**
 * Registry configuration options
 */
export interface GrailRegistryOptions {
  /** Allow overwriting existing registrations */
  allowOverwrite?: boolean;

  /** Cascade unregister to dependents */
  cascadeUnregister?: boolean;

  /** Auto-register core namespace markers */
  autoRegisterCore?: boolean;
}

/**
 * Registry event types
 */
export type RegistryEventType = 'registered' | 'unregistered' | 'cleared';

/**
 * Registry event data
 */
export interface RegistryEventData {
  namespace?: NamespacePath;
  metadata?: ComponentMetadata;
}

/**
 * Registry event handler
 */
export type RegistryEventHandler = (data: RegistryEventData) => void;

/**
 * Registry statistics
 */
export interface RegistryStats {
  totalComponents: number;
  byDomain: Record<GrailDomain, number>;
  totalValuation: string;
  oldestRegistration?: Date;
  newestRegistration?: Date;
}

/**
 * Registry export format
 */
export interface RegistryExport {
  version: string;
  exportedAt: string;
  entries: Array<{
    namespace: NamespacePath;
    metadata: ComponentMetadata;
    registeredAt: string;
  }>;
}

// ============================================================================
// ERROR TYPES
// ============================================================================

/**
 * Registry error codes
 */
export type RegistryErrorCode =
  | 'INVALID_NAMESPACE'
  | 'ALREADY_REGISTERED'
  | 'MISSING_DEPENDENCY'
  | 'NOT_FOUND'
  | 'HAS_DEPENDENTS';

/**
 * Custom error for registry operations
 */
export class GrailRegistryError extends Error {
  constructor(
    message: string,
    public readonly code: RegistryErrorCode
  ) {
    super(message);
    this.name = 'GrailRegistryError';
  }
}

// ============================================================================
// SINGLETON INSTANCE
// ============================================================================

/**
 * Global registry instance
 */
let globalRegistry: GrailRegistry | null = null;

/**
 * Get the global registry instance
 */
export function getGlobalRegistry(): GrailRegistry {
  if (!globalRegistry) {
    globalRegistry = new GrailRegistry({ autoRegisterCore: true });
  }
  return globalRegistry;
}

/**
 * Create a new isolated registry
 */
export function createRegistry(options?: GrailRegistryOptions): GrailRegistry {
  return new GrailRegistry(options);
}
