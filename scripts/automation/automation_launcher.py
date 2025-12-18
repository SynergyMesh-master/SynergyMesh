#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
                    SynergyMesh Automation Launcher
                         全自動化引擎啟動器
═══════════════════════════════════════════════════════════════════════════════

根目錄級別的自動化引擎啟動器。
100% 機器自主操作，零人類介入。

功能：
1. 啟動主控協調器 (Master Orchestrator)
2. 自動發現並註冊所有引擎
3. 自動啟動所有引擎
4. 管理引擎生命週期
5. 執行管道工作流
6. 監控系統健康

使用方式：
    # 啟動全部
    python automation_launcher.py start

    # 查看狀態
    python automation_launcher.py status

    # 啟動特定引擎
    python automation_launcher.py start-engine <engine_id>

    # 執行管道
    python automation_launcher.py execute <pipeline_id>

    # 停止全部
    python automation_launcher.py stop

Version: 1.0.0
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import argparse
import yaml
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# 設置路徑
BASE_PATH = Path(__file__).parent
sys.path.insert(0, str(BASE_PATH / "tools" / "automation"))

# ============================================================================
# ASCII 藝術字
# ============================================================================

BANNER = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ███████╗██╗   ██╗███╗   ██╗███████╗██████╗  ██████╗██╗   ██╗                ║
║   ██╔════╝╚██╗ ██╔╝████╗  ██║██╔════╝██╔══██╗██╔════╝╚██╗ ██╔╝                ║
║   ███████╗ ╚████╔╝ ██╔██╗ ██║█████╗  ██████╔╝██║  ███╗╚████╔╝                 ║
║   ╚════██║  ╚██╔╝  ██║╚██╗██║██╔══╝  ██╔══██╗██║   ██║ ╚██╔╝                  ║
║   ███████║   ██║   ██║ ╚████║███████╗██║  ██║╚██████╔╝  ██║                   ║
║   ╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝   ╚═╝                   ║
║                                                                               ║
║           ███╗   ███╗███████╗███████╗██╗  ██╗                                 ║
║           ████╗ ████║██╔════╝██╔════╝██║  ██║                                 ║
║           ██╔████╔██║█████╗  ███████╗███████║                                 ║
║           ██║╚██╔╝██║██╔══╝  ╚════██║██╔══██║                                 ║
║           ██║ ╚═╝ ██║███████╗███████║██║  ██║                                 ║
║           ╚═╝     ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝                                 ║
║                                                                               ║
║                    🤖 全自動化引擎啟動器 v1.0.0                               ║
║                    100% Machine Autonomous Operation                          ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

# ============================================================================
# 配置
# ============================================================================

DEFAULT_CONFIG = {
    "name": "SynergyMesh-Automation",
    "version": "1.0.0",
    "mode": "autonomous",  # autonomous | supervised | interactive

    # 引擎路徑
    "engine_paths": [
        "tools/automation/engines",
        "tools/refactor",
    ],

    # 自動化設定
    "auto_discover": True,
    "auto_start": True,
    "auto_recover": True,

    # 監控設定
    "health_check_interval": 30,
    "metrics_enabled": True,

    # 日誌設定
    "log_level": "INFO",
    "log_file": ".automation_logs/launcher.log",
}

# ============================================================================
# 啟動器
# ============================================================================

class AutomationLauncher:
    """
    全自動化引擎啟動器

    負責：
    1. 初始化系統
    2. 啟動主控協調器
    3. 管理所有引擎
    4. 提供 CLI 介面
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.orchestrator = None
        self._running = False
        self._start_time = None
        self._heartbeat_task = None
        self._heartbeat_file = BASE_PATH / ".launcher_heartbeat.json"

    async def start(self, show_banner: bool = True) -> bool:
        """啟動全部"""
        if show_banner:
            print(BANNER)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 啟動 SynergyMesh 自動化系統...")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📋 模式: {self.config['mode']}")
        print()

        try:
            # 導入主控協調器
            from master_orchestrator import MasterOrchestrator, OrchestratorConfig

            # 配置主控
            orch_config = OrchestratorConfig(
                name=self.config["name"],
                version=self.config["version"],
                auto_discover=self.config["auto_discover"],
                auto_start_engines=self.config["auto_start"],
                auto_recover=self.config["auto_recover"],
                engines_paths=self.config["engine_paths"],
                health_check_interval=self.config["health_check_interval"],
            )

            # 創建並啟動主控
            self.orchestrator = MasterOrchestrator(orch_config)
            success = await self.orchestrator.start()

            if success:
                self._running = True
                self._start_time = datetime.now()
                
                # Start heartbeat
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

                print()
                print("=" * 70)
                print(f"✅ SynergyMesh 自動化系統啟動成功")
                print(f"   運行模式: {self.config['mode']}")
                print(f"   引擎數量: {len(self.orchestrator.registry.get_all_engines())}")
                print(f"   💓 Heartbeat: Active (Phoenix-ready)")
                print("=" * 70)
                print()
                print("💡 提示: 按 Ctrl+C 停止系統")
                print()

                return True
            else:
                print("❌ 啟動失敗")
                return False

        except ImportError as e:
            print(f"❌ 導入錯誤: {e}")
            print("   請確保已安裝所有依賴")
            return False

        except Exception as e:
            print(f"❌ 啟動錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def stop(self):
        """停止全部"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🛑 停止自動化系統...")
        
        # Stop heartbeat
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        if self.orchestrator:
            await self.orchestrator.stop()

        self._running = False
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 系統已停止")

    async def _heartbeat_loop(self):
        """Send heartbeat to watchdog"""
        while self._running:
            try:
                heartbeat = {
                    "timestamp": datetime.now().isoformat(),
                    "status": "running",
                    "uptime": str(datetime.now() - self._start_time) if self._start_time else "0",
                    "pid": os.getpid()
                }
                
                # Write heartbeat file
                with open(self._heartbeat_file, 'w') as f:
                    json.dump(heartbeat, f, indent=2)
                
                # Wait 20 seconds before next heartbeat
                await asyncio.sleep(20)
                
            except Exception as e:
                # Don't let heartbeat errors crash the system
                print(f"⚠️  Heartbeat error: {e}")
                await asyncio.sleep(20)
    
    async def run_forever(self):
        """持續運行"""
        try:
            while self._running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await self.stop()

    def get_status(self) -> Dict[str, Any]:
        """獲取狀態"""
        if not self.orchestrator:
            return {"running": False, "message": "系統未啟動"}

        status = self.orchestrator.get_status()
        status["launcher"] = {
            "mode": self.config["mode"],
            "uptime": str(datetime.now() - self._start_time) if self._start_time else "N/A",
        }
        return status

    async def start_engine(self, engine_id: str) -> bool:
        """啟動特定引擎"""
        if not self.orchestrator:
            print("❌ 系統未啟動")
            return False
        return await self.orchestrator.start_engine(engine_id)

    async def stop_engine(self, engine_id: str) -> bool:
        """停止特定引擎"""
        if not self.orchestrator:
            print("❌ 系統未啟動")
            return False
        return await self.orchestrator.stop_engine(engine_id)

    async def execute_pipeline(self, pipeline_id: str, input_data: Dict = None) -> Dict:
        """執行管道"""
        if not self.orchestrator:
            return {"success": False, "error": "系統未啟動"}
        return await self.orchestrator.execute_pipeline(pipeline_id, input_data)

    async def execute_task(self, engine_id: str, task: Dict) -> Dict:
        """執行任務"""
        if not self.orchestrator:
            return {"success": False, "error": "系統未啟動"}
        result = await self.orchestrator.execute_task(engine_id, task)
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
        }

    def list_engines(self) -> List[Dict]:
        """列出所有引擎"""
        if not self.orchestrator:
            return []
        return [
            {
                "id": e.engine_id,
                "name": e.engine_name,
                "type": e.engine_type.value,
                "healthy": e.healthy,
            }
            for e in self.orchestrator.registry.get_all_engines()
        ]

    def list_pipelines(self) -> List[str]:
        """列出所有管道"""
        if not self.orchestrator:
            return []
        return list(self.orchestrator.pipeline_executor._pipelines.keys())

# ============================================================================
# CLI
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(
        description="SynergyMesh 全自動化引擎啟動器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  啟動系統:
    python automation_launcher.py start

  查看狀態:
    python automation_launcher.py status

  列出引擎:
    python automation_launcher.py list-engines

  執行任務:
    python automation_launcher.py task <engine_id> --operation scan

  執行管道:
    python automation_launcher.py pipeline <pipeline_id>
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # start 命令
    start_parser = subparsers.add_parser("start", help="啟動系統")
    start_parser.add_argument("--config", "-c", help="配置檔案")
    start_parser.add_argument("--mode", "-m", choices=["autonomous", "supervised", "interactive"],
                              default="autonomous", help="運行模式")
    start_parser.add_argument("--no-banner", action="store_true", help="不顯示橫幅")

    # stop 命令
    subparsers.add_parser("stop", help="停止系統")

    # status 命令
    subparsers.add_parser("status", help="查看狀態")

    # list-engines 命令
    subparsers.add_parser("list-engines", help="列出引擎")

    # list-pipelines 命令
    subparsers.add_parser("list-pipelines", help="列出管道")

    # start-engine 命令
    start_engine_parser = subparsers.add_parser("start-engine", help="啟動引擎")
    start_engine_parser.add_argument("engine_id", help="引擎 ID")

    # stop-engine 命令
    stop_engine_parser = subparsers.add_parser("stop-engine", help="停止引擎")
    stop_engine_parser.add_argument("engine_id", help="引擎 ID")

    # task 命令
    task_parser = subparsers.add_parser("task", help="執行任務")
    task_parser.add_argument("engine_id", help="引擎 ID")
    task_parser.add_argument("--operation", "-o", required=True, help="操作")
    task_parser.add_argument("--params", "-p", help="參數 (JSON)")

    # pipeline 命令
    pipeline_parser = subparsers.add_parser("pipeline", help="執行管道")
    pipeline_parser.add_argument("pipeline_id", help="管道 ID")
    pipeline_parser.add_argument("--input", "-i", help="輸入數據 (JSON)")

    args = parser.parse_args()

    if not args.command:
        print(BANNER)
        parser.print_help()
        return

    # 創建啟動器
    config = DEFAULT_CONFIG.copy()
    if hasattr(args, 'mode') and args.mode:
        config['mode'] = args.mode

    launcher = AutomationLauncher(config)

    # 執行命令
    if args.command == "start":
        success = await launcher.start(show_banner=not args.no_banner)
        if success:
            await launcher.run_forever()

    elif args.command == "stop":
        await launcher.stop()

    elif args.command == "status":
        await launcher.start(show_banner=False)
        status = launcher.get_status()
        print(yaml.dump(status, allow_unicode=True, default_flow_style=False))
        await launcher.stop()

    elif args.command == "list-engines":
        await launcher.start(show_banner=False)
        engines = launcher.list_engines()
        print("\n引擎列表:")
        print("-" * 60)
        for e in engines:
            status = "✅" if e["healthy"] else "❌"
            print(f"  {status} {e['name']} ({e['id']}) - {e['type']}")
        print()
        await launcher.stop()

    elif args.command == "list-pipelines":
        await launcher.start(show_banner=False)
        pipelines = launcher.list_pipelines()
        print("\n管道列表:")
        print("-" * 60)
        for p in pipelines:
            print(f"  - {p}")
        print()
        await launcher.stop()

    elif args.command == "start-engine":
        await launcher.start(show_banner=False)
        success = await launcher.start_engine(args.engine_id)
        print(f"{'✅ 成功' if success else '❌ 失敗'}")
        await launcher.stop()

    elif args.command == "stop-engine":
        await launcher.start(show_banner=False)
        success = await launcher.stop_engine(args.engine_id)
        print(f"{'✅ 成功' if success else '❌ 失敗'}")
        await launcher.stop()

    elif args.command == "task":
        await launcher.start(show_banner=False)
        task = {"operation": args.operation}
        if args.params:
            task["params"] = json.loads(args.params)
        result = await launcher.execute_task(args.engine_id, task)
        print(yaml.dump(result, allow_unicode=True, default_flow_style=False))
        await launcher.stop()

    elif args.command == "pipeline":
        await launcher.start(show_banner=False)
        input_data = json.loads(args.input) if args.input else {}
        result = await launcher.execute_pipeline(args.pipeline_id, input_data)
        print(yaml.dump(result, allow_unicode=True, default_flow_style=False))
        await launcher.stop()

if __name__ == "__main__":
    asyncio.run(main())
