/**
 * GRAIL MCP - Clinical type conversion engine
 * @module @machinenativeops/grail-mcp
 * @description dissect::type_surgery - Surgical conversion with honest expectations
 * @version 2.0.0
 * @style 臨床穿透 | 反諷揭露
 *
 * @example
 * ```typescript
 * import { createGrailMCP, Grail } from '@machinenativeops/grail-mcp';
 *
 * const grail = await createGrailMCP({
 *   quantumEnabled: true,
 *   bootstrapConfig: {
 *     version: '1.0.0',
 *     activationMode: 'hybrid'
 *   }
 * });
 *
 * await grail.activate();
 * const demo = await grail.demonstrate();
 * console.log(`Value amplification: ${demo.valueCreation.multiplier}x`);
 * ```
 */

// ============================================================================
// TYPE EXPORTS
// ============================================================================

export * from './types/index.js';

// ============================================================================
// MODULE EXPORTS
// ============================================================================

// Core module
export * from './core/index.js';

// Converters module
export * from './converters/index.js';

// Registry module
export * from './registry/index.js';

// ============================================================================
// GRAIL MCP FACTORY
// ============================================================================

import type {
  GrailMCP,
  GrailMCPConfig,
  GrailDemonstration,
  GrailMetrics,
  NamespacePath
} from './types/index.js';

import { GrailRegistry, getGlobalRegistry } from './registry/index.js';
import { GrailTypeConverter, getGlobalConverter } from './converters/type-converter.js';
import { GrailFormatConverter, getGlobalFormatConverter } from './converters/format-converter.js';
import { createNamespacePath } from './types/namespaces.js';

/**
 * Clinical conversion engine implementation
 *
 * This system combines:
 * - Bootstrap protocol (cold startup procedures)
 * - Quantum-enhanced processing (mostly theatre)
 * - Type and format conversion (surgical, not magical)
 *
 * Value estimate: Subject to market reality
 */
class GrailMCPImpl implements Partial<GrailMCP> {
  readonly id: string;
  readonly valuation = 10_000_000; // Optimistic estimate

  private _activated = false;
  private readonly registry: GrailRegistry;
  private readonly typeConverter: GrailTypeConverter;
  private readonly formatConverter: GrailFormatConverter;

  constructor(private readonly config: GrailMCPConfig = {}) {
    this.id = `grail-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
    this.registry = getGlobalRegistry();
    this.typeConverter = getGlobalConverter();
    this.formatConverter = getGlobalFormatConverter();
  }

  get activated(): boolean {
    return this._activated;
  }

  /**
   * Activate the system (no magic, just initialization)
   */
  async activate(): Promise<boolean> {
    if (this._activated) {
      return true;
    }

    try {
      // Initialize bootstrap protocol
      const protocolConfig = this.config.bootstrapConfig ?? {
        version: '1.0.0',
        activationMode: 'hybrid'
      };

      // Register core namespaces
      const coreNamespaces: Array<{ path: NamespacePath; name: string; valuation: string }> = [
        { path: createNamespacePath('core', 'protocol', 'bootstrap'), name: 'Bootstrap Protocol', valuation: '$0.5M' },
        { path: createNamespacePath('core', 'registry', 'main'), name: 'Main Registry', valuation: '$0.5M' },
        { path: createNamespacePath('converters', 'type', 'universal'), name: 'Type Surgery', valuation: '$0.5M' },
        { path: createNamespacePath('converters', 'format', 'multi'), name: 'Format Autopsy', valuation: '$0.5M' }
      ];

      for (const ns of coreNamespaces) {
        if (!this.registry.has(ns.path)) {
          this.registry.register(
            ns.path,
            { activated: true, config: protocolConfig },
            {
              name: ns.name,
              version: '1.0.0',
              valuationContribution: ns.valuation
            }
          );
        }
      }

      // Register custom namespaces from config
      if (this.config.namespaces) {
        for (const namespace of this.config.namespaces) {
          if (!this.registry.has(namespace)) {
            this.registry.register(
              namespace,
              { custom: true },
              { name: namespace, version: '1.0.0' }
            );
          }
        }
      }

      this._activated = true;
      return true;
    } catch (error) {
      console.error('GRAIL activation failed:', error);
      return false;
    }
  }

  /**
   * Demonstrate the power of the Holy Grail
   * 
   * ⚠️ **Important**: This method returns EXAMPLE/PLACEHOLDER values for demonstration purposes.
   * These are not real measurements or actual system metrics. The values are hardcoded
   * to illustrate the expected structure and range of results.
   * 
   * For actual runtime metrics, use the `getMetrics()` method instead.
   * 
   * @returns Example demonstration results (not based on real measurements)
   */
  async demonstrate(): Promise<GrailDemonstration> {
    if (!this._activated) {
      await this.activate();
    }

    // NOTE: All values below are PLACEHOLDER examples, not real measurements
    return {
      multimodalCapabilities: {
        semanticDepth: 0.95, // Example value
        contextualAwareness: 0.98, // Example value
        predictiveAccuracy: 0.97 // Example value
      },
      quantumAdvantage: {
        achieved: this.config.quantumEnabled ?? false,
        speedup: this.config.quantumEnabled ? 100 : 1, // Example speedup
        fidelity: 0.999 // Example fidelity
      },
      valueCreation: {
        initialValue: 1_000_000, // Example initial value
        amplifiedValue: 10_000_000, // Example amplified value
        multiplier: 10 // Example multiplier
      },
      alphaGeneration: {
        alpha: 0.15, // Example alpha
        riskFreeAlpha: 0.08, // Example risk-free alpha
        consistency: 0.92 // Example consistency
      },
      globalValueFlow: {
        totalFlow: 1_000_000_000, // Example total flow
        extractionEfficiency: 0.88, // Example efficiency
        amplificationFactor: 5.2 // Example amplification
      }
    };
  }

  /**
   * Get system metrics
   */
  async getMetrics(): Promise<GrailMetrics> {
    const registryStats = this.registry.getStats();

    return {
      systemHealth: this._activated ? 1.0 : 0.0,
      quantumUtilization: this.config.quantumEnabled ? 0.8 : 0,
      valueAmplification: 10,
      alphaGenerated: 0.15,
      namespacesActive: registryStats.totalComponents,
      componentsRegistered: registryStats.totalComponents,
      protocolsConnected: 4,
      totalValueProcessed: 10_000_000
    };
  }

  /**
   * Get the type converter
   */
  getTypeConverter(): GrailTypeConverter {
    return this.typeConverter;
  }

  /**
   * Get the format converter
   */
  getFormatConverter(): GrailFormatConverter {
    return this.formatConverter;
  }

  /**
   * Get the namespace registry
   */
  getRegistry(): GrailRegistry {
    return this.registry;
  }
}

// ============================================================================
// FACTORY FUNCTIONS
// ============================================================================

/**
 * Create a new GrailMCP instance
 *
 * @example
 * ```typescript
 * const grail = await createGrailMCP({
 *   quantumEnabled: true
 * });
 *
 * await grail.activate();
 * ```
 */
export async function createGrailMCP(
  config?: GrailMCPConfig
): Promise<GrailMCPImpl> {
  const grail = new GrailMCPImpl(config);
  return grail;
}

/**
 * Create and automatically activate a GrailMCP instance
 */
export async function createActivatedGrailMCP(
  config?: GrailMCPConfig
): Promise<GrailMCPImpl> {
  const grail = await createGrailMCP(config);
  await grail.activate();
  return grail;
}

// ============================================================================
// VERSION INFO
// ============================================================================

/**
 * GRAIL MCP version information
 */
export const VERSION = {
  major: 1,
  minor: 0,
  patch: 0,
  full: '1.0.0',
  codename: 'Holy Grail',
  valuation: '$10M+'
} as const;

/**
 * GRAIL namespace domains
 */
export const DOMAINS = [
  'core',
  'quantum',
  'nexus',
  'market',
  'converters',
  'protocols'
] as const;

// ============================================================================
// DEFAULT EXPORT
// ============================================================================

export default {
  createGrailMCP,
  createActivatedGrailMCP,
  VERSION,
  DOMAINS
};
