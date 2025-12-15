import { ProvenanceService } from '../services/provenance';
import { writeFile, unlink, mkdir } from 'fs/promises';
import { join, relative } from 'path';
import { tmpdir } from 'os';

describe('ProvenanceService', () => {
  let service: ProvenanceService;
  let testFilePath: string;
  let originalSafeRoot: string | undefined;

  beforeEach(async () => {
    // Set SAFE_ROOT_PATH to tmpdir for testing
    originalSafeRoot = process.env.SAFE_ROOT_PATH;
    process.env.SAFE_ROOT_PATH = tmpdir();

    service = new ProvenanceService();
    testFilePath = join(tmpdir(), `test-${Date.now()}.txt`);
    await writeFile(testFilePath, 'test content for attestation');
  });

  afterEach(async () => {
    // Restore original SAFE_ROOT_PATH
    if (originalSafeRoot !== undefined) {
      process.env.SAFE_ROOT_PATH = originalSafeRoot;
    } else {
      delete process.env.SAFE_ROOT_PATH;
    }

    try {
      await unlink(testFilePath);
    } catch {
      // Ignore cleanup errors
    }
  });

  describe('generateFileDigest', () => {
    it('should generate correct SHA256 digest', async () => {
      // Use relative path from SAFE_ROOT (tmpdir in tests)
      const relativePath = relative(tmpdir(), testFilePath);
      const digest = await service.generateFileDigest(relativePath);
      expect(digest).toMatch(/^sha256:[a-f0-9]{64}$/);
    });

    it('should throw error for non-existent file', async () => {
      await expect(service.generateFileDigest('non/existent/file')).rejects.toThrow();
    });

    it('should reject path traversal attempts', async () => {
      await expect(service.generateFileDigest('../../../etc/passwd')).rejects.toThrow(
        /not allowed/
      );
    });
  });

  describe('createBuildAttestation', () => {
    it('should create valid attestation with required fields', async () => {
      const builder = {
        id: 'https://test.builder.com',
        version: '1.0.0',
      };

      // Use relative path from SAFE_ROOT
      const relativePath = relative(tmpdir(), testFilePath);
      const attestation = await service.createBuildAttestation(relativePath, builder);

      expect(attestation).toMatchObject({
        id: expect.stringMatching(/^att_\d+_[a-z0-9]+$/),
        timestamp: expect.any(String),
        subject: {
          name: expect.stringContaining('test-'),
          digest: expect.stringMatching(/^sha256:[a-f0-9]{64}$/),
          path: expect.any(String),
        },
        predicate: {
          type: 'https://slsa.dev/provenance/v1',
          builder,
          recipe: expect.objectContaining({
            type: 'https://github.com/synergymesh/build',
          }),
          metadata: expect.objectContaining({
            completeness: {
              parameters: true,
              environment: true,
              materials: true,
            },
          }),
        },
      });
    });

    it('should include custom metadata when provided', async () => {
      const builder = { id: 'test-builder', version: '1.0.0' };
      const metadata = {
        reproducible: true,
        buildInvocationId: 'test-build-123',
      };

      const relativePath = relative(tmpdir(), testFilePath);
      const attestation = await service.createBuildAttestation(relativePath, builder, metadata);

      expect(attestation.predicate.metadata.reproducible).toBe(true);
      expect(attestation.predicate.metadata.buildInvocationId).toBe('test-build-123');
    });

    it('should reject directories', async () => {
      // Create a test directory within SAFE_ROOT
      const testDir = join(tmpdir(), 'test-dir-' + Date.now());
      await mkdir(testDir);
      
      try {
        // Use relative path from SAFE_ROOT
        const relativePath = relative(tmpdir(), testDir);
        await expect(
          service.createBuildAttestation(relativePath, {
            id: 'test-builder',
            version: '1.0.0',
          })
        ).rejects.toThrow('Subject path must be a file');
      } finally {
        // Clean up
        try {
          await rmdir(testDir);
        } catch {
          // Directory might not exist or can't be removed
        }
      }
    });
  });

  describe('verifyAttestation', () => {
    it('should verify valid attestation', async () => {
      const builder = { id: 'test-builder', version: '1.0.0' };
      const attestation = await service.createBuildAttestation(testFilePath, builder);

      const isValid = await service.verifyAttestation(attestation);
      expect(isValid).toBe(true);
    });

    it('should reject attestation with invalid structure', async () => {
      const invalidAttestation = {
        id: 'test',
        // Missing required fields
      } as unknown as Attestation;

      const isValid = await service.verifyAttestation(invalidAttestation);
      expect(isValid).toBe(false);
    });

    it('should verify attestation without file path', async () => {
      const attestation = {
        id: 'test-123',
        timestamp: new Date().toISOString(),
        subject: {
          name: 'test-artifact',
          digest: 'sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
        },
        predicate: {
          type: 'https://slsa.dev/provenance/v1',
          builder: { id: 'test', version: '1.0.0' },
          recipe: { type: 'test' },
          metadata: {
            buildStartedOn: new Date().toISOString(),
            buildFinishedOn: new Date().toISOString(),
            completeness: { parameters: true, environment: true, materials: true },
            reproducible: false,
          },
        },
      };

      const isValid = await service.verifyAttestation(attestation);
      expect(isValid).toBe(true);
    });
  });

  describe('exportAttestation', () => {
    it('should export attestation as formatted JSON', async () => {
      const builder = { id: 'test-builder', version: '1.0.0' };
      const attestation = await service.createBuildAttestation(testFilePath, builder);

      const exported = service.exportAttestation(attestation);
      const parsed = JSON.parse(exported);

      expect(parsed).toEqual(attestation);
      expect(exported).toContain('\n'); // Check formatting
    });
  });

  describe('importAttestation', () => {
    it('should import valid attestation JSON', async () => {
      const builder = { id: 'test-builder', version: '1.0.0' };
      const originalAttestation = await service.createBuildAttestation(testFilePath, builder);
      const exported = service.exportAttestation(originalAttestation);

      const imported = service.importAttestation(exported);
      expect(imported).toEqual(originalAttestation);
    });

    it('should reject invalid JSON', () => {
      expect(() => service.importAttestation('invalid json')).toThrow();
    });

    it('should reject JSON without required fields', () => {
      const invalidJson = JSON.stringify({ invalid: 'data' });
      expect(() => service.importAttestation(invalidJson)).toThrow('Invalid attestation format');
    });
  });

  describe('SAFE_ROOT_PATH edge cases', () => {
    afterEach(() => {
      // Restore original SAFE_ROOT_PATH after each edge case test
      if (originalSafeRoot !== undefined) {
        process.env.SAFE_ROOT_PATH = originalSafeRoot;
      } else {
        delete process.env.SAFE_ROOT_PATH;
      }
    });

    it('should throw error when SAFE_ROOT_PATH does not exist', async () => {
      // Set SAFE_ROOT_PATH to a non-existent directory
      const nonExistentPath = join(tmpdir(), 'non-existent-dir-' + Date.now());
      process.env.SAFE_ROOT_PATH = nonExistentPath;
      
      const serviceWithInvalidRoot = new ProvenanceService();
      
      await expect(
        serviceWithInvalidRoot.generateFileDigest('test.txt')
      ).rejects.toThrow(/does not exist or is invalid/);
    });

    it('should throw error when SAFE_ROOT_PATH is a file instead of a directory', async () => {
      // Create a file to use as SAFE_ROOT_PATH
      const filePath = join(tmpdir(), 'not-a-directory-' + Date.now());
      await writeFile(filePath, 'this is a file, not a directory');
      
      process.env.SAFE_ROOT_PATH = filePath;
      const serviceWithFileAsRoot = new ProvenanceService();
      
      try {
        await expect(
          serviceWithFileAsRoot.generateFileDigest('test.txt')
        ).rejects.toThrow(/not a directory|does not exist or is invalid/);
      } finally {
        // Clean up the test file
        await unlink(filePath);
      }
    });

    it('should throw error when SAFE_ROOT_PATH is invalid or malformed', async () => {
      // Test with various invalid path scenarios
      const invalidPaths = [
        '\0invalid', // null byte
        'relative/path/without/resolution', // relative path that doesn't exist
      ];

      for (const invalidPath of invalidPaths) {
        process.env.SAFE_ROOT_PATH = invalidPath;
        const serviceWithInvalidPath = new ProvenanceService();
        
        await expect(
          serviceWithInvalidPath.generateFileDigest('test.txt')
        ).rejects.toThrow();
      }
    });
  });
});
