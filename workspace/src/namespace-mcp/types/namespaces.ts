/**
 * GRAIL MCP Namespace Definitions
 * @module grail::types::namespaces
 * @description The Holy Grail of namespace architecture - Legendary type system
 * @version 1.0.0
 * @valuation $10M+
 */

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

export namespace Grail {
  /**
   * Core namespace - The Sacred Heart of GRAIL
   * Value: $2.5M foundational IP
   */
  export namespace Core {
    /**
     * Divine Protocol - Sacred initialization and lifecycle
     */
    export namespace Protocol {
      export interface DivineConfig {
        readonly version: string;
        readonly activationMode: 'quantum_entanglement' | 'classical' | 'hybrid';
        readonly sacredKeys?: string[];
      }

      export interface ProtocolState {
        readonly initialized: boolean;
        readonly activatedAt?: Date;
        readonly quantumSupremacy: boolean;
      }

      export interface DivineProtocol {
        initiate(config: DivineConfig): Promise<ProtocolState>;
        activate(): Promise<boolean>;
        deactivate(): Promise<void>;
        getState(): ProtocolState;
      }
    }

    /**
     * Registry - Namespace and component registration
     */
    export namespace Registry {
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
    }

    /**
     * Stream - Value stream processing
     */
    export namespace Stream {
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
    }
  }

  // ============================================================================
  // GRAIL QUANTUM NAMESPACE
  // ============================================================================

  /**
   * Quantum namespace - Merlin's Enhancement Magic
   * Value: $2.5M quantum algorithms
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
   * Nexus namespace - The Round Table of Connections
   * Value: $1.5M integration value
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
   * Market namespace - The Quest for Value
   * Value: $2.0M market applications
   */
  export namespace Market {
    /**
     * Alpha Generation Engine
     */
    export namespace Alpha {
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
    }

    /**
     * Liquidity Optimization
     */
    export namespace Liquidity {
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
   * Converters namespace - Excalibur's Transformation Power
   * Value: $1.5M conversion engine
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
     */
    export namespace Quantum {
      export interface QuantumConversionConfig {
        readonly useQuantumOptimization: boolean;
        readonly parallelism: number;
        readonly errorCorrection: boolean;
      }

      export interface QuantumConversionResult<T> {
        readonly result: T;
        readonly quantumAdvantage: boolean;
        readonly speedup: number;
        readonly fidelity: number;
      }

      export interface QuantumAssistedConverter {
        configure(config: QuantumConversionConfig): void;
        convert<S, T>(source: S, targetType: string): Promise<QuantumConversionResult<T>>;
        batchConvert<S, T>(sources: S[], targetType: string): Promise<QuantumConversionResult<T[]>>;
        getQuantumMetrics(): QuantumConversionMetrics;
      }

      export interface QuantumConversionMetrics {
        readonly totalConversions: number;
        readonly averageSpeedup: number;
        readonly quantumUtilization: number;
      }
    }
  }

  // ============================================================================
  // GRAIL PROTOCOLS NAMESPACE
  // ============================================================================

  /**
   * Protocols namespace - Sacred Communication Standards
   */
  export namespace Protocols {
    /**
     * Divine Protocol
     */
    export namespace Divine {
      export interface SacredMessage {
        readonly type: string;
        readonly payload: unknown;
        readonly signature: Uint8Array;
        readonly timestamp: Date;
      }

      export interface SacredProtocol {
        send(message: SacredMessage): Promise<void>;
        receive(): AsyncGenerator<SacredMessage>;
        verify(message: SacredMessage): Promise<boolean>;
        seal(message: SacredMessage): Promise<SacredMessage>;
      }
    }

    /**
     * MCP Extensions
     */
    export namespace MCP {
      export interface GrailToolDefinition {
        readonly name: string;
        readonly description: string;
        readonly namespace: NamespacePath;
        readonly inputSchema: unknown;
        readonly outputSchema: unknown;
      }

      export interface GrailResourceDefinition {
        readonly uri: string;
        readonly name: string;
        readonly namespace: NamespacePath;
        readonly mimeType: string;
      }

      export interface MCPExtension {
        registerTool(tool: GrailToolDefinition): void;
        registerResource(resource: GrailResourceDefinition): void;
        getTools(): GrailToolDefinition[];
        getResources(): GrailResourceDefinition[];
        invoke(toolName: string, params: unknown): Promise<unknown>;
      }
    }

    /**
     * Inter-Protocol Bridge
     */
    export namespace Bridge {
      export interface ProtocolAdapter<T, U> {
        readonly sourceProtocol: string;
        readonly targetProtocol: string;
        adapt(message: T): U;
        reverse(message: U): T;
      }

      export interface InterProtocolBridge {
        registerAdapter<T, U>(adapter: ProtocolAdapter<T, U>): void;
        bridge<T, U>(message: T, sourceProtocol: string, targetProtocol: string): U;
        getSupportedBridges(): Array<[string, string]>;
      }
    }
  }
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

  return {
    domain: parts[1] as GrailDomain,
    subdomain: parts[2],
    component: parts[3],
    fullPath: path
  };
}

/**
 * Validate a namespace path
 */
export function isValidNamespacePath(path: string): path is NamespacePath {
  const regex = /^grail::(core|quantum|nexus|market|converters|protocols)::\w+(::\w+)?$/;
  return regex.test(path);
}

// ============================================================================
// EXPORTS
// ============================================================================

export type {
  GrailDomain,
  NamespacePath,
  NamespaceIdentifier
};
