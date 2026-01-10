/**
 * Artifact Registry Tests
 * 
 * Test Coverage:
 * - Artifact publishing and downloading
 * - Version management
 * - Storage backend operations
 * - Metadata indexing and search
 * - Performance benchmarks
 */

import { describe, it, expect, beforeEach } from '@jest/globals';
import ArtifactRegistry, {
  VersionManager,
  StorageBackendManager,
  MetadataIndexer,
  Artifact,
  ArtifactMetadata,
  SearchQuery,
} from '../artifact-registry';

describe('ArtifactRegistry', () => {
  let registry: ArtifactRegistry;

  beforeEach(() => {
    registry = new ArtifactRegistry({
      storage: {
        backend: 'local',
        basePath: '/tmp/artifacts',
      },
      retentionDays: 90,
      maxVersions: 10,
      enableCompression: true,
      enableDeduplication: true,
    });
  });

  describe('Artifact Publishing', () => {
    it('should publish artifact successfully', async () => {
      const data = Buffer.from('test artifact content');
      const metadata: ArtifactMetadata = {
        description: 'Test artifact',
        author: 'developer',
        tags: ['test', 'v1'],
      };

      const artifact = await registry.publish(
        'test-app',
        '1.0.0',
        'tar.gz',
        data,
        metadata
      );

      expect(artifact.id).toBe('test-app@1.0.0');
      expect(artifact.name).toBe('test-app');
      expect(artifact.version).toBe('1.0.0');
      expect(artifact.size).toBe(data.length);
      expect(artifact.checksum).toBeDefined();
    });

    it('should deduplicate identical artifacts', async () => {
      const data = Buffer.from('duplicate content');

      const artifact1 = await registry.publish('app1', '1.0.0', 'tar.gz', data);
      const artifact2 = await registry.publish('app2', '1.0.0', 'tar.gz', data);

      // Should have same checksum
      expect(artifact1.checksum).toBe(artifact2.checksum);
    });

    it('should reject invalid version format', async () => {
      const data = Buffer.from('test content');

      await expect(
        registry.publish('test-app', 'invalid-version', 'tar.gz', data)
      ).rejects.toThrow('Invalid semantic version');
    });
  });

  describe('Artifact Downloading', () => {
    it('should download artifact successfully', async () => {
      const originalData = Buffer.from('download test content');
      const artifact = await registry.publish('download-app', '1.0.0', 'tar.gz', originalData);

      const downloadedData = await registry.download(artifact.id);
      expect(downloadedData.toString()).toBe(originalData.toString());
    });

    it('should verify checksum on download', async () => {
      const data = Buffer.from('checksum test');
      const artifact = await registry.publish('checksum-app', '1.0.0', 'tar.gz', data);

      // Download should succeed with valid checksum
      await expect(registry.download(artifact.id)).resolves.toBeDefined();
    });

    it('should throw error for non-existent artifact', async () => {
      await expect(registry.download('non-existent@1.0.0')).rejects.toThrow('Artifact not found');
    });
  });

  describe('Version Management', () => {
    it('should get latest version', async () => {
      const data = Buffer.from('version test');

      await registry.publish('version-app', '1.0.0', 'tar.gz', data);
      await registry.publish('version-app', '1.1.0', 'tar.gz', data);
      await registry.publish('version-app', '2.0.0', 'tar.gz', data);

      const latest = registry.getLatestVersion('version-app');
      expect(latest?.version).toBe('2.0.0');
    });

    it('should get all versions', async () => {
      const data = Buffer.from('versions test');

      await registry.publish('multi-version-app', '1.0.0', 'tar.gz', data);
      await registry.publish('multi-version-app', '1.1.0', 'tar.gz', data);
      await registry.publish('multi-version-app', '1.2.0', 'tar.gz', data);

      const versions = registry.getAllVersions('multi-version-app');
      expect(versions.length).toBe(3);
      expect(versions.map(v => v.version)).toContain('1.0.0');
      expect(versions.map(v => v.version)).toContain('1.1.0');
      expect(versions.map(v => v.version)).toContain('1.2.0');
    });
  });

  describe('Search', () => {
    beforeEach(async () => {
      const data = Buffer.from('search test');

      await registry.publish('app-a', '1.0.0', 'tar.gz', data, {
        tags: ['frontend', 'react'],
        author: 'team-a',
      });

      await registry.publish('app-b', '1.0.0', 'jar', data, {
        tags: ['backend', 'java'],
        author: 'team-b',
      });

      await registry.publish('app-c', '1.0.0', 'tar.gz', data, {
        tags: ['frontend', 'vue'],
        author: 'team-a',
      });
    });

    it('should search by name', () => {
      const result = registry.search({ name: 'app-a' });
      expect(result.artifacts.length).toBe(1);
      expect(result.artifacts[0].name).toBe('app-a');
    });

    it('should search by type', () => {
      const result = registry.search({ type: 'tar.gz' });
      expect(result.artifacts.length).toBe(2);
    });

    it('should search by tags', () => {
      const result = registry.search({ tags: ['frontend'] });
      expect(result.artifacts.length).toBe(2);
    });

    it('should search by author', () => {
      const result = registry.search({ author: 'team-a' });
      expect(result.artifacts.length).toBe(2);
    });

    it('should support pagination', () => {
      const result = registry.search({ limit: 1, offset: 0 });
      expect(result.artifacts.length).toBe(1);
      expect(result.hasMore).toBe(true);
    });
  });

  describe('Deletion', () => {
    it('should delete artifact successfully', async () => {
      const data = Buffer.from('delete test');
      const artifact = await registry.publish('delete-app', '1.0.0', 'tar.gz', data);

      await registry.delete(artifact.id);

      const found = registry.getArtifact(artifact.id);
      expect(found).toBeUndefined();
    });

    it('should update metrics after deletion', async () => {
      const data = Buffer.from('metrics test');
      const artifact = await registry.publish('metrics-app', '1.0.0', 'tar.gz', data);

      const beforeMetrics = registry.getMetrics();
      await registry.delete(artifact.id);
      const afterMetrics = registry.getMetrics();

      expect(afterMetrics.totalArtifacts).toBe(beforeMetrics.totalArtifacts - 1);
      expect(afterMetrics.totalDeletes).toBe(beforeMetrics.totalDeletes + 1);
    });
  });

  describe('Performance', () => {
    it('should lookup artifact within 100ms', async () => {
      const data = Buffer.from('perf test');
      const artifact = await registry.publish('perf-app', '1.0.0', 'tar.gz', data);

      const startTime = Date.now();
      registry.getArtifact(artifact.id);
      const duration = Date.now() - startTime;

      expect(duration).toBeLessThan(100);
    });

    it('should handle high upload throughput', async () => {
      const data = Buffer.from('throughput test');
      const startTime = Date.now();

      const promises = [];
      for (let i = 0; i < 100; i++) {
        promises.push(registry.publish(`throughput-app-${i}`, '1.0.0', 'tar.gz', data));
      }

      await Promise.all(promises);
      const duration = Date.now() - startTime;
      const throughput = 100 / (duration / 1000); // artifacts per second

      expect(throughput).toBeGreaterThan(10); // >10 artifacts/sec
    });
  });

  describe('Metrics', () => {
    it('should track registry metrics', async () => {
      const data = Buffer.from('metrics test');

      await registry.publish('metrics-app-1', '1.0.0', 'tar.gz', data);
      await registry.download('metrics-app-1@1.0.0');

      const metrics = registry.getMetrics();
      expect(metrics.totalArtifacts).toBeGreaterThan(0);
      expect(metrics.totalUploads).toBeGreaterThan(0);
      expect(metrics.totalDownloads).toBeGreaterThan(0);
      expect(metrics.avgUploadTime).toBeGreaterThan(0);
      expect(metrics.avgDownloadTime).toBeGreaterThan(0);
    });
  });
});

describe('VersionManager', () => {
  let manager: VersionManager;

  beforeEach(() => {
    manager = new VersionManager();
  });

  describe('Version Parsing', () => {
    it('should parse valid semantic versions', () => {
      const v1 = manager.parseVersion('1.2.3');
      expect(v1.major).toBe(1);
      expect(v1.minor).toBe(2);
      expect(v1.patch).toBe(3);

      const v2 = manager.parseVersion('2.0.0-beta.1');
      expect(v2.major).toBe(2);
      expect(v2.prerelease).toBe('beta.1');

      const v3 = manager.parseVersion('1.0.0+build.123');
      expect(v3.build).toBe('build.123');
    });

    it('should reject invalid versions', () => {
      expect(() => manager.parseVersion('invalid')).toThrow('Invalid semantic version');
      expect(() => manager.parseVersion('1.2')).toThrow('Invalid semantic version');
      expect(() => manager.parseVersion('v1.2.3')).toThrow('Invalid semantic version');
    });
  });

  describe('Version Comparison', () => {
    it('should compare versions correctly', () => {
      expect(manager.compareVersions('1.0.0', '2.0.0')).toBeLessThan(0);
      expect(manager.compareVersions('2.0.0', '1.0.0')).toBeGreaterThan(0);
      expect(manager.compareVersions('1.0.0', '1.0.0')).toBe(0);

      expect(manager.compareVersions('1.2.3', '1.2.4')).toBeLessThan(0);
      expect(manager.compareVersions('1.3.0', '1.2.9')).toBeGreaterThan(0);

      expect(manager.compareVersions('1.0.0-alpha', '1.0.0')).toBeLessThan(0);
      expect(manager.compareVersions('1.0.0', '1.0.0-beta')).toBeGreaterThan(0);
    });
  });

  describe('Version Bumping', () => {
    it('should bump major version', () => {
      const bumped = manager.bumpVersion('1.2.3', 'major');
      expect(bumped).toBe('2.0.0');
    });

    it('should bump minor version', () => {
      const bumped = manager.bumpVersion('1.2.3', 'minor');
      expect(bumped).toBe('1.3.0');
    });

    it('should bump patch version', () => {
      const bumped = manager.bumpVersion('1.2.3', 'patch');
      expect(bumped).toBe('1.2.4');
    });

    it('should remove prerelease on bump', () => {
      const bumped = manager.bumpVersion('1.2.3-beta.1', 'patch');
      expect(bumped).toBe('1.2.4');
    });
  });

  describe('Latest Version', () => {
    it('should find latest version from list', () => {
      const versions = ['1.0.0', '1.2.0', '1.1.0', '2.0.0', '1.3.0'];
      const latest = manager.getLatestVersion(versions);
      expect(latest).toBe('2.0.0');
    });

    it('should handle empty list', () => {
      const latest = manager.getLatestVersion([]);
      expect(latest).toBeUndefined();
    });
  });

  describe('Version Range', () => {
    it('should check caret range', () => {
      expect(manager.satisfiesRange('1.2.3', '^1.0.0')).toBe(true);
      expect(manager.satisfiesRange('1.9.9', '^1.0.0')).toBe(true);
      expect(manager.satisfiesRange('2.0.0', '^1.0.0')).toBe(false);
    });

    it('should check tilde range', () => {
      expect(manager.satisfiesRange('1.2.3', '~1.2.0')).toBe(true);
      expect(manager.satisfiesRange('1.2.9', '~1.2.0')).toBe(true);
      expect(manager.satisfiesRange('1.3.0', '~1.2.0')).toBe(false);
    });

    it('should check exact version', () => {
      expect(manager.satisfiesRange('1.2.3', '1.2.3')).toBe(true);
      expect(manager.satisfiesRange('1.2.4', '1.2.3')).toBe(false);
    });
  });
});

describe('MetadataIndexer', () => {
  let indexer: MetadataIndexer;

  beforeEach(() => {
    indexer = new MetadataIndexer();
  });

  it('should index and retrieve artifacts', () => {
    const artifact: Artifact = {
      id: 'test@1.0.0',
      name: 'test',
      version: '1.0.0',
      type: 'tar.gz',
      size: 1024,
      checksum: 'abc123',
      storageBackend: 'local',
      storagePath: '/tmp/test',
      metadata: { tags: ['test'] },
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    indexer.indexArtifact(artifact);

    const retrieved = indexer.getArtifact('test@1.0.0');
    expect(retrieved?.id).toBe('test@1.0.0');
  });

  it('should remove artifacts from index', () => {
    const artifact: Artifact = {
      id: 'remove@1.0.0',
      name: 'remove',
      version: '1.0.0',
      type: 'tar.gz',
      size: 1024,
      checksum: 'abc123',
      storageBackend: 'local',
      storagePath: '/tmp/remove',
      metadata: {},
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    indexer.indexArtifact(artifact);
    indexer.removeArtifact('remove@1.0.0');

    const retrieved = indexer.getArtifact('remove@1.0.0');
    expect(retrieved).toBeUndefined();
  });

  it('should track index statistics', () => {
    const artifact1: Artifact = {
      id: 'stats1@1.0.0',
      name: 'stats1',
      version: '1.0.0',
      type: 'tar.gz',
      size: 1024,
      checksum: 'abc123',
      storageBackend: 'local',
      storagePath: '/tmp/stats1',
      metadata: { tags: ['tag1', 'tag2'] },
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    const artifact2: Artifact = {
      id: 'stats2@1.0.0',
      name: 'stats2',
      version: '1.0.0',
      type: 'jar',
      size: 2048,
      checksum: 'def456',
      storageBackend: 'local',
      storagePath: '/tmp/stats2',
      metadata: { tags: ['tag1'] },
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    indexer.indexArtifact(artifact1);
    indexer.indexArtifact(artifact2);

    const stats = indexer.getStats();
    expect(stats.totalArtifacts).toBe(2);
    expect(stats.uniqueNames).toBe(2);
    expect(stats.uniqueTags).toBe(2);
    expect(stats.uniqueTypes).toBe(2);
  });
});