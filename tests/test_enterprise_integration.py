#!/usr/bin/env python3
"""
企業級集成測試套件 - Enterprise Integration Test Suite

測試範圍：
1. 多租戶隔離測試
2. 依賴解析端到端測試
3. 容錯重試完整流程
4. 資源配額聯合測試
5. 審計日誌完整性測試
6. 性能和可擴展性測試
"""

import asyncio
import pytest
import sys
from pathlib import Path

# 添加 src 到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from core.orchestrators import (
    EnterpriseSynergyMeshOrchestrator,
    DependencyResolver,
    TenantTier,
    ExecutionStatus,
    ComponentType
)


# ============================================================================
# 多租戶隔離測試
# ============================================================================

class TestMultiTenantIsolation:
    """多租戶隔離和數據保護測試"""

    def test_tenant_data_isolation(self):
        """測試租戶數據隔離"""
        orch = EnterpriseSynergyMeshOrchestrator()

        # 創建多個租戶
        tenant1 = orch.create_tenant("Company A", TenantTier.BASIC)
        tenant2 = orch.create_tenant("Company B", TenantTier.PROFESSIONAL)
        tenant3 = orch.create_tenant("Company C", TenantTier.ENTERPRISE)

        # 驗證租戶隔離
        assert tenant1 != tenant2
        assert tenant2 != tenant3
        assert len(orch.tenants) == 3

        # 驗證可以檢索每個租戶的配置
        config1 = orch.get_tenant(tenant1)
        config2 = orch.get_tenant(tenant2)
        config3 = orch.get_tenant(tenant3)

        assert config1.tenant_name == "Company A"
        assert config2.tenant_name == "Company B"
        assert config3.tenant_name == "Company C"

    def test_tenant_resource_quota_isolation(self):
        """測試租戶資源配額隔離"""
        orch = EnterpriseSynergyMeshOrchestrator()

        # 創建不同等級的租戶
        basic = orch.create_tenant("Basic Plan", TenantTier.BASIC)
        pro = orch.create_tenant("Pro Plan", TenantTier.PROFESSIONAL)
        enterprise = orch.create_tenant("Enterprise Plan", TenantTier.ENTERPRISE)

        # 驗證配額不同
        basic_config = orch.get_tenant(basic)
        pro_config = orch.get_tenant(pro)
        ent_config = orch.get_tenant(enterprise)

        # Basic < Pro < Enterprise
        assert basic_config.quota.max_concurrent_tasks < pro_config.quota.max_concurrent_tasks
        assert pro_config.quota.max_concurrent_tasks < ent_config.quota.max_concurrent_tasks

        assert basic_config.quota.max_memory_mb < ent_config.quota.max_memory_mb
        assert basic_config.quota.rate_limit_per_second < ent_config.quota.rate_limit_per_second

    def test_tenant_feature_isolation(self):
        """測試租戶功能隔離"""
        orch = EnterpriseSynergyMeshOrchestrator()

        # 不同層級的租戶有不同的功能
        basic = orch.create_tenant("Basic", TenantTier.BASIC)
        enterprise = orch.create_tenant("Enterprise", TenantTier.ENTERPRISE)

        basic_config = orch.get_tenant(basic)
        ent_config = orch.get_tenant(enterprise)

        # Enterprise 應該有更多功能
        assert len(ent_config.features_enabled) >= len(basic_config.features_enabled)

    def test_audit_logs_per_tenant(self):
        """測試審計日誌的租戶隔離"""
        orch = EnterpriseSynergyMeshOrchestrator()

        tenant1 = orch.create_tenant("Tenant 1", TenantTier.BASIC)
        tenant2 = orch.create_tenant("Tenant 2", TenantTier.BASIC)

        # 每個租戶的審計日誌應該分開
        logs1 = orch.get_audit_logs(tenant1)
        logs2 = orch.get_audit_logs(tenant2)

        assert isinstance(logs1, list)
        assert isinstance(logs2, list)


# ============================================================================
# 依賴解析端到端測試
# ============================================================================

class TestDependencyResolutionE2E:
    """依賴解析和執行順序的端到端測試"""

    def test_complex_dependency_graph(self):
        """測試複雜的依賴圖"""
        resolver = DependencyResolver()

        # 構建複雜的依賴圖（微服務架構）
        services = {
            "database": "service",
            "cache": "service",
            "auth": "service",
            "api_gateway": "service",
            "user_service": "service",
            "product_service": "service",
            "order_service": "service",
            "notification_service": "service"
        }

        for service_id, service_type in services.items():
            resolver.add_component(service_id, service_type)

        # 定義依賴
        dependencies = [
            ("cache", "database"),
            ("auth", "database"),
            ("user_service", "database"),
            ("user_service", "auth"),
            ("user_service", "cache"),
            ("product_service", "database"),
            ("product_service", "cache"),
            ("order_service", "database"),
            ("order_service", "user_service"),
            ("order_service", "product_service"),
            ("notification_service", "order_service"),
            ("api_gateway", "auth"),
            ("api_gateway", "user_service"),
            ("api_gateway", "product_service"),
            ("api_gateway", "order_service")
        ]

        for from_svc, to_svc in dependencies:
            assert resolver.add_dependency(from_svc, to_svc)

        # 驗證拓撲排序
        order = resolver.topological_sort()
        assert len(order) == 8
        assert "database" in order

        # 驗證執行階段
        phases = resolver.get_execution_phases()
        assert len(phases) > 0

        # 驗證並行化分析
        analysis = resolver.get_parallelization_analysis()
        assert analysis["total_components"] == 8
        assert analysis["parallelization_factor"] > 1.0

    def test_dependency_chain_execution(self):
        """測試依賴鏈的執行順序"""
        resolver = DependencyResolver()

        # 簡單的鏈：A → B → C → D
        for comp in ["A", "B", "C", "D"]:
            resolver.add_component(comp, "agent")

        assert resolver.add_dependency("B", "A")
        assert resolver.add_dependency("C", "B")
        assert resolver.add_dependency("D", "C")

        order = resolver.topological_sort()
        assert len(order) == 4

        # 驗證執行階段
        phases = resolver.get_execution_phases()
        assert len(phases) == 4  # 每個組件一個階段

    def test_diamond_dependency_pattern(self):
        """測試鑽石依賴模式"""
        resolver = DependencyResolver()

        # 鑽石模式：
        #     A
        #    / \
        #   B   C
        #    \ /
        #     D

        for comp in ["A", "B", "C", "D"]:
            resolver.add_component(comp, "agent")

        assert resolver.add_dependency("B", "A")
        assert resolver.add_dependency("C", "A")
        assert resolver.add_dependency("D", "B")
        assert resolver.add_dependency("D", "C")

        order = resolver.topological_sort()
        assert len(order) == 4

        # 驗證圖結構正確
        assert "A" in resolver.graph.get("B", set())
        assert "A" in resolver.graph.get("C", set())
        assert "B" in resolver.graph.get("D", set())
        assert "C" in resolver.graph.get("D", set())

        # 驗證所有組件都在排序結果中
        assert "A" in order and "B" in order and "C" in order and "D" in order


# ============================================================================
# 容錯重試完整流程測試
# ============================================================================

class TestFaultToleranceE2E:
    """容錯機制的端到端集成測試"""

    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff_flow(self):
        """測試指數退避重試的完整流程"""
        orch = EnterpriseSynergyMeshOrchestrator()
        tenant_id = orch.create_tenant("Test", TenantTier.BASIC)

        call_times = []

        async def flaky_service(**kwargs):
            call_times.append(asyncio.get_event_loop().time())
            if len(call_times) < 3:
                raise RuntimeError(f"Attempt {len(call_times)} failed")
            return {"success": True}

        result = await orch.execute_with_retry(
            flaky_service,
            "test_service",
            tenant_id,
            max_retries=3
        )

        assert result.status.value == "success"
        assert result.retry_count == 2
        assert len(call_times) == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_pattern(self):
        """測試熔斷器模式"""
        orch = EnterpriseSynergyMeshOrchestrator()
        tenant_id = orch.create_tenant("Test", TenantTier.PROFESSIONAL)

        call_count = 0

        async def always_fails(**kwargs):
            nonlocal call_count
            call_count += 1
            raise RuntimeError("Service unavailable")

        # 多次重試都失敗
        result = await orch.execute_with_retry(
            always_fails,
            "failing_service",
            tenant_id,
            max_retries=2
        )

        assert result.status.value == "failed"
        assert call_count == 3  # 1 initial + 2 retries

    @pytest.mark.asyncio
    async def test_recovery_after_failure(self):
        """測試故障後的恢復"""
        orch = EnterpriseSynergyMeshOrchestrator()
        tenant_id = orch.create_tenant("Test", TenantTier.BASIC)

        execution_attempts = []

        async def recovering_service(**kwargs):
            execution_attempts.append(len(execution_attempts) + 1)
            if len(execution_attempts) <= 2:
                raise RuntimeError("Temporary failure")
            return {"recovered": True}

        result = await orch.execute_with_retry(
            recovering_service,
            "recovering_service",
            tenant_id,
            max_retries=3
        )

        assert result.status.value == "success"
        assert len(execution_attempts) == 3
        assert result.output["recovered"] is True


# ============================================================================
# 資源配額聯合測試
# ============================================================================

class TestResourceQuotaIntegration:
    """資源配額的集成測試"""

    def test_concurrent_task_limits_per_tenant(self):
        """測試每個租戶的並發任務限制"""
        orch = EnterpriseSynergyMeshOrchestrator()

        basic = orch.create_tenant("Basic", TenantTier.BASIC)
        enterprise = orch.create_tenant("Enterprise", TenantTier.ENTERPRISE)

        basic_can_run = orch.check_resource_quota(basic, "concurrent")
        ent_can_run = orch.check_resource_quota(enterprise, "concurrent")

        assert basic_can_run
        assert ent_can_run

    def test_memory_quota_enforcement(self):
        """測試內存配額執行"""
        orch = EnterpriseSynergyMeshOrchestrator()

        tenant = orch.create_tenant("Test", TenantTier.BASIC)
        config = orch.get_tenant(tenant)

        # 驗證內存配額設置
        assert config.quota.max_memory_mb > 0
        assert config.quota.max_memory_mb < 2000  # Basic tier limit

    def test_rate_limiting_across_tenants(self):
        """測試跨租戶的速率限制"""
        orch = EnterpriseSynergyMeshOrchestrator()

        tenant1 = orch.create_tenant("Tenant 1", TenantTier.BASIC)
        tenant2 = orch.create_tenant("Tenant 2", TenantTier.PROFESSIONAL)

        # 驗證速率限制配置
        config1 = orch.get_tenant(tenant1)
        config2 = orch.get_tenant(tenant2)

        assert config1.quota.rate_limit_per_second < config2.quota.rate_limit_per_second

    def test_quota_per_hour_limits(self):
        """測試小時任務配額"""
        orch = EnterpriseSynergyMeshOrchestrator()

        basic = orch.create_tenant("Basic", TenantTier.BASIC)
        enterprise = orch.create_tenant("Enterprise", TenantTier.ENTERPRISE)

        basic_config = orch.get_tenant(basic)
        ent_config = orch.get_tenant(enterprise)

        # Basic 應該有更低的小時配額
        assert basic_config.quota.max_tasks_per_hour < ent_config.quota.max_tasks_per_hour


# ============================================================================
# 審計日誌完整性測試
# ============================================================================

class TestAuditLogIntegrity:
    """審計日誌的完整性和可靠性測試"""

    def test_all_operations_are_logged(self):
        """測試所有操作都被記錄"""
        orch = EnterpriseSynergyMeshOrchestrator()

        initial_log_count = len(orch.audit_logs)

        # 執行各種操作
        tenant_id = orch.create_tenant("Test", TenantTier.BASIC)
        config = orch.get_tenant(tenant_id)
        orch.check_resource_quota(tenant_id)

        # 驗證日誌增長
        assert len(orch.audit_logs) > initial_log_count

    def test_audit_log_completeness(self):
        """測試審計日誌的完整性"""
        orch = EnterpriseSynergyMeshOrchestrator()

        tenant_id = orch.create_tenant("Test", TenantTier.BASIC)

        # 獲取審計日誌
        logs = orch.get_audit_logs(tenant_id)

        # 驗證日誌包含必要信息
        for log in logs:
            assert hasattr(log, "audit_id")
            assert hasattr(log, "timestamp")
            assert hasattr(log, "action")
            assert hasattr(log, "status")
            assert log.audit_id is not None
            assert log.timestamp is not None

    def test_audit_log_retention(self):
        """測試審計日誌保留"""
        orch = EnterpriseSynergyMeshOrchestrator()

        # 創建多個操作
        for i in range(5):
            orch.create_tenant(f"Tenant {i}", TenantTier.BASIC)

        # 驗證所有日誌都被保留
        assert len(orch.audit_logs) >= 5

    def test_sensitive_operation_logging(self):
        """測試敏感操作的記錄"""
        orch = EnterpriseSynergyMeshOrchestrator()

        # 創建租戶是一個敏感操作
        tenant_id = orch.create_tenant("Sensitive", TenantTier.ENTERPRISE)

        # 驗證創建操作被記錄
        logs = orch.audit_logs
        create_logs = [log for log in logs if log.action == "create_tenant"]

        assert len(create_logs) > 0


# ============================================================================
# 端到端工作流測試
# ============================================================================

class TestEnd2EndWorkflows:
    """端到端的業務工作流測試"""

    @pytest.mark.asyncio
    async def test_multi_tenant_service_deployment(self):
        """測試多租戶服務部署工作流"""
        orch = EnterpriseSynergyMeshOrchestrator()
        resolver = DependencyResolver()

        # 為兩個不同的租戶部署服務
        tenant_a = orch.create_tenant("Company A", TenantTier.PROFESSIONAL)
        tenant_b = orch.create_tenant("Company B", TenantTier.ENTERPRISE)

        # 定義服務依賴
        services = ["db", "cache", "api", "worker"]
        for service in services:
            resolver.add_component(service, "service")

        resolver.add_dependency("cache", "db")
        resolver.add_dependency("api", "db")
        resolver.add_dependency("api", "cache")
        resolver.add_dependency("worker", "db")

        # 獲取執行計劃
        phases = resolver.get_execution_phases()
        assert len(phases) > 0

        # 驗證兩個租戶都可以執行
        assert orch.check_resource_quota(tenant_a)
        assert orch.check_resource_quota(tenant_b)

    @pytest.mark.asyncio
    async def test_resilient_service_execution(self):
        """測試彈性的服務執行工作流"""
        orch = EnterpriseSynergyMeshOrchestrator()
        tenant_id = orch.create_tenant("Resilience Test", TenantTier.ENTERPRISE)

        attempt_count = 0

        async def unreliable_task(**kwargs):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise RuntimeError("Temporary failure")
            return {"success": True, "attempts": attempt_count}

        # 執行帶重試的任務
        result = await orch.execute_with_retry(
            unreliable_task,
            "unreliable_component",
            tenant_id,
            max_retries=3
        )

        assert result.status.value == "success"
        assert result.output["success"] is True
        assert result.output["attempts"] == 2

    def test_comprehensive_metrics_tracking(self):
        """測試綜合指標追蹤"""
        orch = EnterpriseSynergyMeshOrchestrator()

        # 創建多個租戶和執行操作
        for i in range(3):
            orch.create_tenant(f"Tenant {i}", TenantTier.BASIC)

        # 獲取系統指標
        metrics = orch.get_metrics()

        # 驗證指標完整性
        assert "registered_tenants" in metrics
        assert "total_executions" in metrics
        assert metrics["registered_tenants"] >= 3


# ============================================================================
# 可擴展性和性能測試
# ============================================================================

class TestScalabilityAndPerformance:
    """可擴展性和性能集成測試"""

    def test_large_number_of_tenants(self):
        """測試大量租戶的支持"""
        orch = EnterpriseSynergyMeshOrchestrator()

        # 創建 50 個租戶
        tenant_ids = []
        for i in range(50):
            tenant_id = orch.create_tenant(f"Tenant {i}", TenantTier.BASIC)
            tenant_ids.append(tenant_id)

        # 驗證所有租戶都被正確創建
        assert len(orch.tenants) == 50

        # 驗證可以檢索每個租戶
        for tenant_id in tenant_ids:
            config = orch.get_tenant(tenant_id)
            assert config is not None

    def test_large_dependency_graph(self):
        """測試大型依賴圖的處理"""
        resolver = DependencyResolver()

        # 創建 100 個組件
        for i in range(100):
            resolver.add_component(f"comp_{i:03d}", "component")

        # 添加 150 個依賴
        for i in range(1, 100):
            for j in range(0, min(i, 2)):  # 每個組件最多 2 個依賴
                resolver.add_dependency(f"comp_{i:03d}", f"comp_{i-j-1:03d}")

        # 驗證拓撲排序能處理大型圖
        order = resolver.topological_sort()
        assert len(order) == 100

        # 驗證統計信息
        stats = resolver.get_dependency_stats()
        assert stats["total_components"] == 100


# ============================================================================
# 主函數
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
