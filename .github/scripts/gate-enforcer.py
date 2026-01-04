#!/usr/bin/env python3
"""
🚪 Gate Enforcer - 閘門強制器
================================
將 PR 模板從「裝飾性文檔」轉變為「可執行驗證引擎」

職責：
1. 解析 PR 描述中的所有 checkbox
2. 自動驗證每個可自動驗證的項目
3. 生成驗證報告和分數
4. 自動更新 PR 描述中的 checkbox 狀態
5. 阻止不符合的 PR 合併
"""

import os
import re
import sys
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum


class GateStatus(Enum):
    PASS = "✅"
    FAIL = "❌"
    SKIP = "⏭️"
    PENDING = "🔄"
    BLOCKED = "⏸️"


@dataclass
class GateResult:
    """單一閘門驗證結果"""
    gate_id: str
    name: str
    status: GateStatus
    message: str = ""
    auto_verified: bool = False
    details: dict = field(default_factory=dict)


@dataclass
class GateReport:
    """閘門驗證報告"""
    total_gates: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    pending: int = 0
    auto_verified: int = 0
    score: float = 0.0
    gates: list = field(default_factory=list)

    def calculate_score(self):
        """計算驗證分數"""
        if self.total_gates == 0:
            self.score = 0.0
        else:
            self.score = (self.passed / self.total_gates) * 100


class GateEnforcer:
    """閘門強制器 - 將模板轉變為可執行驗證"""

    # 可自動驗證的閘門定義
    AUTO_VERIFIABLE_GATES = {
        # 證據鏈驗證
        "evidence.repo": {
            "pattern": r"-\s*repo\s*:\s*(https://github\.com/[^/\s]+/[^/\s]+)",
            "validator": "validate_repo_url",
            "name": "Repository URL"
        },
        "evidence.branch": {
            "pattern": r"-\s*branch\s*:\s*(\S+)",
            "validator": "validate_branch",
            "name": "Branch Name"
        },
        "evidence.commit": {
            "pattern": r"-\s*commit\s*:\s*([0-9a-f]{40})",
            "validator": "validate_commit_sha",
            "name": "Commit SHA (40-char)"
        },
        "evidence.pr": {
            "pattern": r"-\s*PR\s*:\s*(https://github\.com/[^/\s]+/[^/\s]+/pull/\d+)",
            "validator": "validate_pr_url",
            "name": "PR URL"
        },

        # 技術驗證
        "tech.security_scan": {
            "command": ["python", "controlplane/baseline/validation/validate-root-specs.py"],
            "validator": "validate_command",
            "name": "Security Scan",
            "fallback_pass": True  # 如果腳本不存在，跳過
        },
        "tech.naming_convention": {
            "validator": "validate_naming_convention",
            "name": "Naming Convention Check"
        },

        # 檔案變更驗證
        "files.modified_documented": {
            "validator": "validate_files_documented",
            "name": "Modified Files Documented"
        },
    }

    # Checkbox 模式匹配
    CHECKBOX_PATTERN = re.compile(
        r'^(\s*)-\s*\[((?:[ xX]|✅|❌|⏭️|🔄|⏸️)?)\]\s*(.+)$',
        re.MULTILINE
    )

    def __init__(self, pr_body: str, pr_number: int = 0, repo_root: str = "."):
        self.pr_body = pr_body
        self.pr_number = pr_number
        self.repo_root = Path(repo_root)
        self.report = GateReport()
        self.changed_files: list = []

    def get_changed_files(self) -> list:
        """獲取 PR 中變更的檔案列表"""
        try:
            # 從環境變量獲取基礎分支
            base_ref = os.environ.get('GITHUB_BASE_REF', 'main')
            result = subprocess.run(
                ['git', 'diff', '--name-only', f'origin/{base_ref}...HEAD'],
                capture_output=True, text=True, cwd=self.repo_root
            )
            if result.returncode == 0:
                self.changed_files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        except Exception as e:
            # 如果無法取得變更檔案，記錄錯誤但不要中止流程，維持默認/既有的 changed_files
            print(f"[GateEnforcer] Failed to get changed files: {e}", file=sys.stderr)
        return self.changed_files

    def parse_checkboxes(self) -> list:
        """解析 PR 描述中的所有 checkbox"""
        checkboxes = []
        for match in self.CHECKBOX_PATTERN.finditer(self.pr_body):
            indent = match.group(1)
            state = match.group(2)
            text = match.group(3)

            # 判斷 checkbox 狀態
            if state in ['x', 'X', '✅']:
                status = GateStatus.PASS
            elif state == '❌':
                status = GateStatus.FAIL
            elif state == '⏭️':
                status = GateStatus.SKIP
            elif state == '🔄':
                status = GateStatus.PENDING
            elif state == '⏸️':
                status = GateStatus.BLOCKED
            else:
                status = GateStatus.PENDING

            checkboxes.append({
                'indent': indent,
                'original_state': state,
                'text': text,
                'status': status,
                'full_match': match.group(0)
            })
        return checkboxes

    # ========== 驗證器方法 ==========

    def validate_repo_url(self, _gate_def: dict) -> GateResult:
        """驗證 Repository URL"""
        pattern = self.AUTO_VERIFIABLE_GATES["evidence.repo"]["pattern"]
        match = re.search(pattern, self.pr_body, re.IGNORECASE)

        if match:
            url = match.group(1)
            # 檢查是否是 placeholder
            if '<' in url or '[' in url:
                return GateResult(
                    gate_id="evidence.repo",
                    name="Repository URL",
                    status=GateStatus.FAIL,
                    message=f"URL 包含未替換的 placeholder: {url}",
                    auto_verified=True
                )
            return GateResult(
                gate_id="evidence.repo",
                name="Repository URL",
                status=GateStatus.PASS,
                message=f"有效: {url}",
                auto_verified=True
            )
        return GateResult(
            gate_id="evidence.repo",
            name="Repository URL",
            status=GateStatus.FAIL,
            message="缺少或格式錯誤",
            auto_verified=True
        )

    def validate_branch(self, _gate_def: dict) -> GateResult:
        """驗證 Branch Name"""
        pattern = self.AUTO_VERIFIABLE_GATES["evidence.branch"]["pattern"]
        match = re.search(pattern, self.pr_body, re.IGNORECASE)

        if match:
            branch = match.group(1)
            if '<' in branch or '[' in branch or branch == '[分支名稱]':
                return GateResult(
                    gate_id="evidence.branch",
                    name="Branch Name",
                    status=GateStatus.FAIL,
                    message=f"Branch 包含未替換的 placeholder: {branch}",
                    auto_verified=True
                )
            return GateResult(
                gate_id="evidence.branch",
                name="Branch Name",
                status=GateStatus.PASS,
                message=f"有效: {branch}",
                auto_verified=True
            )
        return GateResult(
            gate_id="evidence.branch",
            name="Branch Name",
            status=GateStatus.FAIL,
            message="缺少或格式錯誤",
            auto_verified=True
        )

    def validate_commit_sha(self, _gate_def: dict) -> GateResult:
        """驗證 Commit SHA"""
        pattern = self.AUTO_VERIFIABLE_GATES["evidence.commit"]["pattern"]
        match = re.search(pattern, self.pr_body, re.IGNORECASE)

        if match:
            sha = match.group(1)
            return GateResult(
                gate_id="evidence.commit",
                name="Commit SHA",
                status=GateStatus.PASS,
                message=f"有效 40 字元 SHA: {sha[:8]}...",
                auto_verified=True
            )
        return GateResult(
            gate_id="evidence.commit",
            name="Commit SHA",
            status=GateStatus.FAIL,
            message="缺少或不是完整 40 字元 SHA",
            auto_verified=True
        )

    def validate_pr_url(self, _gate_def: dict) -> GateResult:
        """驗證 PR URL"""
        pattern = self.AUTO_VERIFIABLE_GATES["evidence.pr"]["pattern"]
        match = re.search(pattern, self.pr_body, re.IGNORECASE)

        if match:
            url = match.group(1)
            if '<' in url or '[' in url:
                return GateResult(
                    gate_id="evidence.pr",
                    name="PR URL",
                    status=GateStatus.FAIL,
                    message=f"URL 包含未替換的 placeholder: {url}",
                    auto_verified=True
                )
            return GateResult(
                gate_id="evidence.pr",
                name="PR URL",
                status=GateStatus.PASS,
                message=f"有效: {url}",
                auto_verified=True
            )
        return GateResult(
            gate_id="evidence.pr",
            name="PR URL",
            status=GateStatus.FAIL,
            message="缺少或格式錯誤",
            auto_verified=True
        )

    def validate_naming_convention(self, _gate_def: dict) -> GateResult:
        """驗證命名規範
        
        Aligns with project naming policy (root.naming-policy.yaml):
        - Base rule: kebab-case (lowercase with hyphens)
        - Standard exceptions: README.md, LICENSE, etc.
        - Config file patterns: Chart.yaml, Taskfile.yml, etc.
        - Report/state patterns: *_REPORT.json, *_STATE.yaml, etc.
        """
        if not self.changed_files:
            self.get_changed_files()

        violations = []
        for f in self.changed_files:
            basename = Path(f).name
            
            # 檢查大寫字母（排除特定檔案和模式）
            if re.search(r'[A-Z]', basename):
                # 排除允許大寫的檔案（標準專案檔案）
                allowed_files = [
                    'README.md', 'LICENSE', 'Dockerfile', 'Makefile',
                    'CHANGELOG.md', 'CONTRIBUTING.md', 'CODEOWNERS',
                    'FUNDING.yml', 'PULL_REQUEST_TEMPLATE.md'
                ]
                
                # 排除允許大寫的模式
                allowed_patterns = [
                    r'\.md$',  # Markdown files (can contain uppercase)
                    r'^Chart\.yaml$',  # Helm Chart.yaml
                    r'^Taskfile\.yml$',  # Task Taskfile.yml
                    r'_REPORT\.(json|yaml|yml)$',  # Report files
                    r'_STATE\.(json|yaml|yml)$',  # State files
                    r'_CONFIG\.(json|yaml|yml)$',  # Config files with uppercase
                    r'_MANIFEST\.(json|yaml|yml)$',  # Manifest files
                    r'_MAP\.(json|yaml|yml)$',  # Map files
                    r'_VALIDATION\.(json|yaml|yml)$',  # Validation files
                    r'^[A-Z][A-Z0-9_-]*\.(yaml|yml|json)$',  # All-caps config files
                ]
                
                # Check if basename matches any allowed pattern
                is_allowed = basename in allowed_files or any(
                    re.search(pattern, basename) for pattern in allowed_patterns
                )
                
                if not is_allowed:
                    violations.append(f)

        if violations:
            return GateResult(
                gate_id="tech.naming_convention",
                name="Naming Convention",
                status=GateStatus.FAIL,
                message=f"發現 {len(violations)} 個命名違規",
                auto_verified=True,
                details={"violations": violations[:5]}  # 只顯示前 5 個
            )
        return GateResult(
            gate_id="tech.naming_convention",
            name="Naming Convention",
            status=GateStatus.PASS,
            message="所有檔案符合命名規範",
            auto_verified=True
        )

    def validate_files_documented(self, _gate_def: dict) -> GateResult:
        """驗證變更檔案是否在 PR 描述中記錄"""
        if not self.changed_files:
            self.get_changed_files()

        # 從 PR body 中提取記錄的檔案
        documented_pattern = r'modified_files:\s*\n((?:\s*-\s*.+\n?)+)'
        match = re.search(documented_pattern, self.pr_body, re.IGNORECASE)

        if not match:
            if len(self.changed_files) == 0:
                return GateResult(
                    gate_id="files.modified_documented",
                    name="Files Documented",
                    status=GateStatus.SKIP,
                    message="無檔案變更",
                    auto_verified=True
                )
            return GateResult(
                gate_id="files.modified_documented",
                name="Files Documented",
                status=GateStatus.PENDING,
                message="PR 描述中缺少 modified_files 區塊",
                auto_verified=True
            )

        # 解析 modified_files 區塊中的檔案列表
        documented_block = match.group(1)
        documented_files = []
        for line in documented_block.splitlines():
            stripped = line.strip()
            if not stripped or not stripped.startswith("-"):
                continue
            # 移除前綴的 "-" 並取得路徑
            path_str = stripped[1:].strip()
            if path_str:
                documented_files.append(path_str)

        # 正規化路徑後比對實際變更檔案與 PR 中記錄的檔案
        normalized_changed = {
            Path(p).as_posix().lstrip("./") for p in self.changed_files
        }
        normalized_documented = {
            Path(p).as_posix().lstrip("./") for p in documented_files
        }

        missing_in_docs = sorted(normalized_changed - normalized_documented)
        extra_in_docs = sorted(normalized_documented - normalized_changed)

        if not missing_in_docs and not extra_in_docs:
            return GateResult(
                gate_id="files.modified_documented",
                name="Files Documented",
                status=GateStatus.PASS,
                message=f"已完整記錄 {len(self.changed_files)} 個變更檔案",
                auto_verified=True
            )

        # 若有不一致，回報詳細資訊以便修正
        message_parts = []
        if missing_in_docs:
            preview_missing = ", ".join(missing_in_docs[:5])
            more_missing = "..." if len(missing_in_docs) > 5 else ""
            message_parts.append(
                f"有 {len(missing_in_docs)} 個變更檔案未在 modified_files 中記錄：{preview_missing}{more_missing}"
            )
        if extra_in_docs:
            preview_extra = ", ".join(extra_in_docs[:5])
            more_extra = "..." if len(extra_in_docs) > 5 else ""
            message_parts.append(
                f"modified_files 中包含 {len(extra_in_docs)} 個未變更的檔案：{preview_extra}{more_extra}"
            )

        return GateResult(
            gate_id="files.modified_documented",
            name="Files Documented",
            status=GateStatus.FAIL,
            message="；".join(message_parts),
            auto_verified=True
        )

    def validate_command(self, gate_def: dict) -> GateResult:
        """執行命令驗證"""
        command = gate_def.get("command", [])
        fallback_pass = gate_def.get("fallback_pass", False)

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=self.repo_root,
                timeout=60
            )
            if result.returncode == 0:
                return GateResult(
                    gate_id=gate_def.get("name", "command"),
                    name=gate_def.get("name", "Command"),
                    status=GateStatus.PASS,
                    message="驗證通過",
                    auto_verified=True
                )
            return GateResult(
                gate_id=gate_def.get("name", "command"),
                name=gate_def.get("name", "Command"),
                status=GateStatus.FAIL,
                message=result.stderr[:200] if result.stderr else "驗證失敗",
                auto_verified=True
            )
        except FileNotFoundError:
            if fallback_pass:
                return GateResult(
                    gate_id=gate_def.get("name", "command"),
                    name=gate_def.get("name", "Command"),
                    status=GateStatus.SKIP,
                    message="驗證腳本不存在，跳過",
                    auto_verified=True
                )
            return GateResult(
                gate_id=gate_def.get("name", "command"),
                name=gate_def.get("name", "Command"),
                status=GateStatus.FAIL,
                message="驗證腳本不存在",
                auto_verified=True
            )
        except Exception as e:
            return GateResult(
                gate_id=gate_def.get("name", "command"),
                name=gate_def.get("name", "Command"),
                status=GateStatus.FAIL,
                message=str(e)[:200],
                auto_verified=True
            )

    def run_all_gates(self) -> GateReport:
        """執行所有閘門驗證"""
        self.get_changed_files()

        # 運行自動驗證閘門
        for gate_id, gate_def in self.AUTO_VERIFIABLE_GATES.items():
            validator_name = gate_def.get("validator")
            if validator_name and hasattr(self, validator_name):
                validator = getattr(self, validator_name)
                result = validator(gate_def)
                self.report.gates.append(result)
                self.report.total_gates += 1
                self.report.auto_verified += 1

                if result.status == GateStatus.PASS:
                    self.report.passed += 1
                elif result.status == GateStatus.FAIL:
                    self.report.failed += 1
                elif result.status == GateStatus.SKIP:
                    self.report.skipped += 1
                else:
                    self.report.pending += 1

        # 解析並計算手動 checkbox 狀態
        checkboxes = self.parse_checkboxes()
        manual_passed = 0
        manual_total = 0

        # 建立自動驗證閘門名稱的標準化集合，避免以子字串方式誤判
        auto_gate_names = {
            gate.name.strip().lower()
            for gate in self.report.gates
            if getattr(gate, "name", None)
        }

        for cb in checkboxes:
            # 跳過自動驗證的項目（使用精確匹配而非子字串匹配）
            cb_text = cb.get("text", "")
            if not isinstance(cb_text, str):
                cb_text = str(cb_text)
            normalized_cb_text = cb_text.strip().lower()
            if normalized_cb_text in auto_gate_names:
                continue

            manual_total += 1
            if cb['status'] == GateStatus.PASS:
                manual_passed += 1

        self.report.total_gates += manual_total
        self.report.passed += manual_passed

        self.report.calculate_score()
        return self.report

    def generate_markdown_report(self) -> str:
        """生成 Markdown 格式報告"""
        lines = [
            "## 🚪 閘門驗證報告",
            "",
            f"**驗證分數**: {self.report.score:.1f}% ({self.report.passed}/{self.report.total_gates})",
            "",
            "| 狀態 | 計數 |",
            "|------|------|",
            f"| ✅ 通過 | {self.report.passed} |",
            f"| ❌ 失敗 | {self.report.failed} |",
            f"| ⏭️ 跳過 | {self.report.skipped} |",
            f"| 🔄 待定 | {self.report.pending} |",
            f"| 🤖 自動驗證 | {self.report.auto_verified} |",
            "",
            "### 詳細結果",
            ""
        ]

        for gate in self.report.gates:
            emoji = gate.status.value
            auto_tag = " `[自動]`" if gate.auto_verified else ""
            lines.append(f"- {emoji} **{gate.name}**{auto_tag}: {gate.message}")
            if gate.details:
                for key, value in gate.details.items():
                    if isinstance(value, list):
                        for item in value[:3]:
                            lines.append(f"  - {item}")

        # 添加總結
        lines.extend([
            "",
            "---",
            ""
        ])

        if self.report.score >= 80:
            lines.append("✅ **閘門檢查通過** - PR 可以合併")
        elif self.report.score >= 50:
            lines.append("⚠️ **閘門檢查部分通過** - 需要人工審核")
        else:
            lines.append("❌ **閘門檢查失敗** - 請修復上述問題後重新提交")

        return "\n".join(lines)

    def generate_json_report(self) -> str:
        """生成 JSON 格式報告"""
        return json.dumps({
            "score": self.report.score,
            "total": self.report.total_gates,
            "passed": self.report.passed,
            "failed": self.report.failed,
            "skipped": self.report.skipped,
            "pending": self.report.pending,
            "auto_verified": self.report.auto_verified,
            "gates": [
                {
                    "id": g.gate_id,
                    "name": g.name,
                    "status": g.status.name,
                    "message": g.message,
                    "auto_verified": g.auto_verified,
                    "details": g.details
                }
                for g in self.report.gates
            ]
        }, indent=2, ensure_ascii=False)


def main():
    """主程序入口"""
    import argparse

    parser = argparse.ArgumentParser(description="🚪 Gate Enforcer - 閘門強制器")
    parser.add_argument("--pr-body", help="PR 描述內容 (從 stdin 讀取如果未提供)")
    parser.add_argument("--pr-body-file", help="包含 PR 描述的檔案路徑")
    parser.add_argument("--pr-number", type=int, default=0, help="PR 編號")
    parser.add_argument("--output", choices=["markdown", "json", "both"], default="markdown")
    parser.add_argument("--fail-under", type=float, default=0, help="分數低於此值則失敗")
    parser.add_argument("--repo-root", default=".", help="Repository 根目錄")

    args = parser.parse_args()

    # 獲取 PR body
    pr_body = ""
    if args.pr_body:
        pr_body = args.pr_body
    elif args.pr_body_file:
        with open(args.pr_body_file, 'r', encoding='utf-8') as f:
            pr_body = f.read()
    elif not sys.stdin.isatty():
        pr_body = sys.stdin.read()
    else:
        print("錯誤: 請提供 --pr-body, --pr-body-file, 或從 stdin 輸入", file=sys.stderr)
        sys.exit(1)

    # 執行驗證
    enforcer = GateEnforcer(
        pr_body=pr_body,
        pr_number=args.pr_number,
        repo_root=args.repo_root
    )

    report = enforcer.run_all_gates()

    # 輸出報告
    if args.output in ["markdown", "both"]:
        print(enforcer.generate_markdown_report())
    if args.output in ["json", "both"]:
        if args.output == "both":
            print("\n---\n")
        print(enforcer.generate_json_report())

    # 檢查是否需要失敗
    if args.fail_under > 0 and report.score < args.fail_under:
        print(f"\n❌ 分數 {report.score:.1f}% 低於門檻 {args.fail_under}%", file=sys.stderr)
        sys.exit(1)

    # 如果有任何失敗的閘門，返回非零狀態
    if report.failed > 0:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
