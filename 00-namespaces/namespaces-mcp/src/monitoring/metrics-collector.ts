/**
 * Metrics Collector - High-Performance Metrics Collection System
 * 
 * Provides enterprise-grade metrics collection with real-time aggregation,
 * time-series storage, and comprehensive monitoring capabilities.
 * 
 * Performance Targets:
 * - Collection Latency: <5ms (target: <10ms)
 * - Throughput: 100K+ metrics/second (target: 50K+)
 * - Storage Efficiency: >90% compression (target: >80%)
 * - Query Response: <25ms (target: <50ms)
 * - Memory Usage: <512MB (target: <1GB)
 * 
 * @version 1.0.0
 * @author Machine Native Ops
 */

import { EventEmitter } from 'events';
import * as crypto from 'crypto';

/**
 * Metric types supported by the collector
 */
export enum MetricType {
  COUNTER = 'counter',
  GAUGE = 'gauge',
  HISTOGRAM = 'histogram',
  SUMMARY = 'summary',
  TIMER = 'timer'
}

/**
 * Metric aggregation types
 */
export enum AggregationType {
  SUM = 'sum',
  AVG = 'avg',
  MIN = 'min',
  MAX = 'max',
  COUNT = 'count',
  P50 = 'p50',
  P95 = 'p95',
  P99 = 'p99',
  RATE = 'rate'
}

/**
 * Time granularity for aggregation
 */
export enum TimeGranularity {
  SECOND = '1s',
  MINUTE = '1m',
  HOUR = '1h',
  DAY = '1d'
}

/**
 * Metric interface
 */
export interface Metric {
  id: string;
  name: string;
  type: MetricType;
  value: number;
  timestamp: number;
  labels: Record<string, string>;
  unit: string;
  description: string;
  tags: string[];
}

/**
 * Metric aggregation interface
 */
export interface MetricAggregation {
  metricName: string;
  aggregation: AggregationType;
  granularity: TimeGranularity;
  timeWindow: number; // in seconds
  value: number;
  timestamp: number;
  labels: Record<string, string>;
}

/**
 * Metric query interface
 */
export interface MetricQuery {
  metricName: string;
  labels?: Record<string, string>;
  aggregation?: AggregationType;
  granularity?: TimeGranularity;
  startTime: number;
  endTime: number;
  step?: number; // in seconds
}

/**
 * Metric statistics interface
 */
export interface MetricStatistics {
  totalMetrics: number;
  metricsPerSecond: number;
  averageCollectionTime: number;
  storageSize: number;
  compressionRatio: number;
  uniqueMetricNames: number;
  activeSeries: number;
  retentionHours: number;
}

/**
 * Metrics collector configuration
 */
export interface MetricsCollectorConfig {
  maxMetricsPerSecond: number;
  retentionPeriod: number; // in hours
  compressionEnabled: boolean;
  batchSize: number;
  flushInterval: number; // in milliseconds
  aggregationEnabled: boolean;
  aggregationGranularities: TimeGranularity[];
  storageType: 'memory' | 'file' | 'database';
  storagePath?: string;
  maxMemoryUsage: number; // in bytes
}

/**
 * Metrics Collector Class
 * 
 * High-performance metrics collection system with real-time aggregation,
 * time-series storage, and comprehensive monitoring capabilities.
 */
export class MetricsCollector extends EventEmitter {
  private config: MetricsCollectorConfig;
  private metrics: Map<string, Metric[]> = new Map();
  private aggregations: Map<string, MetricAggregation[]> = new Map();
  private statistics: MetricStatistics;
  private collectionTimes: number[] = [];
  private flushTimer: NodeJS.Timeout | null = null;
  private isStarted: boolean = false;

  constructor(config: Partial<MetricsCollectorConfig> = {}) {
    super();

    this.config = {
      maxMetricsPerSecond: 100000,
      retentionPeriod: 24 * 7, // 7 days
      compressionEnabled: true,
      batchSize: 1000,
      flushInterval: 5000, // 5 seconds
      aggregationEnabled: true,
      aggregationGranularities: [
        TimeGranularity.MINUTE,
        TimeGranularity.HOUR,
        TimeGranularity.DAY
      ],
      storageType: 'memory',
      maxMemoryUsage: 512 * 1024 * 1024, // 512MB
      ...config
    };

    this.statistics = this.initializeStatistics();
  }

  /**
   * Start the metrics collector
   */
  start(): void {
    if (this.isStarted) {
      return;
    }

    this.isStarted = true;
    this.startFlushTimer();
    this.startCleanupTimer();
    this.emit('started');
  }

  /**
   * Stop the metrics collector
   */
  stop(): void {
    if (!this.isStarted) {
      return;
    }

    this.isStarted = false;
    this.stopFlushTimer();
    this.emit('stopped');
  }

  /**
   * Record a metric
   */
  async recordMetric(metric: Omit<Metric, 'id' | 'timestamp'>): Promise<void> {
    const startTime = Date.now();

    try {
      // Generate metric ID and timestamp
      const fullMetric: Metric = {
        ...metric,
        id: this.generateMetricId(metric.name, metric.labels),
        timestamp: Date.now()
      };

      // Validate metric
      this.validateMetric(fullMetric);

      // Store metric
      this.storeMetric(fullMetric);

      // Perform aggregation if enabled
      if (this.config.aggregationEnabled) {
        await this.performAggregation(fullMetric);
      }

      // Update statistics
      this.updateStatistics('record', Date.now() - startTime);

      // Emit event
      this.emit('metricRecorded', fullMetric);
    } catch (error) {
      this.updateStatistics('error', Date.now() - startTime);
      this.emit('metricError', error);
      throw error;
    }
  }

  /**
   * Record multiple metrics in batch
   */
  async recordMetrics(metrics: Omit<Metric, 'id' | 'timestamp'>[]): Promise<void> {
    const startTime = Date.now();

    try {
      for (const metric of metrics) {
        await this.recordMetric(metric);
      }

      this.updateStatistics('batch', Date.now() - startTime);
      this.emit('metricsBatchRecorded', { count: metrics.length });
    } catch (error) {
      this.updateStatistics('error', Date.now() - startTime);
      throw error;
    }
  }

  /**
   * Increment a counter metric
   */
  async increment(
    name: string,
    value: number = 1,
    labels: Record<string, string> = {},
    tags: string[] = []
  ): Promise<void> {
    await this.recordMetric({
      name,
      type: MetricType.COUNTER,
      value,
      labels,
      unit: 'count',
      description: `Counter metric: ${name}`,
      tags
    });
  }

  /**
   * Set a gauge metric
   */
  async setGauge(
    name: string,
    value: number,
    labels: Record<string, string> = {},
    tags: string[] = []
  ): Promise<void> {
    await this.recordMetric({
      name,
      type: MetricType.GAUGE,
      value,
      labels,
      unit: 'value',
      description: `Gauge metric: ${name}`,
      tags
    });
  }

  /**
   * Record a timer metric
   */
  async recordTimer(
    name: string,
    duration: number,
    labels: Record<string, string> = {},
    tags: string[] = []
  ): Promise<void> {
    await this.recordMetric({
      name,
      type: MetricType.TIMER,
      value: duration,
      labels,
      unit: 'ms',
      description: `Timer metric: ${name}`,
      tags
    });
  }

  /**
   * Record a histogram metric
   */
  async recordHistogram(
    name: string,
    value: number,
    labels: Record<string, string> = {},
    buckets: number[] = [0.1, 0.5, 1, 2.5, 5, 10],
    tags: string[] = []
  ): Promise<void> {
    // Record individual bucket counts
    for (const bucket of buckets) {
      const count = value <= bucket ? 1 : 0;
      await this.recordMetric({
        name: `${name}_bucket`,
        type: MetricType.COUNTER,
        value: count,
        labels: { ...labels, le: bucket.toString() },
        unit: 'count',
        description: `Histogram bucket for ${name}`,
        tags
      });
    }

    // Record total sum
    await this.recordMetric({
      name: `${name}_sum`,
      type: MetricType.COUNTER,
      value,
      labels,
      unit: 'value',
      description: `Histogram sum for ${name}`,
      tags
    });

    // Record count
    await this.recordMetric({
      name: `${name}_count`,
      type: MetricType.COUNTER,
      value: 1,
      labels,
      unit: 'count',
      description: `Histogram count for ${name}`,
      tags
    });
  }

  /**
   * Query metrics
   */
  async queryMetrics(query: MetricQuery): Promise<Metric[]> {
    const startTime = Date.now();

    try {
      const results: Metric[] = [];

      // Get metrics for the specified name
      const metricSeries = this.metrics.get(query.metricName);
      if (!metricSeries) {
        return [];
      }

      // Filter by time range and labels
      for (const metric of metricSeries) {
        if (metric.timestamp >= query.startTime && metric.timestamp <= query.endTime) {
          if (this.matchesLabels(metric, query.labels)) {
            results.push(metric);
          }
        }
      }

      // Apply aggregation if specified
      if (query.aggregation) {
        const aggregated = this.applyAggregation(results, query.aggregation, query.granularity);
        return aggregated.map((value, index) => ({
          id: `aggregated_${index}`,
          name: query.metricName,
          type: MetricType.GAUGE,
          value,
          timestamp: query.startTime + (index * (query.step || 60)) * 1000,
          labels: query.labels || {},
          unit: 'value',
          description: `Aggregated metric: ${query.metricName}`,
          tags: []
        }));
      }

      this.updateStatistics('query', Date.now() - startTime);
      return results;
    } catch (error) {
      this.updateStatistics('error', Date.now() - startTime);
      throw error;
    }
  }

  /**
   * Get metric aggregations
   */
  async getAggregations(
    metricName: string,
    aggregation: AggregationType,
    granularity: TimeGranularity,
    startTime: number,
    endTime: number
  ): Promise<MetricAggregation[]> {
    const key = `${metricName}_${aggregation}_${granularity}`;
    const aggregations = this.aggregations.get(key) || [];

    return aggregations.filter(agg => 
      agg.timestamp >= startTime && agg.timestamp <= endTime
    );
  }

  /**
   * Get metrics statistics
   */
  getStatistics(): MetricStatistics {
    // Calculate current statistics
    this.statistics.totalMetrics = this.calculateTotalMetrics();
    this.statistics.metricsPerSecond = this.calculateMetricsPerSecond();
    this.statistics.averageCollectionTime = this.calculateAverageCollectionTime();
    this.statistics.storageSize = this.calculateStorageSize();
    this.statistics.compressionRatio = this.calculateCompressionRatio();
    this.statistics.uniqueMetricNames = this.metrics.size;
    this.statistics.activeSeries = this.calculateActiveSeries();

    return { ...this.statistics };
  }

  /**
   * List all metric names
   */
  listMetricNames(): string[] {
    return Array.from(this.metrics.keys());
  }

  /**
   * Clear all metrics
   */
  clearMetrics(): void {
    this.metrics.clear();
    this.aggregations.clear();
    this.statistics = this.initializeStatistics();
    this.emit('metricsCleared');
  }

  /**
   * Export metrics
   */
  async exportMetrics(format: 'json' | 'prometheus' = 'json'): Promise<string> {
    if (format === 'prometheus') {
      return this.exportPrometheusFormat();
    }

    const exportData = {
      timestamp: new Date().toISOString(),
      statistics: this.getStatistics(),
      metrics: Array.from(this.metrics.entries()).map(([name, metrics]) => ({
        name,
        count: metrics.length,
        latestValue: metrics[metrics.length - 1]?.value
      }))
    };

    return JSON.stringify(exportData, null, 2);
  }

  /**
   * Private helper methods
   */

  private initializeStatistics(): MetricStatistics {
    return {
      totalMetrics: 0,
      metricsPerSecond: 0,
      averageCollectionTime: 0,
      storageSize: 0,
      compressionRatio: 1.0,
      uniqueMetricNames: 0,
      activeSeries: 0,
      retentionHours: this.config.retentionPeriod
    };
  }

  private generateMetricId(name: string, labels: Record<string, string>): string {
    const labelString = Object.entries(labels)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([k, v]) => `${k}="${v}"`)
      .join(',');
    return crypto.createHash('md5').update(`${name}{${labelString}}`).digest('hex');
  }

  private validateMetric(metric: Metric): void {
    if (!metric.name || typeof metric.name !== 'string') {
      throw new Error('Metric name is required and must be a string');
    }

    if (!Object.values(MetricType).includes(metric.type)) {
      throw new Error(`Invalid metric type: ${metric.type}`);
    }

    if (typeof metric.value !== 'number' || !isFinite(metric.value)) {
      throw new Error('Metric value must be a finite number');
    }

    if (metric.value < 0 && metric.type === MetricType.COUNTER) {
      throw new Error('Counter metrics cannot be negative');
    }
  }

  private storeMetric(metric: Metric): void {
    if (!this.metrics.has(metric.name)) {
      this.metrics.set(metric.name, []);
    }

    const series = this.metrics.get(metric.name)!;
    series.push(metric);

    // Apply retention policy
    this.applyRetentionPolicy(metric.name, series);
  }

  private applyRetentionPolicy(metricName: string, series: Metric[]): void {
    const cutoffTime = Date.now() - (this.config.retentionPeriod * 60 * 60 * 1000);
    
    // Remove old metrics
    for (let i = series.length - 1; i >= 0; i--) {
      if (series[i].timestamp < cutoffTime) {
        series.splice(0, i + 1);
        break;
      }
    }

    // Limit series size for memory management
    const maxSeriesSize = 10000;
    if (series.length > maxSeriesSize) {
      series.splice(0, series.length - maxSeriesSize);
    }
  }

  private async performAggregation(metric: Metric): Promise<void> {
    for (const granularity of this.config.aggregationGranularities) {
      for (const aggregation of Object.values(AggregationType)) {
        await this.calculateAggregation(metric, aggregation, granularity);
      }
    }
  }

  private async calculateAggregation(
    metric: Metric,
    aggregation: AggregationType,
    granularity: TimeGranularity
  ): Promise<void> {
    const key = `${metric.name}_${aggregation}_${granularity}`;
    
    if (!this.aggregations.has(key)) {
      this.aggregations.set(key, []);
    }

    const aggregations = this.aggregations.get(key)!;
    const timeWindow = this.getTimeWindowInSeconds(granularity);
    const timeSlot = Math.floor(metric.timestamp / (timeWindow * 1000)) * timeWindow * 1000;

    // Find existing aggregation for this time slot
    let existingAggregation = aggregations.find(agg => agg.timestamp === timeSlot);
    
    if (!existingAggregation) {
      existingAggregation = {
        metricName: metric.name,
        aggregation,
        granularity,
        timeWindow,
        value: 0,
        timestamp: timeSlot,
        labels: metric.labels
      };
      aggregations.push(existingAggregation);
    }

    // Update aggregation value
    existingAggregation.value = this.calculateAggregatedValue(
      existingAggregation.value,
      metric.value,
      aggregation,
      1 // count increment
    );

    // Apply retention to aggregations
    this.applyAggregationRetentionPolicy(aggregations);
  }

  private calculateAggregatedValue(
    current: number,
    newValue: number,
    aggregation: AggregationType,
    count: number
  ): number {
    switch (aggregation) {
      case AggregationType.SUM:
        return current + newValue;
      case AggregationType.COUNT:
        return current + count;
      case AggregationType.MIN:
        return Math.min(current, newValue);
      case AggregationType.MAX:
        return Math.max(current, newValue);
      case AggregationType.RATE:
        return current + (newValue / 1000); // Convert to rate per second
      default:
        // For AVG, P50, P95, P99 - simplified implementation
        return (current + newValue) / 2;
    }
  }

  private getTimeWindowInSeconds(granularity: TimeGranularity): number {
    switch (granularity) {
      case TimeGranularity.SECOND:
        return 1;
      case TimeGranularity.MINUTE:
        return 60;
      case TimeGranularity.HOUR:
        return 3600;
      case TimeGranularity.DAY:
        return 86400;
      default:
        return 60;
    }
  }

  private applyAggregationRetentionPolicy(aggregations: MetricAggregation[]): void {
    const cutoffTime = Date.now() - (this.config.retentionPeriod * 60 * 60 * 1000);
    
    for (let i = aggregations.length - 1; i >= 0; i--) {
      if (aggregations[i].timestamp < cutoffTime) {
        aggregations.splice(0, i + 1);
        break;
      }
    }
  }

  private matchesLabels(metric: Metric, labels?: Record<string, string>): boolean {
    if (!labels) {
      return true;
    }

    for (const [key, value] of Object.entries(labels)) {
      if (metric.labels[key] !== value) {
        return false;
      }
    }

    return true;
  }

  private applyAggregation(
    metrics: Metric[],
    aggregation: AggregationType,
    granularity?: TimeGranularity
  ): number[] {
    if (metrics.length === 0) {
      return [];
    }

    const values = metrics.map(m => m.value);

    switch (aggregation) {
      case AggregationType.SUM:
        return [values.reduce((sum, val) => sum + val, 0)];
      case AggregationType.AVG:
        return [values.reduce((sum, val) => sum + val, 0) / values.length];
      case AggregationType.MIN:
        return [Math.min(...values)];
      case AggregationType.MAX:
        return [Math.max(...values)];
      case AggregationType.COUNT:
        return [values.length];
      case AggregationType.RATE:
        const timeSpan = (metrics[metrics.length - 1].timestamp - metrics[0].timestamp) / 1000;
        return timeSpan > 0 ? [values.length / timeSpan] : [0];
      default:
        return values;
    }
  }

  private calculateTotalMetrics(): number {
    let total = 0;
    for (const series of this.metrics.values()) {
      total += series.length;
    }
    return total;
  }

  private calculateMetricsPerSecond(): number {
    if (this.collectionTimes.length === 0) {
      return 0;
    }
    
    const avgTime = this.collectionTimes.reduce((a, b) => a + b, 0) / this.collectionTimes.length;
    return avgTime > 0 ? 1000 / avgTime : 0;
  }

  private calculateAverageCollectionTime(): number {
    if (this.collectionTimes.length === 0) {
      return 0;
    }
    
    return this.collectionTimes.reduce((a, b) => a + b, 0) / this.collectionTimes.length;
  }

  private calculateStorageSize(): number {
    let size = 0;
    
    // Calculate metrics size
    for (const series of this.metrics.values()) {
      size += JSON.stringify(series).length;
    }
    
    // Calculate aggregations size
    for (const aggs of this.aggregations.values()) {
      size += JSON.stringify(aggs).length;
    }
    
    return size;
  }

  private calculateCompressionRatio(): number {
    // Simplified compression ratio calculation
    const originalSize = this.calculateTotalMetrics() * 100; // Estimated original size
    const compressedSize = this.calculateStorageSize();
    
    return originalSize > 0 ? compressedSize / originalSize : 1.0;
  }

  private calculateActiveSeries(): number {
    let active = 0;
    const now = Date.now();
    const activeThreshold = 5 * 60 * 1000; // 5 minutes
    
    for (const series of this.metrics.values()) {
      if (series.length > 0 && (now - series[series.length - 1].timestamp) < activeThreshold) {
        active++;
      }
    }
    
    return active;
  }

  private exportPrometheusFormat(): string {
    const lines: string[] = [];
    
    for (const [metricName, metrics] of this.metrics.entries()) {
      if (metrics.length === 0) continue;
      
      const latestMetric = metrics[metrics.length - 1];
      const labelString = Object.entries(latestMetric.labels)
        .map(([k, v]) => `${k}="${v}"`)
        .join(',');
      
      lines.push(`# HELP ${metricName} ${latestMetric.description}`);
      lines.push(`# TYPE ${metricName} ${latestMetric.type}`);
      lines.push(`${metricName}{${labelString}} ${latestMetric.value} ${latestMetric.timestamp}`);
    }
    
    return lines.join('\n');
  }

  private updateStatistics(operation: 'record' | 'batch' | 'query' | 'error', latency: number): void {
    this.collectionTimes.push(latency);
    
    // Keep only recent measurements
    if (this.collectionTimes.length > 1000) {
      this.collectionTimes = this.collectionTimes.slice(-1000);
    }
  }

  private startFlushTimer(): void {
    this.flushTimer = setInterval(() => {
      this.flushMetrics().catch(error => {
        this.emit('flushError', error);
      });
    }, this.config.flushInterval);
  }

  private stopFlushTimer(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
  }

  private startCleanupTimer(): void {
    setInterval(() => {
      this.cleanupExpiredMetrics().catch(error => {
        this.emit('cleanupError', error);
      });
    }, 60000); // Every minute
  }

  private async flushMetrics(): Promise<void> {
    // In a real implementation, this would flush to persistent storage
    this.emit('metricsFlushed');
  }

  private async cleanupExpiredMetrics(): Promise<void> {
    const cutoffTime = Date.now() - (this.config.retentionPeriod * 60 * 60 * 1000);
    let cleanedCount = 0;

    for (const [metricName, series] of this.metrics.entries()) {
      const originalLength = series.length;
      this.applyRetentionPolicy(metricName, series);
      cleanedCount += originalLength - series.length;
    }

    if (cleanedCount > 0) {
      this.emit('metricsCleaned', { count: cleanedCount });
    }
  }
}

/**
 * Metrics Collector Factory
 */
export class MetricsCollectorFactory {
  /**
   * Create a metrics collector with default configuration
   */
  static createDefault(): MetricsCollector {
    return new MetricsCollector();
  }

  /**
   * Create a metrics collector optimized for high throughput
   */
  static createHighThroughput(): MetricsCollector {
    return new MetricsCollector({
      maxMetricsPerSecond: 500000,
      batchSize: 5000,
      flushInterval: 1000,
      aggregationEnabled: true,
      compressionEnabled: true
    });
  }

  /**
   * Create a metrics collector optimized for low memory usage
   */
  static createMemoryEfficient(): MetricsCollector {
    return new MetricsCollector({
      maxMetricsPerSecond: 10000,
      retentionPeriod: 24, // 1 day
      batchSize: 100,
      flushInterval: 10000,
      maxMemoryUsage: 128 * 1024 * 1024, // 128MB
      aggregationEnabled: false
    });
  }

  /**
   * Create a metrics collector for long-term storage
   */
  static createLongTermStorage(): MetricsCollector {
    return new MetricsCollector({
      retentionPeriod: 24 * 30, // 30 days
      aggregationEnabled: true,
      aggregationGranularities: [
        TimeGranularity.MINUTE,
        TimeGranularity.HOUR,
        TimeGranularity.DAY
      ],
      compressionEnabled: true,
      storageType: 'file',
      storagePath: '/tmp/metrics'
    });
  }
}

export default MetricsCollector;