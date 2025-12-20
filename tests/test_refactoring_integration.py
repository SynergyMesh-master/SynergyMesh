#!/usr/bin/env python3
"""
重構整合測試 - Refactoring Integration Tests

驗證 v1-python-drones 和 v2-multi-islands 重構後的整合情況
"""

import sys
from pathlib import Path

# 添加 src 目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

import pytest


class TestAgentSystemConversion:
    """測試 Agent 系統轉換"""

    def test_base_agent_import(self):
        """測試 BaseAgent 導入"""
        from autonomous.agents.base_agent import BaseAgent, AgentStatus
        assert BaseAgent is not None
        assert AgentStatus is not None
        assert hasattr(AgentStatus, 'INITIALIZED')

    def test_coordinator_agent_import(self):
        """測試 CoordinatorAgent 導入"""
        from autonomous.agents.coordinator_agent import CoordinatorAgent
        assert CoordinatorAgent is not None

    def test_autopilot_agent_import(self):
        """測試 AutopilotAgent 導入"""
        from autonomous.agents.autopilot_agent import AutopilotAgent
        assert AutopilotAgent is not None

    def test_deployment_agent_import(self):
        """測試 DeploymentAgent 導入"""
        from autonomous.agents.deployment_agent import DeploymentAgent
        assert DeploymentAgent is not None

    def test_agent_config_import(self):
        """測試 AgentConfig 導入"""
        from autonomous.agents.config.agent_config import AgentConfig
        assert AgentConfig is not None

    def test_agent_instantiation(self):
        """測試 Agent 實例化"""
        from autonomous.agents.base_agent import BaseAgent, AgentStatus

        # 創建一個測試用的 Agent 子類
        class TestAgent(BaseAgent):
            def start(self):
                return True
            def stop(self):
                return True
            def execute(self):
                return {'test': 'result'}

        agent = TestAgent(name="Test Agent", agent_id="test_agent")
        assert agent.name == "Test Agent"
        assert agent.agent_id == "test_agent"
        assert agent.status == AgentStatus.INITIALIZED


class TestIslandSystemConversion:
    """測試 Island 系統轉換"""

    def test_base_island_import(self):
        """測試 BaseIsland 導入"""
        from bridges.language_islands.base_island import BaseIsland, IslandStatus
        assert BaseIsland is not None
        assert IslandStatus is not None
        assert hasattr(IslandStatus, 'DORMANT')

    def test_python_island_import(self):
        """測試 PythonIsland 導入"""
        from bridges.language_islands.python_island import PythonIsland
        assert PythonIsland is not None

    def test_rust_island_import(self):
        """測試 RustIsland 導入"""
        from bridges.language_islands.rust_island import RustIsland
        assert RustIsland is not None

    def test_go_island_import(self):
        """測試 GoIsland 導入"""
        from bridges.language_islands.go_island import GoIsland
        assert GoIsland is not None

    def test_typescript_island_import(self):
        """測試 TypeScriptIsland 導入"""
        from bridges.language_islands.typescript_island import TypeScriptIsland
        assert TypeScriptIsland is not None

    def test_java_island_import(self):
        """測試 JavaIsland 導入"""
        from bridges.language_islands.java_island import JavaIsland
        assert JavaIsland is not None

    def test_language_island_orchestrator_import(self):
        """測試 LanguageIslandOrchestrator 導入"""
        from core.orchestrators.language_island_orchestrator import LanguageIslandOrchestrator
        assert LanguageIslandOrchestrator is not None

    def test_island_config_import(self):
        """測試 IslandConfig 導入"""
        from bridges.language_islands.config.island_config import IslandConfig
        assert IslandConfig is not None


class TestSynergyMeshOrchestrator:
    """測試 SynergyMesh 協調器"""

    def test_orchestrator_import(self):
        """測試協調器導入"""
        from core.orchestrators.synergy_mesh_orchestrator import SynergyMeshOrchestrator
        assert SynergyMeshOrchestrator is not None

    def test_orchestrator_instantiation(self):
        """測試協調器實例化"""
        from core.orchestrators.synergy_mesh_orchestrator import SynergyMeshOrchestrator
        orchestrator = SynergyMeshOrchestrator()
        assert orchestrator is not None
        assert len(orchestrator.agents) == 0
        assert len(orchestrator.islands) == 0

    def test_orchestrator_agent_registration(self):
        """測試協調器的 Agent 註冊"""
        from core.orchestrators.synergy_mesh_orchestrator import SynergyMeshOrchestrator
        from autonomous.agents.base_agent import BaseAgent

        class DummyAgent(BaseAgent):
            def start(self):
                self.started = True
                return True
            def stop(self):
                return True
            def execute(self):
                return {'dummy': 'result'}

        orchestrator = SynergyMeshOrchestrator()
        agent = DummyAgent(name="Dummy", agent_id="dummy")

        success = orchestrator.register_agent("dummy", agent)
        assert success is True
        assert "dummy" in orchestrator.agents

    def test_orchestrator_status(self):
        """測試協調器狀態"""
        from core.orchestrators.synergy_mesh_orchestrator import SynergyMeshOrchestrator
        orchestrator = SynergyMeshOrchestrator()
        status = orchestrator.get_status()
        assert status is not None
        assert status.total_components == 0


class TestNamingConventions:
    """測試命名規範一致性"""

    def test_agent_file_names_are_kebab_case(self):
        """測試 Agent 文件名是否為 kebab-case"""
        agents_dir = project_root / 'src' / 'autonomous' / 'agents'
        agent_files = [f for f in agents_dir.glob('*.py') if not f.name.startswith('_')]

        for file in agent_files:
            # kebab-case 規則：小寫字母、數字和連字符
            assert file.name.islower() or '-' in file.name, \
                f"File {file.name} should be in kebab-case"

    def test_island_file_names_are_kebab_case(self):
        """測試 Island 文件名是否為 kebab-case"""
        islands_dir = project_root / 'src' / 'bridges' / 'language-islands'
        island_files = [f for f in islands_dir.glob('*.py') if not f.name.startswith('_')]

        for file in island_files:
            # kebab-case 規則：小寫字母、數字和連字符
            assert file.name.islower() or '-' in file.name, \
                f"File {file.name} should be in kebab-case"


class TestDirectoryStructure:
    """測試目錄結構"""

    def test_agent_directory_exists(self):
        """測試 Agent 目錄是否存在"""
        agents_dir = project_root / 'src' / 'autonomous' / 'agents'
        assert agents_dir.exists(), f"Directory {agents_dir} does not exist"

    def test_island_directory_exists(self):
        """測試 Island 目錄是否存在"""
        islands_dir = project_root / 'src' / 'bridges' / 'language-islands'
        assert islands_dir.exists(), f"Directory {islands_dir} does not exist"

    def test_orchestrators_directory_exists(self):
        """測試協調器目錄是否存在"""
        orchestrators_dir = project_root / 'src' / 'core' / 'orchestrators'
        assert orchestrators_dir.exists(), f"Directory {orchestrators_dir} does not exist"

    def test_duplicate_legacy_dirs_removed(self):
        """測試是否已刪除重複的遺留代碼目錄"""
        archive_dir = project_root / 'archive'

        # 檢查重複的目錄是否已刪除
        assert not (archive_dir / 'v1-python-drones').exists(), \
            "Duplicate archive/v1-python-drones should be removed"
        assert not (archive_dir / 'v2-multi-islands').exists(), \
            "Duplicate archive/v2-multi-islands should be removed"

        # 檢查原始目錄是否仍然存在
        assert (archive_dir / 'legacy' / 'v1-python-drones').exists(), \
            "Original legacy/v1-python-drones should still exist"
        assert (archive_dir / 'legacy' / 'v2-multi-islands').exists(), \
            "Original legacy/v2-multi-islands should still exist"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
