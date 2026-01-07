#!/usr/bin/env python3
"""
協調器代理 (Coordinator Agent)

負責協調整個代理編隊的運作，包括任務調度、資源管理和健康監控。
對應 config/dev/automation/drone-coordinator.py
"""

import importlib.util
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Import from kebab-case filename base-agent.py
_base_agent_path = Path(__file__).parent / 'base-agent.py'
_spec = importlib.util.spec_from_file_location('base_agent', _base_agent_path)
if _spec and _spec.loader:
    _base_agent_module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_base_agent_module)
    BaseAgent = _base_agent_module.BaseAgent
    AgentStatus = _base_agent_module.AgentStatus
else:
    raise ImportError("Failed to import BaseAgent from base-agent.py")


class CoordinatorAgent(BaseAgent):
    """
    協調器代理

    作為代理編隊的主控制器，負責：
    - 環境分析
    - 任務調度
    - 資源管理
    - 健康監控
    """

    def __init__(self) -> None:
        super().__init__(name="協調器代理", agent_id="coordinator")
        self.fleet: dict[str, Any] = {}
        self.analysis_result: dict[str, Any] | None = None

    def start(self) -> bool:
        """啟動協調器"""
        self.log_info("🤖 啟動協調器代理...")

        if not self.load_config():
            self.log_warn("使用預設配置")

        self.status = AgentStatus.RUNNING
        self.start_time = datetime.now()

        self.log_success("協調器已啟動")
        return True

    def stop(self) -> bool:
        """停止協調器"""
        self.log_info("停止協調器代理...")
        self.status = AgentStatus.STOPPED
        self.log_success("協調器已停止")
        return True

    def execute(self) -> dict[str, Any]:
        """執行協調任務"""
        self.log_info("🔍 執行環境分析...")

        # 分析環境
        analysis = self.analyze_environment()
        self.analysis_result = analysis

        # 顯示分析結果
        self._display_analysis(analysis)

        return analysis

    def analyze_environment(self) -> dict[str, Any]:
        """
        分析當前開發環境

        Returns:
            環境分析結果
        """
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'tools': {},
            'structure': {},
            'recommendations': []
        }

        # 檢查工具
        tools = ['node', 'npm', 'python3', 'docker', 'git']
        for tool in tools:
            try:
                result = subprocess.run(
                    [tool, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                analysis['tools'][tool] = {
                    'installed': result.returncode == 0,
                    'version': result.stdout.strip().split('\n')[0] if result.returncode == 0 else None
                }
            except (FileNotFoundError, subprocess.TimeoutExpired):
                analysis['tools'][tool] = {'installed': False, 'version': None}

        # 檢查專案結構
        required_dirs = ['config/dev', '.vscode', 'v1-python-drones', 'shared', 'migration']
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            analysis['structure'][dir_name] = dir_path.exists()

        # 檢查配置檔案
        config_files = ['drone-config.yml', 'auto-scaffold.json', 'automation-entry.sh']
        for config_file in config_files:
            file_path = self.project_root / config_file
            analysis['structure'][config_file] = file_path.exists()

        # 生成建議
        if not analysis['tools'].get('docker', {}).get('installed'):
            analysis['recommendations'].append("建議安裝 Docker 以支援容器化開發")

        if not analysis['structure'].get('config/dev'):
            analysis['recommendations'].append("缺少 config/dev 目錄")

        return analysis

    def _display_analysis(self, analysis: dict[str, Any]) -> None:
        """顯示分析結果"""
        self.log_info("📊 環境分析報告:")

        print("\n  🔧 工具檢查:")
        for tool, info in analysis['tools'].items():
            status = '✅' if info.get('installed') else '❌'
            version = info.get('version', '未安裝')
            print(f"    {status} {tool}: {version}")

        print("\n  📁 結構檢查:")
        for item, exists in analysis['structure'].items():
            status = '✅' if exists else '❌'
            print(f"    {status} {item}")

        if analysis['recommendations']:
            print("\n  💡 建議:")
            for rec in analysis['recommendations']:
                print(f"    • {rec}")

        print()

    def initialize_fleet(self) -> None:
        """初始化代理編隊"""
        self.log_info("🚁 初始化代理編隊...")

        # 嘗試相對導入
        try:
            from .config import AgentConfig
        except (ImportError, ValueError):
            import sys
            sys.path.insert(0, str(self.project_root / 'src/autonomous/agents'))
            from config import AgentConfig

        config = AgentConfig.load()

        for agent_id, agent_config in config.agent_fleet.items():
            self.fleet[agent_id] = {
                'name': agent_config.get('name', agent_id),
                'script': agent_config.get('script'),
                'priority': agent_config.get('priority', 99),
                'auto_start': agent_config.get('auto_start', False),
                'status': 'initialized'
            }
            self.log_info(f"  ✓ {agent_config.get('name', agent_id)}")

        self.log_success(f"已初始化 {len(self.fleet)} 個代理")

    def dispatch_task(self, agent_id: str, task: str) -> bool:
        """
        調度任務給指定代理

        Args:
            agent_id: 目標代理 ID
            task: 任務名稱

        Returns:
            是否調度成功
        """
        if agent_id not in self.fleet:
            self.log_error(f"代理 {agent_id} 不存在")
            return False

        self.log_info(f"調度任務 '{task}' 給 {self.fleet[agent_id]['name']}")
        # 實際任務調度邏輯
        return True

    def run_core_coordinator(self) -> int:
        """
        執行核心協調器 (config/dev/automation/drone-coordinator.py)

        Returns:
            執行結果代碼
        """
        core_script = self.project_root / 'config/dev' / 'automation' / 'drone-coordinator.py'

        if not core_script.exists():
            self.log_error(f"核心協調器腳本不存在: {core_script}")
            return 1

        self.log_info(f"執行核心協調器: {core_script}")

        try:
            result = subprocess.run(
                ['python3', str(core_script), '--mode=auto'],
                cwd=self.project_root
            )
            return result.returncode
        except Exception as e:
            self.log_error(f"執行失敗: {e}")
            return 1
