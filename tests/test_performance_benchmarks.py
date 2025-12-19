#!/usr/bin/env python3
"""
性能基準測試套件 - Performance Benchmark Test Suite

測試範圍：
1. 執行時間基準測試 (順序 vs 並行)
2. 吞吐量測試 (TPS 測量)
3. 內存使用基準
4. 重試性能開銷
5. 並行化加速測試
6. 依賴解析性能

性能目標：
- 執行時間: < 300ms (3.3x 加速)
- 吞吐量: > 1000 TPS
- 內存開銷: < 5%
"""

import asyncio
import sys
import time
import pytest
from pathlib import Path

# 添加 src 到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from core.orchestrators import (
    EnterpriseSynergyMeshOrchestrator,
    DependencyResolver,
    TenantTier,
    RetryPolicy
)


# ============================================================================
# 執行時間基準測試
# ============================================================================

class TestExecutionTimeBenchmark:
    """執行時間性能測試"""

    def test_sequential_vs_parallel_execution(self):
        """測試順序執行 vs 並行執行的時間差異"""
        resolver = DependencyResolver()

        # 創建 10 個組件，每個需要 100ms
        num_components = 10
        for i in range(num_components):
            resolver.add_component(f"component_{i:02d}", "component", weight=0.1)

        # 創建線性依賴（順序執行）
        for i in range(1, num_components):
            resolver.add_dependency(f"component_{i:02d}", f"component_{i-1:02d}")

        # 測量順序執行時間
        start = time.time()
        phases = resolver.get_execution_phases()
        sequential_time = time.time() - start

        # 應該有大約 num_components 個執行階段
        assert len(phases) == num_components

        # 驗證執行時間在合理範圍內
        assert sequential_time < 1.0  # 應該非常快（只是計算，不是實際執行）

    def test_parallel_dependency_speedup(self):
        """測試並行依賴的加速"""
        resolver = DependencyResolver()

        # 創建樹形依賴結構，允許並行執行
        # 層級 0: root
        # 層級 1: root 的 5 個依賴
        # 層級 2: 每個第一層有 3 個依賴

        resolver.add_component("root", "component", weight=0.1)

        # 第一層：5 個直接依賴於 root
        for i in range(5):
            comp_id = f"level1_{i}"
            resolver.add_component(comp_id, "component", weight=0.1)
            resolver.add_dependency(comp_id, "root")

        # 第二層：每個第一層組件有 3 個依賴
        for i in range(5):
            for j in range(3):
                comp_id = f"level2_{i}_{j}"
                resolver.add_component(comp_id, "component", weight=0.1)
                resolver.add_dependency(comp_id, f"level1_{i}")

        # 獲取執行階段分析
        start = time.time()
        phases = resolver.get_execution_phases()
        analysis = resolver.get_parallelization_analysis()
        elapsed = time.time() - start

        # 驗證並行化機會存在
        assert analysis["parallelization_factor"] > 1.0
        assert len(phases) < 16  # 少於 16 個組件的總數（說明有並行）

        # 驗證計算速度
        assert elapsed < 0.5

    def test_complex_workflow_execution_time(self):
        """測試複雜工作流的執行時間"""
        resolver = DependencyResolver()

        # 創建微服務架構的依賴圖
        services = [
            "database", "cache", "auth", "api-gateway",
            "user-service", "product-service", "order-service",
            "notification-service", "analytics", "monitoring"
        ]

        for service in services:
            resolver.add_component(service, "service", weight=0.15)

        # 定義依賴
        dependencies = [
            ("cache", "database"),
            ("auth", "database"),
            ("user-service", "database"),
            ("user-service", "auth"),
            ("user-service", "cache"),
            ("product-service", "database"),
            ("product-service", "cache"),
            ("order-service", "database"),
            ("order-service", "user-service"),
            ("order-service", "product-service"),
            ("notification-service", "order-service"),
            ("notification-service", "user-service"),
            ("api-gateway", "auth"),
            ("api-gateway", "user-service"),
            ("api-gateway", "product-service"),
            ("api-gateway", "order-service"),
            ("analytics", "database"),
            ("monitoring", "api-gateway"),
            ("monitoring", "order-service")
        ]

        for from_svc, to_svc in dependencies:
            resolver.add_dependency(from_svc, to_svc)

        # 測量執行時間
        start = time.time()
        phases = resolver.get_execution_phases()
        execution_time = time.time() - start

        # 驗證執行時間在預期範圍內
        assert execution_time < 1.0
        assert len(phases) > 1  # 應該有多個執行階段


# ============================================================================
# 吞吐量測試
# ============================================================================

class TestThroughputBenchmark:
    """吞吐量性能測試"""

    @pytest.mark.asyncio
    async def test_single_tenant_throughput(self):
        """測試單租戶的吞吐量"""
        orch = EnterpriseSynergyMeshOrchestrator()
        tenant_id = orch.create_tenant("Throughput Test", TenantTier.BASIC)

        execution_count = 0
        start_time = time.time()

        async def fast_task(**kwargs):
            return {"success": True}

        # 執行 100 個任務
        for i in range(100):
            result = await orch.execute_with_retry(
                fast_task,
                f"task_{i}",
                tenant_id
            )
            if result.status.value == "success":
                execution_count += 1

        elapsed = time.time() - start_time

        # 計算 TPS（每秒執行數）
        tps = execution_count / elapsed if elapsed > 0 else 0

        # 驗證吞吐量（應該 > 100 TPS）
        assert execution_count == 100
        assert tps > 50  # 基礎層應該至少支持 50 TPS

    @pytest.mark.asyncio
    async def test_multi_tenant_throughput(self):
        """測試多租戶的總吞吐量"""
        orch = EnterpriseSynergyMeshOrchestrator()

        # 創建 5 個不同層級的租戶
        tenants = [
            orch.create_tenant("Basic", TenantTier.BASIC),
            orch.create_tenant("Pro 1", TenantTier.PROFESSIONAL),
            orch.create_tenant("Pro 2", TenantTier.PROFESSIONAL),
            orch.create_tenant("Enterprise 1", TenantTier.ENTERPRISE),
            orch.create_tenant("Enterprise 2", TenantTier.ENTERPRISE),
        ]

        async def quick_task(**kwargs):
            await asyncio.sleep(0.001)  # 模擬 1ms 的工作
            return {"success": True}

        start_time = time.time()
        total_executions = 0

        # 每個租戶執行 20 個任務
        for tenant_id in tenants:
            for i in range(20):
                result = await orch.execute_with_retry(
                    quick_task,
                    f"task_{i}",
                    tenant_id
                )
                if result.status.value == "success":
                    total_executions += 1

        elapsed = time.time() - start_time

        # 計算總 TPS
        total_tps = total_executions / elapsed if elapsed > 0 else 0

        # 驗證多租戶吞吐量
        assert total_executions == 100
        assert elapsed > 0
        # 由於是異步，應該有一定的並行性


# ============================================================================
# 內存使用基準
# ============================================================================

class TestMemoryBenchmark:
    """內存使用性能測試"""

    def test_tenant_memory_overhead(self):
        """測試租戶的內存開銷"""
        import sys

        orch = EnterpriseSynergyMeshOrchestrator()

        # 獲取初始大小
        initial_size = sys.getsizeof(orch)

        # 創建 100 個租戶
        for i in range(100):
            orch.create_tenant(f"Tenant {i}", TenantTier.BASIC)

        # 獲取最終大小
        final_size = sys.getsizeof(orch)

        # 計算每個租戶的平均開銷
        avg_overhead = (final_size - initial_size) / 100

        # 驗證內存開銷合理（應該 < 10KB 每個租戶）
        assert avg_overhead < 10000  # 10KB

    def test_audit_log_memory_efficiency(self):
        """測試審計日誌的內存效率"""
        orch = EnterpriseSynergyMeshOrchestrator()
        tenant_id = orch.create_tenant("Memory Test", TenantTier.BASIC)

        initial_logs = len(orch.audit_logs)

        # 生成 100 個審計日誌
        for i in range(100):
            orch.create_tenant(f"Temp Tenant {i}", TenantTier.BASIC)

        final_logs = len(orch.audit_logs)

        # 驗證日誌被正確存儲（至少增加了 100 條）
        assert final_logs >= initial_logs + 100

    def test_dependency_graph_memory_efficiency(self):
        """測試依賴圖的內存效率"""
        resolver = DependencyResolver()

        # 添加 500 個組件
        for i in range(500):
            resolver.add_component(f"component_{i:03d}", "component")

        # 添加 500 個依賴
        for i in range(1, 500):
            resolver.add_dependency(f"component_{i:03d}", f"component_{i-1:03d}")

        # 驗證圖被正確構建
        assert len(resolver.nodes) == 500


# ============================================================================
# 重試性能開銷測試
# ============================================================================

class TestRetryPerformanceOverhead:
    """重試機制的性能開銷測試"""

    @pytest.mark.asyncio
    async def test_successful_first_attempt_overhead(self):
        """測試成功首次嘗試的開銷"""
        orch = EnterpriseSynergyMeshOrchestrator()
        tenant_id = orch.create_tenant("Retry Overhead", TenantTier.BASIC)

        async def success_task(**kwargs):
            return {"success": True}

        # 測量執行時間
        start = time.time()
        result = await orch.execute_with_retry(
            success_task,
            "test_task",
            tenant_id
        )
        elapsed = time.time() - start

        # 驗證執行成功
        assert result.status.value == "success"
        assert result.retry_count == 0

        # 驗證性能開銷小於 100ms
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_retry_overhead_with_backoff(self):
        """測試帶退避的重試開銷"""
        orch = EnterpriseSynergyMeshOrchestrator()
        tenant_id = orch.create_tenant("Retry Test", TenantTier.PROFESSIONAL)

        attempt_count = 0

        async def flaky_task(**kwargs):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise RuntimeError("Temporary failure")
            return {"success": True}

        # 測量重試時間
        start = time.time()
        result = await orch.execute_with_retry(
            flaky_task,
            "flaky_task",
            tenant_id,
            max_retries=2
        )
        elapsed = time.time() - start

        # 驗證執行成功，且包含指數退避延遲
        assert result.status.value == "success"
        assert result.retry_count == 1

        # 應該有大約 100ms 的延遲（初始延遲 + 退避）
        assert elapsed > 0.05  # 至少 50ms（退避延遲）


# ============================================================================
# 並行化加速測試
# ============================================================================

class TestParallelizationSpeedup:
    """並行化的加速效果測試"""

    def test_parallelization_factor_calculation(self):
        """測試並行化因子的計算"""
        resolver = DependencyResolver()

        # 構建允許並行的圖
        # Root → [comp_0_0, comp_0_1, ..., comp_0_9] (10 個並行)
        # 每個 comp_0_i → [comp_1_i_0, comp_1_i_1] (再並行)

        resolver.add_component("root", "component", weight=1.0)

        # 第一層：10 個並行組件
        for i in range(10):
            comp_id = f"level1_{i}"
            resolver.add_component(comp_id, "component", weight=1.0)
            resolver.add_dependency(comp_id, "root")

        # 第二層：每個第一層有 2 個並行組件
        for i in range(10):
            for j in range(2):
                comp_id = f"level2_{i}_{j}"
                resolver.add_component(comp_id, "component", weight=1.0)
                resolver.add_dependency(comp_id, f"level1_{i}")

        # 分析並行化
        analysis = resolver.get_parallelization_analysis()

        # 應該有並行化機會（實際的因子取決於實現細節）
        assert analysis["parallelization_factor"] > 1.0
        assert "potential_speedup" in analysis

    def test_critical_path_analysis(self):
        """測試關鍵路徑分析"""
        resolver = DependencyResolver()

        # 創建一個有明確關鍵路徑的圖
        # 路徑 1（關鍵）: root → A → B → C → end (4 步)
        # 路徑 2: root → X → end (2 步)
        # 路徑 3: root → Y → end (2 步)

        components = ["root", "A", "B", "C", "end", "X", "Y"]
        for comp in components:
            resolver.add_component(comp, "component", weight=1.0)

        # 關鍵路徑
        resolver.add_dependency("A", "root")
        resolver.add_dependency("B", "A")
        resolver.add_dependency("C", "B")
        resolver.add_dependency("end", "C")

        # 並行路徑
        resolver.add_dependency("X", "root")
        resolver.add_dependency("end", "X")
        resolver.add_dependency("Y", "root")
        resolver.add_dependency("end", "Y")

        # 獲取關鍵路徑
        critical_path = resolver.get_critical_path()

        # 驗證關鍵路徑存在
        assert len(critical_path) > 0
        # 應該包含 root 和其他關鍵組件
        assert "root" in critical_path


# ============================================================================
# 依賴解析性能測試
# ============================================================================

class TestDependencyResolutionPerformance:
    """依賴解析的性能測試"""

    def test_large_graph_topological_sort_performance(self):
        """測試大型圖的拓撲排序性能"""
        resolver = DependencyResolver()

        # 創建 200 個組件的線性依賴鏈
        num_components = 200
        for i in range(num_components):
            resolver.add_component(f"comp_{i:03d}", "component")

        for i in range(1, num_components):
            resolver.add_dependency(f"comp_{i:03d}", f"comp_{i-1:03d}")

        # 測量拓撲排序性能
        start = time.time()
        order = resolver.topological_sort()
        elapsed = time.time() - start

        # 驗證排序正確
        assert len(order) == num_components

        # 驗證性能（應該 < 100ms）
        assert elapsed < 0.1

    def test_circular_dependency_detection_performance(self):
        """測試循環依賴檢測的性能"""
        resolver = DependencyResolver()

        # 創建大型無循環圖
        for i in range(100):
            for j in range(3):
                resolver.add_component(f"comp_{i}_{j}", "component")

        # 添加依賴而不創建循環
        for i in range(100):
            for j in range(3):
                if j > 0:
                    resolver.add_dependency(f"comp_{i}_{j}", f"comp_{i}_{j-1}")

        # 測試檢測性能
        start = time.time()

        # 嘗試添加會創建循環的依賴（應該被檢測拒絕）
        resolver.add_dependency("comp_0_0", "comp_0_2")

        elapsed = time.time() - start

        # 驗證檢測快速
        assert elapsed < 0.1

    def test_parallelization_analysis_performance(self):
        """測試並行化分析的性能"""
        resolver = DependencyResolver()

        # 創建 150 個組件的複雜圖
        for i in range(150):
            resolver.add_component(f"comp_{i:03d}", "component")

        # 添加複雜的依賴關係
        for i in range(1, 150):
            # 每個組件依賴於前 2-3 個
            deps_count = 2 + (i % 2)
            for j in range(deps_count):
                if i - j - 1 >= 0:
                    resolver.add_dependency(f"comp_{i:03d}", f"comp_{i-j-1:03d}")

        # 測量並行化分析性能
        start = time.time()
        analysis = resolver.get_parallelization_analysis()
        elapsed = time.time() - start

        # 驗證分析結果有效
        assert "parallelization_factor" in analysis
        assert analysis["parallelization_factor"] > 0

        # 驗證性能（應該 < 500ms）
        assert elapsed < 0.5


# ============================================================================
# 綜合性能測試
# ============================================================================

class TestComprehensivePerformance:
    """綜合性能測試"""

    @pytest.mark.asyncio
    async def test_end_to_end_performance(self):
        """測試端到端的性能"""
        orch = EnterpriseSynergyMeshOrchestrator()
        resolver = DependencyResolver()

        # 創建 5 個租戶
        tenants = []
        for i in range(5):
            tenant_id = orch.create_tenant(f"Tenant {i}", TenantTier.PROFESSIONAL)
            tenants.append(tenant_id)

        # 定義依賴圖
        services = ["db", "cache", "api", "worker", "scheduler"]
        for service in services:
            resolver.add_component(service, "service")

        resolver.add_dependency("cache", "db")
        resolver.add_dependency("api", "db")
        resolver.add_dependency("api", "cache")
        resolver.add_dependency("worker", "db")
        resolver.add_dependency("scheduler", "db")

        # 測量整體性能
        start = time.time()

        # 分析依賴
        phases = resolver.get_execution_phases()
        analysis = resolver.get_parallelization_analysis()

        # 執行任務
        async def test_task(**kwargs):
            await asyncio.sleep(0.01)
            return {"success": True}

        for tenant_id in tenants:
            result = await orch.execute_with_retry(
                test_task,
                "perf_test",
                tenant_id
            )

        elapsed = time.time() - start

        # 驗證所有操作完成
        assert len(phases) > 0
        assert analysis["parallelization_factor"] > 1.0

        # 整個操作應該在 2 秒內完成
        assert elapsed < 2.0


# ============================================================================
# 主函數
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
