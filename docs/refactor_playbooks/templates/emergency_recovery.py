#!/usr/bin/env python3
"""
Emergency Recovery Script - 应急恢复脚本
当automation_launcher.py失效时的紧急启动方案
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import subprocess

# 直接导入核心组件（绕过launcher）
sys.path.insert(0, str(Path(__file__).parent / "tools" / "automation"))

class EmergencyRecovery:
    """
    应急恢复系统
    
    设计原则：
    1. 最小依赖 - 只依赖Python标准库和核心模块
    2. 直接启动 - 绕过launcher直接启动MasterOrchestrator
    3. 状态持久化 - 保存恢复状态便于追踪
    4. 健康检查 - 启动后立即验证系统健康
    """
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.recovery_log = self.base_path / "recovery_logs"
        self.recovery_log.mkdir(exist_ok=True)
        
        # 核心配置（硬编码以避免配置文件依赖）
        self.core_config = {
            "name": "SynergyMesh",
            "version": "1.0.0",
            "mode": "emergency",
            "auto_discover": True,
            "auto_start": True,
            "auto_recover": True,
            "engine_paths": [
                "./tools/automation/engines",
                "./engines"
            ],
            "health_check_interval": 30
        }
        
        self.log_file = self.recovery_log / f"recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    def log(self, message: str, level: str = "INFO"):
        """记录恢复日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    async def check_dependencies(self) -> bool:
        """检查核心依赖是否可用"""
        self.log("🔍 检查核心依赖...")
        
        required_modules = [
            "master_orchestrator",
            "asyncio",
            "pathlib",
            "datetime"
        ]
        
        missing = []
        for module in required_modules:
            try:
                __import__(module)
                self.log(f"  ✓ {module} 可用")
            except ImportError:
                missing.append(module)
                self.log(f"  ✗ {module} 缺失", "ERROR")
        
        if missing:
            self.log(f"❌ 缺少必要模块: {', '.join(missing)}", "ERROR")
            return False
        
        self.log("✅ 所有核心依赖检查通过")
        return True
    
    async def direct_orchestrator_start(self) -> bool:
        """直接启动MasterOrchestrator（绕过launcher）"""
        self.log("🚀 尝试直接启动 MasterOrchestrator...")
        
        try:
            # 动态导入（避免启动时失败）
            from master_orchestrator import MasterOrchestrator, OrchestratorConfig
            
            # 创建最小化配置
            config = OrchestratorConfig(
                name=self.core_config["name"],
                version=self.core_config["version"],
                auto_discover=self.core_config["auto_discover"],
                auto_start_engines=self.core_config["auto_start"],
                auto_recover=self.core_config["auto_recover"],
                engines_paths=self.core_config["engine_paths"],
                health_check_interval=self.core_config["health_check_interval"]
            )
            
            # 实例化orchestrator
            orchestrator = MasterOrchestrator(config)
            
            # 启动orchestrator
            success = await orchestrator.start()
            
            if success:
                self.log("✅ MasterOrchestrator 启动成功")
                
                # 获取引擎状态
                engines = orchestrator.registry.get_all_engines()
                self.log(f"📊 发现 {len(engines)} 个引擎")
                
                for engine in engines:
                    self.log(f"  • {engine.name} [{engine.engine_type.value}] - {'健康' if engine.healthy else '异常'}")
                
                return True
            else:
                self.log("❌ MasterOrchestrator 启动失败", "ERROR")
                return False
                
        except ImportError as e:
            self.log(f"❌ 无法导入 MasterOrchestrator: {e}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ 启动过程出错: {e}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            return False
    
    async def fallback_subprocess_start(self) -> bool:
        """回退方案：使用subprocess直接启动orchestrator进程"""
        self.log("⚠️  尝试回退方案：subprocess启动...")
        
        try:
            orchestrator_path = self.base_path / "tools" / "automation" / "master_orchestrator.py"
            
            if not orchestrator_path.exists():
                self.log(f"❌ 找不到 master_orchestrator.py: {orchestrator_path}", "ERROR")
                return False
            
            # 使用subprocess启动独立进程
            process = subprocess.Popen(
                [sys.executable, str(orchestrator_path), "start"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待进程启动
            await asyncio.sleep(3)
            
            # 检查进程状态
            if process.poll() is None:
                self.log("✅ Orchestrator 进程启动成功")
                self.log(f"   PID: {process.pid}")
                return True
            else:
                stdout, stderr = process.communicate()
                self.log(f"❌ 进程启动失败", "ERROR")
                self.log(f"   STDOUT: {stdout}", "ERROR")
                self.log(f"   STDERR: {stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ subprocess启动失败: {e}", "ERROR")
            return False
    
    async def health_check(self) -> dict:
        """系统健康检查"""
        self.log("🏥 执行系统健康检查...")
        
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        # 检查1: 进程存在性
        try:
            result = subprocess.run(
                ["pgrep", "-f", "master_orchestrator"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                health_status["checks"]["process"] = {
                    "status": "healthy",
                    "pids": pids,
                    "count": len(pids)
                }
                self.log(f"  ✓ 发现 {len(pids)} 个orchestrator进程")
            else:
                health_status["checks"]["process"] = {
                    "status": "unhealthy",
                    "message": "没有运行中的orchestrator进程"
                }
                self.log("  ✗ 未发现orchestrator进程", "WARNING")
        except Exception as e:
            health_status["checks"]["process"] = {
                "status": "error",
                "message": str(e)
            }
            self.log(f"  ✗ 进程检查失败: {e}", "ERROR")
        
        # 检查2: 状态文件
        status_file = self.base_path / ".orchestrator_status"
        if status_file.exists():
            try:
                with open(status_file, 'r') as f:
                    status_data = json.load(f)
                health_status["checks"]["status_file"] = {
                    "status": "healthy",
                    "data": status_data
                }
                self.log(f"  ✓ 状态文件存在: {status_data.get('status', 'unknown')}")
            except Exception as e:
                health_status["checks"]["status_file"] = {
                    "status": "error",
                    "message": str(e)
                }
                self.log(f"  ✗ 状态文件读取失败: {e}", "ERROR")
        else:
            health_status["checks"]["status_file"] = {
                "status": "missing",
                "message": "状态文件不存在"
            }
            self.log("  ✗ 状态文件不存在", "WARNING")
        
        # 检查3: 日志文件
        log_dir = self.base_path / "logs"
        if log_dir.exists():
            recent_logs = sorted(log_dir.glob("*.log"), key=os.path.getmtime, reverse=True)
            if recent_logs:
                latest_log = recent_logs[0]
                health_status["checks"]["logs"] = {
                    "status": "healthy",
                    "latest_log": str(latest_log),
                    "modified": datetime.fromtimestamp(os.path.getmtime(latest_log)).isoformat()
                }
                self.log(f"  ✓ 最新日志: {latest_log.name}")
            else:
                health_status["checks"]["logs"] = {
                    "status": "warning",
                    "message": "日志目录为空"
                }
                self.log("  ⚠ 日志目录为空", "WARNING")
        else:
            health_status["checks"]["logs"] = {
                "status": "missing",
                "message": "日志目录不存在"
            }
            self.log("  ✗ 日志目录不存在", "WARNING")
        
        # 保存健康检查结果
        health_file = self.recovery_log / f"health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(health_file, 'w') as f:
            json.dump(health_status, f, indent=2)
        
        # 总结
        healthy_checks = sum(1 for check in health_status["checks"].values() if check["status"] == "healthy")
        total_checks = len(health_status["checks"])
        
        self.log(f"📊 健康检查完成: {healthy_checks}/{total_checks} 通过")
        
        return health_status
    
    async def run(self):
        """执行应急恢复流程"""
        self.log("=" * 70)
        self.log("🚨 应急恢复系统启动")
        self.log("=" * 70)
        
        # Step 1: 检查依赖
        if not await self.check_dependencies():
            self.log("❌ 依赖检查失败，无法继续恢复", "ERROR")
            return False
        
        # Step 2: 尝试直接启动
        self.log("\n" + "=" * 70)
        self.log("方案1: 直接启动 MasterOrchestrator")
        self.log("=" * 70)
        
        if await self.direct_orchestrator_start():
            self.log("✅ 直接启动成功")
        else:
            # Step 3: 回退方案
            self.log("\n" + "=" * 70)
            self.log("方案2: subprocess 回退启动")
            self.log("=" * 70)
            
            if await self.fallback_subprocess_start():
                self.log("✅ 回退方案启动成功")
            else:
                self.log("❌ 所有恢复方案均失败", "ERROR")
                self.log("💡 建议: 检查日志文件并手动排查问题", "ERROR")
                return False
        
        # Step 4: 健康检查
        self.log("\n" + "=" * 70)
        self.log("健康检查")
        self.log("=" * 70)
        
        await asyncio.sleep(2)  # 等待系统稳定
        health_status = await self.health_check()
        
        # 最终报告
        self.log("\n" + "=" * 70)
        self.log("🎉 应急恢复流程完成")
        self.log("=" * 70)
        self.log(f"📁 恢复日志: {self.log_file}")
        
        return True

async def main():
    """主入口"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║         🚨 SynergyMesh Emergency Recovery System 🚨      ║
    ║                      应急恢复系统                          ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    recovery = EmergencyRecovery()
    success = await recovery.run()
    
    if success:
        print("\n✅ 恢复成功！系统已重新启动。")
        return 0
    else:
        print("\n❌ 恢复失败！请检查日志并手动介入。")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
