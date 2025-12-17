import { realpath } from 'fs/promises';
import path from 'path';

export interface PathValidatorConfig {
  safeRoot?: string;
  allowedAbsolutePrefixes?: string[];
}

export class PathValidationError extends Error {
  public readonly code = 'PATH_VALIDATION_ERROR';

  constructor(message: string) {
    super(message);
    Object.setPrototypeOf(this, PathValidationError.prototype);
  }
}

export class PathValidator {
  protected readonly config: PathValidatorConfig;

  constructor(config: PathValidatorConfig = {}) {
    this.config = config;
  }

  /**
   * Basic path validation to prevent traversal attacks and ensure containment within safeRoot.
   * Resolves to a canonical path or throws on error.
   */
  async validateAndResolvePath(filePath: string): Promise<string> {
    if (!filePath || typeof filePath !== 'string') {
      throw new PathValidationError('Invalid file path');
    }

    if (filePath.includes('\0') || filePath.split(path.sep).includes('..')) {
      throw new PathValidationError('Invalid file path');
    }

    const safeRoot = path.resolve(this.config.safeRoot || process.cwd());
    const resolvedCandidate = path.isAbsolute(filePath)
      ? path.resolve(safeRoot, path.relative('/', filePath))
      : path.resolve(safeRoot, filePath);

    const canonicalPath = await realpath(resolvedCandidate);

    const allowedPrefixes = this.config.allowedAbsolutePrefixes?.map((p) => path.resolve(p)) || [];
    const isAllowedPrefix = allowedPrefixes.some((prefix) => canonicalPath.startsWith(prefix));

    if (!canonicalPath.startsWith(safeRoot) && !isAllowedPrefix) {
      throw new PathValidationError('Path escapes safe root');
    }

    return canonicalPath;
  }
}
