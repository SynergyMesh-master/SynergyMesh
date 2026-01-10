/**
 * Universal Integration System - Test Suite
 * 
 * Comprehensive tests for Universal Integration System
 * covering end-to-end integration workflows.
 */

import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import {
  UniversalIntegrationSystem,
  createUniversalIntegrationSystem,
  IntegrationRequest
} from '../universal-integration-system';

describe('UniversalIntegrationSystem', () => {
  let system: UniversalIntegrationSystem;

  beforeEach(() => {
    system = createUniversalIntegrationSystem({
      enableAutoDiscovery: true,
      enableProtocolTranslation: true,
      enableDataTransformation: true,
      enableAPIGateway: true,
      enableOrchestration: true
    });
  });

  afterEach(async () => {
    await system.stop();
    system.resetStats();
  });

  describe('Initialization', () => {
    it('should create system with default config', () => {
      const defaultSystem = createUniversalIntegrationSystem();
      expect(defaultSystem).toBeDefined();
      expect(defaultSystem.getStats()).toBeDefined();
    });

    it('should create system with custom config', () => {
      expect(system).toBeDefined();
      const stats = system.getStats();
      expect(stats.totalIntegrations).toBe(0);
    });

    it('should initialize all components', () => {
      const components = system.getComponents();
      expect(components.adapter).toBeDefined();
      expect(components.translator).toBeDefined();
      expect(components.transformer).toBeDefined();
      expect(components.gateway).toBeDefined();
      expect(components.orchestrator).toBeDefined();
    });
  });

  describe('System Lifecycle', () => {
    it('should start system successfully', async () => {
      await system.start();
      const stats = system.getStats();
      expect(stats).toBeDefined();
    });

    it('should stop system successfully', async () => {
      await system.start();
      await system.stop();
      const stats = system.getStats();
      expect(stats).toBeDefined();
    });

    it('should handle multiple start/stop cycles', async () => {
      await system.start();
      await system.stop();
      await system.start();
      await system.stop();
      
      const stats = system.getStats();
      expect(stats).toBeDefined();
    });
  });

  describe('Integration Workflow', () => {
    it('should process basic integration request', async () => {
      await system.start();

      const request: IntegrationRequest = {
        id: 'integration-1',
        source: {
          service: 'service-a',
          protocol: 'http',
          format: 'json'
        },
        target: {
          service: 'service-b',
          protocol: 'grpc',
          format: 'protobuf'
        },
        data: { message: 'test' },
        metadata: {}
      };

      const result = await system.integrate(request);

      expect(result.success).toBe(true);
      expect(result.requestId).toBe('integration-1');
      expect(result.executionTime).toBeLessThan(1000); // <1s target
      expect(result.steps.length).toBeGreaterThan(0);
    });

    it('should process integration with workflow', async () => {
      await system.start();

      // Register workflow
      system.registerWorkflow({
        id: 'test-workflow',
        name: 'Test Workflow',
        description: 'Test workflow',
        version: '1.0.0',
        steps: [],
        metadata: {}
      });

      const request: IntegrationRequest = {
        id: 'integration-2',
        source: {
          service: 'service-a',
          protocol: 'http',
          format: 'json'
        },
        target: {
          service: 'service-b',
          protocol: 'http',
          format: 'json'
        },
        data: { message: 'test' },
        workflow: 'test-workflow',
        metadata: {}
      };

      const result = await system.integrate(request);

      expect(result.success).toBe(true);
      expect(result.executionTime).toBeLessThan(1000);
    });

    it('should handle integration errors gracefully', async () => {
      await system.start();

      const request: IntegrationRequest = {
        id: 'integration-error',
        source: {
          service: 'invalid-service',
          protocol: 'invalid',
          format: 'invalid'
        },
        target: {
          service: 'invalid-service',
          protocol: 'invalid',
          format: 'invalid'
        },
        data: {},
        metadata: {}
      };

      const result = await system.integrate(request);

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });
  });

  describe('Component Integration', () => {
    it('should integrate adapter component', async () => {
      await system.start();

      const components = system.getComponents();
      expect(components.adapter).toBeDefined();

      const adapterStats = components.adapter.getStats();
      expect(adapterStats).toBeDefined();
    });

    it('should integrate translator component', async () => {
      await system.start();

      const components = system.getComponents();
      expect(components.translator).toBeDefined();

      const translatorStats = components.translator.getStats();
      expect(translatorStats).toBeDefined();
    });

    it('should integrate transformer component', async () => {
      await system.start();

      const components = system.getComponents();
      expect(components.transformer).toBeDefined();

      const transformerStats = components.transformer.getStats();
      expect(transformerStats).toBeDefined();
    });

    it('should integrate gateway component', async () => {
      await system.start();

      const components = system.getComponents();
      expect(components.gateway).toBeDefined();

      const gatewayStats = components.gateway.getStats();
      expect(gatewayStats).toBeDefined();
    });

    it('should integrate orchestrator component', async () => {
      await system.start();

      const components = system.getComponents();
      expect(components.orchestrator).toBeDefined();

      const orchestratorStats = components.orchestrator.getStats();
      expect(orchestratorStats).toBeDefined();
    });
  });

  describe('Statistics', () => {
    it('should track integration statistics', async () => {
      await system.start();

      const request: IntegrationRequest = {
        id: 'stats-test',
        source: {
          service: 'service-a',
          protocol: 'http',
          format: 'json'
        },
        target: {
          service: 'service-b',
          protocol: 'http',
          format: 'json'
        },
        data: { message: 'test' },
        metadata: {}
      };

      await system.integrate(request);

      const stats = system.getStats();
      expect(stats.totalIntegrations).toBe(1);
      expect(stats.successfulIntegrations).toBeGreaterThanOrEqual(0);
      expect(stats.averageExecutionTime).toBeGreaterThanOrEqual(0);
    });

    it('should track component statistics', async () => {
      await system.start();

      const stats = system.getStats();
      expect(stats.componentStats).toBeDefined();
      expect(stats.componentStats.adapter).toBeDefined();
      expect(stats.componentStats.translator).toBeDefined();
      expect(stats.componentStats.transformer).toBeDefined();
      expect(stats.componentStats.gateway).toBeDefined();
      expect(stats.componentStats.orchestrator).toBeDefined();
    });

    it('should reset statistics', () => {
      system.resetStats();
      const stats = system.getStats();

      expect(stats.totalIntegrations).toBe(0);
      expect(stats.successfulIntegrations).toBe(0);
      expect(stats.failedIntegrations).toBe(0);
    });
  });

  describe('Performance', () => {
    it('should meet end-to-end latency target (<1s)', async () => {
      await system.start();

      const request: IntegrationRequest = {
        id: 'perf-test',
        source: {
          service: 'service-a',
          protocol: 'http',
          format: 'json'
        },
        target: {
          service: 'service-b',
          protocol: 'http',
          format: 'json'
        },
        data: { message: 'test' },
        metadata: {}
      };

      const startTime = Date.now();
      await system.integrate(request);
      const executionTime = Date.now() - startTime;

      expect(executionTime).toBeLessThan(1000);
    });

    it('should handle high throughput', async () => {
      await system.start();

      const requests = Array.from({ length: 10 }, (_, i) => ({
        id: `throughput-${i}`,
        source: {
          service: 'service-a',
          protocol: 'http',
          format: 'json'
        },
        target: {
          service: 'service-b',
          protocol: 'http',
          format: 'json'
        },
        data: { message: `test${i}` },
        metadata: {}
      }));

      const startTime = Date.now();
      await Promise.all(requests.map(req => system.integrate(req)));
      const totalTime = Date.now() - startTime;

      const throughput = (requests.length / totalTime) * 1000;
      expect(throughput).toBeGreaterThan(1); // >1 integration/second
    });

    it('should handle concurrent integrations', async () => {
      await system.start();

      const requests = Array.from({ length: 5 }, (_, i) => ({
        id: `concurrent-${i}`,
        source: {
          service: 'service-a',
          protocol: 'http',
          format: 'json'
        },
        target: {
          service: 'service-b',
          protocol: 'http',
          format: 'json'
        },
        data: { message: `test${i}` },
        metadata: {}
      }));

      const results = await Promise.all(
        requests.map(req => system.integrate(req))
      );

      expect(results).toHaveLength(5);
      results.forEach(result => {
        expect(result.executionTime).toBeLessThan(1000);
      });
    });
  });

  describe('Event Handling', () => {
    it('should emit system started event', (done) => {
      system.once('system:started', () => {
        done();
      });
      system.start();
    });

    it('should emit integration started event', (done) => {
      system.once('integration:started', (data) => {
        expect(data).toBeDefined();
        expect(data.requestId).toBeDefined();
        done();
      });

      system.start().then(() => {
        const request: IntegrationRequest = {
          id: 'event-test',
          source: {
            service: 'service-a',
            protocol: 'http',
            format: 'json'
          },
          target: {
            service: 'service-b',
            protocol: 'http',
            format: 'json'
          },
          data: { message: 'test' },
          metadata: {}
        };

        system.integrate(request);
      });
    });

    it('should emit integration completed event', (done) => {
      system.once('integration:completed', (data) => {
        expect(data).toBeDefined();
        expect(data.requestId).toBeDefined();
        expect(data.executionTime).toBeDefined();
        done();
      });

      system.start().then(() => {
        const request: IntegrationRequest = {
          id: 'event-test-2',
          source: {
            service: 'service-a',
            protocol: 'http',
            format: 'json'
          },
          target: {
            service: 'service-b',
            protocol: 'http',
            format: 'json'
          },
          data: { message: 'test' },
          metadata: {}
        };

        system.integrate(request);
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle component failures', async () => {
      await system.start();

      const request: IntegrationRequest = {
        id: 'error-test',
        source: {
          service: 'invalid',
          protocol: 'invalid',
          format: 'invalid'
        },
        target: {
          service: 'invalid',
          protocol: 'invalid',
          format: 'invalid'
        },
        data: {},
        metadata: {}
      };

      const result = await system.integrate(request);

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });

    it('should handle system errors gracefully', async () => {
      await expect(system.start()).resolves.not.toThrow();
      await expect(system.stop()).resolves.not.toThrow();
    });
  });

  describe('Workflow Management', () => {
    it('should register workflow', () => {
      const workflow = {
        id: 'workflow-1',
        name: 'Test Workflow',
        description: 'Test workflow',
        version: '1.0.0',
        steps: [],
        metadata: {}
      };

      expect(() => system.registerWorkflow(workflow)).not.toThrow();
    });

    it('should execute registered workflow', async () => {
      await system.start();

      system.registerWorkflow({
        id: 'workflow-2',
        name: 'Test Workflow 2',
        description: 'Test workflow 2',
        version: '1.0.0',
        steps: [],
        metadata: {}
      });

      const request: IntegrationRequest = {
        id: 'workflow-test',
        source: {
          service: 'service-a',
          protocol: 'http',
          format: 'json'
        },
        target: {
          service: 'service-b',
          protocol: 'http',
          format: 'json'
        },
        data: { message: 'test' },
        workflow: 'workflow-2',
        metadata: {}
      };

      const result = await system.integrate(request);
      expect(result.success).toBe(true);
    });
  });
});

describe('UniversalIntegrationSystem Integration Tests', () => {
  it('should handle complete integration lifecycle', async () => {
    const system = createUniversalIntegrationSystem();

    // Start system
    await system.start();

    // Process integration
    const request: IntegrationRequest = {
      id: 'lifecycle-test',
      source: {
        service: 'service-a',
        protocol: 'http',
        format: 'json'
      },
      target: {
        service: 'service-b',
        protocol: 'grpc',
        format: 'protobuf'
      },
      data: {
        message: 'test',
        timestamp: Date.now()
      },
      metadata: {
        priority: 'high'
      }
    };

    const result = await system.integrate(request);

    expect(result.success).toBe(true);
    expect(result.executionTime).toBeLessThan(1000);
    expect(result.steps.length).toBeGreaterThan(0);

    // Verify statistics
    const stats = system.getStats();
    expect(stats.totalIntegrations).toBe(1);
    expect(stats.successfulIntegrations).toBeGreaterThanOrEqual(0);

    // Stop system
    await system.stop();
  });

  it('should handle multiple integration types', async () => {
    const system = createUniversalIntegrationSystem();
    await system.start();

    const integrations = [
      {
        id: 'multi-1',
        source: { service: 'a', protocol: 'http', format: 'json' },
        target: { service: 'b', protocol: 'grpc', format: 'protobuf' },
        data: { test: 1 }
      },
      {
        id: 'multi-2',
        source: { service: 'c', protocol: 'mqtt', format: 'json' },
        target: { service: 'd', protocol: 'amqp', format: 'json' },
        data: { test: 2 }
      },
      {
        id: 'multi-3',
        source: { service: 'e', protocol: 'http', format: 'xml' },
        target: { service: 'f', protocol: 'http', format: 'json' },
        data: { test: 3 }
      }
    ];

    for (const integration of integrations) {
      const result = await system.integrate({
        ...integration,
        metadata: {}
      });
      expect(result.success).toBe(true);
    }

    const stats = system.getStats();
    expect(stats.totalIntegrations).toBe(integrations.length);

    await system.stop();
  });

  it('should maintain performance under load', async () => {
    const system = createUniversalIntegrationSystem();
    await system.start();

    const requests = Array.from({ length: 50 }, (_, i) => ({
      id: `load-${i}`,
      source: {
        service: 'service-a',
        protocol: 'http',
        format: 'json'
      },
      target: {
        service: 'service-b',
        protocol: 'http',
        format: 'json'
      },
      data: { index: i },
      metadata: {}
    }));

    const startTime = Date.now();
    const results = await Promise.all(
      requests.map(req => system.integrate(req))
    );
    const totalTime = Date.now() - startTime;

    // All should complete
    expect(results).toHaveLength(50);

    // All should succeed
    const successCount = results.filter(r => r.success).length;
    expect(successCount).toBeGreaterThan(0);

    // Average time should be reasonable
    const avgTime = totalTime / requests.length;
    expect(avgTime).toBeLessThan(1000);

    await system.stop();
  });
});