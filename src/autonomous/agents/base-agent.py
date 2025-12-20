#!/usr/bin/env python3
"""
基礎代理類別

所有代理的抽象基礎類別，定義共通介面和功能。
"""

import sys
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

# 將專案根目錄加入路徑
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


class AgentStatus:
    """代理狀態"""
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class Colors:
    """終端機顏色輸出"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'


class BaseAgent(ABC):
    """
    基礎代理抽象類別

    所有具體代理都應繼承此類別並實作抽象方法。

    Attributes:
        name: 代理名稱
        agent_id: 代理識別碼
        status: 當前狀態
        config: 配置資訊
    """

    def __init__(self, name: str, agent_id: str) -> None:
        self.name = name
        self.agent_id = agent_id
        self.status = AgentStatus.INITIALIZED
        self.config: dict[str, Any] = {}
        self.start_time: datetime | None = None
        self._project_root = self._find_project_root()

    def _find_project_root(self) -> Path:
        """尋找專案根目錄"""
        current = Path(__file__).resolve().parent
        while current != current.parent:
            if (current / 'agent-config.yml').exists():
                return current
            if (current / 'package.json').exists():
                return current
            current = current.parent
        return Path.cwd()

    @property
    def project_root(self) -> Path:
        """取得專案根目錄"""
        return self._project_root

    # 日誌輸出方法
    def log_info(self, message: str) -> None:
        """輸出資訊訊息"""
        print(f"{Colors.BLUE}[{self.name}][INFO]{Colors.NC} {message}")

    def log_success(self, message: str) -> None:
        """輸出成功訊息"""
        print(f"{Colors.GREEN}[{self.name}][SUCCESS]{Colors.NC} {message}")

    def log_warn(self, message: str) -> None:
        """輸出警告訊息"""
        print(f"{Colors.YELLOW}[{self.name}][WARN]{Colors.NC} {message}")

    def log_error(self, message: str) -> None:
        """輸出錯誤訊息"""
        print(f"{Colors.RED}[{self.name}][ERROR]{Colors.NC} {message}")

    def load_config(self) -> bool:
        """
        載入代理配置

        Returns:
            是否載入成功
        """
        try:
            # 嘗試相對導入
            try:
                from .config import AgentConfig
            except (ImportError, ValueError):
                # 如果相對導入失敗，使用絕對路徑導入
                import sys
                sys.path.insert(0, str(self.project_root / 'src/autonomous/agents'))
                from config import AgentConfig

            agent_config = AgentConfig.load()
            self.config = agent_config.get_agent(self.agent_id) or {}
            self.log_success("配置已載入")
            return True
        except Exception as e:
            self.log_error(f"載入配置失敗: {e}")
            return False

    @abstractmethod
    def start(self) -> bool:
        """
        啟動代理

        Returns:
            是否啟動成功
        """
        pass

    @abstractmethod
    def stop(self) -> bool:
        """
        停止代理

        Returns:
            是否停止成功
        """
        pass

    @abstractmethod
    def execute(self) -> Any:
        """
        執行代理主要任務

        Returns:
            執行結果
        """
        pass

    def health_check(self) -> bool:
        """
        健康檢查

        Returns:
            是否健康
        """
        return self.status in [AgentStatus.INITIALIZED, AgentStatus.RUNNING]

    def get_status(self) -> dict[str, Any]:
        """
        取得代理狀態資訊

        Returns:
            狀態資訊字典
        """
        return {
            "name": self.name,
            "agent_id": self.agent_id,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "healthy": self.health_check(),
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', status='{self.status}')>"
