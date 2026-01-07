/**
 * GRAIL Universal Type Converter
 * @module grail::converters::type
 * @description Excalibur's Transformation Power - Universal type conversion engine
 * @version 1.0.0
 * @valuation Core of $1.5M converter subsystem
 */

import type {
  TypeConverter,
  TypeConversion,
  TypeDescriptor
} from '../types/index.js';

// ============================================================================
// TYPE CONVERSION ENGINE
// ============================================================================

/**
 * The Holy Grail Type Converter
 *
 * This converter embodies the legendary transformation capabilities:
 * - Universal type conversion with path finding
 * - Automatic conversion chain discovery
 * - Type validation and coercion
 * - Bidirectional conversion support
 */
export class GrailTypeConverter implements TypeConverter {
  private readonly conversions: Map<string, TypeConversion<unknown, unknown>> = new Map();
  private readonly types: Map<string, TypeDescriptor> = new Map();
  private readonly pathCache: Map<string, string[]> = new Map();

  /**
   * Register a type conversion
   */
  register<S, T>(conversion: TypeConversion<S, T>): void {
    const key = this.makeConversionKey(
      conversion.sourceType.name,
      conversion.targetType.name
    );

    this.conversions.set(key, conversion as TypeConversion<unknown, unknown>);
    this.types.set(conversion.sourceType.name, conversion.sourceType);
    this.types.set(conversion.targetType.name, conversion.targetType);

    // Invalidate path cache
    this.pathCache.clear();
  }

  /**
   * Convert a value from source type to target type
   */
  convert<S, T>(value: S, sourceType: string, targetType: string): T {
    // Direct conversion
    const directKey = this.makeConversionKey(sourceType, targetType);
    const directConversion = this.conversions.get(directKey);

    if (directConversion) {
      if (!directConversion.validate(value)) {
        throw new GrailConversionError(
          `Value does not match source type: ${sourceType}`,
          'VALIDATION_FAILED'
        );
      }
      return directConversion.convert(value) as T;
    }

    // Path-based conversion
    const path = this.getConversionPath(sourceType, targetType);
    if (path.length === 0) {
      throw new GrailConversionError(
        `No conversion path found from ${sourceType} to ${targetType}`,
        'NO_PATH'
      );
    }

    // Execute conversion chain
    let current: unknown = value;
    for (let i = 0; i < path.length - 1; i++) {
      const key = this.makeConversionKey(path[i], path[i + 1]);
      const conversion = this.conversions.get(key);
      if (!conversion) {
        throw new GrailConversionError(
          `Conversion step failed: ${path[i]} -> ${path[i + 1]}`,
          'STEP_FAILED'
        );
      }
      current = conversion.convert(current);
    }

    return current as T;
  }

  /**
   * Check if conversion is possible
   */
  canConvert(sourceType: string, targetType: string): boolean {
    const path = this.getConversionPath(sourceType, targetType);
    return path.length > 0;
  }

  /**
   * Get the conversion path between types
   */
  getConversionPath(sourceType: string, targetType: string): string[] {
    if (sourceType === targetType) {
      return [sourceType];
    }

    const cacheKey = `${sourceType}->${targetType}`;
    if (this.pathCache.has(cacheKey)) {
      return this.pathCache.get(cacheKey)!;
    }

    // BFS to find shortest path
    const queue: Array<{ type: string; path: string[] }> = [
      { type: sourceType, path: [sourceType] }
    ];
    const visited = new Set<string>();

    while (queue.length > 0) {
      const { type, path } = queue.shift()!;

      if (type === targetType) {
        this.pathCache.set(cacheKey, path);
        return path;
      }

      if (visited.has(type)) {
        continue;
      }
      visited.add(type);

      // Find all types this type can convert to
      for (const [key] of this.conversions) {
        const [from, to] = key.split('->');
        if (from === type && !visited.has(to)) {
          queue.push({ type: to, path: [...path, to] });
        }
      }
    }

    this.pathCache.set(cacheKey, []);
    return [];
  }

  /**
   * Get type descriptor
   */
  getType(name: string): TypeDescriptor | undefined {
    return this.types.get(name);
  }

  /**
   * List all registered types
   */
  listTypes(): string[] {
    return Array.from(this.types.keys());
  }

  /**
   * List all available conversions
   */
  listConversions(): Array<{ from: string; to: string }> {
    return Array.from(this.conversions.keys()).map(key => {
      const [from, to] = key.split('->');
      return { from, to };
    });
  }

  /**
   * Create a conversion chain
   */
  chain<A, B, C>(
    first: TypeConversion<A, B>,
    second: TypeConversion<B, C>
  ): TypeConversion<A, C> {
    return {
      sourceType: first.sourceType,
      targetType: second.targetType,
      convert: (source: A) => second.convert(first.convert(source)),
      validate: first.validate
    };
  }

  /**
   * Create an inverse conversion
   */
  inverse<S, T>(
    conversion: TypeConversion<S, T>,
    inverseConvert: (target: T) => S,
    inverseValidate: (value: unknown) => value is T
  ): TypeConversion<T, S> {
    return {
      sourceType: conversion.targetType,
      targetType: conversion.sourceType,
      convert: inverseConvert,
      validate: inverseValidate
    };
  }

  /**
   * Get converter statistics
   */
  getStats(): ConverterStats {
    return {
      registeredTypes: this.types.size,
      registeredConversions: this.conversions.size,
      cachedPaths: this.pathCache.size
    };
  }

  private makeConversionKey(from: string, to: string): string {
    return `${from}->${to}`;
  }
}

// ============================================================================
// BUILT-IN CONVERSIONS
// ============================================================================

/**
 * Create standard primitive conversions
 */
export function createPrimitiveConversions(): Array<TypeConversion<unknown, unknown>> {
  return [
    // string -> number
    {
      sourceType: { name: 'string', schema: { type: 'string' }, nullable: false },
      targetType: { name: 'number', schema: { type: 'number' }, nullable: false },
      convert: (s: unknown) => parseFloat(s as string),
      validate: (v: unknown): v is unknown => typeof v === 'string'
    },
    // number -> string
    {
      sourceType: { name: 'number', schema: { type: 'number' }, nullable: false },
      targetType: { name: 'string', schema: { type: 'string' }, nullable: false },
      convert: (n: unknown) => String(n),
      validate: (v: unknown): v is unknown => typeof v === 'number'
    },
    // string -> boolean
    {
      sourceType: { name: 'string', schema: { type: 'string' }, nullable: false },
      targetType: { name: 'boolean', schema: { type: 'boolean' }, nullable: false },
      convert: (s: unknown) => (s as string).toLowerCase() === 'true',
      validate: (v: unknown): v is unknown => typeof v === 'string'
    },
    // boolean -> string
    {
      sourceType: { name: 'boolean', schema: { type: 'boolean' }, nullable: false },
      targetType: { name: 'string', schema: { type: 'string' }, nullable: false },
      convert: (b: unknown) => String(b),
      validate: (v: unknown): v is unknown => typeof v === 'boolean'
    },
    // number -> boolean
    {
      sourceType: { name: 'number', schema: { type: 'number' }, nullable: false },
      targetType: { name: 'boolean', schema: { type: 'boolean' }, nullable: false },
      convert: (n: unknown) => Boolean(n),
      validate: (v: unknown): v is unknown => typeof v === 'number'
    },
    // boolean -> number
    {
      sourceType: { name: 'boolean', schema: { type: 'boolean' }, nullable: false },
      targetType: { name: 'number', schema: { type: 'number' }, nullable: false },
      convert: (b: unknown) => (b ? 1 : 0),
      validate: (v: unknown): v is unknown => typeof v === 'boolean'
    },
    // string -> Date
    {
      sourceType: { name: 'string', schema: { type: 'string' }, nullable: false },
      targetType: { name: 'Date', schema: { type: 'object' }, nullable: false },
      convert: (s: unknown) => new Date(s as string),
      validate: (v: unknown): v is unknown => typeof v === 'string'
    },
    // Date -> string
    {
      sourceType: { name: 'Date', schema: { type: 'object' }, nullable: false },
      targetType: { name: 'string', schema: { type: 'string' }, nullable: false },
      convert: (d: unknown) => (d as Date).toISOString(),
      validate: (v: unknown): v is unknown => v instanceof Date
    },
    // object -> JSON string
    {
      sourceType: { name: 'object', schema: { type: 'object' }, nullable: false },
      targetType: { name: 'json', schema: { type: 'string' }, nullable: false },
      convert: (o: unknown) => JSON.stringify(o),
      validate: (v: unknown): v is unknown => typeof v === 'object' && v !== null
    },
    // JSON string -> object
    {
      sourceType: { name: 'json', schema: { type: 'string' }, nullable: false },
      targetType: { name: 'object', schema: { type: 'object' }, nullable: false },
      convert: (s: unknown) => JSON.parse(s as string),
      validate: (v: unknown): v is unknown => typeof v === 'string'
    }
  ];
}

/**
 * Create a pre-configured converter with built-in conversions
 */
export function createConfiguredConverter(): GrailTypeConverter {
  const converter = new GrailTypeConverter();

  for (const conversion of createPrimitiveConversions()) {
    converter.register(conversion);
  }

  return converter;
}

// ============================================================================
// TYPES
// ============================================================================

/**
 * Converter statistics
 */
export interface ConverterStats {
  registeredTypes: number;
  registeredConversions: number;
  cachedPaths: number;
}

/**
 * Conversion error codes
 */
export type ConversionErrorCode =
  | 'VALIDATION_FAILED'
  | 'NO_PATH'
  | 'STEP_FAILED'
  | 'INVALID_TYPE';

/**
 * Custom error for conversion operations
 */
export class GrailConversionError extends Error {
  constructor(
    message: string,
    public readonly code: ConversionErrorCode
  ) {
    super(message);
    this.name = 'GrailConversionError';
  }
}

// ============================================================================
// SINGLETON
// ============================================================================

let globalConverter: GrailTypeConverter | null = null;

/**
 * Get the global type converter
 */
export function getGlobalConverter(): GrailTypeConverter {
  if (!globalConverter) {
    globalConverter = createConfiguredConverter();
  }
  return globalConverter;
}
