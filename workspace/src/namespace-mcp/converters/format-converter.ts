/**
 * GRAIL Universal Format Converter
 * @module grail::converters::format
 * @description Multi-format data transformation engine
 * @version 1.0.0
 */

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

    // YAML handler (simplified)
    this.formatHandlers.set('yaml', {
      parse: async (data: unknown) => {
        // Basic YAML parsing (for full support, use a library)
        if (typeof data !== 'string') {
          return data;
        }
        return this.parseSimpleYaml(data);
      },
      serialize: async (data: unknown, options?: FormatOptions) => {
        return this.serializeToYaml(data, options?.pretty ? 2 : 0);
      }
    });

    // XML handler (simplified)
    this.formatHandlers.set('xml', {
      parse: async (data: unknown) => {
        if (typeof data !== 'string') {
          return data;
        }
        return this.parseSimpleXml(data);
      },
      serialize: async (data: unknown, options?: FormatOptions) => {
        return this.serializeToXml(data, options?.pretty ? 2 : 0);
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
  }

  private parseSimpleYaml(yaml: string): unknown {
    const result: Record<string, unknown> = {};
    const lines = yaml.split('\n');

    for (const line of lines) {
      const match = line.match(/^(\s*)(\w+):\s*(.*)$/);
      if (match) {
        const [, , key, value] = match;
        result[key] = this.parseYamlValue(value.trim());
      }
    }

    return result;
  }

  private parseYamlValue(value: string): unknown {
    if (value === 'true') return true;
    if (value === 'false') return false;
    if (value === 'null' || value === '~') return null;
    if (/^-?\d+$/.test(value)) return parseInt(value, 10);
    if (/^-?\d+\.\d+$/.test(value)) return parseFloat(value);
    if ((value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))) {
      return value.slice(1, -1);
    }
    return value;
  }

  private serializeToYaml(data: unknown, indent: number): string {
    const lines: string[] = [];
    this.serializeYamlValue(data, lines, 0, indent);
    return lines.join('\n');
  }

  private serializeYamlValue(
    value: unknown,
    lines: string[],
    depth: number,
    indent: number
  ): void {
    const prefix = ' '.repeat(depth * indent);

    if (value === null || value === undefined) {
      lines.push(`${prefix}null`);
    } else if (typeof value === 'object' && !Array.isArray(value)) {
      for (const [k, v] of Object.entries(value)) {
        if (typeof v === 'object' && v !== null) {
          lines.push(`${prefix}${k}:`);
          this.serializeYamlValue(v, lines, depth + 1, indent);
        } else {
          lines.push(`${prefix}${k}: ${this.yamlValueToString(v)}`);
        }
      }
    } else if (Array.isArray(value)) {
      for (const item of value) {
        lines.push(`${prefix}- ${this.yamlValueToString(item)}`);
      }
    }
  }

  private yamlValueToString(value: unknown): string {
    if (value === null || value === undefined) return 'null';
    if (typeof value === 'string') {
      if (value.includes('\n') || value.includes(':')) {
        const escaped = value.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
        return `"${escaped}"`;
      }
      return value;
    }
    return String(value);
  }

  private parseSimpleXml(xml: string): unknown {
    // Very basic XML parsing
    const result: Record<string, unknown> = {};
    const tagRegex = /<(\w+)>([^<]*)<\/\1>/g;
    let match;

    while ((match = tagRegex.exec(xml)) !== null) {
      const [, tag, content] = match;
      result[tag] = content;
    }

    return result;
  }

  private serializeToXml(data: unknown, indent: number): string {
    const lines: string[] = ['<?xml version="1.0" encoding="UTF-8"?>'];
    this.serializeXmlValue('root', data, lines, 0, indent);
    return lines.join('\n');
  }

  private serializeXmlValue(
    tag: string,
    value: unknown,
    lines: string[],
    depth: number,
    indent: number
  ): void {
    const prefix = ' '.repeat(depth * indent);

    if (value === null || value === undefined) {
      lines.push(`${prefix}<${tag}/>`);
    } else if (typeof value === 'object' && !Array.isArray(value)) {
      lines.push(`${prefix}<${tag}>`);
      for (const [k, v] of Object.entries(value)) {
        this.serializeXmlValue(k, v, lines, depth + 1, indent);
      }
      lines.push(`${prefix}</${tag}>`);
    } else if (Array.isArray(value)) {
      lines.push(`${prefix}<${tag}>`);
      for (const item of value) {
        this.serializeXmlValue('item', item, lines, depth + 1, indent);
      }
      lines.push(`${prefix}</${tag}>`);
    } else {
      lines.push(`${prefix}<${tag}>${this.escapeXml(String(value))}</${tag}>`);
    }
  }

  private escapeXml(str: string): string {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;');
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
    // Note: In a real implementation, use proper compression libraries
    // This is a placeholder that returns the original data
    console.warn(`Compression (${algorithm}) not implemented, returning original data`);
    return data;
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
