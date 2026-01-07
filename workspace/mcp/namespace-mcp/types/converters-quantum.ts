/**
 * GRAIL Quantum-Assisted Conversion Types
 * @module grail::types::converters::quantum
 * @description Type definitions for quantum-assisted format conversion
 * @version 1.0.0
 */

/**
 * Quantum-Assisted Conversion Configuration
 */
export interface QuantumConversionConfig {
  readonly useQuantumOptimization: boolean;
  readonly parallelism: number;
  readonly errorCorrection: boolean;
}

/**
 * Quantum-Assisted Conversion Result
 */
export interface QuantumConversionResult<T> {
  readonly result: T;
  readonly quantumAdvantage: boolean;
  readonly speedup: number;
  readonly fidelity: number;
}

/**
 * Quantum-Assisted Converter Interface
 */
export interface QuantumAssistedConverter {
  configure(config: QuantumConversionConfig): void;
  convert<S, T>(source: S, targetType: string): Promise<QuantumConversionResult<T>>;
  batchConvert<S, T>(sources: S[], targetType: string): Promise<QuantumConversionResult<T[]>>;
  getQuantumMetrics(): QuantumConversionMetrics;
}

/**
 * Quantum Conversion Metrics
 */
export interface QuantumConversionMetrics {
  readonly totalConversions: number;
  readonly averageSpeedup: number;
  readonly quantumUtilization: number;
}
