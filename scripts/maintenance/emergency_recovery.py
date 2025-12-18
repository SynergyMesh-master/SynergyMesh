#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
                        Emergency Recovery System
                           緊急恢復系統
═══════════════════════════════════════════════════════════════════════════════

Standalone emergency recovery script that can bootstrap the entire system
from scratch when everything else fails.

This is the LAST LINE OF DEFENSE - runs with minimal dependencies and can
rebuild the system even when core components are broken.

Features:
- Zero external dependencies (only stdlib)
- Can run when automation_launcher.py fails
- Bootstraps system from scratch
- Self-contained and minimal
- Creates all necessary directories and files
- Restarts critical services

Usage:
    python emergency_recovery.py

Author: SynergyMesh Team
Version: 1.0.0
Created: 2025-12-09

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# ============================================================================
# Configuration
# ============================================================================

BASE_PATH = Path(__file__).parent
RECOVERY_LOG = BASE_PATH / ".automation_logs" / "emergency_recovery.log"

# Critical components that must exist
CRITICAL_COMPONENTS = [
    "automation_launcher.py",
    "services/agents/recovery/phoenix_agent.py",
    "services/watchdog/system_watchdog.py",
    "config/recovery-system.yaml"
]

# Critical directories
CRITICAL_DIRECTORIES = [
    ".automation_logs",
    "services/agents/recovery",
    "services/watchdog",
    "config/agents/profiles"
]

# ============================================================================
# Emergency Recovery System
# ============================================================================

class EmergencyRecovery:
    """
    Emergency Recovery System
    
    Last line of defense when all other systems fail.
    """
    
    def __init__(self):
        self.base_path = BASE_PATH
        self.log_messages: List[str] = []
        self.start_time = datetime.now()
        self.issues_found: List[Dict[str, Any]] = []
        self.fixes_applied: List[Dict[str, Any]] = []
        
        # Ensure log directory exists
        RECOVERY_LOG.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {message}"
        
        self.log_messages.append(formatted)
        print(formatted)
        
        # Write to log file
        try:
            with open(RECOVERY_LOG, 'a') as f:
                f.write(formatted + "\n")
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")
    
    def run(self) -> bool:
        """Run emergency recovery"""
        self.log("=" * 70)
        self.log("🚨 EMERGENCY RECOVERY SYSTEM ACTIVATED")
        self.log("=" * 70)
        self.log("")
        
        # Phase 1: Diagnostic
        self.log("Phase 1: System Diagnostic")
        self.log("-" * 70)
        self.diagnose_system()
        self.log("")
        
        # Phase 2: Critical Repairs
        self.log("Phase 2: Critical Repairs")
        self.log("-" * 70)
        self.repair_critical_components()
        self.log("")
        
        # Phase 3: Service Recovery
        self.log("Phase 3: Service Recovery")
        self.log("-" * 70)
        self.recover_services()
        self.log("")
        
        # Phase 4: Verification
        self.log("Phase 4: System Verification")
        self.log("-" * 70)
        success = self.verify_system()
        self.log("")
        
        # Final Report
        self.generate_report(success)
        
        return success
    
    def diagnose_system(self):
        """Phase 1: Diagnose system"""
        self.log("🔍 Checking critical components...")
        
        # Check critical files
        for component in CRITICAL_COMPONENTS:
            path = self.base_path / component
            if not path.exists():
                self.log(f"   ❌ Missing: {component}", "ERROR")
                self.issues_found.append({
                    "type": "missing_file",
                    "component": component,
                    "path": str(path)
                })
            else:
                self.log(f"   ✅ Found: {component}")
        
        # Check critical directories
        for directory in CRITICAL_DIRECTORIES:
            path = self.base_path / directory
            if not path.exists():
                self.log(f"   ❌ Missing directory: {directory}", "ERROR")
                self.issues_found.append({
                    "type": "missing_directory",
                    "directory": directory,
                    "path": str(path)
                })
            else:
                self.log(f"   ✅ Directory exists: {directory}")
        
        # Check running processes
        self.log("")
        self.log("🔍 Checking critical processes...")
        self.check_processes()
        
        # Check Python environment
        self.log("")
        self.log("🔍 Checking Python environment...")
        self.check_python_environment()
        
        # Summary
        if self.issues_found:
            self.log(f"")
            self.log(f"⚠️  Found {len(self.issues_found)} issues", "WARNING")
        else:
            self.log(f"")
            self.log("✅ No critical issues found")
    
    def check_processes(self):
        """Check if critical processes are running"""
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            processes = result.stdout
            
            # Check for automation_launcher
            if "automation_launcher.py" in processes:
                self.log("   ✅ automation_launcher.py is running")
            else:
                self.log("   ❌ automation_launcher.py is NOT running", "WARNING")
                self.issues_found.append({
                    "type": "process_not_running",
                    "process": "automation_launcher.py"
                })
            
            # Check for phoenix_agent
            if "phoenix_agent.py" in processes:
                self.log("   ✅ phoenix_agent.py is running")
            else:
                self.log("   ❌ phoenix_agent.py is NOT running", "WARNING")
                self.issues_found.append({
                    "type": "process_not_running",
                    "process": "phoenix_agent.py"
                })
            
            # Check for watchdog
            if "system_watchdog.py" in processes:
                self.log("   ✅ system_watchdog.py is running")
            else:
                self.log("   ❌ system_watchdog.py is NOT running", "WARNING")
                self.issues_found.append({
                    "type": "process_not_running",
                    "process": "system_watchdog.py"
                })
                
        except Exception as e:
            self.log(f"   ⚠️  Could not check processes: {e}", "WARNING")
    
    def check_python_environment(self):
        """Check Python environment"""
        self.log(f"   Python version: {sys.version}")
        self.log(f"   Python executable: {sys.executable}")
        
        # Check required modules
        required_modules = ["asyncio", "yaml", "psutil"]
        for module in required_modules:
            try:
                __import__(module)
                self.log(f"   ✅ Module available: {module}")
            except ImportError:
                self.log(f"   ❌ Module missing: {module}", "ERROR")
                self.issues_found.append({
                    "type": "missing_module",
                    "module": module
                })
    
    def repair_critical_components(self):
        """Phase 2: Repair critical components"""
        if not self.issues_found:
            self.log("✅ No repairs needed")
            return
        
        self.log(f"🔧 Attempting to fix {len(self.issues_found)} issues...")
        
        for issue in self.issues_found:
            issue_type = issue["type"]
            
            if issue_type == "missing_directory":
                self.repair_missing_directory(issue)
            elif issue_type == "missing_file":
                self.log(f"   ⚠️  Cannot auto-fix missing file: {issue['component']}", "WARNING")
            elif issue_type == "missing_module":
                self.repair_missing_module(issue)
            elif issue_type == "process_not_running":
                # Will be handled in service recovery phase
                pass
    
    def repair_missing_directory(self, issue: Dict[str, Any]):
        """Repair missing directory"""
        directory = issue["directory"]
        path = Path(issue["path"])
        
        try:
            path.mkdir(parents=True, exist_ok=True)
            self.log(f"   ✅ Created directory: {directory}")
            self.fixes_applied.append({
                "type": "created_directory",
                "directory": directory,
                "success": True
            })
        except Exception as e:
            self.log(f"   ❌ Failed to create directory {directory}: {e}", "ERROR")
            self.fixes_applied.append({
                "type": "created_directory",
                "directory": directory,
                "success": False,
                "error": str(e)
            })
    
    def repair_missing_module(self, issue: Dict[str, Any]):
        """Repair missing Python module"""
        module = issue["module"]
        
        self.log(f"   🔧 Installing missing module: {module}")
        
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", module],
                check=True,
                capture_output=True,
                timeout=120
            )
            self.log(f"   ✅ Installed module: {module}")
            self.fixes_applied.append({
                "type": "installed_module",
                "module": module,
                "success": True
            })
        except subprocess.CalledProcessError as e:
            self.log(f"   ❌ Failed to install {module}: {e}", "ERROR")
            self.fixes_applied.append({
                "type": "installed_module",
                "module": module,
                "success": False,
                "error": str(e)
            })
        except Exception as e:
            self.log(f"   ❌ Error installing {module}: {e}", "ERROR")
            self.fixes_applied.append({
                "type": "installed_module",
                "module": module,
                "success": False,
                "error": str(e)
            })
    
    def recover_services(self):
        """Phase 3: Recover services"""
        self.log("🔄 Attempting to restart services...")
        
        # Try to start automation_launcher
        if any(issue["type"] == "process_not_running" and 
               issue["process"] == "automation_launcher.py" 
               for issue in self.issues_found):
            self.start_automation_launcher()
        
        # Give it time to start
        time.sleep(5)
        
        # Try to start watchdog
        if any(issue["type"] == "process_not_running" and 
               issue["process"] == "system_watchdog.py" 
               for issue in self.issues_found):
            self.start_watchdog()
    
    def start_automation_launcher(self):
        """Start automation launcher"""
        launcher_path = self.base_path / "automation_launcher.py"
        
        if not launcher_path.exists():
            self.log("   ❌ Cannot start automation_launcher.py - file not found", "ERROR")
            return
        
        self.log("   🔄 Starting automation_launcher.py...")
        
        try:
            # Start in background
            subprocess.Popen(
                [sys.executable, str(launcher_path), "start"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            self.log("   ✅ Started automation_launcher.py")
            self.fixes_applied.append({
                "type": "started_service",
                "service": "automation_launcher.py",
                "success": True
            })
        except Exception as e:
            self.log(f"   ❌ Failed to start automation_launcher.py: {e}", "ERROR")
            self.fixes_applied.append({
                "type": "started_service",
                "service": "automation_launcher.py",
                "success": False,
                "error": str(e)
            })
    
    def start_watchdog(self):
        """Start watchdog service"""
        watchdog_path = self.base_path / "services" / "watchdog" / "system_watchdog.py"
        
        if not watchdog_path.exists():
            self.log("   ❌ Cannot start system_watchdog.py - file not found", "ERROR")
            return
        
        self.log("   🔄 Starting system_watchdog.py...")
        
        try:
            # Start in background
            subprocess.Popen(
                [sys.executable, str(watchdog_path), "start"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            self.log("   ✅ Started system_watchdog.py")
            self.fixes_applied.append({
                "type": "started_service",
                "service": "system_watchdog.py",
                "success": True
            })
        except Exception as e:
            self.log(f"   ❌ Failed to start system_watchdog.py: {e}", "ERROR")
            self.fixes_applied.append({
                "type": "started_service",
                "service": "system_watchdog.py",
                "success": False,
                "error": str(e)
            })
    
    def verify_system(self) -> bool:
        """Phase 4: Verify system"""
        self.log("✅ Running system verification...")
        
        all_good = True
        
        # Re-check critical files
        self.log("")
        self.log("   Checking critical files...")
        for component in CRITICAL_COMPONENTS:
            path = self.base_path / component
            if path.exists():
                self.log(f"      ✅ {component}")
            else:
                self.log(f"      ❌ {component} still missing", "ERROR")
                all_good = False
        
        # Re-check directories
        self.log("")
        self.log("   Checking directories...")
        for directory in CRITICAL_DIRECTORIES:
            path = self.base_path / directory
            if path.exists():
                self.log(f"      ✅ {directory}")
            else:
                self.log(f"      ❌ {directory} still missing", "ERROR")
                all_good = False
        
        return all_good
    
    def generate_report(self, success: bool):
        """Generate final report"""
        duration = (datetime.now() - self.start_time).seconds
        
        self.log("")
        self.log("=" * 70)
        self.log("📊 EMERGENCY RECOVERY REPORT")
        self.log("=" * 70)
        self.log(f"Status: {'✅ SUCCESS' if success else '❌ PARTIAL RECOVERY'}")
        self.log(f"Duration: {duration} seconds")
        self.log(f"Issues Found: {len(self.issues_found)}")
        self.log(f"Fixes Applied: {len(self.fixes_applied)}")
        
        if self.fixes_applied:
            self.log("")
            self.log("Fixes Applied:")
            for fix in self.fixes_applied:
                status = "✅" if fix.get("success") else "❌"
                self.log(f"   {status} {fix['type']}")
        
        self.log("")
        self.log("Next Steps:")
        if success:
            self.log("   1. Monitor system logs for stability")
            self.log("   2. Review automated fixes")
            self.log("   3. Check that all services are running correctly")
        else:
            self.log("   1. Review error log: .automation_logs/emergency_recovery.log")
            self.log("   2. Manual intervention may be required")
            self.log("   3. Contact system administrator")
        
        self.log("=" * 70)
        
        # Save report
        self.save_report(success)
    
    def save_report(self, success: bool):
        """Save recovery report"""
        report_path = self.base_path / ".automation_logs" / "emergency_recovery_report.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - self.start_time).seconds,
            "success": success,
            "issues_found": self.issues_found,
            "fixes_applied": self.fixes_applied,
            "log_file": str(RECOVERY_LOG)
        }
        
        try:
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            self.log(f"")
            self.log(f"📄 Report saved: {report_path}")
        except Exception as e:
            self.log(f"⚠️  Could not save report: {e}", "WARNING")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point"""
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                    🚨 EMERGENCY RECOVERY SYSTEM 🚨                            ║
║                         緊急恢復系統                                           ║
║                                                                               ║
║   This system will attempt to diagnose and repair critical system failures   ║
║   本系統將嘗試診斷並修復關鍵系統故障                                            ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    recovery = EmergencyRecovery()
    success = recovery.run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
