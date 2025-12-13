/**
 * @fileoverview Application configuration management with Zod validation.
 *
 * This module provides type-safe environment variable parsing and validation
 * using Zod schemas. It ensures all required configuration is present and
 * correctly typed at application startup, failing fast if configuration is invalid.
 *
 * Features:
 * - Type-safe configuration with TypeScript inference
 * - Runtime validation with detailed error messages
 * - Sensible defaults for development
 * - Immutable configuration object (Object.freeze)
 * - Reusable validation function for testing
 *
 * @module config
 */

import { z } from 'zod';

/**
 * Zod schema defining the application's environment variables.
 *
 * Each variable has specific validation rules and defaults where appropriate.
 * The schema is used both for runtime validation and TypeScript type inference.
 *
 * @property {string} NODE_ENV - Execution environment (development/production/test)
 * @property {number} PORT - HTTP server port (1-65535, default: 3000)
 * @property {string} LOG_LEVEL - Logging verbosity (error/warn/info/debug)
 * @property {string} SERVICE_NAME - Identifier for this service instance
 * @property {string} SERVICE_VERSION - Semantic version of the service
 * @property {string} [DATABASE_URL] - Optional PostgreSQL connection string
 * @property {string} [REDIS_URL] - Optional Redis connection string
 * @property {string} [BUILD_SHA] - Git commit SHA for build traceability
 * @property {string} [BUILD_TIME] - ISO timestamp of build creation
 * @property {string} [WE_TONKE] - Optional external API token
 */
const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.coerce.number().min(1).max(65535).default(3000),
  LOG_LEVEL: z.enum(['error', 'warn', 'info', 'debug']).default('info'),
  SERVICE_NAME: z.string().default('contracts-l1'),
  SERVICE_VERSION: z.string().default('1.0.0'),
  DATABASE_URL: z.string().optional(),
  REDIS_URL: z.string().optional(),
  BUILD_SHA: z.string().optional(),
  BUILD_TIME: z.string().optional(),
  WE_TONKE: z.string().optional(),
});

/**
 * TypeScript type for the validated configuration object.
 * Automatically inferred from the Zod schema to ensure type safety.
 */
export type Config = z.infer<typeof envSchema>;

/**
 * Loads and validates application configuration from environment variables.
 *
 * This function:
 * 1. Parses all environment variables through the Zod schema
 * 2. Applies default values where not specified
 * 3. Logs successful configuration load with non-sensitive details
 * 4. Exits the process with code 1 if validation fails
 *
 * Called once at module initialization to ensure configuration is valid
 * before the application starts accepting requests.
 *
 * @returns Validated configuration object
 * @throws Never returns on validation failure (exits process)
 *
 * @example
 * // Typical process.env for production:
 * // NODE_ENV=production
 * // PORT=8080
 * // LOG_LEVEL=info
 * // DATABASE_URL=postgres://user:pass@host:5432/db
 *
 * const config = loadConfig();
 * // config.PORT is number 8080
 * // config.NODE_ENV is 'production'
 *
 * @private
 */
function loadConfig(): Config {
  try {
    const parsed = envSchema.parse(process.env);
    console.log('Configuration loaded successfully:', {
      NODE_ENV: parsed.NODE_ENV,
      PORT: parsed.PORT,
      SERVICE_NAME: parsed.SERVICE_NAME,
      sources: {
        env_file: !!process.env.npm_config_env,
        process_env: true,
        defaults_applied: true,
      },
      timestamp: new Date().toISOString(),
    });
    return parsed;
  } catch (error) {
    console.error('Configuration validation failed:', error);
    process.exit(1);
  }
}

/**
 * Immutable application configuration object.
 *
 * Loaded and validated once at module initialization. The object is frozen
 * to prevent accidental mutation during application runtime.
 *
 * @example
 * import config from './config';
 *
 * // Access configuration values
 * const port = config.PORT;
 * const isDev = config.NODE_ENV === 'development';
 *
 * // This will throw a TypeError in strict mode or silently fail in non-strict mode (object is frozen):
 * // config.PORT = 9000;
 */
export const config: Readonly<Config> = Object.freeze(loadConfig());

/**
 * Validates an environment object against the configuration schema.
 *
 * Useful for testing configuration scenarios without modifying process.env.
 * Throws ZodError if validation fails, allowing callers to handle invalid
 * configurations gracefully in test contexts.
 *
 * @param env - Object containing environment variable key-value pairs
 * @returns Validated configuration object
 * @throws {z.ZodError} If validation fails
 *
 * @example
 * // In tests:
 * import { validateConfig } from './config';
 *
 * test('validates port range', () => {
 *   expect(() => validateConfig({ PORT: '99999' })).toThrow();
 *   expect(() => validateConfig({ PORT: '3000' })).not.toThrow();
 * });
 *
 * @example
 * // Create valid config for testing:
 * const testConfig = validateConfig({
 *   NODE_ENV: 'test',
 *   PORT: '4000',
 *   LOG_LEVEL: 'error',
 * });
 */
export const validateConfig = (env: Record<string, unknown>): Config => envSchema.parse(env);

export default config;
