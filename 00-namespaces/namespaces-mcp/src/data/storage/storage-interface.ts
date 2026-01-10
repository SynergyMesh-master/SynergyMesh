/**
 * Storage Interface - Core Storage Abstraction Layer
 * 
 * Provides a unified interface for all storage implementations.
 * 
 * Performance Targets:
 * - Read Operations: <5ms (target: <10ms)
 * - Write Operations: <5ms (target: <10ms)
 * 
 * @version 1.0.0
 * @author Machine Native Ops
 */

export interface StorageRecord<K, V> {
  key: K;
  value: V;
  metadata?: {
    createdAt: number;
    updatedAt: number;
    version: number;
    checksum: string;
    size: number;
  };
}

export interface QueryOptions<K, V = unknown> {
  filter?: (record: StorageRecord<K, V>) => boolean;
  limit?: number;
  offset?: number;
  sortBy?: keyof StorageRecord<K, V>;
  sortOrder?: 'asc' | 'desc';
}

export interface QueryResult<K, V> {
  records: StorageRecord<K, V>[];
  total: number;
  hasMore: boolean;
  queryTime: number;
}

export interface StorageTransaction<K, V> {
  id: string;
  status: 'pending' | 'committed' | 'rolledback';
  operations: Array<{
    type: 'read' | 'write' | 'delete';
    key: K;
    value?: V;
  }>;
  commit(): Promise<void>;
  rollback(): Promise<void>;
}

export interface StorageStatistics {
  totalRecords: number;
  totalSize: number;
  readOperations: number;
  writeOperations: number;
  deleteOperations: number;
  averageReadLatency: number;
  averageWriteLatency: number;
  errorRate: number;
  uptime: number;
}

export interface StorageConfig {
  maxSize?: number;
  maxRecords?: number;
  compressionEnabled?: boolean;
  encryptionEnabled?: boolean;
  indexingEnabled?: boolean;
}

export type StorageEventType = 
  | 'record:created'
  | 'record:updated'
  | 'record:deleted'
  | 'transaction:committed'
  | 'transaction:rolledback';

export type StorageEventHandler<K = unknown, V = unknown> = (
  event: StorageEventType,
  data: { key?: K; value?: V; [key: string]: unknown }
) => void;

export abstract class BaseStorage<K, V> implements IStorage<K, V> {
  protected config: Required<StorageConfig>;
  protected eventHandlers: Map<StorageEventType, Set<StorageEventHandler<K, V>>>;
  protected readLatencies: number[] = [];
  protected writeLatencies: number[] = [];
  protected errorCount: number = 0;
  protected operationCount: number = 0;
  protected startTime: number = Date.now();

  constructor(config: StorageConfig = {}) {
    this.config = {
      maxSize: config.maxSize || Number.MAX_SAFE_INTEGER,
      maxRecords: config.maxRecords || Number.MAX_SAFE_INTEGER,
      compressionEnabled: config.compressionEnabled || false,
      encryptionEnabled: config.encryptionEnabled || false,
      indexingEnabled: config.indexingEnabled || true
    };
    this.eventHandlers = new Map();
  }

  on(event: StorageEventType, handler: StorageEventHandler<K, V>): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)!.add(handler);
  }

  off(event: StorageEventType, handler: StorageEventHandler<K, V>): void {
    this.eventHandlers.get(event)?.delete(handler);
  }

  protected emit(event: StorageEventType, data: { key?: K; value?: V; [key: string]: unknown }): void {
    this.eventHandlers.get(event)?.forEach(handler => handler(event, data));
  }

  protected recordLatency(type: 'read' | 'write' | 'delete', latency: number): void {
    if (type === 'read') {
      this.readLatencies.push(latency);
      if (this.readLatencies.length > 1000) this.readLatencies.shift();
    } else if (type === 'write') {
      this.writeLatencies.push(latency);
      if (this.writeLatencies.length > 1000) this.writeLatencies.shift();
    }
  }

  protected recordError(): void {
    this.errorCount++;
    this.operationCount++;
  }

  protected recordSuccess(): void {
    this.operationCount++;
  }

  abstract get(key: K): Promise<V | null>;
  abstract set(key: K, value: V, options?: { ttl?: number }): Promise<void>;
  abstract delete(key: K): Promise<boolean>;
  abstract has(key: K): Promise<boolean>;
  abstract keys(): Promise<K[]>;
  abstract query(options: QueryOptions<K>): Promise<QueryResult<K, V>>;
  abstract createTransaction(): StorageTransaction<K, V>;
  abstract clear(): Promise<void>;

  getStatistics(): StorageStatistics {
    const avgReadLatency = this.readLatencies.length > 0
      ? this.readLatencies.reduce((a, b) => a + b, 0) / this.readLatencies.length
      : 0;
    
    const avgWriteLatency = this.writeLatencies.length > 0
      ? this.writeLatencies.reduce((a, b) => a + b, 0) / this.writeLatencies.length
      : 0;

    return {
      totalRecords: 0,
      totalSize: 0,
      readOperations: this.readLatencies.length,
      writeOperations: this.writeLatencies.length,
      deleteOperations: 0,
      averageReadLatency: avgReadLatency,
      averageWriteLatency: avgWriteLatency,
      errorRate: this.operationCount > 0 ? this.errorCount / this.operationCount : 0,
      uptime: Date.now() - this.startTime
    };
  }
}

export interface IStorage<K, V> {
  get(key: K): Promise<V | null>;
  set(key: K, value: V, options?: { ttl?: number }): Promise<void>;
  delete(key: K): Promise<boolean>;
  has(key: K): Promise<boolean>;
  keys(): Promise<K[]>;
  query(options: QueryOptions<K>): Promise<QueryResult<K, V>>;
  createTransaction(): StorageTransaction<K, V>;
  getStatistics(): StorageStatistics;
  clear(): Promise<void>;
  on(event: StorageEventType, handler: StorageEventHandler<K, V>): void;
  off(event: StorageEventType, handler: StorageEventHandler<K, V>): void;
}

export class StorageFactory {
  static async createMemoryStorage<V>(config?: StorageConfig): Promise<IStorage<string, V>> {
    const { MemoryStorage } = await import('./memory-storage');
    return new MemoryStorage<V>(config);
  }

  static async createFileStorage<V>(config?: StorageConfig): Promise<IStorage<string, V>> {
    const { FileStorage } = await import('./file-storage');
    return new FileStorage<V>(config);
  }

  static async createDatabaseStorage<V>(
    adapter: IDatabaseAdapter<V>,
    dbConfig: { type: string; host?: string; port?: number; database?: string },
    config?: StorageConfig
  ): Promise<IStorage<string, V>> {
    const { DatabaseStorage } = await import('./database-storage');
    return new DatabaseStorage<V>(adapter, dbConfig, config);
  }
}
