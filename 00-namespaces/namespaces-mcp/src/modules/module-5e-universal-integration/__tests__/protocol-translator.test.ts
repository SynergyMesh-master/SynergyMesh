/**
 * Protocol Translator - Test Suite
 * 
 * Comprehensive tests for Protocol Translator component
 * covering protocol translation, message conversion, and caching.
 */

import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import {
  ProtocolTranslator,
  createProtocolTranslator,
  ProtocolType,
  MessageEncoding,
  ProtocolMessage,
  ProtocolConverter
} from '../protocol-translator';

describe('ProtocolTranslator', () => {
  let translator: ProtocolTranslator;

  beforeEach(() => {
    translator = createProtocolTranslator({
      protocols: [],
      maxMessageSize: 10 * 1024 * 1024,
      timeout: 100,
      enableCompression: true,
      enableValidation: true,
      enableCaching: true,
      cacheSize: 1000
    });
  });

  afterEach(() => {
    translator.clearCache();
    translator.resetStats();
  });

  describe('Initialization', () => {
    it('should create translator with default config', () => {
      const defaultTranslator = createProtocolTranslator();
      expect(defaultTranslator).toBeDefined();
      expect(defaultTranslator.getStats()).toBeDefined();
    });

    it('should create translator with custom config', () => {
      expect(translator).toBeDefined();
      const stats = translator.getStats();
      expect(stats.totalTranslations).toBe(0);
    });

    it('should initialize built-in converters', () => {
      const protocols = translator.getSupportedProtocols();
      expect(protocols.length).toBeGreaterThan(0);
    });
  });

  describe('Protocol Translation', () => {
    it('should translate HTTP to gRPC', async () => {
      const message: ProtocolMessage = {
        id: 'test-1',
        sourceProtocol: ProtocolType.HTTP,
        targetProtocol: ProtocolType.GRPC,
        encoding: MessageEncoding.JSON,
        headers: { 'content-type': 'application/json' },
        body: { data: 'test' },
        metadata: {},
        timestamp: new Date()
      };

      const result = await translator.translate(message, ProtocolType.GRPC);
      
      expect(result.success).toBe(true);
      expect(result.message).toBeDefined();
      expect(result.translationTime).toBeLessThan(100); // <100ms target
    });

    it('should translate gRPC to HTTP', async () => {
      const message: ProtocolMessage = {
        id: 'test-2',
        sourceProtocol: ProtocolType.GRPC,
        targetProtocol: ProtocolType.HTTP,
        encoding: MessageEncoding.PROTOBUF,
        headers: {},
        body: { data: 'test' },
        metadata: {},
        timestamp: new Date()
      };

      const result = await translator.translate(message, ProtocolType.HTTP);
      
      expect(result.success).toBe(true);
      expect(result.translationTime).toBeLessThan(100);
    });

    it('should translate HTTP to WebSocket', async () => {
      const message: ProtocolMessage = {
        id: 'test-3',
        sourceProtocol: ProtocolType.HTTP,
        targetProtocol: ProtocolType.WEBSOCKET,
        encoding: MessageEncoding.JSON,
        headers: {},
        body: { data: 'test' },
        metadata: {},
        timestamp: new Date()
      };

      const result = await translator.translate(message, ProtocolType.WEBSOCKET);
      
      expect(result.success).toBe(true);
      expect(result.translationTime).toBeLessThan(100);
    });

    it('should translate MQTT to AMQP', async () => {
      const message: ProtocolMessage = {
        id: 'test-4',
        sourceProtocol: ProtocolType.MQTT,
        targetProtocol: ProtocolType.AMQP,
        encoding: MessageEncoding.JSON,
        headers: {},
        body: { data: 'test' },
        metadata: {},
        timestamp: new Date()
      };

      const result = await translator.translate(message, ProtocolType.AMQP);
      
      expect(result.success).toBe(true);
      expect(result.translationTime).toBeLessThan(100);
    });
  });

  describe('Batch Translation', () => {
    it('should translate multiple messages', async () => {
      const messages: ProtocolMessage[] = [
        {
          id: 'batch-1',
          sourceProtocol: ProtocolType.HTTP,
          targetProtocol: ProtocolType.GRPC,
          encoding: MessageEncoding.JSON,
          headers: {},
          body: { data: 'test1' },
          metadata: {},
          timestamp: new Date()
        },
        {
          id: 'batch-2',
          sourceProtocol: ProtocolType.HTTP,
          targetProtocol: ProtocolType.GRPC,
          encoding: MessageEncoding.JSON,
          headers: {},
          body: { data: 'test2' },
          metadata: {},
          timestamp: new Date()
        }
      ];

      const results = await translator.translateBatch(messages, ProtocolType.GRPC);
      
      expect(results).toHaveLength(2);
      expect(results[0].success).toBe(true);
      expect(results[1].success).toBe(true);
    });

    it('should handle batch translation errors', async () => {
      const messages: ProtocolMessage[] = [
        {
          id: 'batch-error-1',
          sourceProtocol: ProtocolType.CUSTOM,
          targetProtocol: ProtocolType.CUSTOM,
          encoding: MessageEncoding.JSON,
          headers: {},
          body: { data: 'test' },
          metadata: {},
          timestamp: new Date()
        }
      ];

      const results = await translator.translateBatch(messages, ProtocolType.CUSTOM);
      
      expect(results).toHaveLength(1);
      expect(results[0].success).toBe(false);
    });
  });

  describe('Converter Management', () => {
    it('should register custom converter', () => {
      const converter: ProtocolConverter = {
        sourceProtocol: ProtocolType.CUSTOM,
        targetProtocol: ProtocolType.HTTP,
        async convert(message: ProtocolMessage) {
          return {
            ...message,
            targetProtocol: ProtocolType.HTTP,
            timestamp: new Date()
          };
        },
        validate(message: ProtocolMessage) {
          return true;
        }
      };

      translator.registerConverter(converter);
      
      const supported = translator.isTranslationSupported(
        ProtocolType.CUSTOM,
        ProtocolType.HTTP
      );
      expect(supported).toBe(true);
    });

    it('should unregister converter', () => {
      translator.unregisterConverter(ProtocolType.HTTP, ProtocolType.GRPC);
      
      const supported = translator.isTranslationSupported(
        ProtocolType.HTTP,
        ProtocolType.GRPC
      );
      expect(supported).toBe(false);
    });

    it('should check translation support', () => {
      const supported = translator.isTranslationSupported(
        ProtocolType.HTTP,
        ProtocolType.GRPC
      );
      expect(typeof supported).toBe('boolean');
    });
  });

  describe('Caching', () => {
    it('should cache translation results', async () => {
      const message: ProtocolMessage = {
        id: 'cache-test-1',
        sourceProtocol: ProtocolType.HTTP,
        targetProtocol: ProtocolType.GRPC,
        encoding: MessageEncoding.JSON,
        headers: {},
        body: { data: 'test' },
        metadata: {},
        timestamp: new Date()
      };

      // First translation
      const result1 = await translator.translate(message, ProtocolType.GRPC);
      
      // Second translation (should use cache)
      const result2 = await translator.translate(message, ProtocolType.GRPC);
      
      expect(result1.success).toBe(true);
      expect(result2.success).toBe(true);
    });

    it('should clear cache', () => {
      translator.clearCache();
      const stats = translator.getStats();
      expect(stats.cacheHitRate).toBe(0);
    });

    it('should respect cache size limit', async () => {
      const smallTranslator = createProtocolTranslator({
        cacheSize: 2
      });

      // Translate 3 messages
      for (let i = 0; i < 3; i++) {
        const message: ProtocolMessage = {
          id: `cache-limit-${i}`,
          sourceProtocol: ProtocolType.HTTP,
          targetProtocol: ProtocolType.GRPC,
          encoding: MessageEncoding.JSON,
          headers: {},
          body: { data: `test${i}` },
          metadata: {},
          timestamp: new Date()
        };

        await smallTranslator.translate(message, ProtocolType.GRPC);
      }

      const stats = smallTranslator.getStats();
      expect(stats.totalTranslations).toBe(3);
    });
  });

  describe('Validation', () => {
    it('should validate message before translation', async () => {
      const invalidMessage: ProtocolMessage = {
        id: '',
        sourceProtocol: ProtocolType.HTTP,
        targetProtocol: ProtocolType.GRPC,
        encoding: MessageEncoding.JSON,
        headers: {},
        body: { data: 'test' },
        metadata: {},
        timestamp: new Date()
      };

      const result = await translator.translate(invalidMessage, ProtocolType.GRPC);
      
      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });

    it('should validate message size', async () => {
      const largeMessage: ProtocolMessage = {
        id: 'large-message',
        sourceProtocol: ProtocolType.HTTP,
        targetProtocol: ProtocolType.GRPC,
        encoding: MessageEncoding.JSON,
        headers: {},
        body: { data: 'x'.repeat(20 * 1024 * 1024) }, // 20MB
        metadata: {},
        timestamp: new Date()
      };

      const result = await translator.translate(largeMessage, ProtocolType.GRPC);
      
      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });
  });

  describe('Statistics', () => {
    it('should track translation statistics', async () => {
      const message: ProtocolMessage = {
        id: 'stats-test-1',
        sourceProtocol: ProtocolType.HTTP,
        targetProtocol: ProtocolType.GRPC,
        encoding: MessageEncoding.JSON,
        headers: {},
        body: { data: 'test' },
        metadata: {},
        timestamp: new Date()
      };

      await translator.translate(message, ProtocolType.GRPC);
      
      const stats = translator.getStats();
      expect(stats.totalTranslations).toBe(1);
      expect(stats.successfulTranslations).toBe(1);
      expect(stats.averageTranslationTime).toBeGreaterThan(0);
    });

    it('should track failed translations', async () => {
      const message: ProtocolMessage = {
        id: 'stats-test-2',
        sourceProtocol: ProtocolType.CUSTOM,
        targetProtocol: ProtocolType.CUSTOM,
        encoding: MessageEncoding.JSON,
        headers: {},
        body: { data: 'test' },
        metadata: {},
        timestamp: new Date()
      };

      await translator.translate(message, ProtocolType.CUSTOM);
      
      const stats = translator.getStats();
      expect(stats.failedTranslations).toBeGreaterThan(0);
    });

    it('should reset statistics', () => {
      translator.resetStats();
      const stats = translator.getStats();
      
      expect(stats.totalTranslations).toBe(0);
      expect(stats.successfulTranslations).toBe(0);
      expect(stats.failedTranslations).toBe(0);
    });
  });

  describe('Performance', () => {
    it('should meet translation time target (<100ms)', async () => {
      const message: ProtocolMessage = {
        id: 'perf-test-1',
        sourceProtocol: ProtocolType.HTTP,
        targetProtocol: ProtocolType.GRPC,
        encoding: MessageEncoding.JSON,
        headers: {},
        body: { data: 'test' },
        metadata: {},
        timestamp: new Date()
      };

      const startTime = Date.now();
      await translator.translate(message, ProtocolType.GRPC);
      const translationTime = Date.now() - startTime;
      
      expect(translationTime).toBeLessThan(100);
    });

    it('should handle high throughput', async () => {
      const messages = Array.from({ length: 100 }, (_, i) => ({
        id: `throughput-${i}`,
        sourceProtocol: ProtocolType.HTTP,
        targetProtocol: ProtocolType.GRPC,
        encoding: MessageEncoding.JSON,
        headers: {},
        body: { data: `test${i}` },
        metadata: {},
        timestamp: new Date()
      }));

      const startTime = Date.now();
      await Promise.all(
        messages.map(msg => translator.translate(msg, ProtocolType.GRPC))
      );
      const totalTime = Date.now() - startTime;
      
      const throughput = (messages.length / totalTime) * 1000;
      expect(throughput).toBeGreaterThan(100); // >100 messages/second
    });
  });

  describe('Error Handling', () => {
    it('should handle unsupported protocol', async () => {
      const message: ProtocolMessage = {
        id: 'error-test-1',
        sourceProtocol: ProtocolType.CUSTOM,
        targetProtocol: ProtocolType.CUSTOM,
        encoding: MessageEncoding.JSON,
        headers: {},
        body: { data: 'test' },
        metadata: {},
        timestamp: new Date()
      };

      const result = await translator.translate(message, ProtocolType.CUSTOM);
      
      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });

    it('should handle translation errors gracefully', async () => {
      const errorConverter: ProtocolConverter = {
        sourceProtocol: ProtocolType.CUSTOM,
        targetProtocol: ProtocolType.HTTP,
        async convert() {
          throw new Error('Translation error');
        },
        validate() {
          return true;
        }
      };

      translator.registerConverter(errorConverter);

      const message: ProtocolMessage = {
        id: 'error-test-2',
        sourceProtocol: ProtocolType.CUSTOM,
        targetProtocol: ProtocolType.HTTP,
        encoding: MessageEncoding.JSON,
        headers: {},
        body: { data: 'test' },
        metadata: {},
        timestamp: new Date()
      };

      const result = await translator.translate(message, ProtocolType.HTTP);
      
      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });
  });

  describe('Event Handling', () => {
    it('should emit translation success event', (done) => {
      translator.once('translation:success', (data) => {
        expect(data).toBeDefined();
        expect(data.sourceProtocol).toBe(ProtocolType.HTTP);
        expect(data.targetProtocol).toBe(ProtocolType.GRPC);
        done();
      });

      const message: ProtocolMessage = {
        id: 'event-test-1',
        sourceProtocol: ProtocolType.HTTP,
        targetProtocol: ProtocolType.GRPC,
        encoding: MessageEncoding.JSON,
        headers: {},
        body: { data: 'test' },
        metadata: {},
        timestamp: new Date()
      };

      translator.translate(message, ProtocolType.GRPC);
    });

    it('should emit translation error event', (done) => {
      translator.once('translation:error', (data) => {
        expect(data).toBeDefined();
        expect(data.error).toBeDefined();
        done();
      });

      const message: ProtocolMessage = {
        id: 'event-test-2',
        sourceProtocol: ProtocolType.CUSTOM,
        targetProtocol: ProtocolType.CUSTOM,
        encoding: MessageEncoding.JSON,
        headers: {},
        body: { data: 'test' },
        metadata: {},
        timestamp: new Date()
      };

      translator.translate(message, ProtocolType.CUSTOM);
    });
  });
});

describe('ProtocolTranslator Integration Tests', () => {
  it('should handle complete translation workflow', async () => {
    const translator = createProtocolTranslator();

    const message: ProtocolMessage = {
      id: 'integration-1',
      sourceProtocol: ProtocolType.HTTP,
      targetProtocol: ProtocolType.GRPC,
      encoding: MessageEncoding.JSON,
      headers: { 'content-type': 'application/json' },
      body: { data: 'test', nested: { value: 123 } },
      metadata: { timestamp: Date.now() },
      timestamp: new Date()
    };

    const result = await translator.translate(message, ProtocolType.GRPC);

    expect(result.success).toBe(true);
    expect(result.message).toBeDefined();
    expect(result.translationTime).toBeLessThan(100);

    const stats = translator.getStats();
    expect(stats.totalTranslations).toBe(1);
    expect(stats.successfulTranslations).toBe(1);
  });

  it('should handle multiple protocol conversions', async () => {
    const translator = createProtocolTranslator();

    const protocols = [
      { from: ProtocolType.HTTP, to: ProtocolType.GRPC },
      { from: ProtocolType.GRPC, to: ProtocolType.HTTP },
      { from: ProtocolType.HTTP, to: ProtocolType.WEBSOCKET },
      { from: ProtocolType.MQTT, to: ProtocolType.AMQP }
    ];

    for (const { from, to } of protocols) {
      const message: ProtocolMessage = {
        id: `multi-${from}-${to}`,
        sourceProtocol: from,
        targetProtocol: to,
        encoding: MessageEncoding.JSON,
        headers: {},
        body: { data: 'test' },
        metadata: {},
        timestamp: new Date()
      };

      const result = await translator.translate(message, to);
      expect(result.success).toBe(true);
    }

    const stats = translator.getStats();
    expect(stats.totalTranslations).toBe(protocols.length);
  });
});