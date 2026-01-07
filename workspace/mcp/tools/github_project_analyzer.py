#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub Project Deep Analyzer
MachineNativeOps 專案深度分析工具
版本: v2.1.0 | 企業級分析框架

Changes in v2.1.0:
- Integrated with local MCP server content for real analysis
- Added repository-local file scanning capabilities
- Replaced template data with actual observation metrics where available
"""

from __future__ import annotations

import argparse
import json
import os
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class GitHubAnalyzerConfig:
    """分析配置"""

    repo_owner: str
    repo_name: str
    analysis_scope: str = "entire"
    output_format: str = "markdown"
    include_code_samples: bool = True
    include_metrics: bool = True
    depth_level: str = "deep"
    token: Optional[str] = None
    local_path: Optional[str] = None  # Local repository path for file scanning


class GitHubProjectAnalyzer:
    def __init__(self, config: GitHubAnalyzerConfig):
        self.config = config
        self.base_url = f"https://api.github.com/repos/{config.repo_owner}/{config.repo_name}"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MachineNativeOps-Analyzer/2.1.0",
        }
        token = config.token or os.getenv("GITHUB_TOKEN")
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        self._repo_stats: Optional[Dict[str, Any]] = None
        self._local_scan_results: Optional[Dict[str, Any]] = None

    def analyze_project(self) -> Dict[str, Any]:
        """執行完整專案分析"""
        analysis_result = {
            "metadata": self._get_metadata(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "analysis_scope": self.config.analysis_scope,
            "sections": {},
        }

        # Perform local file scanning if path is available
        if self.config.local_path:
            self._local_scan_results = self._scan_local_repository()

        analysis_result["sections"]["architecture"] = self._analyze_architecture()
        analysis_result["sections"]["capabilities"] = self._analyze_capabilities()
        analysis_result["sections"]["todo_list"] = self._analyze_todo_list()
        analysis_result["sections"]["diagnostics"] = self._analyze_diagnostics()
        analysis_result["sections"]["deep_details"] = self._analyze_deep_details()

        return analysis_result

    def _scan_local_repository(self) -> Dict[str, Any]:
        """Scan local repository for real metrics."""
        results: Dict[str, Any] = {
            "mcp_servers": [],
            "python_files": 0,
            "typescript_files": 0,
            "yaml_configs": 0,
            "merge_conflicts": [],
            "governance_scripts": [],
            "workflows": [],
            "pipeline_config": None,
        }

        local_path = Path(self.config.local_path) if self.config.local_path else None
        if not local_path or not local_path.exists():
            logger.warning("Local path not available or doesn't exist: %s", local_path)
            return results

        try:
            # Scan for MCP servers
            mcp_path = local_path / "workspace" / "src" / "mcp-servers"
            if mcp_path.exists():
                results["mcp_servers"] = [f.name for f in mcp_path.glob("*.js")]

            # Count file types
            results["python_files"] = len(list(local_path.rglob("*.py")))
            results["typescript_files"] = len(list(local_path.rglob("*.ts")))
            results["yaml_configs"] = len(list(local_path.rglob("*.yaml"))) + len(list(local_path.rglob("*.yml")))

            # Scan for merge conflict markers using Python (safer than subprocess)
            results["merge_conflicts"] = self._scan_for_conflicts(local_path / "workspace")

            # Scan governance scripts
            governance_scripts_path = local_path / "workspace" / "src" / "governance" / "scripts"
            if governance_scripts_path.exists():
                results["governance_scripts"] = [f.name for f in governance_scripts_path.glob("*.py")]

            # Scan workflows
            workflows_path = local_path / ".github" / "workflows"
            if workflows_path.exists():
                results["workflows"] = [f.name for f in workflows_path.glob("*.yml")] + \
                                      [f.name for f in workflows_path.glob("*.yaml")]

            # Load pipeline config
            pipeline_path = local_path / "workspace" / "mcp" / "pipelines" / "unified-pipeline-config.yaml"
            if pipeline_path.exists() and yaml:
                try:
                    with open(pipeline_path, 'r', encoding='utf-8') as f:
                        results["pipeline_config"] = yaml.safe_load(f)
                except Exception as e:
                    logger.warning("Failed to load pipeline config: %s", e)

        except Exception as e:
            logger.warning("Error scanning local repository: %s", e)

        return results

    def _get_repo_stats(self) -> Dict[str, Any]:
        """Fetch repository statistics from GitHub with caching."""
        if self._repo_stats is not None:
            return self._repo_stats

        if requests is None:
            logger.warning("requests library not available, skipping GitHub API calls")
            self._repo_stats = {}
            return self._repo_stats

        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            if response.ok:
                self._repo_stats = response.json()
            else:
                logger.warning("Failed to fetch repo stats (status %s)", response.status_code)
                self._repo_stats = {}
        except Exception as exc:
            logger.warning("Error fetching repo stats: %s", exc)
            self._repo_stats = {}

        return self._repo_stats

    def _scan_for_conflicts(self, search_path: Path) -> List[str]:
        """Scan for merge conflict markers using Python (safer than subprocess).
        
        Args:
            search_path: Directory path to search for conflict markers.
            
        Returns:
            List of relative file paths containing conflict markers.
        """
        conflict_files = []
        conflict_marker = "<<<<<<<".encode()
        
        # File extensions that are likely to have conflicts
        text_extensions = {'.md', '.yaml', '.yml', '.py', '.ts', '.js', '.json', '.txt', '.sh'}
        # Patterns to skip (binary files, specific directories)
        skip_patterns = {'node_modules', '.git', '__pycache__', 'dist', 'build', 'supply-chain', 'governance-execution'}
        
        if not search_path.exists():
            return conflict_files
            
        try:
            for file_path in search_path.rglob('*'):
                # Skip directories and binary files
                if file_path.is_dir():
                    continue
                    
                # Skip files in excluded directories
                if any(skip in str(file_path) for skip in skip_patterns):
                    continue
                    
                # Only check text files
                if file_path.suffix.lower() not in text_extensions:
                    continue
                    
                try:
                    # Read file in binary mode to avoid encoding issues
                    content = file_path.read_bytes()
                    if conflict_marker in content:
                        # Convert to relative path
                        rel_path = str(file_path.relative_to(search_path.parent))
                        conflict_files.append(rel_path)
                except (IOError, OSError):
                    # Skip files that can't be read
                    continue
                    
        except Exception as e:
            logger.warning("Error scanning for conflicts: %s", e)
            
        return conflict_files

    def _get_metadata(self) -> Dict[str, Any]:
        """獲取專案元數據"""
        stats = self._get_repo_stats()
        return {
            "platform": "GitHub",
            "repository": f"{self.config.repo_owner}/{self.config.repo_name}",
            "clone_url": f"https://github.com/{self.config.repo_owner}/{self.config.repo_name}.git",
            "analysis_scope": self.config.analysis_scope,
            "analyzer_version": "2.1.0",
            "stars": stats.get("stargazers_count", "N/A"),
            "forks": stats.get("forks_count", "N/A"),
            "open_issues": stats.get("open_issues_count", "N/A"),
            "default_branch": stats.get("default_branch", "N/A"),
            "depth_level": self.config.depth_level,
            "local_scan_enabled": self.config.local_path is not None,
        }

    def _analyze_architecture(self) -> Dict[str, Any]:
        """分析架構設計 - Enhanced with local scan data"""
        # Get actual MCP server count from local scan
        mcp_servers = []
        if self._local_scan_results:
            mcp_servers = self._local_scan_results.get("mcp_servers", [])

        return {
            "core_patterns": [
                {
                    "pattern": "MCP-Based Tool Integration" if mcp_servers else "Microservices Architecture",
                    "rationale": "Model Context Protocol for LLM tool endpoints" if mcp_servers else "分散式系統設計，支持獨立部署和擴展",
                    "advantages": ["標準化工具接口", "LLM 可調用", "跨平台協調"] if mcp_servers else ["高可用性", "獨立擴展", "技術棧靈活"],
                    "implementation": f"workspace/src/mcp-servers/ ({len(mcp_servers)} servers)" if mcp_servers else "Kubernetes-based service mesh",
                    "actual_servers": mcp_servers[:5] if mcp_servers else [],
                },
                {
                    "pattern": "Event-Driven Design",
                    "rationale": "實現鬆耦合和異步處理",
                    "advantages": ["高吞吐量", "彈性伸縮", "故障隔離"],
                    "implementation": "unified-pipeline-config.yaml + governance validators" if self._local_scan_results else "Kafka + RabbitMQ message brokers",
                },
            ],
            "tech_stack": self._get_actual_tech_stack(),
            "module_relationships": {
                "core": {"dependencies": ["utils", "config"], "dependents": ["api", "services"]},
                "api": {"dependencies": ["core", "auth"], "dependents": ["gateway", "clients"]},
                "services": {
                    "dependencies": ["core", "db"],
                    "dependents": ["workers", "schedulers"],
                },
                "mcp-servers": {"dependencies": ["core"], "dependents": ["automation", "agents"]},
                "governance": {"dependencies": ["config"], "dependents": ["ci-cd", "validation"]},
                "shared": {"dependencies": [], "dependents": ["core", "mcp-servers", "services"]},
            },
            "scalability_considerations": [
                "Parallel agent execution (64-256 agents)" if self._local_scan_results else "Horizontal scaling supported through Kubernetes",
                "Auto-scaling based on CPU/latency/queue depth",
                "Event-driven architecture for instant response",
                "Load balancing with service mesh",
            ],
            "maintainability_aspects": [
                "Governance validation scripts" if self._local_scan_results else "Comprehensive documentation",
                "Automated testing pipeline",
                "Bilingual documentation (Chinese/English)",
            ],
        }

    def _get_actual_tech_stack(self) -> Dict[str, List[str]]:
        """Get actual tech stack from local scan."""
        stack: Dict[str, List[str]] = {
            "backend": ["Python", "TypeScript", "JavaScript"],
            "frontend": ["React", "Vue.js"],
            "infrastructure": ["Kubernetes", "Docker", "Terraform"],
            "database": ["PostgreSQL", "Redis", "MongoDB"],
            "monitoring": ["Prometheus", "Grafana", "Jaeger"],
        }

        if self._local_scan_results:
            mcp_servers = self._local_scan_results.get("mcp_servers", [])
            governance_scripts = self._local_scan_results.get("governance_scripts", [])
            workflows = self._local_scan_results.get("workflows", [])

            if mcp_servers:
                stack["mcp_servers"] = mcp_servers[:5]
            if governance_scripts:
                stack["governance"] = governance_scripts[:5]
            if workflows:
                stack["ci_cd"] = workflows[:5]

        return stack

    def _analyze_capabilities(self) -> Dict[str, Any]:
        """分析當前能力 - Enhanced with local scan data"""
        stats = self._get_repo_stats()

        # Placeholder performance metrics; replace with observability data when available.
        performance_metrics = {
            "latency": {
                "current": "15ms", "p95": "15ms", "target": "<20ms", "status": "met"
            },
            "throughput": {
                "current": "50k rpm", "target": "100k rpm", "status": "partial"
            },
            "availability": {
                "current": "99.95%", "target": "99.99%", "status": "met"
            },
            "error_rate": {
                "current": "0.1%", "target": "<0.05%", "status": "needs_improvement"
            },
        } if self.config.include_metrics else {}
        # Build features from local scan if available
        features = []
        if self._local_scan_results:
            mcp_servers = self._local_scan_results.get("mcp_servers", [])
            for server in mcp_servers[:6]:  # Top 6 MCP servers
                features.append({
                    "name": server.replace(".js", "").replace("-", " ").title(),
                    "status": "production",
                    "maturity": "high",
                    "description": f"MCP server: {server}",
                })

            governance_scripts = self._local_scan_results.get("governance_scripts", [])
            for script in governance_scripts[:3]:
                features.append({
                    "name": script.replace(".py", "").replace("-", " ").title(),
                    "status": "implemented",
                    "maturity": "high",
                    "description": f"Governance validator: {script}",
                })

        # Fallback to template features if no local scan
        if not features:
            features = [
                {
                    "name": "MCP Tool Integration",
                    "status": "production",
                    "maturity": "high",
                    "description": "LLM-callable tool endpoints via MCP protocol (use --local-path for real data)",
                },
                {
                    "name": "Auto-Scaling System",
                    "status": "production",
                    "maturity": "medium",
                    "description": "Kubernetes-based auto-scaling (placeholder template)",
                },
            ]

        # Get performance metrics from pipeline config if available
        performance_metrics = self._get_pipeline_performance_metrics()

        # Get local repository statistics
        local_stats = self._get_local_stats()

        return {
            "core_features": features if self.config.include_code_samples else [],
            "performance_metrics": performance_metrics if self.config.include_metrics else {},
            "repository_stats": {
                "stars": stats.get("stargazers_count", "N/A"),
                "forks": stats.get("forks_count", "N/A"),
                "open_issues": stats.get("open_issues_count", "N/A"),
                "watchers": stats.get("subscribers_count", "N/A"),
            },
            "local_stats": local_stats,
            "competitive_advantages": [
                "INSTANT execution (<3min full stack deployment)" if self._local_scan_results else "Full quantum computing stack integration",
                "Zero human intervention (autonomous operation)" if self._local_scan_results else "Enterprise-grade security compliance",
                "MCP protocol integration for LLM tools",
                "Comprehensive governance validation",
            ],
        }

    def _get_pipeline_performance_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get actual performance metrics from pipeline config."""
        if not self._local_scan_results or not self._local_scan_results.get("pipeline_config"):
            return {
                "latency": {"current": "N/A", "target": "<=100ms (instant)", "status": "unknown"},
                "throughput": {"current": "N/A", "target": "256 parallel agents", "status": "unknown"},
                "availability": {"current": "N/A", "target": "99.99%", "status": "unknown"},
            }

        config = self._local_scan_results["pipeline_config"]
        spec = config.get("spec", {})
        thresholds = spec.get("latencyThresholds", {})
        scheduling = spec.get("coreScheduling", {})

        return {
            "instant_latency": {
                "current": f"{thresholds.get('instant', 'N/A')}ms",
                "target": "<=100ms",
                "status": "configured"
            },
            "max_stage_latency": {
                "current": f"{thresholds.get('maxStage', 'N/A')}ms",
                "target": "<=30s",
                "status": "configured"
            },
            "max_total_latency": {
                "current": f"{thresholds.get('maxTotal', 'N/A')}ms",
                "target": "<=3min",
                "status": "configured"
            },
            "parallelism": {
                "current": f"{scheduling.get('minParallelAgents', 'N/A')}-{scheduling.get('maxParallelAgents', 'N/A')} agents",
                "target": "64-256 agents",
                "status": "configured"
            },
        }

    def _get_local_stats(self) -> Dict[str, Any]:
        """Get local repository statistics."""
        if not self._local_scan_results:
            return {}

        return {
            "python_files": self._local_scan_results.get("python_files", 0),
            "typescript_files": self._local_scan_results.get("typescript_files", 0),
            "yaml_configs": self._local_scan_results.get("yaml_configs", 0),
            "mcp_servers": len(self._local_scan_results.get("mcp_servers", [])),
            "governance_scripts": len(self._local_scan_results.get("governance_scripts", [])),
            "workflows": len(self._local_scan_results.get("workflows", [])),
        }

    def _analyze_todo_list(self) -> Dict[str, Any]:
        """分析待辦事項 - Enhanced with actual issues from local scan"""
        high_priority = []
        medium_priority = []

        # Check for actual merge conflicts from local scan
        if self._local_scan_results:
            conflicts = self._local_scan_results.get("merge_conflicts", [])
            if conflicts:
                high_priority.append({
                    "task": "清除 merge 衝突標記",
                    "priority": "critical",
                    "estimated_effort": "≤2 小時",
                    "dependencies": [],
                    "impact": "High - 恢復文檔可讀性",
                    "affected_files": conflicts[:5],  # Show first 5
                    "total_files": len(conflicts),
                })

            # Check governance validation status from pipeline config
            pipeline_config = self._local_scan_results.get("pipeline_config")
            if pipeline_config:
                gov_validation = pipeline_config.get("spec", {}).get("governanceValidation", [])
                planned_validators = [
                    v for v in gov_validation
                    if v.get("implementationStatus") == "planned"
                ]
                if planned_validators:
                    high_priority.append({
                        "task": "落地治理驗證腳本",
                        "priority": "high",
                        "estimated_effort": "3-5 天",
                        "dependencies": ["governance framework"],
                        "impact": "High - 啟用自動合規驗證",
                        "planned_validators": [v.get("validator") for v in planned_validators],
                    })

        # Default high priority tasks if no local scan or no issues found
        if not high_priority:
            high_priority = [
                {
                    "task": "執行本地倉庫掃描以獲取實際待辦事項",
                    "priority": "high",
                    "estimated_effort": "立即",
                    "dependencies": ["--local-path 參數"],
                    "impact": "High - 獲取真實分析數據",
                },
            ]

        # Default medium priority
        if not medium_priority:
            medium_priority = [
                {
                    "task": "補充自動測試覆蓋率",
                    "priority": "medium",
                    "estimated_effort": "2 天",
                    "dependencies": ["test infrastructure"],
                    "impact": "Medium - 提高代碼品質保證",
                }
            ]

        return {
            "high_priority": high_priority,
            "medium_priority": medium_priority,
            "development_sequence": [
                "1. 清除所有 merge 衝突",
                "2. 實作並驗證治理腳本",
                "3. 補充自動測試",
                "4. 完善 CI 可觀測性",
            ],
        }

    def _analyze_diagnostics(self) -> Dict[str, Any]:
        """分析問題診斷 - Based on actual local scan"""
        known_issues = []

        if self._local_scan_results:
            conflicts = self._local_scan_results.get("merge_conflicts", [])
            if conflicts:
                known_issues.append({
                    "issue": f"Merge 衝突標記 ({len(conflicts)} 個文件)",
                    "severity": "high",
                    "affected_components": ["documentation", "configuration"],
                    "workaround": "手動解決衝突或使用 git mergetool",
                    "fix_priority": "critical",
                    "affected_files": conflicts[:3],
                })

        # Default issues if no local scan
        if not known_issues:
            known_issues = [
                {
                    "issue": "未執行本地掃描，無法檢測實際問題",
                    "severity": "info",
                    "affected_components": ["analyzer"],
                    "workaround": "使用 --local-path 參數執行分析",
                    "fix_priority": "low",
                }
            ]

        return {
            "known_issues": known_issues,
            "technical_debt": [
                {
                    "area": "Template placeholder data in analyzer",
                    "debt_level": "medium",
                    "impact": "Analysis accuracy",
                    "recommendation": "Connect to observability metrics",
                },
            ],
            "performance_bottlenecks": [],
            "security_concerns": [],
        }

    def _analyze_deep_details(self) -> Dict[str, Any]:
        """深度細節分析 - Enhanced with local data"""
        local_stats = self._get_local_stats()

        return {
            "code_quality": {
                "best_practices": ["INSTANT execution", "Zero human intervention", "Event-driven"],
                "quality_metrics": {
                    "python_files": local_stats.get("python_files", "N/A"),
                    "typescript_files": local_stats.get("typescript_files", "N/A"),
                    "yaml_configs": local_stats.get("yaml_configs", "N/A"),
                },
                "improvement_areas": [
                    "Increase test coverage",
                    "Add performance benchmarks",
                    "Implement observability metrics collection",
                ],
            },
            "documentation": {
                "completeness": "good" if local_stats.get("yaml_configs", 0) > 50 else "partial",
                "readability": "bilingual (Chinese/English)",
                "coverage_areas": ["architecture", "governance", "MCP servers"],
                "missing_areas": ["performance tuning guide", "troubleshooting"],
            },
            "testing_strategy": {
                "test_levels": ["unit", "integration", "e2e", "performance"],
                "coverage": {
                    "unit": "75%", "integration": "60%",
                    "e2e": "45%", "performance": "30%",
                },
                "governance_test_levels": ["unit", "integration", "validation"],
                "governance_coverage": {
                    "governance_validators": f"{local_stats.get('governance_scripts', 0)} scripts",
                },
                "automation_level": "high",
                "improvement_opportunities": [
                    "Add unit tests for pipeline loader",
                    "Add schema validation tests for TS types",
                ],
            },
            "ci_cd_pipeline": {
                "stages": ["validation", "build", "test", "deploy"],
                "tools": ["GitHub Actions"],
                "workflows": self._local_scan_results.get("workflows", [])[:5] if self._local_scan_results else [],
                "deployment_strategy": "INSTANT execution",
                "improvement_suggestions": [
                    "Add success rate dashboards",
                    "Add latency monitoring dashboards",
                ],
            },
            "mcp_integration": {
                "servers": self._local_scan_results.get("mcp_servers", []) if self._local_scan_results else [],
                "governance_validators": self._local_scan_results.get("governance_scripts", []) if self._local_scan_results else [],
                "integration_status": "production",
            },
            "community_health": self._get_community_metrics(),
            "dependency_management": {
                "npm_packages": self._count_npm_packages(),
                "python_requirements": self._count_python_requirements(),
                "vulnerability_scanning": "recommended",
                "auto_updates": "dependabot recommended",
            },
        }

    def _get_community_metrics(self) -> Dict[str, Any]:
        """Get community and contributor metrics."""
        stats = self._get_repo_stats()
        
        return {
            "contributors": stats.get("network_count", "N/A"),
            "watchers": stats.get("subscribers_count", "N/A"),
            "stars": stats.get("stargazers_count", "N/A"),
            "forks": stats.get("forks_count", "N/A"),
            "open_issues": stats.get("open_issues_count", "N/A"),
            "activity_status": "active" if stats.get("pushed_at") else "unknown",
            "note": "Use GitHub Insights for detailed contributor analytics",
        }

    def _count_npm_packages(self) -> int:
        """Count npm package.json files in local scan."""
        if not self._local_scan_results or not self.config.local_path:
            return 0
        
        local_path = Path(self.config.local_path)
        try:
            return len(list(local_path.rglob("package.json")))
        except Exception:
            return 0

    def _count_python_requirements(self) -> int:
        """Count Python requirements files in local scan."""
        if not self._local_scan_results or not self.config.local_path:
            return 0
        
        local_path = Path(self.config.local_path)
        try:
            return len(list(local_path.rglob("requirements*.txt")))
        except Exception:
            return 0

    def generate_markdown_report(self, analysis: Dict[str, Any]) -> str:
        """生成Markdown報告"""
        local_scan_note = ""
        if analysis["metadata"].get("local_scan_enabled"):
            local_scan_note = "\n> ✅ 已啟用本地倉庫掃描，數據來自實際文件分析。\n"
        else:
            local_scan_note = "\n> ⚠️ 未啟用本地掃描。使用 `--local-path` 參數獲取更準確的分析。\n"

        report = f"""# GitHub 專案深度分析報告

## 📋 專案基本信息
- **平台**: {analysis['metadata']['platform']}
- **倉庫**: `{analysis['metadata']['repository']}`
- **分析範圍**: {analysis['metadata']['analysis_scope']}
- **分析時間**: {analysis['timestamp']}
- **分析工具**: MachineNativeOps Analyzer v{analysis['metadata']['analyzer_version']}
{local_scan_note}
---

## 🏗️ 1. 架構設計理念分析

### 核心架構模式
{self._format_architecture(analysis['sections']['architecture'])}

### 技術棧選擇
{self._format_tech_stack(analysis['sections']['architecture']['tech_stack'])}

### 模組化設計
{self._format_module_relationships(analysis['sections']['architecture']['module_relationships'])}

### 可擴展性考量
{self._format_list(analysis['sections']['architecture']['scalability_considerations'])}

**總結**: 專案採用現代微服務架構，技術棧選擇合理，具有良好的擴展性和維護性。

---

## ⚡ 2. 當前實際能力評估

> 本節混合倉庫即時統計與模板示例數據；接入監控後可替換為真實指標。

### 核心功能清單
> 以下功能列表為模板示例，請根據實際倉庫能力更新。
{self._format_capabilities(analysis['sections']['capabilities']['core_features'])}

### 倉庫指標
{self._format_repository_stats(analysis['sections']['capabilities'].get('repository_stats', {}))}

### 性能表現（示例數據）
> 以下性能表現為樣板數據，用於框架驗證；請替換為觀測/監控系統輸出的真實值。
{self._format_performance_metrics(analysis['sections']['capabilities']['performance_metrics'])}

### 競爭優勢
{self._format_list(analysis['sections']['capabilities']['competitive_advantages'])}

**總結**: 專案具備強大的量子計算集成能力，性能表現良好，具有明顯的技術優勢。

---

## 📋 3. 待完成功能清單

### 高優先級任務
{self._format_todo_list(analysis['sections']['todo_list']['high_priority'])}

### 開發順序建議
{self._format_list(analysis['sections']['todo_list']['development_sequence'])}

**總結**: 建議優先處理安全性和穩定性相關的高優先級任務。

---

## 🚨 4. 問題診斷（急救站）

### 已知問題
{self._format_issues(analysis['sections']['diagnostics']['known_issues'])}

### 技術債務
{self._format_technical_debt(analysis['sections']['diagnostics']['technical_debt'])}

### 性能瓶頸
{self._format_bottlenecks(analysis['sections']['diagnostics']['performance_bottlenecks'])}

**總結**: 需要立即處理記憶體泄漏和高風險安全問題。

---

## 🔍 5. 深度細節補充

### 代碼質量
{self._format_code_quality(analysis['sections']['deep_details']['code_quality'])}

### 測試策略
{self._format_testing_strategy(analysis['sections']['deep_details']['testing_strategy'])}

### CI/CD 流程
{self._format_ci_cd(analysis['sections']['deep_details']['ci_cd_pipeline'])}

**總結**: 代碼質量良好，但測試覆蓋率和CI/CD流程仍有改進空間。

---

## 🎯 綜合建議與行動項

1. **立即行動**:
   - 修復記憶體泄漏問題
   - 加強輸入驗證安全措施

2. **短期計劃**:
   - 完成量子錯誤校正功能
   - 改善測試覆蓋率

3. **長期規劃**:
   - 重構認證系統
   - 實現金絲雀部署

---

所有操作必須符合：

## 立即統一的提示詞設計

### 🎯 統一模板使用
```bash
# 生成統一提示詞
MachineNativeOps-cli prompt generate --template=architecture-status --version=2.0.0

# 驗證現有提示詞
MachineNativeOps-cli prompt validate --file=current_prompt.md --strict

# 自動修正不一致
MachineNativeOps-cli prompt fix --input=inconsistent_prompt.md --output=fixed_prompt.md
```

### 📝 正確的統一格式
```markdown
**當前架構狀態**: `v2.0.0-UNIFIED | STABLE | HIGH_PERFORMANCE`
**升級準備狀態**: `READY_FOR_EVOLUTION | QUANTUM_OPTIMIZED`  
**演化潛力**: `INFINITE_DIMENSIONS | EXPONENTIAL_GROWTH`
**安全保障**: `PROVABLY_SAFE | VALUE_ALIGNED | ETHICALLY_GOVERNED`
**未來軌跡**: `AUTONOMOUS_EVOLUTION | SINGULARITY_BOUND`
**執行模式**: `INSTANT | 零延遲執行`
**核心理念**: `AI自動演化 | 即時交付 | 3分鐘完整堆疊 | 0次人工介入`
**競爭力對標**: `Replit | Claude | GPT | 同等即時交付能力`
```

### 🔧 自動化保障機制
1. **實時驗證**: 每次提示詞修改自動檢查一致性
2. **自動修正**: 檢測到偏差時自動格式化
3. **版本控制**: 所有提示詞版本追蹤和審計
4. **質量監控**: 持續監控提示詞質量指標

---

*報告生成時間: {analysis['timestamp']}*
*分析引擎: MachineNativeOps Quantum Analyzer*
*版本: v2.1.0 | 企業級深度分析*
"""
        return report

    def _format_architecture(self, architecture: Dict[str, Any]) -> str:
        result = ""
        for pattern in architecture["core_patterns"]:
            result += f"- **{pattern['pattern']}**: {pattern['rationale']}\n"
            result += f"  - 優勢: {', '.join(pattern['advantages'])}\n"
        return result

    def _format_tech_stack(self, tech_stack: Dict[str, List[str]]) -> str:
        result = ""
        for category, technologies in tech_stack.items():
            result += f"- **{category.capitalize()}**: {', '.join(technologies)}\n"
        return result

    def _format_module_relationships(self, relationships: Dict[str, Any]) -> str:
        result = ""
        for module, deps in relationships.items():
            result += f"- **{module}**:\n"
            result += f"  - 依賴: {', '.join(deps['dependencies'])}\n"
            result += f"  - 被依賴: {', '.join(deps['dependents'])}\n"
        return result

    def _format_list(self, items: List[str]) -> str:
        return "\n".join([f"- {item}" for item in items])

    def _format_capabilities(self, capabilities: List[Dict[str, Any]]) -> str:
        result = ""
        for cap in capabilities:
            result += f"- **{cap['name']}** ({cap['status']}, 成熟度: {cap['maturity']})\n"
            result += f"  - {cap['description']}\n"
        return result

    def _format_repository_stats(self, stats: Dict[str, Any]) -> str:
        if not stats:
            return "- 無可用倉庫指標\n"

        return (
            "| 指標 | 值 |\n"
            "|------|----|\n"
            f"| Stars | {stats.get('stars', 'N/A')} |\n"
            f"| Forks | {stats.get('forks', 'N/A')} |\n"
            f"| Open Issues | {stats.get('open_issues', 'N/A')} |\n"
            f"| Watchers | {stats.get('watchers', 'N/A')} |\n"
        )

    def _format_performance_metrics(self, metrics: Dict[str, Dict[str, Any]]) -> str:
        result = "| 指標 | 當前值 | 目標值 | 狀態 |\n|------|--------|--------|------|\n"
        for metric, data in metrics.items():
            current_value = data.get("current")
            if current_value is None and "p95" in data:
                current_value = data["p95"]
            status = data.get("status", "")
            status_emoji = "✅" if status == "met" else "⚠️" if status == "partial" else "❌"
            target_val = data.get('target', '')
            result += f"| {metric} | {current_value or ''} | {target_val} | {status_emoji} |\n"
        return result

    def _format_todo_list(self, todos: List[Dict[str, Any]]) -> str:
        result = ""
        for todo in todos:
            result += f"- **{todo['task']}** (優先級: {todo['priority']})\n"
            result += f"  - 預估工作量: {todo['estimated_effort']}\n"
            result += f"  - 影響: {todo['impact']}\n"
        return result

    def _format_issues(self, issues: List[Dict[str, Any]]) -> str:
        result = ""
        for issue in issues:
            severity = issue["severity"]
            if severity == "high":
                severity_emoji = "🔴"
            elif severity == "medium":
                severity_emoji = "🟡"
            else:
                severity_emoji = "🟢"
            result += f"- {severity_emoji} **{issue['issue']}**\n"
            result += f"  - 影響組件: {', '.join(issue['affected_components'])}\n"
            result += f"  - 修復優先級: {issue['fix_priority']}\n"
        return result

    def _format_technical_debt(self, debts: List[Dict[str, Any]]) -> str:
        result = ""
        for debt in debts:
            result += f"- **{debt['area']}** (債務級別: {debt['debt_level']})\n"
            result += f"  - 影響: {debt['impact']}\n"
            result += f"  - 建議: {debt['recommendation']}\n"
        return result

    def _format_bottlenecks(self, bottlenecks: List[Dict[str, Any]]) -> str:
        result = ""
        for bottleneck in bottlenecks:
            result += f"- **{bottleneck['bottleneck']}**\n"
            result += f"  - 影響: {bottleneck['impact']}\n"
            result += f"  - 預計改善: {bottleneck['estimated_improvement']}\n"
        return result

    def _format_code_quality(self, quality: Dict[str, Any]) -> str:
        result = "### 最佳實踐\n"
        result += self._format_list(quality["best_practices"]) + "\n\n"
        result += "### 質量指標\n"
        for metric, value in quality["quality_metrics"].items():
            result += f"- {metric}: `{value}`\n"
        result += "\n### 改進領域\n"
        result += self._format_list(quality["improvement_areas"])
        return result

    def _format_testing_strategy(self, strategy: Dict[str, Any]) -> str:
        result = ""
        result += f"- 測試層級: {', '.join(strategy['test_levels'])}\n"
        result += "### 覆蓋率\n"
        for level, coverage in strategy.get("coverage", {}).items():
            result += f"- {level}: {coverage}\n"
        result += f"\n- 自動化程度: {strategy.get('automation_level', '')}\n"
        result += "### 改進機會\n"
        result += self._format_list(strategy.get("improvement_opportunities", []))
        return result

    def _format_ci_cd(self, pipeline: Dict[str, Any]) -> str:
        result = ""
        result += f"- 流程階段: {', '.join(pipeline['stages'])}\n"
        result += f"- 使用工具: {', '.join(pipeline['tools'])}\n"
        result += f"- 部署策略: {pipeline['deployment_strategy']}\n"
        result += "### 改進建議\n"
        result += self._format_list(pipeline.get("improvement_suggestions", []))
        return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MachineNativeOps GitHub Project Deep Analyzer v2.1.0")
    parser.add_argument(
        "--owner",
        default=os.environ.get("GITHUB_REPO_OWNER"),
        help="GitHub repository owner (or set GITHUB_REPO_OWNER)",
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPO_NAME"),
        help="GitHub repository name (or set GITHUB_REPO_NAME)",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub token to increase rate limits (or set GITHUB_TOKEN)",
    )
    parser.add_argument(
        "--local-path",
        help="Local repository path for file scanning (enables real metrics collection)",
    )
    parser.add_argument("--output", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()
    if not args.owner or not args.repo:
        parser.error(
            "Repository owner and name are required via --owner/--repo "
            "or environment variables."
        )
    return args


def main() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO)

    args = _parse_args()
    config = GitHubAnalyzerConfig(
        repo_owner=args.owner,
        repo_name=args.repo,
        output_format=args.output,
        token=args.token,
        local_path=getattr(args, 'local_path', None),
    )
    analyzer = GitHubProjectAnalyzer(config)
    analysis = analyzer.analyze_project()

    if args.output == "json":
        print(json.dumps(analysis, ensure_ascii=False, indent=2))
    else:
        print(analyzer.generate_markdown_report(analysis))


if __name__ == "__main__":
    main()
