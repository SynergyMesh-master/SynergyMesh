#!/usr/bin/env python3
"""
Instant Governance Restructuring Migration Tool
即時治理重組遷移工具

Purpose: Automatically migrate all references from legacy directories to new structure
Target: Complete migration in < 60 seconds
Status: Production-ready automation tool

Author: SynergyMesh Governance Team
Version: 1.0.0
Date: 2025-12-12
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import json
import yaml

class InstantMigrationTool:
    """Instant automated migration for governance restructuring"""
    
    def __init__(self, project_root: Path):
        """TODO: Add function documentation"""
        self.project_root = project_root
        self.governance_root = project_root / "governance"
        
        # Migration mappings
        self.directory_mappings = {
            "governance/10-stakeholder": "governance/_legacy/10-stakeholder",
            "governance/20-information": "governance/_legacy/20-information",
            "governance/30-integration": "governance/_legacy/30-integration",
            "governance/policies": "governance/23-policies",
            "governance/schemas": "governance/31-schemas",
            "governance/scripts": "governance/35-scripts",
        }
        
        # Alternative mappings for integration references
        self.integration_mappings = {
            "30-integration": "30-agents",
            "20-information": "20-intent",
            "10-stakeholder": "10-policy",
        }
        
        self.stats = {
            "files_scanned": 0,
            "files_updated": 0,
            "references_updated": 0,
            "errors": []
        }
    
    def scan_and_update_file(self, file_path: Path) -> int:
        """Scan and update a single file for legacy references"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            updates = 0
            
            # Update directory references
            for old_path, new_path in self.directory_mappings.items():
                if old_path in content:
                    # Don't update if it's already pointing to new location
                    if new_path not in content or old_path != new_path:
                        content = content.replace(old_path, new_path)
                        updates += 1
            
            # Update dimension references in specific contexts
            for old_dim, new_dim in self.integration_mappings.items():
                # Match patterns like "30-integration" but not in _legacy paths
                pattern = rf'(?<!_legacy/)({re.escape(old_dim)})(?=/|:|\s|"|\'|$)'
                if re.search(pattern, content):
                    content = re.sub(pattern, new_dim, content)
                    updates += 1
            
            # Write back if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return updates
            
            return 0
            
        except Exception as e:
            self.stats["errors"].append(f"Error processing {file_path}: {str(e)}")
            return 0
    
    def scan_directory(self, directory: Path, extensions: List[str]) -> None:
        """Recursively scan directory for files to update"""
        for ext in extensions:
            for file_path in directory.rglob(f"*{ext}"):
                # Skip certain directories
                if any(skip in str(file_path) for skip in [
                    '.git', 'node_modules', '__pycache__', 'venv', 
                    '.venv', 'dist', 'build', '_legacy'
                ]):
                    continue
                
                self.stats["files_scanned"] += 1
                updates = self.scan_and_update_file(file_path)
                
                if updates > 0:
                    self.stats["files_updated"] += 1
                    self.stats["references_updated"] += updates
                    print(f"  ✅ Updated: {file_path.relative_to(self.project_root)} ({updates} changes)")
    
    def validate_migration(self) -> bool:
        """Validate that migration is complete"""
        print("\n🔍 Validating migration...")
        
        issues = []
        
        # Check that legacy directories exist
        for old_path in ["10-stakeholder", "20-information", "30-integration"]:
            legacy_path = self.governance_root / "_legacy" / old_path
            if not legacy_path.exists():
                issues.append(f"Legacy directory missing: {legacy_path}")
        
        # Check that new directories exist
        for new_dir in ["10-policy", "20-intent", "30-agents", "23-policies", "31-schemas", "35-scripts"]:
            new_path = self.governance_root / new_dir
            if not new_path.exists():
                issues.append(f"New directory missing: {new_path}")
        
        # Check for remaining old references in key files
        key_files = [
            self.governance_root / "README.md",
            self.governance_root / "governance-map.yaml",
        ]
        
        for key_file in key_files:
            if key_file.exists():
                with open(key_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for non-legacy references to old paths
                for old_path in ["governance/10-stakeholder", "governance/20-information", "governance/30-integration"]:
                    if old_path in content and "_legacy" not in content[max(0, content.index(old_path)-50):content.index(old_path)+50]:
                        issues.append(f"Old reference found in {key_file}: {old_path}")
        
        if issues:
            print("\n⚠️  Validation issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        
        print("✅ Validation passed!")
        return True
    
    def generate_report(self) -> Dict:
        """Generate migration report"""
        return {
            "status": "complete" if self.stats["errors"] == [] else "completed_with_errors",
            "timestamp": "2025-12-12T12:22:00Z",
            "statistics": {
                "files_scanned": self.stats["files_scanned"],
                "files_updated": self.stats["files_updated"],
                "references_updated": self.stats["references_updated"],
                "errors": len(self.stats["errors"])
            },
            "errors": self.stats["errors"]
        }
    
    def run(self) -> bool:
        # NOTE: Consider refactoring this function (complexity > 50 lines)
        """Execute instant migration"""
        print("=" * 70)
        print("🚀 INSTANT GOVERNANCE MIGRATION TOOL")
        print("=" * 70)
        print()
        
        print("📋 Migration mappings:")
        for old, new in self.directory_mappings.items():
            print(f"  {old} → {new}")
        print()
        
        print("🔄 Scanning and updating files...")
        
        # Scan Python files
        print("\n📝 Python files:")
        self.scan_directory(self.project_root, ['.py'])
        
        # Scan YAML files
        print("\n📄 YAML files:")
        self.scan_directory(self.project_root, ['.yaml', '.yml'])
        
        # Scan Markdown files
        print("\n📖 Markdown files:")
        self.scan_directory(self.project_root, ['.md'])
        
        # Scan shell scripts
        print("\n🔧 Shell scripts:")
        self.scan_directory(self.project_root, ['.sh'])
        
        # Validate migration
        validation_passed = self.validate_migration()
        
        # Generate report
        report = self.generate_report()
        
        # Save report
        report_path = self.governance_root / "migration-report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 MIGRATION SUMMARY")
        print("=" * 70)
        print(f"Files scanned: {self.stats['files_scanned']}")
        print(f"Files updated: {self.stats['files_updated']}")
        print(f"References updated: {self.stats['references_updated']}")
        print(f"Errors: {len(self.stats['errors'])}")
        print(f"Validation: {'✅ PASSED' if validation_passed else '❌ FAILED'}")
        print(f"\nReport saved to: {report_path}")
        print("=" * 70)
        
        if self.stats['errors']:
            print("\n⚠️  Errors encountered:")
            for error in self.stats['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")
        
        return validation_passed and len(self.stats['errors']) == 0


def main():
    """Main entry point"""
    # Detect project root
    current_dir = Path(__file__).resolve().parent
    
    # Try to find project root (contains .git)
    project_root = current_dir
    while project_root.parent != project_root:
        if (project_root / ".git").exists():
            break
        project_root = project_root.parent
    
    if not (project_root / ".git").exists():
        print("❌ Error: Could not find project root (.git directory)")
        return 1
    
    print(f"📁 Project root: {project_root}")
    print()
    
    # Run migration
    migrator = InstantMigrationTool(project_root)
    success = migrator.run()
    
    if success:
        print("\n✅ INSTANT MIGRATION COMPLETED SUCCESSFULLY!")
        print("\n🎯 Next steps:")
        print("  1. Review migration-report.json")
        print("  2. Test governance functionality")
        print("  3. Commit changes")
        return 0
    else:
        print("\n⚠️  MIGRATION COMPLETED WITH ISSUES")
        print("Please review errors and re-run if needed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
