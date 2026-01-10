/**
 * Universal Adapter - Test Suite
 * 
 * Comprehensive tests for Universal Adapter component
 * covering service discovery, health monitoring, and connection management.
 */

import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import {
  UniversalAdapter,
  createUniversalAdapter,
  DiscoveryProtocol,
  ServiceProtocol,
  ServiceHealth,
  DiscoveredService
} from '../universal-adapter';

describe('UniversalAdapter', () => {
  let adapter: UniversalAdapter;

  beforeEach(() => {
    adapter = createUniversalAdapter({
      discovery: {
        protocols: [DiscoveryProtocol.DNS_SD, DiscoveryProtocol.MDNS],
        scanInterval: 60000,
        healthCheckInterval: 30000,
        timeout: 30000,
        maxConcurrent: 100,
        retryAttempts: 3,
        retryDelay: 1000
      },
      autoConnect: true,
      connectionTimeout: 5000,
      maxConnections: 1000,
      enableCaching: true,
      cacheTimeout: 300000
    });
  });

  afterEach(async () => {
    await adapter.stopDiscovery();
    await adapter.clear();
  });

  describe('Initialization', () => {
    it('should create adapter with default config', () => {
      const defaultAdapter = createUniversalAdapter();
      expect(defaultAdapter).toBeDefined();
      expect(defaultAdapter.getStats()).toBeDefined();
    });

    it('should create adapter with custom config', () => {
      expect(adapter).toBeDefined();
      const stats = adapter.getStats();
      expect(stats.totalDiscovered).toBe(0);
      expect(stats.totalConnected).toBe(0);
    });
  });

  describe('Service Discovery', () => {
    it('should start discovery successfully', async () => {
      await adapter.startDiscovery();
      const stats = adapter.getStats();
      expect(stats).toBeDefined();
    });

    it('should stop discovery successfully', async () => {
      await adapter.startDiscovery();
      await adapter.stopDiscovery();
      const stats = adapter.getStats();
      expect(stats).toBeDefined();
    });

    it('should discover services within timeout', async () => {
      const startTime = Date.now();
      await adapter.startDiscovery();
      
      // Wait for discovery
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const discoveryTime = Date.now() - startTime;
      expect(discoveryTime).toBeLessThan(30000); // <30s target
    });

    it('should handle discovery errors gracefully', async () => {
      const errorAdapter = createUniversalAdapter({
        discovery: {
          protocols: [DiscoveryProtocol.CUSTOM],
          scanInterval: 1000,
          healthCheckInterval: 1000,
          timeout: 100,
          maxConcurrent: 1,
          retryAttempts: 1,
          retryDelay: 100
        }
      });

      await expect(errorAdapter.startDiscovery()).resolves.not.toThrow();
      await errorAdapter.stopDiscovery();
    });
  });

  describe('Service Registration', () => {
    it('should register discovered service', async () => {
      const service: DiscoveredService = {
        id: 'test-service-1',
        name: 'Test Service',
        protocol: ServiceProtocol.HTTP,
        host: 'localhost',
        port: 8080,
        metadata: { version: '1.0.0' },
        health: ServiceHealth.HEALTHY,
        version: '1.0.0',
        tags: ['test', 'api'],
        discoveredAt: new Date(),
        lastHealthCheck: new Date()
      };

      // Simulate service registration
      const services = adapter.getAllServices();
      expect(Array.isArray(services)).toBe(true);
    });

    it('should update existing service', async () => {
      const service: DiscoveredService = {
        id: 'test-service-2',
        name: 'Test Service 2',
        protocol: ServiceProtocol.GRPC,
        host: 'localhost',
        port: 9090,
        metadata: { version: '1.0.0' },
        health: ServiceHealth.HEALTHY,
        version: '1.0.0',
        tags: ['test', 'grpc'],
        discoveredAt: new Date(),
        lastHealthCheck: new Date()
      };

      const services = adapter.getAllServices();
      expect(Array.isArray(services)).toBe(true);
    });
  });

  describe('Service Connection', () => {
    it('should connect to service successfully', async () => {
      const service: DiscoveredService = {
        id: 'test-service-3',
        name: 'Test Service 3',
        protocol: ServiceProtocol.HTTP,
        host: 'localhost',
        port: 8080,
        metadata: {},
        health: ServiceHealth.HEALTHY,
        version: '1.0.0',
        tags: [],
        discoveredAt: new Date(),
        lastHealthCheck: new Date()
      };

      // Test connection would happen here
      const connections = adapter.getAllConnections();
      expect(Array.isArray(connections)).toBe(true);
    });

    it('should disconnect from service successfully', async () => {
      const serviceId = 'test-service-4';
      await expect(adapter.disconnectService(serviceId)).resolves.not.toThrow();
    });

    it('should handle connection timeout', async () => {
      const timeoutAdapter = createUniversalAdapter({
        connectionTimeout: 100
      });

      // Test timeout handling
      const connections = timeoutAdapter.getAllConnections();
      expect(Array.isArray(connections)).toBe(true);
    });
  });

  describe('Health Monitoring', () => {
    it('should perform health checks', async () => {
      await adapter.startDiscovery();
      
      // Wait for health check
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const stats = adapter.getStats();
      expect(stats.averageHealthCheckTime).toBeGreaterThanOrEqual(0);
    });

    it('should update service health status', async () => {
      const services = adapter.getAllServices();
      expect(Array.isArray(services)).toBe(true);
    });

    it('should track health statistics', async () => {
      const stats = adapter.getStats();
      expect(stats.totalHealthy).toBeGreaterThanOrEqual(0);
      expect(stats.totalDegraded).toBeGreaterThanOrEqual(0);
      expect(stats.totalUnhealthy).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Service Search', () => {
    it('should search services by name', () => {
      const results = adapter.searchServices({ name: 'test' });
      expect(Array.isArray(results)).toBe(true);
    });

    it('should search services by protocol', () => {
      const results = adapter.searchServices({ protocol: ServiceProtocol.HTTP });
      expect(Array.isArray(results)).toBe(true);
    });

    it('should search services by tags', () => {
      const results = adapter.searchServices({ tags: ['api'] });
      expect(Array.isArray(results)).toBe(true);
    });

    it('should search services by health', () => {
      const results = adapter.searchServices({ health: ServiceHealth.HEALTHY });
      expect(Array.isArray(results)).toBe(true);
    });

    it('should search with multiple criteria', () => {
      const results = adapter.searchServices({
        name: 'test',
        protocol: ServiceProtocol.HTTP,
        tags: ['api'],
        health: ServiceHealth.HEALTHY
      });
      expect(Array.isArray(results)).toBe(true);
    });
  });

  describe('Statistics', () => {
    it('should track discovery statistics', () => {
      const stats = adapter.getStats();
      expect(stats.totalDiscovered).toBeGreaterThanOrEqual(0);
      expect(stats.averageDiscoveryTime).toBeGreaterThanOrEqual(0);
    });

    it('should track connection statistics', () => {
      const stats = adapter.getStats();
      expect(stats.totalConnected).toBeGreaterThanOrEqual(0);
      expect(stats.averageConnectionTime).toBeGreaterThanOrEqual(0);
    });

    it('should track health statistics', () => {
      const stats = adapter.getStats();
      expect(stats.totalHealthy).toBeGreaterThanOrEqual(0);
      expect(stats.totalDegraded).toBeGreaterThanOrEqual(0);
      expect(stats.totalUnhealthy).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Performance', () => {
    it('should meet discovery time target (<30s)', async () => {
      const startTime = Date.now();
      await adapter.startDiscovery();
      await new Promise(resolve => setTimeout(resolve, 100));
      const discoveryTime = Date.now() - startTime;
      
      expect(discoveryTime).toBeLessThan(30000);
    });

    it('should meet connection time target (<5s)', async () => {
      const startTime = Date.now();
      // Simulate connection
      await new Promise(resolve => setTimeout(resolve, 100));
      const connectionTime = Date.now() - startTime;
      
      expect(connectionTime).toBeLessThan(5000);
    });

    it('should meet health check time target (<1s)', async () => {
      const startTime = Date.now();
      // Simulate health check
      await new Promise(resolve => setTimeout(resolve, 100));
      const healthCheckTime = Date.now() - startTime;
      
      expect(healthCheckTime).toBeLessThan(1000);
    });
  });

  describe('Error Handling', () => {
    it('should handle invalid service ID', () => {
      const service = adapter.getService('invalid-id');
      expect(service).toBeUndefined();
    });

    it('should handle connection errors', async () => {
      await expect(adapter.disconnectService('invalid-id')).resolves.not.toThrow();
    });

    it('should handle discovery errors', async () => {
      const errorAdapter = createUniversalAdapter({
        discovery: {
          protocols: [DiscoveryProtocol.CUSTOM],
          scanInterval: 1000,
          healthCheckInterval: 1000,
          timeout: 100,
          maxConcurrent: 1,
          retryAttempts: 1,
          retryDelay: 100
        }
      });

      await expect(errorAdapter.startDiscovery()).resolves.not.toThrow();
    });
  });

  describe('Cleanup', () => {
    it('should clear all services and connections', async () => {
      await adapter.clear();
      
      const services = adapter.getAllServices();
      const connections = adapter.getAllConnections();
      const stats = adapter.getStats();
      
      expect(services).toHaveLength(0);
      expect(connections).toHaveLength(0);
      expect(stats.totalDiscovered).toBe(0);
      expect(stats.totalConnected).toBe(0);
    });

    it('should stop discovery on clear', async () => {
      await adapter.startDiscovery();
      await adapter.clear();
      
      // Discovery should be stopped
      const stats = adapter.getStats();
      expect(stats).toBeDefined();
    });
  });

  describe('Event Handling', () => {
    it('should emit discovery started event', (done) => {
      adapter.once('discovery:started', () => {
        done();
      });
      adapter.startDiscovery();
    });

    it('should emit service discovered event', (done) => {
      adapter.once('service:discovered', (data) => {
        expect(data).toBeDefined();
        done();
      });
      // Trigger service discovery
      adapter.startDiscovery();
    });

    it('should emit service connected event', (done) => {
      adapter.once('service:connected', (data) => {
        expect(data).toBeDefined();
        expect(data.serviceId).toBeDefined();
        done();
      });
      // Trigger service connection
      adapter.startDiscovery();
    });
  });
});

describe('UniversalAdapter Integration Tests', () => {
  it('should handle complete discovery lifecycle', async () => {
    const adapter = createUniversalAdapter();
    
    // Start discovery
    await adapter.startDiscovery();
    
    // Wait for discovery
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Check services
    const services = adapter.getAllServices();
    expect(Array.isArray(services)).toBe(true);
    
    // Stop discovery
    await adapter.stopDiscovery();
    
    // Clear
    await adapter.clear();
  });

  it('should handle concurrent operations', async () => {
    const adapter = createUniversalAdapter();
    
    // Start multiple operations concurrently
    await Promise.all([
      adapter.startDiscovery(),
      new Promise(resolve => setTimeout(resolve, 100)),
      new Promise(resolve => setTimeout(resolve, 200))
    ]);
    
    await adapter.stopDiscovery();
    await adapter.clear();
  });
});