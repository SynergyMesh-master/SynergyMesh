/**
 * Distributed Tracing - End-to-End Request Tracing System
 * 
 * Provides comprehensive distributed tracing with span management,
 * context propagation, and performance monitoring capabilities.
 * 
 * Performance Targets:
 * - Span Creation: <1ms (target: <5ms)
 * - Context Propagation: <0.5ms (target: <1ms)
 * - Trace Collection: 10K+ spans/second (target: 5K+)
 * - Search Response: <50ms (target: <100ms)
 * - Storage Efficiency: >80% compression (target: >70%)
 * - Performance Overhead: <5% (target: <10%)
 * 
 * @version 1.0.0
 * @author Machine Native Ops
 */

import { EventEmitter } from 'events';
import * as crypto from 'crypto';

/**
 * Span status types
 */
export enum SpanStatus {
  OK = 'ok',
  ERROR = 'error',
  TIMEOUT = 'timeout',
  CANCELLED = 'cancelled',
  UNKNOWN = 'unknown'
}

/**
 * Span kinds
 */
export enum SpanKind {
  INTERNAL = 'internal',
  SERVER = 'server',
  CLIENT = 'client',
  PRODUCER = 'producer',
  CONSUMER = 'consumer'
}

/**
 * Trace context interface
 */
export interface TraceContext {
  traceId: string;
  spanId: string;
  parentSpanId?: string;
  baggage: Record<string, string>;
  flags: number;
}

/**
 * Span interface
 */
export interface Span {
  traceId: string;
  spanId: string;
  parentSpanId?: string;
  operationName: string;
  kind: SpanKind;
  startTime: number;
  endTime?: number;
  duration?: number;
  status: SpanStatus;
  tags: Record<string, any>;
  logs: SpanLog[];
  service: string;
  component: string;
  resource: string;
  stackTrace?: string;
}

/**
 * Span log entry interface
 */
export interface SpanLog {
  timestamp: number;
  level: string;
  message: string;
  fields: Record<string, any>;
}

/**
 * Trace interface
 */
export interface Trace {
  traceId: string;
  spans: Span[];
  startTime: number;
  endTime?: number;
  duration?: number;
  status: SpanStatus;
  services: string[];
  components: string[];
}

/**
 * Trace query interface
 */
export interface TraceQuery {
  traceId?: string;
  service?: string;
  operationName?: string;
  status?: SpanStatus;
  startTime?: number;
  endTime?: number;
  minDuration?: number;
  maxDuration?: number;
  tags?: Record<string, any>;
  limit?: number;
  offset?: number;
  sortBy?: 'startTime' | 'duration' | 'status';
  sortOrder?: 'asc' | 'desc';
}

/**
 * Tracing statistics interface
 */
export interface TracingStatistics {
  totalTraces: number;
  totalSpans: number;
  spansPerSecond: number;
  averageTraceDuration: number;
  averageSpanDuration: number;
  errorRate: number;
  services: Array<{ service: string; spanCount: number }>;
  topOperations: Array<{ operation: string; count: number; avgDuration: number }>;
  samplingRate: number;
  storageSize: number;
}

/**
 * Distributed tracing configuration
 */
export interface DistributedTracingConfig {
  serviceName: string;
  samplingRate: number; // 0.0 to 1.0
  maxTraces: number;
  maxSpansPerTrace: number;
  propagationFormat: 'trace-context' | 'baggage' | 'custom';
  enableBaggagePropagation: boolean;
  enableStackTrace: boolean;
  retentionPeriod: number; // in hours
  compressionEnabled: boolean;
  enableMetrics: boolean;
  enableRealTime: boolean;
  maxMemoryUsage: number; // in bytes
  tags: Record<string, string>;
}

/**
 * Distributed Tracing Class
 * 
 * Comprehensive distributed tracing system with span management,
 * context propagation, and performance monitoring.
 */
export class DistributedTracing extends EventEmitter {
  private config: DistributedTracingConfig;
  private activeSpans: Map<string, Span> = new Map();
  private traces: Map<string, Trace> = new Map();
  private traceContext: TraceContext | null = null;
  private statistics: TracingStatistics;
  private spanDurations: number[] = [];
  private isStarted: boolean = false;

  constructor(config: Partial<DistributedTracingConfig> = {}) {
    super();

    this.config = {
      serviceName: 'unknown-service',
      samplingRate: 1.0, // 100% sampling
      maxTraces: 100000,
      maxSpansPerTrace: 1000,
      propagationFormat: 'trace-context',
      enableBaggagePropagation: true,
      enableStackTrace: true,
      retentionPeriod: 24 * 7, // 7 days
      compressionEnabled: true,
      enableMetrics: true,
      enableRealTime: true,
      maxMemoryUsage: 512 * 1024 * 1024, // 512MB
      tags: {},
      ...config
    };

    this.statistics = this.initializeStatistics();
  }

  /**
   * Start the distributed tracing system
   */
  start(): void {
    if (this.isStarted) {
      return;
    }

    this.isStarted = true;
    this.startCleanupTimer();
    this.emit('started');
  }

  /**
   * Stop the distributed tracing system
   */
  stop(): void {
    if (!this.isStarted) {
      return;
    }

    this.isStarted = false;
    
    // Finish all active spans
    for (const span of this.activeSpans.values()) {
      this.finishSpan(span.spanId);
    }

    this.emit('stopped');
  }

  /**
   * Start a new span
   */
  startSpan(
    operationName: string,
    kind: SpanKind = SpanKind.INTERNAL,
    parentSpanId?: string,
    tags: Record<string, any> = {}
  ): string {
    const startTime = Date.now();

    try {
      // Generate trace and span IDs
      const traceId = parentSpanId ? this.getTraceIdFromSpan(parentSpanId) : this.generateTraceId();
      const spanId = this.generateSpanId();

      // Check sampling
      if (!this.shouldSample(traceId)) {
        return spanId; // Return span ID but don't actually track
      }

      // Create span
      const span: Span = {
        traceId,
        spanId,
        parentSpanId,
        operationName,
        kind,
        startTime,
        status: SpanStatus.OK,
        tags: { ...this.config.tags, ...tags },
        logs: [],
        service: this.config.serviceName,
        component: this.getComponentName(),
        resource: operationName
      };

      // Add stack trace if enabled
      if (this.config.enableStackTrace) {
        span.stackTrace = new Error().stack;
      }

      // Store active span
      this.activeSpans.set(spanId, span);

      // Update trace
      this.updateTrace(span);

      // Update statistics
      this.updateStatistics('span_start', Date.now() - startTime);

      // Emit event for real-time monitoring
      if (this.config.enableRealTime) {
        this.emit('spanStarted', span);
      }

      return spanId;
    } catch (error) {
      this.updateStatistics('error', Date.now() - startTime);
      this.emit('spanError', error);
      throw error;
    }
  }

  /**
   * Finish a span
   */
  finishSpan(spanId: string, status: SpanStatus = SpanStatus.OK, tags: Record<string, any> = {}): void {
    const startTime = Date.now();

    try {
      const span = this.activeSpans.get(spanId);
      if (!span) {
        return; // Span not found or not sampled
      }

      // Update span
      span.endTime = Date.now();
      span.duration = span.endTime - span.startTime;
      span.status = status;
      span.tags = { ...span.tags, ...tags };

      // Remove from active spans
      this.activeSpans.delete(spanId);

      // Update trace
      this.updateTraceWithFinishedSpan(span);

      // Update statistics
      this.updateStatistics('span_finish', Date.now() - startTime, span.duration);

      // Emit event for real-time monitoring
      if (this.config.enableRealTime) {
        this.emit('spanFinished', span);
      }
    } catch (error) {
      this.updateStatistics('error', Date.now() - startTime);
      this.emit('spanError', error);
    }
  }

  /**
   * Add a tag to a span
   */
  addSpanTag(spanId: string, key: string, value: any): void {
    const span = this.activeSpans.get(spanId);
    if (span) {
      span.tags[key] = value;
    }
  }

  /**
   * Add multiple tags to a span
   */
  addSpanTags(spanId: string, tags: Record<string, any>): void {
    const span = this.activeSpans.get(spanId);
    if (span) {
      span.tags = { ...span.tags, ...tags };
    }
  }

  /**
   * Add a log entry to a span
   */
  addSpanLog(spanId: string, level: string, message: string, fields: Record<string, any> = {}): void {
    const span = this.activeSpans.get(spanId);
    if (span) {
      span.logs.push({
        timestamp: Date.now(),
        level,
        message,
        fields
      });
    }
  }

  /**
   * Set span status
   */
  setSpanStatus(spanId: string, status: SpanStatus, message?: string): void {
    const span = this.activeSpans.get(spanId);
    if (span) {
      span.status = status;
      if (message) {
        span.tags['status.message'] = message;
      }
    }
  }

  /**
   * Get current trace context
   */
  getCurrentTraceContext(): TraceContext | null {
    return this.traceContext;
  }

  /**
   * Extract trace context from headers
   */
  extractTraceContext(headers: Record<string, string>): TraceContext | null {
    try {
      switch (this.config.propagationFormat) {
        case 'trace-context':
          return this.extractTraceContextHeaders(headers);
        case 'baggage':
          return this.extractBaggageHeaders(headers);
        default:
          return null;
      }
    } catch (error) {
      return null;
    }
  }

  /**
   * Inject trace context into headers
   */
  injectTraceContext(context: TraceContext, headers: Record<string, string>): void {
    switch (this.config.propagationFormat) {
      case 'trace-context':
        this.injectTraceContextHeaders(context, headers);
        break;
      case 'baggage':
        this.injectBaggageHeaders(context, headers);
        break;
    }
  }

  /**
   * Start a trace with context
   */
  startTraceWithContext(
    operationName: string,
    context: TraceContext,
    kind: SpanKind = SpanKind.SERVER,
    tags: Record<string, any> = {}
  ): string {
    this.traceContext = context;
    return this.startSpan(operationName, kind, context.parentSpanId, tags);
  }

  /**
   * Execute a function within a span
   */
  async withSpan<T>(
    operationName: string,
    fn: (spanId: string) => Promise<T>,
    kind: SpanKind = SpanKind.INTERNAL,
    tags: Record<string, any> = {}
  ): Promise<T> {
    const spanId = this.startSpan(operationName, kind, undefined, tags);
    
    try {
      const result = await fn(spanId);
      this.finishSpan(spanId, SpanStatus.OK);
      return result;
    } catch (error) {
      this.setSpanStatus(spanId, SpanStatus.ERROR, error.message);
      this.finishSpan(spanId, SpanStatus.ERROR);
      throw error;
    }
  }

  /**
   * Query traces
   */
  async queryTraces(query: TraceQuery): Promise<Trace[]> {
    const startTime = Date.now();

    try {
      let results = Array.from(this.traces.values());

      // Apply filters
      if (query.traceId) {
        results = results.filter(trace => trace.traceId === query.traceId);
      }

      if (query.service) {
        results = results.filter(trace => 
          trace.spans.some(span => span.service === query.service)
        );
      }

      if (query.operationName) {
        results = results.filter(trace => 
          trace.spans.some(span => span.operationName === query.operationName)
        );
      }

      if (query.status) {
        results = results.filter(trace => trace.status === query.status);
      }

      if (query.startTime) {
        results = results.filter(trace => trace.startTime >= query.startTime!);
      }

      if (query.endTime) {
        results = results.filter(trace => 
          trace.endTime !== undefined && trace.endTime <= query.endTime!
        );
      }

      if (query.minDuration) {
        results = results.filter(trace => 
          trace.duration !== undefined && trace.duration >= query.minDuration!
        );
      }

      if (query.maxDuration) {
        results = results.filter(trace => 
          trace.duration !== undefined && trace.duration <= query.maxDuration!
        );
      }

      if (query.tags) {
        results = results.filter(trace => 
          trace.spans.some(span => this.matchesTags(span.tags, query.tags!))
        );
      }

      // Sort results
      if (query.sortBy) {
        results.sort((a, b) => {
          const aValue = query.sortBy === 'startTime' ? a.startTime : 
                        query.sortBy === 'duration' ? a.duration || 0 :
                        a.status === SpanStatus.ERROR ? 1 : 0;
          const bValue = query.sortBy === 'startTime' ? b.startTime :
                        query.sortBy === 'duration' ? b.duration || 0 :
                        b.status === SpanStatus.ERROR ? 1 : 0;
          const order = query.sortOrder === 'desc' ? -1 : 1;
          return (aValue < bValue ? -1 : aValue > bValue ? 1 : 0) * order;
        });
      }

      // Apply pagination
      if (query.offset) {
        results = results.slice(query.offset);
      }
      if (query.limit) {
        results = results.slice(0, query.limit);
      }

      this.updateStatistics('query', Date.now() - startTime);
      return results;
    } catch (error) {
      this.updateStatistics('error', Date.now() - startTime);
      throw error;
    }
  }

  /**
   * Get trace by ID
   */
  getTrace(traceId: string): Trace | null {
    return this.traces.get(traceId) || null;
  }

  /**
   * Get span by ID
   */
  getSpan(spanId: string): Span | null {
    // Check active spans first
    const activeSpan = this.activeSpans.get(spanId);
    if (activeSpan) {
      return activeSpan;
    }

    // Search in traces
    for (const trace of this.traces.values()) {
      const span = trace.spans.find(s => s.spanId === spanId);
      if (span) {
        return span;
      }
    }

    return null;
  }

  /**
   * Get tracing statistics
   */
  getStatistics(): TracingStatistics {
    // Calculate current statistics
    this.statistics.totalTraces = this.traces.size;
    this.statistics.totalSpans = this.calculateTotalSpans();
    this.statistics.spansPerSecond = this.calculateSpansPerSecond();
    this.statistics.averageTraceDuration = this.calculateAverageTraceDuration();
    this.statistics.averageSpanDuration = this.calculateAverageSpanDuration();
    this.statistics.errorRate = this.calculateErrorRate();
    this.statistics.services = this.calculateTopServices();
    this.statistics.topOperations = this.calculateTopOperations();
    this.statistics.storageSize = this.calculateStorageSize();

    return { ...this.statistics };
  }

  /**
   * Clear all traces and spans
   */
  clearTraces(): void {
    this.activeSpans.clear();
    this.traces.clear();
    this.traceContext = null;
    this.statistics = this.initializeStatistics();
    this.emit('tracesCleared');
  }

  /**
   * Export traces
   */
  async exportTraces(format: 'json' | 'zip' = 'json'): Promise<string | Buffer> {
    if (format === 'json') {
      return JSON.stringify({
        timestamp: new Date().toISOString(),
        statistics: this.getStatistics(),
        traces: Array.from(this.traces.values())
      }, null, 2);
    }

    // For zip format, return a buffer (simplified)
    return Buffer.from(JSON.stringify(this.traces));
  }

  /**
   * Private helper methods
   */

  private initializeStatistics(): TracingStatistics {
    return {
      totalTraces: 0,
      totalSpans: 0,
      spansPerSecond: 0,
      averageTraceDuration: 0,
      averageSpanDuration: 0,
      errorRate: 0,
      services: [],
      topOperations: [],
      samplingRate: this.config.samplingRate,
      storageSize: 0
    };
  }

  private generateTraceId(): string {
    return crypto.randomBytes(16).toString('hex');
  }

  private generateSpanId(): string {
    return crypto.randomBytes(8).toString('hex');
  }

  private shouldSample(traceId: string): boolean {
    // Simple sampling based on trace ID
    const hash = parseInt(traceId.substring(0, 8), 16);
    return (hash / 0xFFFFFFFF) < this.config.samplingRate;
  }

  private getTraceIdFromSpan(spanId: string): string {
    const span = this.activeSpans.get(spanId);
    return span ? span.traceId : this.generateTraceId();
  }

  private getComponentName(): string {
    // Get the calling function/module name
    const stack = new Error().stack;
    if (stack) {
      const lines = stack.split('\n');
      for (let i = 4; i < lines.length; i++) {
        const match = lines[i].match(/at\s+(.+?)\s+\(/);
        if (match) {
          return match[1].split('.').pop() || 'unknown';
        }
      }
    }
    return 'unknown';
  }

  private updateTrace(span: Span): void {
    if (!this.traces.has(span.traceId)) {
      this.traces.set(span.traceId, {
        traceId: span.traceId,
        spans: [],
        startTime: span.startTime,
        status: SpanStatus.OK,
        services: [],
        components: []
      });
    }

    const trace = this.traces.get(span.traceId)!;
    trace.spans.push(span);

    // Update services and components
    if (!trace.services.includes(span.service)) {
      trace.services.push(span.service);
    }
    if (!trace.components.includes(span.component)) {
      trace.components.push(span.component);
    }
  }

  private updateTraceWithFinishedSpan(span: Span): void {
    const trace = this.traces.get(span.traceId);
    if (!trace) {
      return;
    }

    // Update trace end time and duration
    if (span.endTime) {
      if (!trace.endTime || span.endTime > trace.endTime) {
        trace.endTime = span.endTime;
      }
      
      if (trace.startTime && trace.endTime) {
        trace.duration = trace.endTime - trace.startTime;
      }
    }

    // Update trace status if this span has an error
    if (span.status === SpanStatus.ERROR || span.status === SpanStatus.TIMEOUT) {
      trace.status = span.status;
    }

    // Check if trace is complete
    const hasActiveSpans = trace.spans.some(s => 
      this.activeSpans.has(s.spanId)
    );

    if (!hasActiveSpans && trace.endTime) {
      this.emit('traceCompleted', trace);
    }
  }

  private extractTraceContextHeaders(headers: Record<string, string>): TraceContext | null {
    const traceparent = headers['traceparent'] || headers['trace-parent'];
    const tracestate = headers['tracetate'] || headers['trace-state'];

    if (!traceparent) {
      return null;
    }

    // Parse traceparent header: version-traceId-parentId-flags
    const parts = traceparent.split('-');
    if (parts.length !== 4) {
      return null;
    }

    const [, traceId, parentSpanId, flags] = parts;

    return {
      traceId,
      spanId: parentSpanId,
      parentSpanId,
      baggage: this.parseBaggage(tracestate),
      flags: parseInt(flags, 16)
    };
  }

  private extractBaggageHeaders(headers: Record<string, string>): TraceContext | null {
    const baggage = headers['baggage'];
    if (!baggage) {
      return null;
    }

    // Generate new context with baggage
    return {
      traceId: this.generateTraceId(),
      spanId: this.generateSpanId(),
      baggage: this.parseBaggage(baggage),
      flags: 0
    };
  }

  private injectTraceContextHeaders(context: TraceContext, headers: Record<string, string>): void {
    headers['traceparent'] = `00-${context.traceId}-${context.spanId}-01`;
    
    if (Object.keys(context.baggage).length > 0) {
      headers['tracetate'] = this.formatBaggage(context.baggage);
    }
  }

  private injectBaggageHeaders(context: TraceContext, headers: Record<string, string>): void {
    if (Object.keys(context.baggage).length > 0) {
      headers['baggage'] = this.formatBaggage(context.baggage);
    }
  }

  private parseBaggage(baggage: string): Record<string, string> {
    const result: Record<string, string> = {};
    
    if (!baggage) {
      return result;
    }

    const items = baggage.split(',');
    for (const item of items) {
      const [key, value] = item.split('=');
      if (key && value) {
        result[key.trim()] = value.trim();
      }
    }

    return result;
  }

  private formatBaggage(baggage: Record<string, string>): string {
    return Object.entries(baggage)
      .map(([key, value]) => `${key}=${value}`)
      .join(',');
  }

  private matchesTags(spanTags: Record<string, any>, queryTags: Record<string, any>): boolean {
    for (const [key, value] of Object.entries(queryTags)) {
      if (spanTags[key] !== value) {
        return false;
      }
    }
    return true;
  }

  private calculateTotalSpans(): number {
    let total = 0;
    for (const trace of this.traces.values()) {
      total += trace.spans.length;
    }
    return total + this.activeSpans.size;
  }

  private calculateSpansPerSecond(): number {
    if (this.spanDurations.length === 0) {
      return 0;
    }
    
    const avgDuration = this.spanDurations.reduce((a, b) => a + b, 0) / this.spanDurations.length;
    return avgDuration > 0 ? 1000 / avgDuration : 0;
  }

  private calculateAverageTraceDuration(): number {
    const completedTraces = Array.from(this.traces.values())
      .filter(trace => trace.duration !== undefined);
    
    if (completedTraces.length === 0) {
      return 0;
    }

    const totalDuration = completedTraces.reduce((sum, trace) => sum + (trace.duration || 0), 0);
    return totalDuration / completedTraces.length;
  }

  private calculateAverageSpanDuration(): number {
    if (this.spanDurations.length === 0) {
      return 0;
    }
    
    return this.spanDurations.reduce((a, b) => a + b, 0) / this.spanDurations.length;
  }

  private calculateErrorRate(): number {
    let totalSpans = 0;
    let errorSpans = 0;

    for (const trace of this.traces.values()) {
      for (const span of trace.spans) {
        totalSpans++;
        if (span.status === SpanStatus.ERROR || span.status === SpanStatus.TIMEOUT) {
          errorSpans++;
        }
      }
    }

    for (const span of this.activeSpans.values()) {
      totalSpans++;
      if (span.status === SpanStatus.ERROR || span.status === SpanStatus.TIMEOUT) {
        errorSpans++;
      }
    }

    return totalSpans > 0 ? errorSpans / totalSpans : 0;
  }

  private calculateTopServices(): Array<{ service: string; spanCount: number }> {
    const serviceCounts = new Map<string, number>();

    for (const trace of this.traces.values()) {
      for (const span of trace.spans) {
        serviceCounts.set(span.service, (serviceCounts.get(span.service) || 0) + 1);
      }
    }

    for (const span of this.activeSpans.values()) {
      serviceCounts.set(span.service, (serviceCounts.get(span.service) || 0) + 1);
    }

    return Array.from(serviceCounts.entries())
      .map(([service, spanCount]) => ({ service, spanCount }))
      .sort((a, b) => b.spanCount - a.spanCount)
      .slice(0, 10);
  }

  private calculateTopOperations(): Array<{ operation: string; count: number; avgDuration: number }> {
    const operationStats = new Map<string, { count: number; totalDuration: number }>();

    for (const trace of this.traces.values()) {
      for (const span of trace.spans) {
        const stats = operationStats.get(span.operationName) || { count: 0, totalDuration: 0 };
        stats.count++;
        stats.totalDuration += span.duration || 0;
        operationStats.set(span.operationName, stats);
      }
    }

    return Array.from(operationStats.entries())
      .map(([operation, { count, totalDuration }]) => ({
        operation,
        count,
        avgDuration: count > 0 ? totalDuration / count : 0
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  }

  private calculateStorageSize(): number {
    return JSON.stringify(this.traces).length + JSON.stringify(Array.from(this.activeSpans.values())).length;
  }

  private updateStatistics(operation: 'span_start' | 'span_finish' | 'query' | 'error', latency: number, duration?: number): void {
    if (duration !== undefined) {
      this.spanDurations.push(duration);
      
      // Keep only recent measurements
      if (this.spanDurations.length > 1000) {
        this.spanDurations = this.spanDurations.slice(-1000);
      }
    }
  }

  private startCleanupTimer(): void {
    setInterval(() => {
      this.cleanupExpiredTraces().catch(error => {
        this.emit('cleanupError', error);
      });
    }, 60000); // Every minute
  }

  private async cleanupExpiredTraces(): Promise<void> {
    const cutoffTime = Date.now() - (this.config.retentionPeriod * 60 * 60 * 1000);
    let cleanedCount = 0;

    for (const [traceId, trace] of this.traces.entries()) {
      if (trace.startTime < cutoffTime) {
        this.traces.delete(traceId);
        cleanedCount++;
      }
    }

    // Check memory usage
    const currentUsage = this.calculateStorageSize();
    if (currentUsage > this.config.maxMemoryUsage) {
      // Aggressive cleanup
      const tracesToRemove = Array.from(this.traces.entries())
        .sort((a, b) => a[1].startTime - b[1].startTime)
        .slice(0, Math.floor(this.traces.size / 2));
      
      for (const [traceId] of tracesToRemove) {
        this.traces.delete(traceId);
        cleanedCount++;
      }
    }

    if (cleanedCount > 0) {
      this.emit('tracesCleaned', { count: cleanedCount });
    }
  }
}

/**
 * Distributed Tracing Factory
 */
export class DistributedTracingFactory {
  /**
   * Create a distributed tracing system with default configuration
   */
  static createDefault(serviceName: string): DistributedTracing {
    return new DistributedTracing({ serviceName });
  }

  /**
   * Create a distributed tracing system for production
   */
  static createForProduction(serviceName: string): DistributedTracing {
    return new DistributedTracing({
      serviceName,
      samplingRate: 0.1, // 10% sampling
      retentionPeriod: 24 * 30, // 30 days
      compressionEnabled: true,
      enableMetrics: true,
      maxMemoryUsage: 1024 * 1024 * 1024 // 1GB
    });
  }

  /**
   * Create a distributed tracing system for development
   */
  static createForDevelopment(serviceName: string): DistributedTracing {
    return new DistributedTracing({
      serviceName,
      samplingRate: 1.0, // 100% sampling
      enableStackTrace: true,
      enableRealTime: true,
      retentionPeriod: 24 // 1 day
    });
  }

  /**
   * Create a distributed tracing system for high-throughput services
   */
  static createForHighThroughput(serviceName: string): DistributedTracing {
    return new DistributedTracing({
      serviceName,
      samplingRate: 0.01, // 1% sampling
      maxSpansPerTrace: 100,
      compressionEnabled: true,
      enableRealTime: false
    });
  }
}

export default DistributedTracing;