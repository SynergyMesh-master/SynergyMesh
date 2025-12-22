#!/usr/bin/env python3
"""
MachineNativeOps Namespace Converter

Converts legacy namespace references to MachineNativeOps standard namespace.
Supports comprehensive conversion rules aligned with mno-namespace.yaml.

Usage:
    python namespace-converter.py [--dry-run] [--verbose] <path>
    python namespace-converter.py --validate <path>

Examples:
    python namespace-converter.py --dry-run .
    python namespace-converter.py --verbose src/
    python namespace-converter.py --validate config/

Version: 2.0.0
Author: MachineNativeOps Platform Team
"""

import re
import sys
import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ConversionResult:
    """Represents the result of a conversion operation."""
    file_path: str
    conversions: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    patterns_matched: Dict[str, int] = field(default_factory=dict)


class NamespaceConverter:
    """
    Advanced namespace converter aligned with MachineNativeOps standards.
    """
    
    def __init__(self, dry_run=False, verbose=False, validate_only=False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.validate_only = validate_only
        self.results: List[ConversionResult] = []
        
        # Comprehensive conversion rules aligned with mno-namespace.yaml
        self.conversion_rules = {
            # API Version conversions
            r'apiVersion:\s*axiom\.io/v(\d+)': r'apiVersion: machinenativeops.io/v\1',
            r'axiom\.io/v(\d+)': r'machinenativeops.io/v\1',
            
            # Namespace conversions
            r'\baxiom\b(?!\.io)': r'machinenativeops',
            r'namespace:\s*axiom': r'namespace: machinenativeops',
            
            # Kind conversions
            r'\bMachineNativeOpsGlobalBaseline\b': r'MachineNativeOpsGlobalBaseline',
            r'\bAxiom([A-Z]\w+)': r'MachineNativeOps\1',
            
            # URN conversions
            r'urn:machinenativeops:': r'urn:machinenativeops:',
            
            # Domain conversions
            r'axiom\.io/': r'machinenativeops.io/',
            
            # Resource name conversions (with word boundaries)
            r'\bmachinenativeops-': r'machinenativeops-',
            r'(["\']|^)machinenativeops-': r'\1machinenativeops-',
            
            # Registry conversions
            r'registry\.axiom\.io': r'registry.machinenativeops.io',
            
            # Path conversions
            r'/etc/axiom': r'/etc/machinenativeops',
            r'/opt/axiom': r'/opt/machinenativeops',
            r'/var/lib/axiom': r'/var/lib/machinenativeops',
            r'/var/log/axiom': r'/var/log/machinenativeops',
            
            # Cluster name conversions
            r'\bmachinenativeops-etcd-cluster\b': r'super-agent-etcd-cluster',
            
            # Label key conversions
            r'axiom\.io/(\w+)': r'machinenativeops.io/\1',
        }
        
        # Validation patterns (must NOT exist after conversion)
        self.forbidden_patterns = [
            (r'\baxiom\.io/', "Legacy machinenativeops.io domain found"),
            (r'\bAxiom[A-Z]', "Legacy Axiom class name found"),
            (r'urn:machinenativeops:', "Legacy axiom URN found"),
            (r'/etc/machinenativeops/', "Legacy axiom path found"),
        ]
        
        # File extensions to process
        self.processable_extensions = {
            '.yaml', '.yml', '.json', '.py', '.js', '.ts',
            '.md', '.sh', '.txt', '.conf', '.toml'
        }
        
        # Excluded directories
        self.excluded_dirs = {
            '.git', 'node_modules', '__pycache__', '.venv',
            'venv', 'dist', 'build', 'target', 'archive'
        }
    
    def load_namespace_config(self, config_path: str = 'mno-namespace.yaml') -> Dict:
        """Load namespace configuration from mno-namespace.yaml."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            if self.verbose:
                print(f"Warning: {config_path} not found, using default rules")
            return {}
        except Exception as e:
            print(f"Error loading namespace config: {e}")
            return {}
    
    def convert_file(self, file_path: Path) -> ConversionResult:
        """Convert namespace references in a single file."""
        result = ConversionResult(file_path=str(file_path))
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply conversion rules
            for pattern, replacement in self.conversion_rules.items():
                matches = list(re.finditer(pattern, content, re.MULTILINE))
                if matches:
                    match_count = len(matches)
                    result.conversions += match_count
                    result.patterns_matched[pattern] = match_count
                    
                    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                    
                    if self.verbose:
                        print(f"  Pattern '{pattern}': {match_count} matches")
            
            # Validate converted content
            if self.validate_only or (result.conversions > 0):
                self._validate_content(content, result)
            
            # Write converted content
            if result.conversions > 0 and not self.dry_run and not self.validate_only:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                if self.verbose:
                    print(f"✓ Updated {file_path}: {result.conversions} conversions")
            elif result.conversions > 0 and self.dry_run:
                if self.verbose:
                    print(f"⊡ Would update {file_path}: {result.conversions} conversions")
            
        except Exception as e:
            error_msg = f"Error processing {file_path}: {e}"
            result.errors.append(error_msg)
            print(error_msg)
        
        return result
    
    def _validate_content(self, content: str, result: ConversionResult):
        """Validate that no forbidden patterns exist in content."""
        for pattern, message in self.forbidden_patterns:
            matches = list(re.finditer(pattern, content, re.MULTILINE))
            if matches:
                warning = f"{message}: {len(matches)} occurrences"
                result.warnings.append(warning)
                if self.verbose:
                    print(f"  ⚠ {warning}")
    
    def should_process_file(self, file_path: Path) -> bool:
        """Determine if a file should be processed."""
        # Check file extension
        if file_path.suffix not in self.processable_extensions:
            return False
        
        # Check if in excluded directory
        for parent in file_path.parents:
            if parent.name in self.excluded_dirs:
                return False
        
        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            return False
        
        return True
    
    def convert_directory(self, directory_path: Path) -> List[ConversionResult]:
        """Recursively convert all files in a directory."""
        results = []
        
        for file_path in directory_path.rglob('*'):
            if file_path.is_file() and self.should_process_file(file_path):
                result = self.convert_file(file_path)
                if result.conversions > 0 or result.warnings or result.errors:
                    results.append(result)
        
        return results
    
    def convert_path(self, path: Path) -> List[ConversionResult]:
        """Convert namespace in a file or directory."""
        if path.is_file():
            return [self.convert_file(path)]
        elif path.is_dir():
            return self.convert_directory(path)
        else:
            print(f"Error: {path} is not a valid file or directory")
            return []
    
    def generate_report(self) -> str:
        """Generate a detailed conversion report."""
        total_files = len(self.results)
        total_conversions = sum(r.conversions for r in self.results)
        total_errors = sum(len(r.errors) for r in self.results)
        total_warnings = sum(len(r.warnings) for r in self.results)
        
        report = []
        report.append("=" * 80)
        report.append("MachineNativeOps Namespace Conversion Report")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Mode: {'Validation Only' if self.validate_only else 'Dry Run' if self.dry_run else 'Live Conversion'}")
        report.append("")
        report.append("Summary")
        report.append("-" * 80)
        report.append(f"Files processed:     {total_files}")
        report.append(f"Total conversions:   {total_conversions}")
        report.append(f"Errors:              {total_errors}")
        report.append(f"Warnings:            {total_warnings}")
        report.append("")
        
        if self.results:
            report.append("Detailed Results")
            report.append("-" * 80)
            for result in self.results:
                if result.conversions > 0 or result.errors or result.warnings:
                    report.append(f"\nFile: {result.file_path}")
                    report.append(f"  Conversions: {result.conversions}")
                    
                    if result.patterns_matched:
                        report.append("  Patterns matched:")
                        for pattern, count in result.patterns_matched.items():
                            report.append(f"    - {pattern[:50]}...: {count}")
                    
                    if result.warnings:
                        report.append("  Warnings:")
                        for warning in result.warnings:
                            report.append(f"    ⚠ {warning}")
                    
                    if result.errors:
                        report.append("  Errors:")
                        for error in result.errors:
                            report.append(f"    ✗ {error}")
        
        report.append("")
        report.append("=" * 80)
        
        if total_conversions == 0 and total_warnings == 0:
            report.append("✓ All files are compliant with MachineNativeOps namespace standards")
        elif total_errors == 0:
            report.append("✓ Conversion completed successfully")
        else:
            report.append("✗ Conversion completed with errors")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_report(self, report: str, output_path: str = "namespace-conversion-report.txt"):
        """Save report to file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\nReport saved to: {output_path}")
        except Exception as e:
            print(f"Error saving report: {e}")


def main():
    """Main entry point for the namespace converter."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='MachineNativeOps Namespace Converter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run on current directory
  python namespace-converter.py --dry-run .
  
  # Convert all files in src/ directory
  python namespace-converter.py src/
  
  # Validate files without conversion
  python namespace-converter.py --validate config/
  
  # Verbose output with report
  python namespace-converter.py --verbose --report .
        """
    )
    
    parser.add_argument('path', type=str, help='File or directory path to process')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without modifying files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--validate', action='store_true', help='Validate only, do not convert')
    parser.add_argument('--report', action='store_true', help='Generate detailed report file')
    parser.add_argument('--report-path', type=str, default='namespace-conversion-report.txt', 
                       help='Path for report file (default: namespace-conversion-report.txt)')
    
    args = parser.parse_args()
    
    # Validate path exists
    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path {path} does not exist")
        sys.exit(1)
    
    # Create converter
    converter = NamespaceConverter(
        dry_run=args.dry_run or args.validate,
        verbose=args.verbose,
        validate_only=args.validate
    )
    
    # Load namespace config if available
    converter.load_namespace_config()
    
    # Perform conversion
    print(f"{'Validating' if args.validate else 'Converting'} namespace in: {path}")
    if args.dry_run:
        print("(DRY RUN - no files will be modified)")
    print()
    
    converter.results = converter.convert_path(path)
    
    # Generate and display report
    report = converter.generate_report()
    print("\n" + report)
    
    # Save report if requested
    if args.report:
        converter.save_report(report, args.report_path)
    
    # Exit with appropriate code
    total_errors = sum(len(r.errors) for r in converter.results)
    sys.exit(1 if total_errors > 0 else 0)
Namespace Converter Tool
命名空間轉換工具

Converts legacy namespaces and naming conventions to the new MachineNativeOps standard.
將舊的命名空間和命名慣例轉換為新的 MachineNativeOps 標準。

Usage:
    python namespace-converter.py --input <file> --output <file>
    python namespace-converter.py --scan <directory>
    python namespace-converter.py --dry-run <file>
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NamespaceConverter:
    """Converts namespaces according to mno-namespace.yaml configuration"""
    
    def __init__(self, config_path: str = "mno-namespace.yaml"):
        """Initialize converter with namespace configuration"""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.conversion_rules = self._build_conversion_rules()
        self.stats = {
            "files_scanned": 0,
            "files_converted": 0,
            "replacements_made": 0,
            "errors": 0
        }
    
    def _load_config(self) -> dict:
        """Load namespace configuration from YAML"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded namespace config from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def _build_conversion_rules(self) -> List[Tuple[str, str, str]]:
        """Build conversion rules from configuration"""
        rules = []
        
        # Get migration mappings
        migration = self.config.get("migration", {})
        mapping = migration.get("mapping", {})
        
        # Primary namespace
        primary_ns = self.config.get("namespace", {}).get("primary", "machinenativeops")
        
        # Add rules for each legacy namespace
        for old_ns, new_ns in mapping.items():
            # Pattern 1: Direct replacement
            rules.append((
                r'\b' + re.escape(old_ns) + r'\b',
                new_ns,
                f"Direct namespace replacement: {old_ns} → {new_ns}"
            ))
            
            # Pattern 2: In URLs
            rules.append((
                re.escape(old_ns) + r'\.io',
                f"{new_ns}.io",
                f"Domain replacement: {old_ns}.io → {new_ns}.io"
            ))
            
            # Pattern 3: In paths
            rules.append((
                r'/' + re.escape(old_ns) + r'/',
                f"/{new_ns}/",
                f"Path replacement: /{old_ns}/ → /{new_ns}/"
            ))
        
        # Registry conversions
        registries = self.config.get("registries", {})
        if "primary" in registries:
            primary_registry = registries["primary"].get("url", "")
            if primary_registry:
                # Convert docker.io/machine-native-ops to registry.machinenativeops.io
                rules.append((
                    r'docker\.io/machine-native-ops',
                    f"{primary_registry}/machinenativeops",
                    f"Registry conversion to {primary_registry}"
                ))
        
        logger.info(f"Built {len(rules)} conversion rules")
        return rules
    
    def convert_content(self, content: str) -> Tuple[str, int]:
        """
        Convert content using defined rules
        
        Returns:
            Tuple of (converted_content, number_of_replacements)
        """
        replacements = 0
        result = content
        
        for pattern, replacement, description in self.conversion_rules:
            new_result, count = re.subn(pattern, replacement, result)
            if count > 0:
                logger.debug(f"{description}: {count} replacements")
                replacements += count
                result = new_result
        
        return result, replacements
    
    def convert_file(self, input_path: Path, output_path: Path = None, dry_run: bool = False) -> bool:
        """
        Convert a single file
        
        Args:
            input_path: Path to input file
            output_path: Path to output file (None = overwrite)
            dry_run: If True, don't write changes
        
        Returns:
            True if changes were made
        """
        self.stats["files_scanned"] += 1
        
        try:
            # Read file
            with open(input_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Convert
            converted_content, replacements = self.convert_content(original_content)
            
            # Check if changes were made
            if replacements == 0:
                logger.debug(f"No changes needed for {input_path}")
                return False
            
            self.stats["replacements_made"] += replacements
            
            # Report changes
            logger.info(f"{'[DRY RUN] ' if dry_run else ''}Converting {input_path}: {replacements} replacements")
            
            if not dry_run:
                # Write output
                output_path = output_path or input_path
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(converted_content)
                logger.info(f"Wrote converted file to {output_path}")
                self.stats["files_converted"] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error converting {input_path}: {e}")
            self.stats["errors"] += 1
            return False
    
    def scan_directory(self, directory: Path, patterns: List[str] = None, dry_run: bool = False) -> None:
        """
        Scan and convert all files in a directory
        
        Args:
            directory: Directory to scan
            patterns: File patterns to match (default: ['*.yaml', '*.yml', '*.md'])
            dry_run: If True, don't write changes
        """
        if patterns is None:
            patterns = ['*.yaml', '*.yml', '*.md', '*.json', '*.sh', '*.py']
        
        directory = Path(directory)
        if not directory.is_dir():
            logger.error(f"Not a directory: {directory}")
            return
        
        logger.info(f"Scanning directory: {directory}")
        
        for pattern in patterns:
            for file_path in directory.rglob(pattern):
                # Skip hidden files and directories
                if any(part.startswith('.') for part in file_path.parts):
                    continue
                    
                # Skip node_modules, dist, etc.
                skip_dirs = {'node_modules', 'dist', 'build', '.git', '__pycache__'}
                if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                    continue
                
                self.convert_file(file_path, dry_run=dry_run)
        
        self.print_stats()
    
    def print_stats(self) -> None:
        """Print conversion statistics"""
        print("\n" + "="*60)
        print("Namespace Conversion Statistics")
        print("="*60)
        print(f"Files scanned:      {self.stats['files_scanned']}")
        print(f"Files converted:    {self.stats['files_converted']}")
        print(f"Replacements made:  {self.stats['replacements_made']}")
        print(f"Errors:             {self.stats['errors']}")
        print("="*60 + "\n")
    
    def validate_conversion(self, file_path: Path) -> Dict[str, any]:
        """
        Validate a converted file
        
        Returns:
            Dictionary with validation results
        """
        results = {
            "file": str(file_path),
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for legacy namespaces
            migration = self.config.get("migration", {})
            legacy_namespaces = migration.get("legacy_namespaces", [])
            
            for legacy_ns in legacy_namespaces:
                if legacy_ns in content:
                    results["issues"].append(f"Legacy namespace '{legacy_ns}' still present")
                    results["valid"] = False
            
            # Check for correct primary namespace
            primary_ns = self.config.get("namespace", {}).get("primary", "")
            if primary_ns and primary_ns not in content:
                # This is just a warning, not an error
                results["warnings"].append(f"Primary namespace '{primary_ns}' not found")
            
        except Exception as e:
            results["valid"] = False
            results["issues"].append(f"Validation error: {e}")
        
        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Convert namespaces to MachineNativeOps standard"
    )
    parser.add_argument(
        "--config",
        default="mno-namespace.yaml",
        help="Path to namespace configuration file"
    )
    parser.add_argument(
        "--input",
        help="Input file to convert"
    )
    parser.add_argument(
        "--output",
        help="Output file (default: overwrite input)"
    )
    parser.add_argument(
        "--scan",
        help="Scan and convert all files in directory"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without writing"
    )
    parser.add_argument(
        "--validate",
        help="Validate a converted file"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Initialize converter
    converter = NamespaceConverter(config_path=args.config)
    
    # Execute requested operation
    if args.validate:
        results = converter.validate_conversion(Path(args.validate))
        print(f"\nValidation results for {results['file']}:")
        print(f"Valid: {results['valid']}")
        if results['issues']:
            print("\nIssues:")
            for issue in results['issues']:
                print(f"  - {issue}")
        if results['warnings']:
            print("\nWarnings:")
            for warning in results['warnings']:
                print(f"  - {warning}")
        sys.exit(0 if results['valid'] else 1)
    
    elif args.scan:
        converter.scan_directory(Path(args.scan), dry_run=args.dry_run)
    
    elif args.input:
        input_path = Path(args.input)
        output_path = Path(args.output) if args.output else None
        
        if converter.convert_file(input_path, output_path, dry_run=args.dry_run):
            print(f"\n✅ Conversion complete!")
            if args.dry_run:
                print("(Dry run - no files were modified)")
        else:
            print("\nℹ️  No changes needed")
        
        converter.print_stats()
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
