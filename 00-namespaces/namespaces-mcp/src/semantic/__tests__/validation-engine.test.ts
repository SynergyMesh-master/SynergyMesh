/**
 * Validation Engine Tests
 * 
 * Test Coverage:
 * - Schema validation (JSON Schema, Avro, Protobuf)
 * - Data quality checking
 * - Custom rule validation
 * - Performance benchmarks
 * - Cache efficiency
 */

import { describe, it, expect, beforeEach } from '@jest/globals';
import ValidationEngine, {
  SchemaValidator,
  DataQualityChecker,
  ValidationSchema,
  ValidationRule,
} from '../validation-engine';

describe('ValidationEngine', () => {
  let engine: ValidationEngine;

  beforeEach(() => {
    engine = new ValidationEngine({
      enableCache: true,
      cacheSize: 100,
      cacheTTL: 60000,
    });
  });

  describe('Schema Validation', () => {
    it('should validate JSON Schema successfully', async () => {
      const schema: ValidationSchema = {
        id: 'user-schema',
        name: 'User Schema',
        version: '1.0.0',
        format: 'json-schema',
        schema: {
          type: 'object',
          required: ['name', 'email'],
          properties: {
            name: { type: 'string' },
            email: { type: 'string' },
            age: { type: 'number' },
          },
        },
      };

      engine.registerSchema(schema);

      const validData = {
        name: 'John Doe',
        email: 'john@example.com',
        age: 30,
      };

      const result = await engine.validate('user-schema', validData);
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
      expect(result.metadata.duration).toBeLessThan(50);
    });

    it('should detect missing required fields', async () => {
      const schema: ValidationSchema = {
        id: 'product-schema',
        name: 'Product Schema',
        version: '1.0.0',
        format: 'json-schema',
        schema: {
          type: 'object',
          required: ['name', 'price'],
          properties: {
            name: { type: 'string' },
            price: { type: 'number' },
          },
        },
      };

      engine.registerSchema(schema);

      const invalidData = {
        name: 'Product A',
        // missing price
      };

      const result = await engine.validate('product-schema', invalidData);
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.errors[0].rule).toBe('required');
    });

    it('should validate with custom rules', async () => {
      const rules: ValidationRule[] = [
        {
          id: 'email-format',
          name: 'Email Format',
          type: 'format',
          field: 'email',
          constraint: 'email',
          severity: 'error',
          message: 'Invalid email format',
        },
        {
          id: 'age-range',
          name: 'Age Range',
          type: 'range',
          field: 'age',
          constraint: { min: 18, max: 100 },
          severity: 'warning',
          message: 'Age must be between 18 and 100',
        },
      ];

      const schema: ValidationSchema = {
        id: 'user-with-rules',
        name: 'User Schema with Rules',
        version: '1.0.0',
        format: 'json-schema',
        schema: { type: 'object' },
        rules,
      };

      engine.registerSchema(schema);

      const data = {
        email: 'invalid-email',
        age: 150,
      };

      const result = await engine.validate('user-with-rules', data);
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.warnings.length).toBeGreaterThan(0);
    });
  });

  describe('Data Quality Checking', () => {
    it('should check data completeness', async () => {
      const data = [
        { name: 'John', email: 'john@example.com', age: 30 },
        { name: 'Jane', email: 'jane@example.com', age: null },
        { name: 'Bob', email: '', age: 25 },
      ];

      const metrics = await engine.checkQuality(data);
      expect(metrics.completeness).toBeGreaterThan(0);
      expect(metrics.completeness).toBeLessThanOrEqual(1);
    });

    it('should check data accuracy', async () => {
      const data = [
        { date: '2024-01-01', count: 100 },
        { date: 'invalid-date', count: -50 },
        { date: '2024-01-02', count: 200 },
      ];

      const metrics = await engine.checkQuality(data);
      expect(metrics.accuracy).toBeGreaterThan(0);
      expect(metrics.accuracy).toBeLessThanOrEqual(1);
    });

    it('should check data consistency', async () => {
      const data = [
        { id: 1, value: 'string' },
        { id: 2, value: 'string' },
        { id: 3, value: 123 }, // inconsistent type
      ];

      const metrics = await engine.checkQuality(data);
      expect(metrics.consistency).toBeGreaterThan(0);
      expect(metrics.consistency).toBeLessThanOrEqual(1);
    });

    it('should calculate overall quality score', async () => {
      const data = [
        { name: 'John', email: 'john@example.com', timestamp: new Date().toISOString() },
        { name: 'Jane', email: 'jane@example.com', timestamp: new Date().toISOString() },
      ];

      const metrics = await engine.checkQuality(data);
      expect(metrics.overall).toBeGreaterThan(0);
      expect(metrics.overall).toBeLessThanOrEqual(1);
      expect(metrics.overall).toBe(
        (metrics.completeness + metrics.accuracy + metrics.consistency + metrics.timeliness) / 4
      );
    });
  });

  describe('Performance', () => {
    it('should validate within 50ms', async () => {
      const schema: ValidationSchema = {
        id: 'perf-schema',
        name: 'Performance Schema',
        version: '1.0.0',
        format: 'json-schema',
        schema: {
          type: 'object',
          required: ['field1', 'field2', 'field3'],
        },
      };

      engine.registerSchema(schema);

      const data = {
        field1: 'value1',
        field2: 'value2',
        field3: 'value3',
      };

      const startTime = Date.now();
      await engine.validate('perf-schema', data);
      const duration = Date.now() - startTime;

      expect(duration).toBeLessThan(50);
    });

    it('should achieve >80% cache hit rate', async () => {
      const schema: ValidationSchema = {
        id: 'cache-schema',
        name: 'Cache Schema',
        version: '1.0.0',
        format: 'json-schema',
        schema: { type: 'object' },
      };

      engine.registerSchema(schema);

      const data = { test: 'value' };

      // First validation (cache miss)
      await engine.validate('cache-schema', data);

      // Subsequent validations (cache hits)
      for (let i = 0; i < 10; i++) {
        await engine.validate('cache-schema', data);
      }

      const stats = engine.getStats();
      expect(stats.cacheHitRate).toBeGreaterThan(0.8);
    });
  });

  describe('Metrics', () => {
    it('should track validation metrics', async () => {
      const schema: ValidationSchema = {
        id: 'metrics-schema',
        name: 'Metrics Schema',
        version: '1.0.0',
        format: 'json-schema',
        schema: { type: 'object', required: ['field'] },
      };

      engine.registerSchema(schema);

      // Valid validation
      await engine.validate('metrics-schema', { field: 'value' });

      // Invalid validation
      try {
        await engine.validate('metrics-schema', {});
      } catch (error) {
        // Expected
      }

      const metrics = engine.getMetrics();
      expect(metrics.validations).toBeGreaterThan(0);
      expect(metrics.avgDuration).toBeGreaterThan(0);
    });
  });
});

describe('SchemaValidator', () => {
  let validator: SchemaValidator;

  beforeEach(() => {
    validator = new SchemaValidator();
  });

  it('should support multiple schema formats', () => {
    const jsonSchema: ValidationSchema = {
      id: 'json-1',
      name: 'JSON Schema',
      version: '1.0.0',
      format: 'json-schema',
      schema: {},
    };

    const avroSchema: ValidationSchema = {
      id: 'avro-1',
      name: 'Avro Schema',
      version: '1.0.0',
      format: 'avro',
      schema: {},
    };

    validator.registerSchema(jsonSchema);
    validator.registerSchema(avroSchema);

    const stats = validator.getStats();
    expect(stats.schemasRegistered).toBe(2);
  });
});

describe('DataQualityChecker', () => {
  let checker: DataQualityChecker;

  beforeEach(() => {
    checker = new DataQualityChecker();
  });

  it('should handle empty datasets', async () => {
    const metrics = await checker.checkQuality([]);
    expect(metrics.completeness).toBe(0);
    expect(metrics.overall).toBe(0);
  });

  it('should handle perfect quality data', async () => {
    const data = [
      { name: 'John', email: 'john@example.com', count: 100, timestamp: new Date().toISOString() },
      { name: 'Jane', email: 'jane@example.com', count: 200, timestamp: new Date().toISOString() },
    ];

    const metrics = await checker.checkQuality(data);
    expect(metrics.completeness).toBe(1);
    expect(metrics.accuracy).toBeGreaterThan(0.9);
    expect(metrics.consistency).toBe(1);
  });
});