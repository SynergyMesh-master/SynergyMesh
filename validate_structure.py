#!/usr/bin/env python3
"""
Structure Validation Script for MachineNativeOps AAPS
Validates FHS compliance and file integrity
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple

class StructureValidator:
    def __init__(self, root_path: str = "."):
        self.root = Path(root_path).resolve()
        self.errors = []
        self.warnings = []
        self.info = []
        
    def validate_all(self) -> bool:
        """Run all validation checks"""
        print("🔍 Starting Structure Validation...\n")
        
        self.validate_fhs_directories()
        self.validate_controlplane_structure()
        self.validate_workspace_structure()
        self.validate_root_files()
        self.validate_file_counts()
        
        self.print_results()
        return len(self.errors) == 0
    
    def validate_fhs_directories(self):
        """Validate FHS directory structure"""
        print("📁 Validating FHS Directories...")
        
        required_fhs = {
            "bin": "Essential user command binaries",
            "etc": "Host-specific system configuration",
            "home": "User home directories",
            "lib": "Essential shared libraries",
            "sbin": "System administration binaries",
            "srv": "Service data",
            "usr": "Secondary hierarchy for user data",
            "var": "Variable data"
        }
        
        for dir_name, description in required_fhs.items():
            dir_path = self.root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                self.info.append(f"✅ FHS directory exists: {dir_name}/ - {description}")
            else:
                self.errors.append(f"❌ Missing FHS directory: {dir_name}/")
    
    def validate_controlplane_structure(self):
        """Validate controlplane directory structure"""
        print("🎛️  Validating Controlplane Structure...")
        
        controlplane = self.root / "controlplane"
        if not controlplane.exists():
            self.errors.append("❌ Missing controlplane/ directory")
            return
        
        # Check baseline structure
        baseline = controlplane / "baseline"
        if not baseline.exists():
            self.errors.append("❌ Missing controlplane/baseline/ directory")
            return
        
        baseline_dirs = {
            "config": 12,
            "registries": 4,
            "specifications": 8,
            "integration": 1,
            "documentation": 1,
            "validation": None  # Variable number of files
        }
        
        for dir_name, expected_files in baseline_dirs.items():
            dir_path = baseline / dir_name
            if not dir_path.exists():
                self.errors.append(f"❌ Missing controlplane/baseline/{dir_name}/")
                continue
            
            if expected_files is not None:
                actual_files = len([f for f in dir_path.iterdir() if f.is_file()])
                if actual_files < expected_files:
                    self.warnings.append(
                        f"⚠️  controlplane/baseline/{dir_name}/ has {actual_files} files, "
                        f"expected at least {expected_files}"
                    )
                else:
                    self.info.append(
                        f"✅ controlplane/baseline/{dir_name}/ has {actual_files} files"
                    )
        
        # Check governance structure
        governance = controlplane / "governance"
        if governance.exists():
            gov_dirs = ["docs", "policies", "reports"]
            for dir_name in gov_dirs:
                dir_path = governance / dir_name
                if dir_path.exists():
                    self.info.append(f"✅ controlplane/governance/{dir_name}/ exists")
                else:
                    self.warnings.append(f"⚠️  Missing controlplane/governance/{dir_name}/")
    
    def validate_workspace_structure(self):
        """Validate workspace directory structure"""
        print("💼 Validating Workspace Structure...")
        
        workspace = self.root / "workspace"
        if not workspace.exists():
            self.errors.append("❌ Missing workspace/ directory")
            return
        
        # Count subdirectories
        subdirs = [d for d in workspace.iterdir() if d.is_dir()]
        self.info.append(f"✅ workspace/ has {len(subdirs)} subdirectories")
    
    def validate_root_files(self):
        """Validate root bootstrap files"""
        print("📄 Validating Root Files...")
        
        required_files = [
            "root.bootstrap.yaml",
            "root.env.sh",
            "root.fs.map"
        ]
        
        for filename in required_files:
            file_path = self.root / filename
            if file_path.exists() and file_path.is_file():
                size = file_path.stat().st_size
                self.info.append(f"✅ {filename} exists ({size} bytes)")
            else:
                self.errors.append(f"❌ Missing root file: {filename}")
    
    def validate_file_counts(self):
        """Validate expected file counts"""
        print("🔢 Validating File Counts...")
        
        # Count files in root (should be minimal)
        root_files = [f for f in self.root.iterdir() if f.is_file()]
        if len(root_files) > 10:
            self.warnings.append(
                f"⚠️  Root directory has {len(root_files)} files, "
                "should be minimal (ideally < 10)"
            )
        else:
            self.info.append(f"✅ Root directory has {len(root_files)} files (minimal)")
        
        # Check for unwanted directories in root
        unwanted = [".vscode", ".local", ".github-private", "outputs", "init.d"]
        for dir_name in unwanted:
            dir_path = self.root / dir_name
            if dir_path.exists():
                self.warnings.append(f"⚠️  Unwanted directory in root: {dir_name}/")
    
    def print_results(self):
        """Print validation results"""
        print("\n" + "="*70)
        print("📊 VALIDATION RESULTS")
        print("="*70 + "\n")
        
        if self.info:
            print("ℹ️  Information:")
            for msg in self.info:
                print(f"  {msg}")
            print()
        
        if self.warnings:
            print("⚠️  Warnings:")
            for msg in self.warnings:
                print(f"  {msg}")
            print()
        
        if self.errors:
            print("❌ Errors:")
            for msg in self.errors:
                print(f"  {msg}")
            print()
        
        print("="*70)
        print(f"Summary: {len(self.info)} info, {len(self.warnings)} warnings, "
              f"{len(self.errors)} errors")
        print("="*70 + "\n")
        
        if self.errors:
            print("❌ VALIDATION FAILED")
            return False
        elif self.warnings:
            print("⚠️  VALIDATION PASSED WITH WARNINGS")
            return True
        else:
            print("✅ VALIDATION PASSED")
            return True

def main():
    """Main entry point"""
    validator = StructureValidator()
    success = validator.validate_all()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()