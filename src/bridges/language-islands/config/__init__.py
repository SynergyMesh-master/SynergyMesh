"""
Language Islands Configuration

島嶼配置管理模組
"""

import importlib

island_config_module = importlib.import_module('bridges.language-islands.config.island-config')
IslandConfig = island_config_module.IslandConfig

__all__ = [
    "IslandConfig",
]
