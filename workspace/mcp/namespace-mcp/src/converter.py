#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MachineNativeOps 命名空間 MCP 轉換器
版本: 1.0.0
描述: 六層治理對齊的開源專案自動轉換核心引擎
"""

import os
import re
import json
import yaml
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MachineNativeOps.Converter')


@dataclass
class ConversionRule:
    """轉換規則數據結構"""
    name: str
    pattern: str
    replacement: str
    file_types: List[str]
    context: str
    priority: int
    description: str


@dataclass
class ConversionResult:
    """轉換結果數據結構"""
    layer: str
    files_processed: int
    changes_made: int
    success: bool
    details: Dict[str, Any]
    timestamp: str


class MachineNativeConverter:
    """MachineNativeOps 核心轉換器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化轉換器"""
        self.config = self._load_config(config_path)
        self.mcp_rules = self._load_mcp_rules()
        self.governance_rules = self._load_governance_rules()
        self.conversion_rules = self._build_conversion_rules()
        self.ssot_registry = {}
        
        logger.info("MachineNativeOps 轉換器初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加載配置文件"""
        default_path = Path(__file__).parent.parent / "config" / "conversion.yaml"
        config_file = Path(config_path) if config_path else default_path
        
        if not config_file.exists():
            logger.warning(f"配置文件不存在: {config_file}，使用默認配置")
            return self._get_default_config()
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"成功加載配置: {config_file}")
                return config
        except Exception as e:
            logger.error(f"加載配置失敗: {e}")
            return self._get_default_config()
    
    def _load_mcp_rules(self) -> Dict[str, Any]:
        """加載 MCP 規則"""
        mcp_rules_path = Path(__file__).parent.parent / "config" / "mcp-rules.yaml"
        
        if not mcp_rules_path.exists():
            logger.warning("MCP 規則文件不存在，使用默認規則")
            return {}
        
        try:
            with open(mcp_rules_path, 'r', encoding='utf-8') as f:
                rules = yaml.safe_load(f)
                logger.info("成功加載 MCP 規則")
                return rules
        except Exception as e:
            logger.error(f"加載 MCP 規則失敗: {e}")
            return {}
    
    def _load_governance_rules(self) -> Dict[str, Any]:
        """加載治理規則"""
        governance_path = Path(__file__).parent.parent / "config" / "governance.yaml"
        
        if not governance_path.exists():
            logger.warning("治理規則文件不存在，使用默認規則")
            return {}
        
        try:
            with open(governance_path, 'r', encoding='utf-8') as f:
                rules = yaml.safe_load(f)
                logger.info("成功加載治理規則")
                return rules
        except Exception as e:
            logger.error(f"加載治理規則失敗: {e}")
            return {}
    
    def _get_default_config(self) -> Dict[str, Any]:
        """獲取默認配置"""
        return {
            "enterprise": {
                "prefix": "machine-native",
                "namespace": "mnops",
                "domain": "machinenativeops.com"
            },
            "file_types": {
                "source_code": [".py", ".js", ".ts", ".java", ".go"],
                "config_files": [".json", ".yaml", ".yml"],
                "documentation": [".md", ".rst", ".txt"]
            }
        }
    
    def _build_conversion_rules(self) -> Dict[str, List[ConversionRule]]:
        """構建轉換規則"""
        rules = {
            "namespace": self._build_namespace_rules(),
            "dependency": self._build_dependency_rules(),
            "reference": self._build_reference_rules(),
            "structure": self._build_structure_rules(),
            "semantic": self._build_semantic_rules(),
            "governance": self._build_governance_rules()
        }
        
        logger.info(f"構建了 {sum(len(r) for r in rules.values())} 條轉換規則")
        return rules
    
    def _build_namespace_rules(self) -> List[ConversionRule]:
        """構建命名空間規則"""
        return [
            ConversionRule(
                name="class_naming",
                pattern=r'class\s+([A-Z][a-zA-Z0-9_]*)',
                replacement=r'class MachineNative\1',
                file_types=["source_code"],
                context="class_names",
                priority=100,
                description="類名添加 MachineNative 前綴"
            ),
            ConversionRule(
                name="method_naming",
                pattern=r'def\s+([a-z][a-zA-Z0-9_]*)\s*\(',
                replacement=r'def mnops_\1(',
                file_types=["source_code"],
                context="method_names",
                priority=95,
                description="方法名添加 mnops_ 前綴"
            ),
            ConversionRule(
                name="constant_naming",
                pattern=r'\b([A-Z][A-Z0-9_]+)\s*=',
                replacement=r'MNOPS_\1 =',
                file_types=["source_code"],
                context="constant_names",
                priority=90,
                description="常量名添加 MNOPS_ 前綴"
            )
        ]
    
    def _build_dependency_rules(self) -> List[ConversionRule]:
        """構建依賴規則 - v2.0 增強版：支援裸導入和字串導入"""
        dependency_mapping = self.config.get("dependency_mapping", {})
        rules = []
        
        for lang, mappings in dependency_mapping.items():
            for old_dep, new_dep in mappings.items():
                # 轉義特殊字符
                escaped_old = re.escape(old_dep)
                
                # 規則 1: 字串形式的依賴 (如 "django", 'flask')
                rules.append(ConversionRule(
                    name=f"dependency_{lang}_{old_dep}_string",
                    pattern=f'["\']({escaped_old})["\']',
                    replacement=f'"{new_dep}"',
                    file_types=["source_code", "config_files"],
                    context=f"{lang}_dependencies_string",
                    priority=90,
                    description=f"替換字串依賴 {old_dep} 為 {new_dep}"
                ))
                
                # 規則 2: Python 裸導入 (import django, from flask import)
                if lang == "python":
                    module_name = new_dep.replace("-", "_")
                    # 支援星號與逗號分隔的匯入項目（含括號形式）
                    from_import_targets = r'(?:\((?:[a-zA-Z_]\w*(?:\s*,\s*[a-zA-Z_]\w*)*|\*)\s*\)|(?:[a-zA-Z_]\w*(?:\s*,\s*[a-zA-Z_]\w*)*|\*))'
                    # import django
                    rules.append(ConversionRule(
                        name=f"dependency_{lang}_{old_dep}_bare_import",
                        pattern=f'\\bimport\\s+{escaped_old}\\b',
                        replacement=f'import {module_name}  # namespace-mcp: {new_dep}',
                        file_types=["source_code"],
                        context=f"{lang}_dependencies_bare",
                        priority=95,
                        description=f"替換裸導入 import {old_dep}"
                    ))
                    
                    # from django import
                    rules.append(ConversionRule(
                        name=f"dependency_{lang}_{old_dep}_from_import",
                        pattern=f'\\bfrom\\s+{escaped_old}\\s+import\\s+({from_import_targets})',
                        replacement=f'from {module_name} import \\1  # namespace-mcp: {new_dep}',
                        file_types=["source_code"],
                        context=f"{lang}_dependencies_from",
                        priority=95,
                        description=f"替換 from {old_dep} import"
                    ))
                
                # 規則 3: JavaScript require/import
                if lang == "javascript":
                    # require('express')
                    rules.append(ConversionRule(
                        name=f"dependency_{lang}_{old_dep}_require",
                        pattern=f'require\\(["\']({escaped_old})["\']\\)',
                        replacement=f'require("{new_dep}")',
                        file_types=["source_code"],
                        context=f"{lang}_dependencies_require",
                        priority=95,
                        description=f"替換 require('{old_dep}')"
                    ))
                    
                    # import express from 'express'
                    rules.append(ConversionRule(
                        name=f"dependency_{lang}_{old_dep}_import",
                        pattern=f'from\\s+["\']({escaped_old})["\']',
                        replacement=f'from "{new_dep}"',
                        file_types=["source_code"],
                        context=f"{lang}_dependencies_import",
                        priority=95,
                        description=f"替換 from '{old_dep}'"
                    ))
        
        return rules
    
    def _build_reference_rules(self) -> List[ConversionRule]:
        """構建引用規則"""
        return [
            ConversionRule(
                name="python_import",
                pattern=r'from\s+([.\w]+)\s+import',
                replacement=r'from machine_native.\1 import',
                file_types=["source_code"],
                context="python_imports",
                priority=80,
                description="Python 導入語句標準化"
            ),
            ConversionRule(
                name="javascript_require",
                pattern=r'require\(["\']([^"\']+)["\']\)',
                replacement=r'require("machine-native/\1")',
                file_types=["source_code"],
                context="javascript_requires",
                priority=75,
                description="JavaScript require 語句標準化"
            )
        ]
    
    def _build_structure_rules(self) -> List[ConversionRule]:
        """構建結構規則"""
        return [
            ConversionRule(
                name="source_directory",
                pattern=r'^src/',
                replacement='lib/',
                file_types=["all"],
                context="directory_structure",
                priority=70,
                description="源代碼目錄重命名"
            ),
            ConversionRule(
                name="docs_directory",
                pattern=r'^docs/',
                replacement='documentation/',
                file_types=["all"],
                context="directory_structure",
                priority=65,
                description="文檔目錄重命名"
            )
        ]
    
    def _build_semantic_rules(self) -> List[ConversionRule]:
        """構建語意規則"""
        return [
            ConversionRule(
                name="semantic_naming",
                pattern=r'\b(process|handle|execute)([A-Z][a-zA-Z0-9]*)',
                replacement=r'mnops_\1_\2',
                file_types=["source_code"],
                context="semantic_methods",
                priority=60,
                description="語意方法名標準化"
            )
        ]
    
    def _build_governance_rules(self) -> List[ConversionRule]:
        """構建治理規則"""
        license_header = self.governance_rules.get("license", {}).get("header_template", "")
        
        return [
            ConversionRule(
                name="license_conversion",
                pattern=r'license\s*[:=]\s*["\']([^"\']+)["\']',
                replacement='license: "MachineNativeOps Enterprise License v1.0"',
                file_types=["config_files"],
                context="license_update",
                priority=100,
                description="許可證轉換"
            ),
            ConversionRule(
                name="copyright_header",
                pattern=r'^(#!/[^\n]*\n)?',
                replacement=f'\\1{license_header}\n\n',
                file_types=["source_code"],
                context="copyright_header",
                priority=95,
                description="添加版權頭"
            )
        ]
    
    def convert_project(self, source_path: str, target_path: str) -> Dict[str, ConversionResult]:
        """執行專案轉換"""
        logger.info(f"開始轉換專案: {source_path} → {target_path}")
        
        source_dir = Path(source_path)
        target_dir = Path(target_path)
        
        if not source_dir.exists():
            raise ValueError(f"源專案路徑不存在: {source_path}")
        
        # 創建目標目錄
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 複製專案結構
        self._copy_project_structure(source_dir, target_dir)
        
        # 執行六層轉換
        results = {}
        layers = ["namespace", "dependency", "reference", "structure", "semantic", "governance"]
        
        for layer in layers:
            logger.info(f"執行 {layer} 層轉換...")
            results[layer] = self._apply_layer_conversion(layer, target_dir)
        
        # 生成轉換報告
        self._generate_conversion_report(results, target_dir)
        
        logger.info("專案轉換完成")
        return results
    
    def _copy_project_structure(self, source: Path, target: Path):
        """複製專案結構"""
        import shutil
        
        if target.exists():
            shutil.rmtree(target)
        
        ignore_patterns = shutil.ignore_patterns(
            '.git', '.svn', '.DS_Store', '__pycache__', 'node_modules',
            '*.pyc', '*.class', '*.jar', '.idea', '.vscode'
        )
        
        shutil.copytree(source, target, ignore=ignore_patterns)
        logger.info(f"專案結構已複製: {source} → {target}")
    
    def _apply_layer_conversion(self, layer: str, target_dir: Path) -> ConversionResult:
        """應用層級轉換"""
        rules = self.conversion_rules.get(layer, [])
        files_processed = 0
        changes_made = 0
        details = {}
        
        for rule in rules:
            try:
                rule_changes = self._apply_conversion_rule(rule, target_dir)
                changes_made += rule_changes
                details[rule.context] = rule_changes
                logger.debug(f"規則 {rule.name} 應用完成，變更數: {rule_changes}")
            except Exception as e:
                logger.error(f"規則 {rule.name} 應用失敗: {e}")
                details[rule.context] = {"error": str(e)}
        
        # 統計處理的文件數
        for root, _, files in os.walk(target_dir):
            files_processed += len(files)
        
        return ConversionResult(
            layer=layer,
            files_processed=files_processed,
            changes_made=changes_made,
            success=changes_made > 0,
            details=details,
            timestamp=datetime.now().isoformat()
        )
    
    def _apply_conversion_rule(self, rule: ConversionRule, target_dir: Path) -> int:
        """應用單個轉換規則"""
        changes_made = 0
        
        for root, _, files in os.walk(target_dir):
            for file in files:
                file_path = Path(root) / file
                
                # 檢查文件類型
                if not self._should_process_file(file_path, rule.file_types):
                    continue
                
                try:
                    # 讀取文件內容
                    content = file_path.read_text(encoding='utf-8')
                    
                    # 應用轉換規則
                    new_content, changes = self._apply_pattern_replacement(
                        content, rule.pattern, rule.replacement
                    )
                    
                    if changes > 0:
                        # 寫入轉換後內容
                        file_path.write_text(new_content, encoding='utf-8')
                        changes_made += changes
                        
                        # 記錄到 SSOT
                        self._register_ssot_change(
                            file_path, rule.context, changes, rule.priority / 100
                        )
                        
                        logger.debug(f"文件 {file_path} 轉換完成，變更數: {changes}")
                
                except Exception as e:
                    logger.warning(f"處理文件失敗 {file_path}: {e}")
                    continue
        
        return changes_made
    
    def _should_process_file(self, file_path: Path, allowed_types: List[str]) -> bool:
        """檢查是否應該處理文件"""
        if "all" in allowed_types:
            return True
        
        file_extension = file_path.suffix.lower()
        file_type_mapping = self.config.get("file_types", {})
        
        for file_type, extensions in file_type_mapping.items():
            if file_type in allowed_types and file_extension in extensions:
                return True
        
        return False
    
    def _apply_pattern_replacement(self, content: str, pattern: str, replacement: str) -> Tuple[str, int]:
        """應用模式替換"""
        new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
        return new_content, count
    
    def _register_ssot_change(self, file_path: Path, context: str, changes: int, confidence: float):
        """註冊 SSOT 變更"""
        file_key = str(file_path)
        if file_key not in self.ssot_registry:
            self.ssot_registry[file_key] = []
        
        self.ssot_registry[file_key].append({
            "context": context,
            "changes": changes,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "signature": self._generate_change_signature(file_path, context)
        })
    
    def _generate_change_signature(self, file_path: Path, context: str) -> str:
        """生成變更簽名"""
        data = f"{file_path}:{context}:{datetime.now().timestamp()}"
        return hashlib.sha3_512(data.encode()).hexdigest()
    
    def _generate_conversion_report(self, results: Dict[str, ConversionResult], target_dir: Path):
        """生成轉換報告"""
        report = {
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "source_project": str(target_dir),
            "slsa_level": "L3+",
            "conversion_results": {},
            "summary": {
                "total_files": sum(r.files_processed for r in results.values()),
                "total_changes": sum(r.changes_made for r in results.values()),
                "successful_layers": sum(1 for r in results.values() if r.success),
                "total_layers": len(results)
            },
            "ssot_hash": self._generate_ssot_hash()
        }
        
        for layer, result in results.items():
            report["conversion_results"][layer] = asdict(result)
        
        # 寫入 JSON 報告
        report_path = target_dir / "conversion-report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 生成 Markdown 報告
        self._generate_markdown_report(report, target_dir)
        
        logger.info(f"轉換報告已生成: {report_path}")
    
    def _generate_ssot_hash(self) -> str:
        """生成 SSOT 哈希"""
        ssot_data = json.dumps(self.ssot_registry, sort_keys=True)
        return hashlib.sha3_512(ssot_data.encode()).hexdigest()
    
    def _generate_markdown_report(self, report: Dict[str, Any], target_dir: Path):
        """生成 Markdown 報告"""
        md_content = [
            "# MachineNativeOps 專案轉換報告",
            "",
            "## 📊 轉換摘要",
            "",
            f"- **轉換版本**: `{report['version']}`",
            f"- **轉換時間**: `{report['timestamp']}`",
            f"- **目標專案**: `{report['source_project']}`",
            f"- **SLSA 等級**: `{report['slsa_level']}`",
            f"- **總文件數**: `{report['summary']['total_files']}`",
            f"- **總變更數**: `{report['summary']['total_changes']}`",
            f"- **成功層級**: `{report['summary']['successful_layers']}/{report['summary']['total_layers']}`",
            f"- **SSOT 哈希**: `{report['ssot_hash'][:32]}...`",
            "",
            "## 🎯 層級轉換結果",
            "",
            "| 治理層級 | 文件數 | 變更數 | 狀態 |",
            "|----------|--------|--------|------|"
        ]
        
        for layer, result in report["conversion_results"].items():
            status_icon = "✅" if result["success"] else "⚠️"
            md_content.append(
                f"| {layer} | {result['files_processed']} | {result['changes_made']} | {status_icon} |"
            )
        
        md_content.extend([
            "",
            "## 🔍 詳細結果",
            ""
        ])
        
        for layer, result in report["conversion_results"].items():
            md_content.append(f"### {layer.capitalize()} 層")
            md_content.append("")
            
            for context, details in result["details"].items():
                if isinstance(details, dict) and "error" in details:
                    md_content.append(f"- **{context}**: ❌ {details['error']}")
                else:
                    md_content.append(f"- **{context}**: {details} 處變更")
            md_content.append("")
        
        md_content.extend([
            "## 🔐 安全合規",
            "",
            f"- **SSOT 完整性**: `{report['ssot_hash'][:64]}...`",
            "- **審計跟踪**: 所有變更已記錄到 SSOT",
            f"- **合規等級**: `{report['slsa_level']}`",
            "",
            "---",
            f"*生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])
        
        report_path = target_dir / "CONVERSION-REPORT.md"
        report_path.write_text("\n".join(md_content), encoding='utf-8')
        
        logger.info(f"Markdown 報告已生成: {report_path}")


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MachineNativeOps 專案轉換器')
    parser.add_argument('source', nargs='?', help='源專案路徑')
    parser.add_argument('target', nargs='?', help='目標專案路徑')
    parser.add_argument('--config', '-c', help='配置文件路徑')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細輸出')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not args.source or not args.target:
        resolved_path = Path(__file__).resolve()
        repo_root: Optional[Path] = None
        for candidate in [resolved_path.parent] + list(resolved_path.parents):
            if (candidate / ".git").exists():
                repo_root = candidate
                break
        
        repo_root = repo_root or Path.cwd()
        default_target = repo_root / "outputs" / "namespace-mcp-scan"
        
        if not args.source:
            args.source = str(repo_root)
        if not args.target:
            args.target = str(default_target)
        
        logger.info(
            "未提供路徑，使用默認路徑: source=%s, target=%s",
            args.source,
            args.target,
        )
    
    try:
        converter = MachineNativeConverter(args.config)
        results = converter.convert_project(args.source, args.target)
        
        total_changes = sum(r.changes_made for r in results.values())
        successful_layers = sum(1 for r in results.values() if r.success)
        
        print(f"\n✅ 轉換完成!")
        print(f"📊 總變更數: {total_changes}")
        print(f"🎯 成功層級: {successful_layers}/{len(results)}")
        print(f"📝 報告文件: {args.target}/CONVERSION-REPORT.md")
        
    except Exception as e:
        logger.error(f"轉換過程出錯: {e}")
        print(f"❌ 轉換失敗: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
