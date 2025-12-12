#!/usr/bin/env python3
"""
Instant Governance CLI - One-Command Execution
即時治理命令行介面 - 單一命令執行

Purpose: Single command to deploy and validate governance restructuring
Usage: python instant-governance-cli.py [deploy|validate|status]
Time: < 30 seconds for full deployment

Author: SynergyMesh Governance Team
Version: 1.0.0
Date: 2025-12-12
"""

import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
import time

class GovernanceCLI:
    """Instant execution CLI for governance operations"""
    
    def __init__(self):
        """TODO: Add function documentation"""
        self.script_dir = Path(__file__).parent
        self.scripts_dir = self.script_dir / "35-scripts"
        
    def print_header(self, title: str):
        """Print formatted header"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70 + "\n")
    
    def run_command(self, cmd: list, description: str) -> bool:
        """Run a command and report status"""
        print(f"🔄 {description}...")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✅ {description} - COMPLETE")
            if result.stdout:
                print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ {description} - FAILED")
            if e.stderr:
                print(f"Error: {e.stderr}")
            return False
    
    def deploy(self) -> int:
        """Deploy governance restructuring instantly"""
        self.print_header("🚀 INSTANT GOVERNANCE DEPLOYMENT")
        
        start_time = time.time()
        
        # Step 1: Run migration
        if not self.run_command(
            ["python3", str(self.scripts_dir / "instant-migration.py")],
            "Running instant migration"
        ):
            return 1
        
        # Step 2: Run deployment script
        deploy_script = self.scripts_dir / "instant-deploy.sh"
        if deploy_script.exists():
            if not self.run_command(
                ["bash", str(deploy_script)],
                "Running deployment validation"
            ):
                return 1
        
        duration = time.time() - start_time
        
        print("\n" + "=" * 70)
        print(f"✅ DEPLOYMENT COMPLETE")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        
        if duration < 60:
            print("🎉 INSTANT STANDARD MET (< 60 seconds)")
        
        print("=" * 70 + "\n")
        
        return 0
    
    def validate(self) -> int:
        """Validate governance structure"""
        self.print_header("🔍 GOVERNANCE VALIDATION")
        
        validation_script = self.scripts_dir / "validate-governance-structure.py"
        
        if not validation_script.exists():
            print(f"❌ Validation script not found: {validation_script}")
            return 1
        
        if not self.run_command(
            ["python3", str(validation_script)],
            "Validating governance structure"
        ):
            return 1
        
        print("\n✅ VALIDATION COMPLETE\n")
        return 0
    
    def status(self) -> int:
        """Show current governance status"""
        self.print_header("📊 GOVERNANCE STATUS")
        
        # Check for report files
        report_files = [
            self.script_dir / "instant-deployment-report.json",
            self.script_dir / "migration-report.json",
        ]
        
        for report_file in report_files:
            if report_file.exists():
                print(f"\n📄 {report_file.name}:")
                try:
                    with open(report_file, 'r') as f:
                        report = json.load(f)
                    print(json.dumps(report, indent=2))
                except Exception as e:
                    print(f"  Error reading report: {e}")
        
        # Check structure
        print("\n📁 Directory Structure:")
        
        layered_dirs = ["10-policy", "20-intent", "30-agents", "60-contracts", "70-audit", "80-feedback"]
        legacy_dirs = ["_legacy/10-stakeholder", "_legacy/20-information", "_legacy/30-integration"]
        
        print("\n  Layered Framework:")
        for dir_name in layered_dirs:
            dir_path = self.script_dir / dir_name
            status = "✅" if dir_path.exists() else "❌"
            print(f"    {status} {dir_name}")
        
        print("\n  Legacy Directories:")
        for dir_name in legacy_dirs:
            dir_path = self.script_dir / dir_name
            status = "✅" if dir_path.exists() else "❌"
            print(f"    {status} {dir_name}")
        
        print("\n" + "=" * 70 + "\n")
        return 0
    
    def help(self):
        """Show help message"""
        print("""
╔══════════════════════════════════════════════════════════════════╗
║           INSTANT GOVERNANCE CLI - ONE-COMMAND EXECUTION         ║
╚══════════════════════════════════════════════════════════════════╝

Usage:
  python instant-governance-cli.py <command>

Commands:
  deploy      Deploy governance restructuring instantly (< 60s)
  validate    Validate governance structure
  status      Show current governance status
  help        Show this help message

Examples:
  # Deploy everything instantly
  python instant-governance-cli.py deploy

  # Check validation
  python instant-governance-cli.py validate

  # View current status
  python instant-governance-cli.py status

Features:
  ⚡ Instant execution (< 60 seconds)
  🔄 Automated migration
  ✅ Built-in validation
  📊 Real-time status reporting

Target: Meet market AI standards for instant, complete solutions
Version: 1.0.0
        """)

def main():
    """Main entry point"""
    cli = GovernanceCLI()
    
    if len(sys.argv) < 2:
        print("❌ Error: No command specified\n")
        cli.help()
        return 1
    
    command = sys.argv[1].lower()
    
    if command == "deploy":
        return cli.deploy()
    elif command == "validate":
        return cli.validate()
    elif command == "status":
        return cli.status()
    elif command == "help" or command == "--help" or command == "-h":
        cli.help()
        return 0
    else:
        print(f"❌ Error: Unknown command '{command}'\n")
        cli.help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
