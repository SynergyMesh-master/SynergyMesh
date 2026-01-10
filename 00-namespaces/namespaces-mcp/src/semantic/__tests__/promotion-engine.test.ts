/**
 * Promotion Engine Tests
 * 
 * Test Coverage:
 * - Stage management and transitions
 * - Approval workflow
 * - Release coordination
 * - Rollback functionality
 * - Performance benchmarks
 */

import { describe, it, expect, beforeEach } from '@jest/globals';
import PromotionEngine, {
  StageManager,
  ApprovalWorkflow,
  ReleaseCoordinator,
  PromotionRequest,
  ApprovalPolicy,
  Release,
} from '../promotion-engine';

describe('PromotionEngine', () => {
  let engine: PromotionEngine;

  beforeEach(() => {
    const approvalPolicies: ApprovalPolicy[] = [
      {
        stage: 'staging',
        requiredApprovals: 1,
        approvers: ['dev-lead'],
        autoApprove: false,
      },
      {
        stage: 'prod',
        requiredApprovals: 2,
        approvers: ['tech-lead', 'product-manager'],
        autoApprove: false,
      },
    ];

    engine = new PromotionEngine({
      approvalPolicies,
      autoRollback: true,
      rollbackTimeout: 30000,
    });
  });

  describe('Promotion Request', () => {
    it('should create promotion request successfully', async () => {
      const request: PromotionRequest = {
        id: 'promo-1',
        artifactId: 'app-v1.0.0',
        version: '1.0.0',
        fromStage: 'dev',
        toStage: 'staging',
        requestedBy: 'developer',
        requestedAt: new Date(),
        reason: 'New feature release',
      };

      const promotion = await engine.requestPromotion(request);
      expect(promotion.id).toBe('promo-1');
      expect(promotion.status).toBe('pending');
      expect(promotion.approvals.length).toBeGreaterThan(0);
    });

    it('should reject invalid stage transitions', async () => {
      const request: PromotionRequest = {
        id: 'promo-2',
        artifactId: 'app-v1.0.0',
        version: '1.0.0',
        fromStage: 'dev',
        toStage: 'prod', // Invalid: should go through staging first
        requestedBy: 'developer',
        requestedAt: new Date(),
      };

      await expect(engine.requestPromotion(request)).rejects.toThrow('Invalid stage transition');
    });
  });

  describe('Approval Workflow', () => {
    it('should approve promotion with single approval', async () => {
      const request: PromotionRequest = {
        id: 'promo-3',
        artifactId: 'app-v1.0.0',
        version: '1.0.0',
        fromStage: 'dev',
        toStage: 'staging',
        requestedBy: 'developer',
        requestedAt: new Date(),
      };

      const promotion = await engine.requestPromotion(request);
      expect(promotion.status).toBe('pending');

      await engine.approvePromotion('promo-3', 'dev-lead', 'Looks good');
      
      const updated = engine.getPromotion('promo-3');
      expect(updated?.status).toBe('completed');
    });

    it('should require multiple approvals for production', async () => {
      // First promote to staging
      const stagingRequest: PromotionRequest = {
        id: 'promo-4',
        artifactId: 'app-v1.0.0',
        version: '1.0.0',
        fromStage: 'dev',
        toStage: 'staging',
        requestedBy: 'developer',
        requestedAt: new Date(),
      };

      await engine.requestPromotion(stagingRequest);
      await engine.approvePromotion('promo-4', 'dev-lead');

      // Then promote to production
      const prodRequest: PromotionRequest = {
        id: 'promo-5',
        artifactId: 'app-v1.0.0',
        version: '1.0.0',
        fromStage: 'staging',
        toStage: 'prod',
        requestedBy: 'developer',
        requestedAt: new Date(),
      };

      const promotion = await engine.requestPromotion(prodRequest);
      expect(promotion.approvals.length).toBe(2);

      // First approval
      await engine.approvePromotion('promo-5', 'tech-lead');
      let updated = engine.getPromotion('promo-5');
      expect(updated?.status).toBe('pending'); // Still pending second approval

      // Second approval
      await engine.approvePromotion('promo-5', 'product-manager');
      updated = engine.getPromotion('promo-5');
      expect(updated?.status).toBe('completed');
    });

    it('should reject promotion', async () => {
      const request: PromotionRequest = {
        id: 'promo-6',
        artifactId: 'app-v1.0.0',
        version: '1.0.0',
        fromStage: 'dev',
        toStage: 'staging',
        requestedBy: 'developer',
        requestedAt: new Date(),
      };

      await engine.requestPromotion(request);
      await engine.rejectPromotion('promo-6', 'dev-lead', 'Tests failing');

      const promotion = engine.getPromotion('promo-6');
      expect(promotion?.status).toBe('rejected');
    });
  });

  describe('Rollback', () => {
    it('should rollback failed promotion', async () => {
      const request: PromotionRequest = {
        id: 'promo-7',
        artifactId: 'app-v1.0.0',
        version: '1.0.0',
        fromStage: 'dev',
        toStage: 'staging',
        requestedBy: 'developer',
        requestedAt: new Date(),
      };

      const promotion = await engine.requestPromotion(request);
      await engine.approvePromotion('promo-7', 'dev-lead');

      // Simulate failure and rollback
      await engine.rollbackPromotion('promo-7', 'operator', 'Service unhealthy');

      const updated = engine.getPromotion('promo-7');
      expect(updated?.status).toBe('rolled-back');
      expect(updated?.rollbackInfo).toBeDefined();
      expect(updated?.rollbackInfo?.success).toBe(true);
    });

    it('should complete rollback within 30 seconds', async () => {
      const request: PromotionRequest = {
        id: 'promo-8',
        artifactId: 'app-v1.0.0',
        version: '1.0.0',
        fromStage: 'dev',
        toStage: 'staging',
        requestedBy: 'developer',
        requestedAt: new Date(),
      };

      await engine.requestPromotion(request);
      await engine.approvePromotion('promo-8', 'dev-lead');

      const startTime = Date.now();
      await engine.rollbackPromotion('promo-8', 'operator', 'Test rollback');
      const duration = Date.now() - startTime;

      expect(duration).toBeLessThan(30000);

      const promotion = engine.getPromotion('promo-8');
      expect(promotion?.rollbackInfo?.duration).toBeLessThan(30000);
    });
  });

  describe('Performance', () => {
    it('should complete promotion within 5 minutes', async () => {
      const request: PromotionRequest = {
        id: 'promo-9',
        artifactId: 'app-v1.0.0',
        version: '1.0.0',
        fromStage: 'dev',
        toStage: 'staging',
        requestedBy: 'developer',
        requestedAt: new Date(),
      };

      const startTime = Date.now();
      await engine.requestPromotion(request);
      await engine.approvePromotion('promo-9', 'dev-lead');
      const duration = Date.now() - startTime;

      expect(duration).toBeLessThan(300000); // 5 minutes
    });
  });

  describe('Metrics', () => {
    it('should track promotion metrics', async () => {
      const request: PromotionRequest = {
        id: 'promo-10',
        artifactId: 'app-v1.0.0',
        version: '1.0.0',
        fromStage: 'dev',
        toStage: 'staging',
        requestedBy: 'developer',
        requestedAt: new Date(),
      };

      await engine.requestPromotion(request);
      await engine.approvePromotion('promo-10', 'dev-lead');

      const metrics = engine.getMetrics();
      expect(metrics.totalPromotions).toBeGreaterThan(0);
      expect(metrics.successful).toBeGreaterThan(0);
      expect(metrics.avgPromotionTime).toBeGreaterThan(0);
    });
  });

  describe('Stage Statistics', () => {
    it('should track stage statistics', async () => {
      const request: PromotionRequest = {
        id: 'promo-11',
        artifactId: 'app-v1.0.0',
        version: '1.0.0',
        fromStage: 'dev',
        toStage: 'staging',
        requestedBy: 'developer',
        requestedAt: new Date(),
      };

      await engine.requestPromotion(request);
      await engine.approvePromotion('promo-11', 'dev-lead');

      const stats = engine.getStageStats('staging');
      expect(stats.totalReleases).toBeGreaterThan(0);
      expect(stats.activeRelease).toBeDefined();
    });
  });
});

describe('StageManager', () => {
  let manager: StageManager;

  beforeEach(() => {
    manager = new StageManager();
  });

  it('should validate stage transitions', () => {
    expect(manager.validateTransition('dev', 'staging')).toBe(true);
    expect(manager.validateTransition('staging', 'prod')).toBe(true);
    expect(manager.validateTransition('dev', 'prod')).toBe(false);
    expect(manager.validateTransition('prod', 'staging')).toBe(false);
  });

  it('should deploy release to stage', async () => {
    const release: Release = {
      id: 'release-1',
      version: '1.0.0',
      stage: 'staging',
      artifacts: ['app-v1.0.0'],
      deployedAt: new Date(),
      deployedBy: 'developer',
      status: 'active',
    };

    await manager.deployRelease(release);

    const current = manager.getCurrentRelease('staging');
    expect(current?.id).toBe('release-1');
    expect(current?.status).toBe('active');
  });

  it('should rollback to previous release', async () => {
    const release1: Release = {
      id: 'release-1',
      version: '1.0.0',
      stage: 'staging',
      artifacts: ['app-v1.0.0'],
      deployedAt: new Date(),
      deployedBy: 'developer',
      status: 'active',
    };

    const release2: Release = {
      id: 'release-2',
      version: '1.1.0',
      stage: 'staging',
      artifacts: ['app-v1.1.0'],
      deployedAt: new Date(),
      deployedBy: 'developer',
      status: 'active',
    };

    await manager.deployRelease(release1);
    await manager.deployRelease(release2);

    const previous = await manager.rollback('staging');
    expect(previous?.id).toBe('release-1');
    expect(previous?.status).toBe('active');

    const current = manager.getCurrentRelease('staging');
    expect(current?.id).toBe('release-1');
  });
});

describe('ApprovalWorkflow', () => {
  let workflow: ApprovalWorkflow;

  beforeEach(() => {
    const policies: ApprovalPolicy[] = [
      {
        stage: 'staging',
        requiredApprovals: 1,
        approvers: ['dev-lead'],
      },
      {
        stage: 'prod',
        requiredApprovals: 2,
        approvers: ['tech-lead', 'product-manager'],
      },
    ];

    workflow = new ApprovalWorkflow(policies);
  });

  it('should handle auto-approval', async () => {
    const autoApprovePolicy: ApprovalPolicy[] = [
      {
        stage: 'dev',
        requiredApprovals: 0,
        approvers: [],
        autoApprove: true,
      },
    ];

    const autoWorkflow = new ApprovalWorkflow(autoApprovePolicy);

    const promotion = {
      id: 'promo-auto',
      request: {
        id: 'promo-auto',
        artifactId: 'app-v1.0.0',
        version: '1.0.0',
        fromStage: 'dev' as const,
        toStage: 'staging' as const,
        requestedBy: 'developer',
        requestedAt: new Date(),
      },
      status: 'pending' as const,
      approvals: [],
    };

    await autoWorkflow.requestApproval(promotion);
    expect(autoWorkflow.isFullyApproved('promo-auto')).toBe(true);
  });
});