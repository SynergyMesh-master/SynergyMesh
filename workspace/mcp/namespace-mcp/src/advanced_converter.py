#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MachineNativeOps 高級命名空間 MCP 轉換器
提供對現有 MachineNativeConverter 的薄封裝，作為 README 所列「高級轉換器」入口。
"""

import copy
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from converter import MachineNativeConverter

logger = logging.getLogger("MachineNativeOps.AdvancedConverter")


class AdvancedMachineNativeConverter(MachineNativeConverter):
    """高級轉換器占位實現，復用基礎轉換流程並保留擴展掛鉤。"""

    def __init__(self, config_path: Optional[str] = None, enable_semantic: bool = True):
        super().__init__(config_path=config_path)
        self.enable_semantic = enable_semantic
        self._semantic_rules_backup = copy.deepcopy(self.conversion_rules.get("semantic", []))
        logger.info("AdvancedMachineNativeConverter 初始化完成 (enable_semantic=%s)", enable_semantic)

    def convert_project(self, source_path: str, target_path: str) -> Dict[str, Any]:
        """
        目前直接調用基礎轉換器，預留高級語意/增強策略掛鉤。
        """
        semantic_backup = copy.deepcopy(self._semantic_rules_backup)

        if not self.enable_semantic:
            # 暫時允許禁用語意層，透過移除該層規則實現
            self.conversion_rules["semantic"] = []
            logger.info("已禁用語意層轉換 (semantic layer skipped)")

        try:
            return super().convert_project(source_path, target_path)
        finally:
            # 恢復原規則以避免重複實例或多次調用時的副作用
            self.conversion_rules["semantic"] = semantic_backup


def main():
    import argparse

    parser = argparse.ArgumentParser(description="MachineNativeOps 高級轉換器入口")
    parser.add_argument("source", help="源專案路徑")
    parser.add_argument("target", help="目標專案路徑")
    parser.add_argument("--config", "-c", help="配置文件路徑")
    parser.add_argument("--disable-semantic", action="store_true", help="禁用語意層轉換")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細輸出")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    converter = AdvancedMachineNativeConverter(
        config_path=args.config,
        enable_semantic=not args.disable_semantic,
    )

    converter.convert_project(args.source, args.target)


if __name__ == "__main__":
    main()
