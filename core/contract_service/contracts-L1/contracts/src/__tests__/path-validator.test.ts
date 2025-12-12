import { writeFile, unlink, mkdir, symlink, rm } from 'fs/promises';
import { join } from 'path';
import { tmpdir } from 'os';

import { PathValidator, PathValidationError } from '../utils/path-validator';

describe('PathValidator', () => {
  let validator: PathValidator;
  let testDir: string;
  let testFilePath: string;

  beforeEach(async () => {
    validator = new PathValidator();
    testDir = join(tmpdir(), `test-path-validator-${Date.now()}`);
    await mkdir(testDir, { recursive: true });
    testFilePath = join(testDir, 'test-file.txt');
    await writeFile(testFilePath, 'test content');
  });

  afterEach(async () => {
    try {
      await rm(testDir, { recursive: true, force: true });
    } catch {
      // Ignore cleanup errors
    }
  });

  describe('validateAndResolvePath', () => {
    it('should resolve absolute paths successfully', async () => {
      const resolved = await validator.validateAndResolvePath(testFilePath);
      expect(resolved).toBeTruthy();
      expect(resolved).toContain('test-file.txt');
    });

    it('should throw ENOENT error for non-existent absolute paths', async () => {
      const nonExistentPath = join(testDir, 'non-existent.txt');
      await expect(validator.validateAndResolvePath(nonExistentPath)).rejects.toThrow(/ENOENT/);
    });

    it('should throw PathValidationError for paths outside allowed directories', async () => {
      const restrictedValidator = new PathValidator({
        allowedAbsolutePrefixes: [testDir],
      });
      const outsidePath = join(tmpdir(), 'outside-file.txt');
      await writeFile(outsidePath, 'test');

      try {
        await expect(restrictedValidator.validateAndResolvePath(outsidePath)).rejects.toThrow(
          PathValidationError
        );
      } finally {
        await unlink(outsidePath);
      }
    });

    it('should handle symlinks correctly', async () => {
      const symlinkPath = join(testDir, 'symlink.txt');
      await symlink(testFilePath, symlinkPath);

      const resolved = await validator.validateAndResolvePath(symlinkPath);
      expect(resolved).toEqual(await validator.validateAndResolvePath(testFilePath));

      await unlink(symlinkPath);
    });

    it('should resolve relative paths against safe root', async () => {
      const customValidator = new PathValidator({
        safeRoot: testDir,
      });
      const relativePath = 'test-file.txt';

      const resolved = await customValidator.validateAndResolvePath(relativePath);
      expect(resolved).toContain('test-file.txt');
    });

    it('should throw PathValidationError for relative paths outside safe root', async () => {
      const customValidator = new PathValidator({
        safeRoot: testDir,
      });
      const relativePath = '../outside.txt';

      await expect(customValidator.validateAndResolvePath(relativePath)).rejects.toThrow(
        PathValidationError
      );
    });
  });

  describe('getSafeRoot', () => {
    it('should return the configured safe root', () => {
      const safeRoot = validator.getSafeRoot();
      expect(safeRoot).toBeTruthy();
      expect(typeof safeRoot).toBe('string');
    });

    it('should return custom safe root when configured', () => {
      const customRoot = '/custom/safe/root';
      const customValidator = new PathValidator({
        safeRoot: customRoot,
      });
      expect(customValidator.getSafeRoot()).toBe(customRoot);
    });
  });

  describe('getAllowedPrefixes', () => {
    it('should return array of allowed prefixes', () => {
      const prefixes = validator.getAllowedPrefixes();
      expect(Array.isArray(prefixes)).toBe(true);
      expect(prefixes.length).toBeGreaterThan(0);
    });

    it('should return copy of prefixes array', () => {
      const prefixes1 = validator.getAllowedPrefixes();
      const prefixes2 = validator.getAllowedPrefixes();
      expect(prefixes1).toEqual(prefixes2);
      expect(prefixes1).not.toBe(prefixes2); // Different array instances
    });
  });

  describe('PathValidationError', () => {
    it('should create error with message and code', () => {
      const error = new PathValidationError('Test error', 'TEST_CODE');
      expect(error.message).toBe('Test error');
      expect(error.code).toBe('TEST_CODE');
      expect(error.name).toBe('PathValidationError');
    });

    it('should be instanceof Error', () => {
      const error = new PathValidationError('Test error');
      expect(error instanceof Error).toBe(true);
      expect(error instanceof PathValidationError).toBe(true);
    });
  });

  describe('custom configuration', () => {
    it('should accept custom allowed prefixes', () => {
      const customPrefixes = [testDir];
      const customValidator = new PathValidator({
        allowedAbsolutePrefixes: customPrefixes,
      });
      expect(customValidator.getAllowedPrefixes()).toEqual(customPrefixes);
    });

    it('should use default configuration when not provided', () => {
      const defaultValidator = new PathValidator();
      expect(defaultValidator.getSafeRoot()).toBeTruthy();
      expect(defaultValidator.getAllowedPrefixes().length).toBeGreaterThan(0);
    });
  });
});
