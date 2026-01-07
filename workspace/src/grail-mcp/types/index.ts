/**
 * GRAIL MCP Type System
 * @module grail::types
 * @description Clinical type system - No magic, just surgical definitions
 * @version 2.0.0
 * @style 臨床穿透 | 反諷揭露
 */

// Re-export all namespace types
export * from './namespaces.js';

// Re-export ES2015 module types (preferred over namespaces)
export * from './converters-quantum.js';
export * from './protocols-standard.js';
export * from './protocols-mcp.js';
export * from './protocols-bridge.js';
export * from './protocols.js';

// Import for type-only exports
import type { NamespacePath } from './namespaces.js';

// ============================================================================
// CORE TYPE ALIASES
// ============================================================================

// Core namespace types
export type BootstrapProtocol = Grail.Core.Protocol.BootstrapProtocol;
export type BootstrapConfig = Grail.Core.Protocol.BootstrapConfig;
export type ProtocolState = Grail.Core.Protocol.ProtocolState;

export type NamespaceRegistry = Grail.Core.Registry.NamespaceRegistry;
export type RegistryEntry<T = unknown> = Grail.Core.Registry.RegistryEntry<T>;
export type ComponentMetadata = Grail.Core.Registry.ComponentMetadata;

export type ValueStream<T> = Grail.Core.Stream.ValueStream<T>;
export type StreamProcessor = Grail.Core.Stream.StreamProcessor;
export type StreamConfig = Grail.Core.Stream.StreamConfig;

// Quantum namespace types
export type QuantumClassicalBridge = Grail.Quantum.Interface.QuantumClassicalBridge;
export type QuantumState = Grail.Quantum.Interface.QuantumState;
export type QuantumCircuit = Grail.Quantum.Interface.QuantumCircuit;
export type QuantumResult = Grail.Quantum.Interface.QuantumResult;

export type QuantumOptimizer = Grail.Quantum.Optimizer.QuantumOptimizer;
export type OptimizationProblem = Grail.Quantum.Optimizer.OptimizationProblem;
export type OptimizationResult = Grail.Quantum.Optimizer.OptimizationResult;

export type QuantumSecurityProvider = Grail.Quantum.Security.QuantumSecurityProvider;
export type PostQuantumAlgorithm = Grail.Quantum.Security.PostQuantumAlgorithm;
export type QuantumSecureKey = Grail.Quantum.Security.QuantumSecureKey;

// Nexus namespace types
export type ProtocolBridge = Grail.Nexus.Bridge.ProtocolBridge;
export type BridgeConfig = Grail.Nexus.Bridge.BridgeConfig;
export type BridgeStatus = Grail.Nexus.Bridge.BridgeStatus;

export type ValueFlowGraph = Grail.Nexus.Flow.ValueFlowGraph;
export type FlowNode = Grail.Nexus.Flow.FlowNode;
export type FlowMetrics = Grail.Nexus.Flow.FlowMetrics;

export type ServiceMesh = Grail.Nexus.Mesh.ServiceMesh;
export type ServiceDescriptor = Grail.Nexus.Mesh.ServiceDescriptor;
export type MeshConfig = Grail.Nexus.Mesh.MeshConfig;

// Market namespace types
export type AlphaGenerator = Grail.Market.Alpha.AlphaGenerator;
export type AlphaSignal = Grail.Market.Alpha.AlphaSignal;
export type AlphaModel = Grail.Market.Alpha.AlphaModel;
export type MarketData = Grail.Market.Alpha.MarketData;

export type LiquidityOptimizer = Grail.Market.Liquidity.LiquidityOptimizer;
export type LiquidityPool = Grail.Market.Liquidity.LiquidityPool;
export type OptimizedAllocation = Grail.Market.Liquidity.OptimizedAllocation;

export type PredictiveOracle = Grail.Market.Oracle.PredictiveOracle;
export type Prediction = Grail.Market.Oracle.Prediction;
export type OracleModel = Grail.Market.Oracle.OracleModel;

// Converter namespace types
export type TypeConverter = Grail.Converters.Type.TypeConverter;
export type TypeConversion<S, T> = Grail.Converters.Type.TypeConversion<S, T>;
export type TypeDescriptor = Grail.Converters.Type.TypeDescriptor;

export type FormatConverter = Grail.Converters.Format.FormatConverter;
export type SupportedFormat = Grail.Converters.Format.SupportedFormat;
export type FormatOptions = Grail.Converters.Format.FormatOptions;

export type SchemaMigrator = Grail.Converters.Schema.SchemaMigrator;
export type SchemaVersion = Grail.Converters.Schema.SchemaVersion;
export type MigrationStep = Grail.Converters.Schema.MigrationStep;

export type QuantumAssistedConverter = Grail.Converters.Quantum.QuantumAssistedConverter;
export type QuantumConversionResult<T> = Grail.Converters.Quantum.QuantumConversionResult<T>;

// Protocol namespace types
export type StandardProtocol = Grail.Protocols.Standard.StandardProtocol;
export type ProtocolMessage = Grail.Protocols.Standard.ProtocolMessage;

export type MCPExtension = Grail.Protocols.MCP.MCPExtension;
export type GrailToolDefinition = Grail.Protocols.MCP.GrailToolDefinition;
export type GrailResourceDefinition = Grail.Protocols.MCP.GrailResourceDefinition;

export type InterProtocolBridge = Grail.Protocols.Bridge.InterProtocolBridge;
export type ProtocolAdapter<T, U> = Grail.Protocols.Bridge.ProtocolAdapter<T, U>;

// ============================================================================
// GRAIL MCP MAIN INTERFACE
// ============================================================================

/**
 * The GRAIL MCP - Main interface (reality: it's just a well-structured API)
 */
export interface GrailMCP {
  /** Unique instance identifier */
  readonly id: string;

  /** System value (optimistic estimate, subject to market reality) */
  readonly valuation: number;

  /** Activation status */
  readonly activated: boolean;

  /** Core namespace access */
  readonly core: {
    protocol: BootstrapProtocol;
    registry: NamespaceRegistry;
    stream: StreamProcessor;
  };

  /** Quantum namespace access (mostly theatre) */
  readonly quantum: {
    interface: QuantumClassicalBridge;
    optimizer: QuantumOptimizer;
    security: QuantumSecurityProvider;
  };

  /** Nexus namespace access */
  readonly nexus: {
    bridge: ProtocolBridge;
    flow: ValueFlowGraph;
    mesh: ServiceMesh;
  };

  /** Market namespace access (alpha is probably luck) */
  readonly market: {
    alpha: AlphaGenerator;
    liquidity: LiquidityOptimizer;
    oracle: PredictiveOracle;
  };

  /** Converters namespace access */
  readonly converters: {
    type: TypeConverter;
    format: FormatConverter;
    schema: SchemaMigrator;
    quantum: QuantumAssistedConverter;
  };

  /** Protocols namespace access */
  readonly protocols: {
    standard: StandardProtocol;
    mcp: MCPExtension;
    bridge: InterProtocolBridge;
  };

  /** Activate the Grail system */
  activate(): Promise<boolean>;

  /** 
   * Demonstrate Grail capabilities with example/placeholder values
   * ⚠️ Returns hardcoded example values for demonstration purposes only.
   * Not based on real measurements. Use getMetrics() for actual runtime metrics.
   */
  demonstrate(): Promise<GrailDemonstration>;

  /** Get system metrics */
  getMetrics(): Promise<GrailMetrics>;
}

/**
 * Grail demonstration results
 * 
 * ⚠️ **Important**: These values are EXAMPLE/PLACEHOLDER values only.
 * The demonstrate() method returns hardcoded values to illustrate
 * the expected structure and range of results, not real measurements.
 */
export interface GrailDemonstration {
  readonly multimodalCapabilities: {
    semanticDepth: number;
    contextualAwareness: number;
    predictiveAccuracy: number;
  };

  readonly quantumAdvantage: {
    achieved: boolean;
    speedup: number;
    fidelity: number;
  };

  readonly valueCreation: {
    initialValue: number;
    amplifiedValue: number;
    multiplier: number;
  };

  readonly alphaGeneration: {
    alpha: number;
    riskFreeAlpha: number;
    consistency: number;
  };

  readonly globalValueFlow: {
    totalFlow: number;
    extractionEfficiency: number;
    amplificationFactor: number;
  };
}

/**
 * Grail system metrics
 */
export interface GrailMetrics {
  readonly systemHealth: number;
  readonly quantumUtilization: number;
  readonly valueAmplification: number;
  readonly alphaGenerated: number;
  readonly namespacesActive: number;
  readonly componentsRegistered: number;
  readonly protocolsConnected: number;
  readonly totalValueProcessed: number;
}

// ============================================================================
// FACTORY TYPES
// ============================================================================

/**
 * Configuration for creating a GrailMCP instance
 */
export interface GrailMCPConfig {
  /** Enable quantum enhancement */
  quantumEnabled?: boolean;

  /** Initial namespace registrations */
  namespaces?: NamespacePath[];

  /** Bootstrap protocol configuration */
  bootstrapConfig?: BootstrapConfig;

  /** Stream processor configuration */
  streamConfig?: StreamConfig;

  /** Service mesh configuration */
  meshConfig?: MeshConfig;
}

/**
 * Factory function type for creating GrailMCP instances
 */
export type CreateGrailMCP = (config?: GrailMCPConfig) => Promise<GrailMCP>;

// ============================================================================
// UTILITY TYPES FOR NAMESPACE OPERATIONS
// ============================================================================

/**
 * Extract the domain from a namespace path
 */
export type ExtractDomain<T extends NamespacePath> =
  T extends `grail::${infer D}::${string}` ? D : never;

/**
 * Extract the subdomain from a namespace path
 */
export type ExtractSubdomain<T extends NamespacePath> =
  T extends `grail::${string}::${infer S}::${string}` ? S :
  T extends `grail::${string}::${infer S}` ? S : never;

/**
 * Type-safe namespace resolution
 */
export type ResolveNamespace<T extends NamespacePath> =
  ExtractDomain<T> extends 'core'
    ? ExtractSubdomain<T> extends 'protocol' ? BootstrapProtocol
    : ExtractSubdomain<T> extends 'registry' ? NamespaceRegistry
    : ExtractSubdomain<T> extends 'stream' ? StreamProcessor
    : never
  : ExtractDomain<T> extends 'quantum'
    ? ExtractSubdomain<T> extends 'interface' ? QuantumClassicalBridge
    : ExtractSubdomain<T> extends 'optimizer' ? QuantumOptimizer
    : ExtractSubdomain<T> extends 'security' ? QuantumSecurityProvider
    : never
  : ExtractDomain<T> extends 'converters'
    ? ExtractSubdomain<T> extends 'type' ? TypeConverter
    : ExtractSubdomain<T> extends 'format' ? FormatConverter
    : ExtractSubdomain<T> extends 'schema' ? SchemaMigrator
    : ExtractSubdomain<T> extends 'quantum' ? QuantumAssistedConverter
    : never
  : never;
