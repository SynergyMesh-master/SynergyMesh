/**
 * GRAIL Universal Format Converter
 * @module grail::converters::format
 * @description Multi-format data transformation engine
 * @version 1.0.0
 */

import yaml from 'js-yaml';
import { XMLParser, XMLBuilder } from 'fast-xml-parser';
import * as yaml from 'js-yaml';
import type {
  FormatConverter,
  SupportedFormat,
  FormatOptions
} from '../types/index.js';

// ============================================================================
// FORMAT CONVERSION ENGINE
// ============================================================================

/**
 * The Holy Grail Format Converter
 *
 * Handles conversion between data formats:
 * - JSON, YAML, XML, CSV
 * - Binary formats (Protobuf, Avro, Parquet)
 * - Automatic format detection
 * - Compression support
 */
export class GrailFormatConverter implements FormatConverter {
  private readonly formatHandlers: Map<SupportedFormat, FormatHandler> = new Map();

  constructor() {
    this.registerDefaultHandlers();
  }

  /**
   * Convert data between formats
   */
  async convert(
    data: unknown,
    from: SupportedFormat,
    to: SupportedFormat,
    options?: FormatOptions
  ): Promise<unknown> {
    // Serialize from source format
    const sourceHandler = this.formatHandlers.get(from);
    if (!sourceHandler) {
      throw new FormatConversionError(
        `Unsupported source format: ${from}`,
        'UNSUPPORTED_FORMAT'
      );
    }

    // Get intermediate representation
    const intermediate = await sourceHandler.parse(data);

    // Serialize to target format
    const targetHandler = this.formatHandlers.get(to);
    if (!targetHandler) {
      throw new FormatConversionError(
        `Unsupported target format: ${to}`,
        'UNSUPPORTED_FORMAT'
      );
    }

    return targetHandler.serialize(intermediate, options);
  }

  /**
   * Serialize data to bytes
   */
  async serialize(
    data: unknown,
    format: SupportedFormat,
    options?: FormatOptions
  ): Promise<Uint8Array> {
    const handler = this.formatHandlers.get(format);
    if (!handler) {
      throw new FormatConversionError(
        `Unsupported format: ${format}`,
        'UNSUPPORTED_FORMAT'
      );
    }

    const serialized = await handler.serialize(data, options);
    const bytes = new TextEncoder().encode(
      typeof serialized === 'string' ? serialized : JSON.stringify(serialized)
    );

    // Apply compression if requested
    if (options?.compression && options.compression !== 'none') {
      return this.compress(bytes, options.compression);
    }

    return bytes;
  }

  /**
   * Deserialize bytes to data
   */
  async deserialize(
    data: Uint8Array,
    format: SupportedFormat
  ): Promise<unknown> {
    const handler = this.formatHandlers.get(format);
    if (!handler) {
      throw new FormatConversionError(
        `Unsupported format: ${format}`,
        'UNSUPPORTED_FORMAT'
      );
    }

    const text = new TextDecoder().decode(data);
    return handler.parse(text);
  }

  /**
   * Detect format from data
   */
  async detectFormat(data: Uint8Array): Promise<SupportedFormat | null> {
    const text = new TextDecoder().decode(data.slice(0, 1000));
    const trimmed = text.trim();

    // JSON detection
    if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
      try {
        JSON.parse(trimmed.length < 1000 ? trimmed : text);
        return 'json';
      } catch {
        // Not valid JSON
      }
    }

    // XML detection
    if (trimmed.startsWith('<?xml') || trimmed.startsWith('<')) {
      return 'xml';
    }

    // YAML detection (basic heuristic)
    if (trimmed.includes(':') && !trimmed.startsWith('{')) {
      const lines = trimmed.split('\n');
      if (lines.some(line => /^\s*\w+:\s*.+/.test(line))) {
        return 'yaml';
      }
    }

    // CSV detection
    const firstLine = trimmed.split('\n')[0];
    if (firstLine && firstLine.includes(',')) {
      const commaCount = (firstLine.match(/,/g) || []).length;
      if (commaCount > 0) {
        return 'csv';
      }
    }

    // Binary format detection (magic bytes)
    if (data.length >= 4) {
      // Parquet magic bytes
      if (data[0] === 0x50 && data[1] === 0x41 && data[2] === 0x52 && data[3] === 0x31) {
        return 'parquet';
      }

      // Avro magic bytes
      if (data[0] === 0x4f && data[1] === 0x62 && data[2] === 0x6a && data[3] === 0x01) {
        return 'avro';
      }
    }

    return null;
  }

  /**
   * Register a custom format handler
   */
  registerHandler(format: SupportedFormat, handler: FormatHandler): void {
    this.formatHandlers.set(format, handler);
  }

  /**
   * List supported formats
   */
  listFormats(): SupportedFormat[] {
    return Array.from(this.formatHandlers.keys());
  }

  // ============================================================================
  // PRIVATE METHODS
  // ============================================================================

  private registerDefaultHandlers(): void {
    // JSON handler
    this.formatHandlers.set('json', {
      parse: async (data: unknown) => {
        if (typeof data === 'string') {
          return JSON.parse(data);
        }
        return data;
      },
      serialize: async (data: unknown, options?: FormatOptions) => {
        return options?.pretty
          ? JSON.stringify(data, null, 2)
          : JSON.stringify(data);
      }
    });

    // YAML handler using js-yaml library
    // YAML handler (using js-yaml library)
    this.formatHandlers.set('yaml', {
      parse: async (data: unknown) => {
        if (typeof data !== 'string') {
          return data;
        }
        try {
          return yaml.load(data);
        } catch (error) {
          throw new FormatConversionError(
            `YAML parsing failed: ${error instanceof Error ? error.message : String(error)}`,
            'PARSE_ERROR'
          );
        }
      },
      serialize: async (data: unknown, options?: FormatOptions) => {
        try {
          return yaml.dump(data, {
            indent: options?.pretty ? 2 : 0,
            lineWidth: -1,
            noRefs: true
          });
        } catch (error) {
          throw new FormatConversionError(
            `YAML serialization failed: ${error instanceof Error ? error.message : String(error)}`,
            'SERIALIZE_ERROR'
          );
        }
      }
    });

    // XML handler using fast-xml-parser
    this.formatHandlers.set('xml', {
      parse: async (data: unknown) => {
        if (typeof data !== 'string') {
          return data;
        }
        const parser = new XMLParser({
          ignoreAttributes: false,
          attributeNamePrefix: '@_',
          textNodeName: '#text',
          parseAttributeValue: true,
          trimValues: true
        });
        return parser.parse(data);
      },
      serialize: async (data: unknown, options?: FormatOptions) => {
        const builder = new XMLBuilder({
          ignoreAttributes: false,
          attributeNamePrefix: '@_',
          textNodeName: '#text',
          format: options?.pretty,
          indentBy: options?.pretty ? '  ' : '',
          suppressEmptyNode: true
        });
        return builder.build(data);
      }
    });

    // CSV handler
    this.formatHandlers.set('csv', {
      parse: async (data: unknown) => {
        if (typeof data !== 'string') {
          return data;
        }
        return this.parseCsv(data);
      },
      serialize: async (data: unknown) => {
        return this.serializeToCsv(data as unknown[]);
      }
    });

    // ------------------------------------------------------------------------
    // Binary format handlers (opaque pass-through)
    //
    // NOTE:
    // These handlers provide minimal, generic support for binary formats by
    // treating the payload as opaque data. Full schema-aware parsing and
    // serialization should be implemented by callers using dedicated
    // format-specific libraries (e.g., for Protobuf/Avro/Parquet).
    // ------------------------------------------------------------------------

    const parseBinary = async (data: unknown): Promise<unknown> => {
      // For now, simply return the data as-is. Callers are responsible for
      // interpreting binary payloads using appropriate libraries.
      return data;
    };

    const serializeBinary = async (data: unknown): Promise<unknown> => {
      // Likewise, perform no transformation and return the binary data as-is.
      return data;
    };

    // Protobuf handler (opaque)
    this.formatHandlers.set('protobuf', {
      parse: parseBinary,
      serialize: serializeBinary
    });

    // Avro handler (opaque)
    this.formatHandlers.set('avro', {
      parse: parseBinary,
      serialize: serializeBinary
    });

    // Parquet handler (opaque)
    this.formatHandlers.set('parquet', {
      parse: parseBinary,
      serialize: serializeBinary
    });
  }


  private parseCsv(csv: string): unknown[] {
    const lines = csv.trim().split('\n');
    if (lines.length === 0) return [];

    const headers = this.parseCsvLine(lines[0]);
    const result: unknown[] = [];

    for (let i = 1; i < lines.length; i++) {
      const values = this.parseCsvLine(lines[i]);
      const row: Record<string, unknown> = {};
      for (let j = 0; j < headers.length; j++) {
        row[headers[j]] = values[j] ?? null;
      }
      result.push(row);
    }

    return result;
  }

  private parseCsvLine(line: string): string[] {
    const result: string[] = [];
    let current = '';
    let inQuotes = false;

    for (let i = 0; i < line.length; i++) {
      const char = line[i];

      if (char === '"') {
        if (inQuotes && line[i + 1] === '"') {
          current += '"';
          i++;
        } else {
          inQuotes = !inQuotes;
        }
      } else if (char === ',' && !inQuotes) {
        result.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }

    result.push(current.trim());
    return result;
  }

  private serializeToCsv(data: unknown[]): string {
    if (data.length === 0) return '';

    const firstRow = data[0] as Record<string, unknown>;
    const headers = Object.keys(firstRow);

    const lines: string[] = [headers.map(h => this.escapeCsvValue(h)).join(',')];

    for (const row of data) {
      const values = headers.map(h => {
        const value = (row as Record<string, unknown>)[h];
        return this.escapeCsvValue(String(value ?? ''));
      });
      lines.push(values.join(','));
    }

    return lines.join('\n');
  }

  private escapeCsvValue(value: string): string {
    if (value.includes(',') || value.includes('"') || value.includes('\n')) {
      return `"${value.replace(/"/g, '""')}"`;
    }
    return value;
  }

  private async compress(
    data: Uint8Array,
    algorithm: 'gzip' | 'brotli'
  ): Promise<Uint8Array> {
    // Compression is not currently implemented; fail explicitly to avoid
    // silently returning uncompressed data when compression was requested.
    throw new FormatConversionError(
      `Compression algorithm "${algorithm}" is not implemented`,
      'COMPRESSION_ERROR'
    );
  }
}

// ============================================================================
// TYPES
// ============================================================================

/**
 * Format handler interface
 */
export interface FormatHandler {
  parse(data: unknown): Promise<unknown>;
  serialize(data: unknown, options?: FormatOptions): Promise<unknown>;
}

/**
 * Format conversion error codes
 */
export type FormatErrorCode =
  | 'UNSUPPORTED_FORMAT'
  | 'PARSE_ERROR'
  | 'SERIALIZE_ERROR'
  | 'COMPRESSION_ERROR';

/**
 * Custom error for format conversion
 */
export class FormatConversionError extends Error {
  constructor(
    message: string,
    public readonly code: FormatErrorCode
  ) {
    super(message);
    this.name = 'FormatConversionError';
  }
}

// ============================================================================
// SINGLETON
// ============================================================================

let globalFormatConverter: GrailFormatConverter | null = null;

/**
 * Get the global format converter
 */
export function getGlobalFormatConverter(): GrailFormatConverter {
  if (!globalFormatConverter) {
    globalFormatConverter = new GrailFormatConverter();
  }
  return globalFormatConverter;
}
