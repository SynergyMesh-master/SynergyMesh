/**
 * Promotion Engine - Version Promotion & Release Management
 * 
 * Features:
 * - Multi-stage promotion (dev → staging → prod)
 * - Approval workflow with multi-level authorization
 * - Automated rollback on failure
 * - Release coordination with dependency management
 * 
 * Performance Targets:
 * - Promotion Time: <5 minutes
 * - Rollback Time: <30 seconds
 * - Approval Processing: <10 seconds
 * - Success Rate: >99%
 * 
 * @module PromotionEngine
 */

import { EventEmitter } from 'events';

// ============================================================================
// Type Definitions
// ============================================================================

export type Stage = 'dev' | 'staging' | 'prod';
export type PromotionStatus = 'pending' | 'approved' | 'rejected' | 'in-progress' | 'completed' | 'failed' | 'rolled-back';
export type ApprovalStatus = 'pending' | 'approved' | 'rejected';

export interface PromotionRequest {
  id: string;
  artifactId: string;
  version: string;
  fromStage: Stage;
  toStage: Stage;
  requestedBy: string;
  requestedAt: Date;
  reason?: string;
  metadata?: Record<string, any>;
}

export interface Promotion {
  id: string;
  request: PromotionRequest;
  status: PromotionStatus;
  approvals: Approval[];
  startedAt?: Date;
  completedAt?: Date;
  error?: string;
  rollbackInfo?: RollbackInfo;
}

export interface Approval {
  id: string;
  promotionId: string;
  approverId: string;
  status: ApprovalStatus;
  level: number;
  approvedAt?: Date;
  rejectedAt?: Date;
  comment?: string;
}

export interface ApprovalPolicy {
  stage: Stage;
  requiredApprovals: number;
  approvers: string[];
  autoApprove?: boolean;
  timeout?: number; // milliseconds
}

export interface RollbackInfo {
  triggeredBy: string;
  triggeredAt: Date;
  reason: string;
  previousVersion: string;
  success: boolean;
  duration: number;
}

export interface Release {
  id: string;
  version: string;
  stage: Stage;
  artifacts: string[];
  deployedAt: Date;
  deployedBy: string;
  status: 'active' | 'inactive' | 'rolled-back';
  metadata?: Record<string, any>;
}

export interface PromotionConfig {
  approvalPolicies: ApprovalPolicy[];
  autoRollback?: boolean;
  rollbackTimeout?: number;
  healthCheckInterval?: number;
  maxRetries?: number;
}

// ============================================================================
// Stage Manager
// ============================================================================

export class StageManager {
  private stages: Map<Stage, Release[]> = new Map([
    ['dev', []],
    ['staging', []],
    ['prod', []],
  ]);

  /**
   * Get current release for a stage
   */
  getCurrentRelease(stage: Stage): Release | undefined {
    const releases = this.stages.get(stage) || [];
    return releases.find(r => r.status === 'active');
  }

  /**
   * Get all releases for a stage
   */
  getReleases(stage: Stage): Release[] {
    return this.stages.get(stage) || [];
  }

  /**
   * Deploy release to stage
   */
  async deployRelease(release: Release): Promise<void> {
    const releases = this.stages.get(release.stage) || [];
    
    // Deactivate current release
    const current = releases.find(r => r.status === 'active');
    if (current) {
      current.status = 'inactive';
    }

    // Add new release
    releases.push(release);
    this.stages.set(release.stage, releases);
  }

  /**
   * Rollback to previous release
   */
  async rollback(stage: Stage): Promise<Release | undefined> {
    const releases = this.stages.get(stage) || [];
    const current = releases.find(r => r.status === 'active');
    
    if (!current) {
      throw new Error(`No active release found for stage: ${stage}`);
    }

    // Find previous release
    const currentIndex = releases.indexOf(current);
    const previous = releases[currentIndex - 1];

    if (!previous) {
      throw new Error(`No previous release found for rollback`);
    }

    // Rollback
    current.status = 'rolled-back';
    previous.status = 'active';

    return previous;
  }

  /**
   * Validate stage transition
   */
  validateTransition(from: Stage, to: Stage): boolean {
    const validTransitions: Record<Stage, Stage[]> = {
      dev: ['staging'],
      staging: ['prod'],
      prod: [],
    };

    return validTransitions[from]?.includes(to) || false;
  }

  /**
   * Get stage statistics
   */
  getStats(stage: Stage): {
    totalReleases: number;
    activeRelease?: string;
    lastDeployment?: Date;
  } {
    const releases = this.stages.get(stage) || [];
    const active = releases.find(r => r.status === 'active');
    const lastRelease = releases[releases.length - 1];

    return {
      totalReleases: releases.length,
      activeRelease: active?.version,
      lastDeployment: lastRelease?.deployedAt,
    };
  }
}

// ============================================================================
// Approval Workflow
// ============================================================================

export class ApprovalWorkflow {
  private policies: Map<Stage, ApprovalPolicy> = new Map();
  private approvals: Map<string, Approval[]> = new Map();

  constructor(policies: ApprovalPolicy[]) {
    for (const policy of policies) {
      this.policies.set(policy.stage, policy);
    }
  }

  /**
   * Request approval for promotion
   */
  async requestApproval(promotion: Promotion): Promise<void> {
    const policy = this.policies.get(promotion.request.toStage);
    if (!policy) {
      throw new Error(`No approval policy found for stage: ${promotion.request.toStage}`);
    }

    // Auto-approve if enabled
    if (policy.autoApprove) {
      const approval: Approval = {
        id: `approval-${Date.now()}`,
        promotionId: promotion.id,
        approverId: 'system',
        status: 'approved',
        level: 1,
        approvedAt: new Date(),
        comment: 'Auto-approved by system',
      };
      this.approvals.set(promotion.id, [approval]);
      return;
    }

    // Create pending approvals
    const approvals: Approval[] = [];
    for (let i = 0; i < policy.requiredApprovals; i++) {
      approvals.push({
        id: `approval-${promotion.id}-${i}`,
        promotionId: promotion.id,
        approverId: policy.approvers[i] || 'pending',
        status: 'pending',
        level: i + 1,
      });
    }

    this.approvals.set(promotion.id, approvals);
  }

  /**
   * Approve promotion
   */
  async approve(
    promotionId: string,
    approverId: string,
    comment?: string
  ): Promise<boolean> {
    const approvals = this.approvals.get(promotionId);
    if (!approvals) {
      throw new Error(`No approvals found for promotion: ${promotionId}`);
    }

    // Find pending approval for this approver
    const approval = approvals.find(
      a => a.status === 'pending' && (a.approverId === approverId || a.approverId === 'pending')
    );

    if (!approval) {
      throw new Error(`No pending approval found for approver: ${approverId}`);
    }

    // Approve
    approval.approverId = approverId;
    approval.status = 'approved';
    approval.approvedAt = new Date();
    approval.comment = comment;

    // Check if all approvals are complete
    return this.isFullyApproved(promotionId);
  }

  /**
   * Reject promotion
   */
  async reject(
    promotionId: string,
    approverId: string,
    comment?: string
  ): Promise<void> {
    const approvals = this.approvals.get(promotionId);
    if (!approvals) {
      throw new Error(`No approvals found for promotion: ${promotionId}`);
    }

    // Find pending approval for this approver
    const approval = approvals.find(
      a => a.status === 'pending' && (a.approverId === approverId || a.approverId === 'pending')
    );

    if (!approval) {
      throw new Error(`No pending approval found for approver: ${approverId}`);
    }

    // Reject
    approval.approverId = approverId;
    approval.status = 'rejected';
    approval.rejectedAt = new Date();
    approval.comment = comment;
  }

  /**
   * Check if promotion is fully approved
   */
  isFullyApproved(promotionId: string): boolean {
    const approvals = this.approvals.get(promotionId);
    if (!approvals) return false;

    return approvals.every(a => a.status === 'approved');
  }

  /**
   * Check if promotion is rejected
   */
  isRejected(promotionId: string): boolean {
    const approvals = this.approvals.get(promotionId);
    if (!approvals) return false;

    return approvals.some(a => a.status === 'rejected');
  }

  /**
   * Get approval status
   */
  getApprovalStatus(promotionId: string): Approval[] {
    return this.approvals.get(promotionId) || [];
  }
}

// ============================================================================
// Release Coordinator
// ============================================================================

export class ReleaseCoordinator {
  private stageManager: StageManager;
  private config: Required<PromotionConfig>;

  constructor(stageManager: StageManager, config: PromotionConfig) {
    this.stageManager = stageManager;
    this.config = {
      approvalPolicies: config.approvalPolicies,
      autoRollback: config.autoRollback ?? true,
      rollbackTimeout: config.rollbackTimeout ?? 30000,
      healthCheckInterval: config.healthCheckInterval ?? 5000,
      maxRetries: config.maxRetries ?? 3,
    };
  }

  /**
   * Execute promotion
   */
  async executePromotion(promotion: Promotion): Promise<void> {
    const startTime = Date.now();
    promotion.status = 'in-progress';
    promotion.startedAt = new Date();

    try {
      // Create release
      const release: Release = {
        id: `release-${Date.now()}`,
        version: promotion.request.version,
        stage: promotion.request.toStage,
        artifacts: [promotion.request.artifactId],
        deployedAt: new Date(),
        deployedBy: promotion.request.requestedBy,
        status: 'active',
        metadata: promotion.request.metadata,
      };

      // Deploy to stage
      await this.stageManager.deployRelease(release);

      // Health check
      const healthy = await this.performHealthCheck(release);
      if (!healthy) {
        throw new Error('Health check failed after deployment');
      }

      // Mark as completed
      promotion.status = 'completed';
      promotion.completedAt = new Date();

    } catch (error) {
      promotion.status = 'failed';
      promotion.error = error instanceof Error ? error.message : 'Unknown error';

      // Auto-rollback if enabled
      if (this.config.autoRollback) {
        await this.rollback(promotion, 'system', 'Auto-rollback on failure');
      }

      throw error;
    }
  }

  /**
   * Rollback promotion
   */
  async rollback(
    promotion: Promotion,
    triggeredBy: string,
    reason: string
  ): Promise<void> {
    const startTime = Date.now();

    try {
      const previous = await this.stageManager.rollback(promotion.request.toStage);

      promotion.rollbackInfo = {
        triggeredBy,
        triggeredAt: new Date(),
        reason,
        previousVersion: previous?.version || 'unknown',
        success: true,
        duration: Date.now() - startTime,
      };

      promotion.status = 'rolled-back';

    } catch (error) {
      promotion.rollbackInfo = {
        triggeredBy,
        triggeredAt: new Date(),
        reason,
        previousVersion: 'unknown',
        success: false,
        duration: Date.now() - startTime,
      };

      throw error;
    }
  }

  /**
   * Perform health check
   */
  private async performHealthCheck(release: Release): Promise<boolean> {
    // Simplified health check
    // In production, this would check actual service health
    await new Promise(resolve => setTimeout(resolve, 1000));
    return Math.random() > 0.05; // 95% success rate
  }

  /**
   * Get release history
   */
  getReleaseHistory(stage: Stage): Release[] {
    return this.stageManager.getReleases(stage);
  }
}

// ============================================================================
// Promotion Engine
// ============================================================================

export class PromotionEngine extends EventEmitter {
  private stageManager: StageManager;
  private approvalWorkflow: ApprovalWorkflow;
  private releaseCoordinator: ReleaseCoordinator;
  private promotions: Map<string, Promotion> = new Map();
  private metrics: {
    totalPromotions: number;
    successful: number;
    failed: number;
    rolledBack: number;
    avgPromotionTime: number;
    avgRollbackTime: number;
  };

  constructor(config: PromotionConfig) {
    super();
    this.stageManager = new StageManager();
    this.approvalWorkflow = new ApprovalWorkflow(config.approvalPolicies);
    this.releaseCoordinator = new ReleaseCoordinator(this.stageManager, config);
    this.metrics = {
      totalPromotions: 0,
      successful: 0,
      failed: 0,
      rolledBack: 0,
      avgPromotionTime: 0,
      avgRollbackTime: 0,
    };
  }

  /**
   * Request promotion
   */
  async requestPromotion(request: PromotionRequest): Promise<Promotion> {
    // Validate stage transition
    if (!this.stageManager.validateTransition(request.fromStage, request.toStage)) {
      throw new Error(`Invalid stage transition: ${request.fromStage} → ${request.toStage}`);
    }

    // Create promotion
    const promotion: Promotion = {
      id: request.id,
      request,
      status: 'pending',
      approvals: [],
    };

    this.promotions.set(promotion.id, promotion);

    // Request approvals
    await this.approvalWorkflow.requestApproval(promotion);
    promotion.approvals = this.approvalWorkflow.getApprovalStatus(promotion.id);

    // Check if auto-approved
    if (this.approvalWorkflow.isFullyApproved(promotion.id)) {
      promotion.status = 'approved';
      await this.executePromotion(promotion.id);
    }

    this.emit('promotion:requested', { promotion });
    return promotion;
  }

  /**
   * Approve promotion
   */
  async approvePromotion(
    promotionId: string,
    approverId: string,
    comment?: string
  ): Promise<void> {
    const promotion = this.promotions.get(promotionId);
    if (!promotion) {
      throw new Error(`Promotion not found: ${promotionId}`);
    }

    const fullyApproved = await this.approvalWorkflow.approve(promotionId, approverId, comment);
    promotion.approvals = this.approvalWorkflow.getApprovalStatus(promotionId);

    if (fullyApproved) {
      promotion.status = 'approved';
      this.emit('promotion:approved', { promotion });
      await this.executePromotion(promotionId);
    }
  }

  /**
   * Reject promotion
   */
  async rejectPromotion(
    promotionId: string,
    approverId: string,
    comment?: string
  ): Promise<void> {
    const promotion = this.promotions.get(promotionId);
    if (!promotion) {
      throw new Error(`Promotion not found: ${promotionId}`);
    }

    await this.approvalWorkflow.reject(promotionId, approverId, comment);
    promotion.status = 'rejected';
    promotion.approvals = this.approvalWorkflow.getApprovalStatus(promotionId);

    this.emit('promotion:rejected', { promotion });
  }

  /**
   * Execute promotion
   */
  private async executePromotion(promotionId: string): Promise<void> {
    const promotion = this.promotions.get(promotionId);
    if (!promotion) {
      throw new Error(`Promotion not found: ${promotionId}`);
    }

    const startTime = Date.now();

    try {
      await this.releaseCoordinator.executePromotion(promotion);

      // Update metrics
      this.metrics.totalPromotions++;
      this.metrics.successful++;
      this.metrics.avgPromotionTime =
        (this.metrics.avgPromotionTime * (this.metrics.totalPromotions - 1) +
          (Date.now() - startTime)) /
        this.metrics.totalPromotions;

      this.emit('promotion:completed', { promotion });

    } catch (error) {
      this.metrics.totalPromotions++;
      this.metrics.failed++;

      if (promotion.status === 'rolled-back') {
        this.metrics.rolledBack++;
        if (promotion.rollbackInfo) {
          this.metrics.avgRollbackTime =
            (this.metrics.avgRollbackTime * (this.metrics.rolledBack - 1) +
              promotion.rollbackInfo.duration) /
            this.metrics.rolledBack;
        }
      }

      this.emit('promotion:failed', { promotion, error });
      throw error;
    }
  }

  /**
   * Rollback promotion
   */
  async rollbackPromotion(
    promotionId: string,
    triggeredBy: string,
    reason: string
  ): Promise<void> {
    const promotion = this.promotions.get(promotionId);
    if (!promotion) {
      throw new Error(`Promotion not found: ${promotionId}`);
    }

    await this.releaseCoordinator.rollback(promotion, triggeredBy, reason);
    this.emit('promotion:rolled-back', { promotion });
  }

  /**
   * Get promotion status
   */
  getPromotion(promotionId: string): Promotion | undefined {
    return this.promotions.get(promotionId);
  }

  /**
   * Get stage statistics
   */
  getStageStats(stage: Stage) {
    return this.stageManager.getStats(stage);
  }

  /**
   * Get promotion metrics
   */
  getMetrics(): typeof this.metrics {
    return { ...this.metrics };
  }

  /**
   * Get release history
   */
  getReleaseHistory(stage: Stage): Release[] {
    return this.releaseCoordinator.getReleaseHistory(stage);
  }
}

// ============================================================================
// Export
// ============================================================================

export default PromotionEngine;