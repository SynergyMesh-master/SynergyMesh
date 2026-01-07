/**
 * GRAIL MCP Namespace Definitions
 * @module grail::types::namespaces
 * @description Clinical dissection namespace architecture - Type system surgery
 * @version 2.0.0
 * @style 臨床穿透 | 反諷揭露
 */

// Import ES2015 module types for re-export in namespaces
import type * as ProtocolsTypes from './protocols.js';

// ============================================================================
// NAMESPACE PATH UTILITIES
// ============================================================================

/**
 * Valid namespace domains in the GRAIL architecture
 */
export type GrailDomain =
  | 'core'
  | 'quantum'
  | 'nexus'
  | 'market'
  | 'converters'
  | 'protocols';

/**
 * Array of valid GRAIL domains for runtime validation.
 * IMPORTANT: Must be kept in sync with the GrailDomain type above.
 */
export const VALID_GRAIL_DOMAINS: readonly GrailDomain[] = [
  'core',
  'quantum',
  'nexus',
  'market',
  'converters',
  'protocols'
] as const;

/**
 * Namespace path pattern: grail::{domain}::{subdomain}::{component}
 */
export type NamespacePath = `grail::${GrailDomain}::${string}`;

/**
 * Full namespace identifier with validation
 */
export interface NamespaceIdentifier {
  readonly domain: GrailDomain;
  readonly subdomain: string;
  readonly component?: string;
  readonly fullPath: NamespacePath;
}

// ============================================================================
// GRAIL CORE NAMESPACE
// ============================================================================

/**
 * Bootstrap Protocol - Cold startup procedures
 */
export interface BootstrapConfig {
  readonly version: string;
  readonly activationMode: 'quantum_entanglement' | 'classical' | 'hybrid';
  readonly configKeys?: string[];
}

export interface ProtocolState {
  readonly initialized: boolean;
  readonly activatedAt?: Date;
  readonly quantumSupremacy: boolean;
}

export interface BootstrapProtocol {
  initiate(config: BootstrapConfig): Promise<ProtocolState>;
  activate(): Promise<boolean>;
  deactivate(): Promise<void>;
  getState(): ProtocolState;
}

/**
 * Registry - Namespace and component registration
 */
export interface RegistryEntry<T = unknown> {
  readonly namespace: NamespacePath;
  readonly component: T;
  readonly metadata: ComponentMetadata;
  readonly registeredAt: Date;
}

export interface ComponentMetadata {
  readonly name: string;
  readonly version: string;
  readonly description?: string;
  readonly dependencies?: NamespacePath[];
  readonly valuationContribution?: string;
}

export interface NamespaceRegistry {
  register<T>(namespace: NamespacePath, component: T, metadata: ComponentMetadata): void;
  resolve<T>(namespace: NamespacePath): T | undefined;
  list(domain?: GrailDomain): RegistryEntry[];
  unregister(namespace: NamespacePath): boolean;
}

/**
 * Stream - Value stream processing
 */
export interface StreamConfig {
  readonly bufferSize?: number;
  readonly backpressure?: 'drop' | 'buffer' | 'block';
  readonly quantumEnhanced?: boolean;
}

export interface ValueStream<T> {
  push(value: T): Promise<void>;
  pull(): Promise<T | undefined>;
  transform<U>(fn: (value: T) => U): ValueStream<U>;
  filter(predicate: (value: T) => boolean): ValueStream<T>;
  amplify(factor: number): ValueStream<T>;
}

export interface StreamProcessor {
  createStream<T>(config?: StreamConfig): ValueStream<T>;
  connect<T, U>(source: ValueStream<T>, sink: ValueStream<U>, transformer: (t: T) => U): void;
  getAmplificationFactor(): number;
}

  // ============================================================================
  // GRAIL QUANTUM NAMESPACE
  // ============================================================================

  /**
   * Quantum namespace - hype::quantum_theatre (mostly performance art)
   * Reality check: 99% is theatre, 1% might be real
   */
  export namespace Quantum {
    /**
     * Quantum-Classical Interface
     */
    export namespace Interface {
      export interface QuantumState {
        readonly qubits: number;
        readonly coherenceTime: number;
        readonly entangled: boolean;
      }

      export interface QuantumClassicalBridge {
        createEntanglement(): Promise<QuantumState>;
        measureState(): Promise<number[]>;
        maintainCoherence(): Promise<number>;
        executeQuantumCircuit(circuit: QuantumCircuit): Promise<QuantumResult>;
      }

      export interface QuantumCircuit {
        readonly gates: QuantumGate[];
        readonly qubits: number;
      }

      export interface QuantumGate {
        readonly type: 'H' | 'X' | 'Y' | 'Z' | 'CNOT' | 'T' | 'S';
        readonly target: number;
        readonly control?: number;
      }

      export interface QuantumResult {
        readonly measurements: number[];
        readonly probability: number;
        readonly fidelity: number;
      }
    }

    /**
     * Quantum Optimization
     */
    export namespace Optimizer {
      export interface OptimizationProblem {
        readonly objective: (x: number[]) => number;
        readonly constraints?: Array<(x: number[]) => boolean>;
        readonly dimensions: number;
        readonly bounds?: Array<[number, number]>;
      }

      export interface OptimizationResult {
        readonly solution: number[];
        readonly value: number;
        readonly iterations: number;
        readonly quantumAdvantage: boolean;
      }

      export interface QuantumOptimizer {
        optimize(problem: OptimizationProblem): Promise<OptimizationResult>;
        setMaxIterations(n: number): void;
        enableQuantumAnnealing(enabled: boolean): void;
      }
    }

    /**
     * Post-Quantum Security
     */
    export namespace Security {
      export type PostQuantumAlgorithm =
        | 'CRYSTALS-Kyber'
        | 'CRYSTALS-Dilithium'
        | 'SPHINCS+'
        | 'FALCON';

      export interface QuantumSecureKey {
        readonly algorithm: PostQuantumAlgorithm;
        readonly publicKey: Uint8Array;
        readonly privateKey?: Uint8Array;
      }

      export interface QuantumSecurityProvider {
        generateKeyPair(algorithm: PostQuantumAlgorithm): Promise<QuantumSecureKey>;
        encrypt(data: Uint8Array, publicKey: Uint8Array): Promise<Uint8Array>;
        decrypt(data: Uint8Array, privateKey: Uint8Array): Promise<Uint8Array>;
        sign(data: Uint8Array, privateKey: Uint8Array): Promise<Uint8Array>;
        verify(data: Uint8Array, signature: Uint8Array, publicKey: Uint8Array): Promise<boolean>;
      }
    }
  }

  // ============================================================================
  // GRAIL NEXUS NAMESPACE
  // ============================================================================

  /**
   * Nexus namespace - ops::pipeline (just pipes connecting things)
   * No round tables, just data flowing through tubes
   */
  export namespace Nexus {
    /**
     * Protocol Bridge
     */
    export namespace Bridge {
      export type ProtocolType = 'mcp' | 'grpc' | 'rest' | 'graphql' | 'websocket';

      export interface BridgeConfig {
        readonly sourceProtocol: ProtocolType;
        readonly targetProtocol: ProtocolType;
        readonly transformers?: MessageTransformer[];
      }

      export interface MessageTransformer {
        readonly name: string;
        transform(message: unknown): unknown;
      }

      export interface ProtocolBridge {
        connect(config: BridgeConfig): Promise<void>;
        send(message: unknown): Promise<unknown>;
        disconnect(): Promise<void>;
        getStatus(): BridgeStatus;
      }

      export interface BridgeStatus {
        readonly connected: boolean;
        readonly latency: number;
        readonly messagesProcessed: number;
      }
    }

    /**
     * Value Flow Management
     */
    export namespace Flow {
      export interface FlowNode {
        readonly id: string;
        readonly type: 'source' | 'processor' | 'sink';
        readonly handler: (value: unknown) => Promise<unknown>;
      }

      export interface FlowEdge {
        readonly source: string;
        readonly target: string;
        readonly weight?: number;
      }

      export interface ValueFlowGraph {
        addNode(node: FlowNode): void;
        addEdge(edge: FlowEdge): void;
        removeNode(id: string): void;
        execute(input: unknown): Promise<unknown>;
        getMetrics(): FlowMetrics;
      }

      export interface FlowMetrics {
        readonly totalValueProcessed: number;
        readonly extractionEfficiency: number;
        readonly amplificationFactor: number;
      }
    }

    /**
     * Service Mesh Integration
     */
    export namespace Mesh {
      export interface ServiceDescriptor {
        readonly name: string;
        readonly namespace: NamespacePath;
        readonly endpoints: string[];
        readonly healthCheck?: string;
      }

      export interface MeshConfig {
        readonly loadBalancing: 'round-robin' | 'least-connections' | 'weighted';
        readonly retryPolicy?: RetryPolicy;
        readonly circuitBreaker?: CircuitBreakerConfig;
      }

      export interface RetryPolicy {
        readonly maxRetries: number;
        readonly backoffMs: number;
        readonly exponential: boolean;
      }

      export interface CircuitBreakerConfig {
        readonly threshold: number;
        readonly timeout: number;
        readonly halfOpenRequests: number;
      }

      export interface ServiceMesh {
        register(service: ServiceDescriptor): Promise<void>;
        discover(namespace: NamespacePath): Promise<ServiceDescriptor[]>;
        invoke(namespace: NamespacePath, method: string, params: unknown): Promise<unknown>;
        getHealth(): Promise<Map<string, 'healthy' | 'degraded' | 'unhealthy'>>;
      }
    }
  }

  // ============================================================================
  // GRAIL MARKET NAMESPACE
  // ============================================================================

  /**
   * Market namespace - reality::alpha_is_luck
   * Uncomfortable truth: most alpha is just luck and timing
   */
  export namespace Market {
    /**
     * Alpha Generation Engine
     */
    export interface AlphaSignal {
      readonly symbol: string;
      readonly direction: 'long' | 'short' | 'neutral';
      readonly strength: number;
      readonly confidence: number;
      readonly timestamp: Date;
    }

    export interface AlphaModel {
      readonly name: string;
      readonly type: 'momentum' | 'mean-reversion' | 'statistical-arbitrage' | 'ml-based';
      generateSignals(data: MarketData[]): Promise<AlphaSignal[]>;
      backtest(historicalData: MarketData[]): Promise<BacktestResult>;
    }

    export interface MarketData {
      readonly symbol: string;
      readonly open: number;
      readonly high: number;
      readonly low: number;
      readonly close: number;
      readonly volume: number;
      readonly timestamp: Date;
    }

    export interface BacktestResult {
      readonly returns: number;
      readonly sharpeRatio: number;
      readonly maxDrawdown: number;
      readonly winRate: number;
    }

    export interface AlphaGenerator {
      registerModel(model: AlphaModel): void;
      generateAlpha(symbols: string[]): Promise<number>;
      getRiskFreeAlpha(): Promise<number>;
      getPerformanceMetrics(): AlphaMetrics;
    }

    export interface AlphaMetrics {
      readonly totalAlpha: number;
      readonly consistencyScore: number;
      readonly riskAdjustedReturn: number;
    }



    /**
     * Liquidity Optimization
     */
    export interface LiquidityPool {
      readonly id: string;
      readonly assets: string[];
      readonly totalValueLocked: number;
      readonly apr: number;
    }

    export interface OptimizationParams {
      readonly targetReturn: number;
      readonly maxSlippage: number;
      readonly rebalanceThreshold: number;
    }

    export interface LiquidityOptimizer {
      analyzePools(pools: LiquidityPool[]): Promise<LiquidityAnalysis>;
      optimize(params: OptimizationParams): Promise<OptimizedAllocation>;
      rebalance(currentAllocation: Map<string, number>): Promise<RebalanceResult>;
    }

    export interface LiquidityAnalysis {
      readonly score: number;
      readonly executionEfficiency: number;
      readonly slippageReduction: number;
    }

    export interface OptimizedAllocation {
      readonly allocations: Map<string, number>;
      readonly expectedReturn: number;
      readonly risk: number;
    }

    export interface RebalanceResult {
      readonly trades: Trade[];
      readonly estimatedCost: number;
      readonly newAllocation: Map<string, number>;
    }

    export interface Trade {
      readonly from: string;
      readonly to: string;
      readonly amount: number;
      readonly price: number;
    }
    /**
     * Predictive Oracle
     */
    export namespace Oracle {
      export interface Prediction {
        readonly target: string;
        readonly value: number;
        readonly confidence: number;
        readonly horizon: string;
        readonly timestamp: Date;
      }

      export interface OracleModel {
        readonly name: string;
        readonly accuracy: number;
        predict(input: unknown): Promise<Prediction>;
        calibrate(historicalData: unknown[]): Promise<void>;
      }

      export interface PredictiveOracle {
        registerModel(model: OracleModel): void;
        getPrediction(target: string, horizon: string): Promise<Prediction>;
        getConsensus(target: string): Promise<Prediction>;
        getAccuracyMetrics(): Promise<Map<string, number>>;
      }
    }
  }

  // ============================================================================
  // GRAIL CONVERTERS NAMESPACE
  // ============================================================================

  /**
   * Converters namespace - dissect::type_surgery (clinical format operations)
   * No magic swords, just surgical type conversions
   */
  export namespace Converters {
    /**
     * Type Conversion
     */
    export namespace Type {
      export interface TypeDescriptor {
        readonly name: string;
        readonly schema: unknown;
        readonly nullable: boolean;
        readonly default?: unknown;
      }

      export interface TypeConversion<S, T> {
        readonly sourceType: TypeDescriptor;
        readonly targetType: TypeDescriptor;
        convert(source: S): T;
        validate(value: unknown): value is S;
      }

      export interface TypeConverter {
        register<S, T>(conversion: TypeConversion<S, T>): void;
        convert<S, T>(value: S, sourceType: string, targetType: string): T;
        canConvert(sourceType: string, targetType: string): boolean;
        getConversionPath(sourceType: string, targetType: string): string[];
      }
    }

    /**
     * Format Conversion
     */
    export namespace Format {
      export type SupportedFormat =
        | 'json'
        | 'yaml'
        | 'xml'
        | 'csv'
        | 'protobuf'
        | 'avro'
        | 'parquet';

      export interface FormatOptions {
        readonly pretty?: boolean;
        readonly encoding?: string;
        readonly compression?: 'gzip' | 'brotli' | 'none';
      }

      export interface FormatConverter {
        convert(data: unknown, from: SupportedFormat, to: SupportedFormat, options?: FormatOptions): Promise<unknown>;
        serialize(data: unknown, format: SupportedFormat, options?: FormatOptions): Promise<Uint8Array>;
        deserialize(data: Uint8Array, format: SupportedFormat): Promise<unknown>;
        detectFormat(data: Uint8Array): Promise<SupportedFormat | null>;
      }
    }

    /**
     * Schema Migration
     */
    export namespace Schema {
      export interface SchemaVersion {
        readonly version: string;
        readonly schema: unknown;
        readonly createdAt: Date;
      }

      export interface MigrationStep {
        readonly fromVersion: string;
        readonly toVersion: string;
        readonly up: (data: unknown) => unknown;
        readonly down: (data: unknown) => unknown;
      }

      export interface SchemaMigrator {
        registerSchema(version: SchemaVersion): void;
        addMigration(step: MigrationStep): void;
        migrate(data: unknown, fromVersion: string, toVersion: string): Promise<unknown>;
        getMigrationPath(fromVersion: string, toVersion: string): MigrationStep[];
        validateAgainstSchema(data: unknown, version: string): Promise<boolean>;
      }
    }

    /**
     * Quantum-Assisted Conversion
     * @deprecated Use direct imports from './converters-quantum.js' instead
   *
   * NOTE: Previously modeled using nested TypeScript namespaces:
   *   - Protocols.Standard
   *   - Protocols.MCP
   *   - Protocols.Bridge
   *
   * To align with ES2015 module style, these are now expressed as
   * flat, exported interfaces with names that encode the hierarchy.
   */
  export interface ProtocolsStandardProtocolMessage {
    readonly type: string;
    readonly payload: unknown;
    readonly signature: Uint8Array;
    readonly timestamp: Date;
  }

  export interface ProtocolsStandardProtocol {
    send(message: ProtocolsStandardProtocolMessage): Promise<void>;
    receive(): AsyncGenerator<ProtocolsStandardProtocolMessage>;
    verify(message: ProtocolsStandardProtocolMessage): Promise<boolean>;
    seal(message: ProtocolsStandardProtocolMessage): Promise<ProtocolsStandardProtocolMessage>;
  }

  /**
   * MCP Extensions (previously Protocols.MCP.*)
   */
  export interface ProtocolsMCPGrailToolDefinition {
    readonly name: string;
    readonly description: string;
    readonly namespace: NamespacePath;
    readonly inputSchema: unknown;
    readonly outputSchema: unknown;
  }

  export interface ProtocolsMCPGrailResourceDefinition {
    readonly uri: string;
    readonly name: string;
    readonly namespace: NamespacePath;
    readonly mimeType: string;
  }

  export interface ProtocolsMCPExtension {
    registerTool(tool: ProtocolsMCPGrailToolDefinition): void;
    registerResource(resource: ProtocolsMCPGrailResourceDefinition): void;
    getTools(): ProtocolsMCPGrailToolDefinition[];
    getResources(): ProtocolsMCPGrailResourceDefinition[];
    invoke(toolName: string, params: unknown): Promise<unknown>;
  }

  /**
   * Inter-Protocol Bridge (previously Protocols.Bridge.*)
   */
  export interface ProtocolsBridgeProtocolAdapter<T, U> {
    readonly sourceProtocol: string;
    readonly targetProtocol: string;
    adapt(message: T): U;
    reverse(message: U): T;
  }

  export interface ProtocolsBridgeInterProtocolBridge {
    registerAdapter<T, U>(adapter: ProtocolsBridgeProtocolAdapter<T, U>): void;
    bridge<T, U>(message: T, sourceProtocol: string, targetProtocol: string): U;
    getSupportedBridges(): Array<[string, string]>;
  }

  // End of Protocols-related type declarations.
}

// ============================================================================
// UTILITY TYPES
// ============================================================================

/**
 * Create a namespace path from parts
 */
export function createNamespacePath(
  domain: GrailDomain,
  subdomain: string,
  component?: string
): NamespacePath {
  if (component) {
    return `grail::${domain}::${subdomain}::${component}` as NamespacePath;
  }
  return `grail::${domain}::${subdomain}` as NamespacePath;
}

/**
 * Parse a namespace path into its components
 */
export function parseNamespacePath(path: NamespacePath): NamespaceIdentifier {
  const parts = path.split('::');
  if (parts.length < 3 || parts[0] !== 'grail') {
    throw new Error(`Invalid namespace path: ${path}`);
  }

  const domain = parts[1];
  if (!VALID_GRAIL_DOMAINS.includes(domain as GrailDomain)) {
    throw new Error(`Invalid domain in namespace path: ${path}. Domain "${domain}" is not a valid GrailDomain.`);
  }

  return {
    domain: domain as GrailDomain,
    subdomain: parts[2],
    component: parts[3],
    fullPath: path
  };
}

/**
 * Validate a namespace path
 */
export function isValidNamespacePath(path: string): path is NamespacePath {
  const domainPattern = VALID_GRAIL_DOMAINS.join('|');
  const regex = new RegExp(`^grail::(${domainPattern})::\\w+(::\\w+)?$`);
  return regex.test(path);
}

// ============================================================================
// END OF NAMESPACE DEFINITIONS
// ============================================================================
