#!/usr/bin/env python3
"""
Island AI 品牌替換工具
Brand Replacement Tool v1.0

用於自動化替換所有 Copilot 相關術語為 Island AI 品牌
"""

import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class BrandReplacer:
    """品牌替換器"""

    def __init__(self, config_path: str = "config/brand-mapping.yaml"):
        self.project_root = Path(__file__).parent.parent
        self.config_path = self.project_root / config_path
        self.config = self._load_config()
        self.replacements_made = 0
        self.files_modified = []
        self.files_renamed = []

    def _load_config(self) -> dict[str, Any]:
        """載入品牌映射配置"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置檔案不存在: {self.config_path}")

        with open(self.config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _build_replacement_map(self) -> dict[str, str]:
        """建立替換映射表"""
        mapping = {}
        brand_mapping = self.config.get("brand_mapping", {})

        # 處理主要品牌
        for item in brand_mapping.get("primary", []):
            mapping[item["old"]] = item["new"]

        # 處理模組
        for item in brand_mapping.get("modules", []):
            mapping[item["old"]] = item["new"]

        # 處理指令
        for item in brand_mapping.get("commands", []):
            mapping[item["old"]] = item["new"]

        return mapping

    def _build_file_rename_map(self) -> dict[str, str]:
        """建立檔案重命名映射表"""
        mapping = {}
        for item in self.config.get("brand_mapping", {}).get("files", []):
            mapping[item["old"]] = item["new"]
        return mapping

    def replace_in_file(self, file_path: Path) -> bool:
        """替換單一檔案中的品牌術語"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError):
            return False

        original_content = content
        replacement_map = self._build_replacement_map()

        # 按長度排序，先替換較長的字串
        sorted_keys = sorted(replacement_map.keys(), key=len, reverse=True)

        for old_term in sorted_keys:
            new_term = replacement_map[old_term]
            # 使用正則表達式進行大小寫不敏感的替換
            pattern = re.compile(re.escape(old_term), re.IGNORECASE)

            def replace_match(match: re.Match) -> str:
                # 保持原始大小寫模式
                original = match.group(0)
                if original.isupper():
                    return new_term.upper()
                elif original[0].isupper():
                    return new_term[0].upper() + new_term[1:]
                return new_term

            content = pattern.sub(replace_match, content)

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.files_modified.append(str(file_path))
            self.replacements_made += 1
            return True

        return False

    def rename_files(self) -> list[tuple[str, str]]:
        """重命名檔案"""
        rename_map = self._build_file_rename_map()
        renamed = []

        for old_name, new_name in rename_map.items():
            # 搜索所有匹配的檔案
            for file_path in self.project_root.rglob(old_name):
                if ".git" in str(file_path):
                    continue

                new_path = file_path.parent / new_name
                if file_path.exists() and not new_path.exists():
                    shutil.move(str(file_path), str(new_path))
                    renamed.append((str(file_path), str(new_path)))
                    self.files_renamed.append((str(file_path), str(new_path)))

        return renamed

    def process_all_files(self) -> dict[str, Any]:
        """處理所有檔案"""
        extensions = {".md", ".yml", ".yaml", ".json", ".sh", ".txt", ".py", ".ts", ".js"}
        exclude_dirs = {".git", "node_modules", "dist", "build", "__pycache__", ".venv"}

        processed = 0
        for file_path in self.project_root.rglob("*"):
            if any(ex in str(file_path) for ex in exclude_dirs):
                continue

            if file_path.is_file() and file_path.suffix in extensions:
                if self.replace_in_file(file_path):
                    processed += 1

        return {
            "files_processed": processed,
            "files_modified": self.files_modified,
            "files_renamed": self.files_renamed,
            "replacements_made": self.replacements_made,
        }

    def generate_report(self) -> str:
        """生成替換報告"""
        report = f"""
# Island AI 品牌替換報告
生成時間: {datetime.now().isoformat()}

## 統計
- 修改檔案數: {len(self.files_modified)}
- 重命名檔案數: {len(self.files_renamed)}
- 總替換次數: {self.replacements_made}

## 修改的檔案
"""
        for f in self.files_modified:
            report += f"- {f}\n"

        report += "\n## 重命名的檔案\n"
        for old, new in self.files_renamed:
            report += f"- {old} → {new}\n"

        return report


def main():
    """主程式"""
    print("=" * 60)
    print("Island AI 品牌替換工具 v1.0")
    print("=" * 60)

    replacer = BrandReplacer()

    # 先重命名檔案
    print("\n[1/2] 重命名檔案...")
    renamed = replacer.rename_files()
    for old, new in renamed:
        print(f"  ✓ {old} → {new}")

    # 替換內容
    print("\n[2/2] 替換檔案內容...")
    result = replacer.process_all_files()
    print(f"  處理檔案: {result['files_processed']}")
    print(f"  修改檔案: {len(result['files_modified'])}")

    # 生成報告
    report = replacer.generate_report()
    report_path = Path("ops/reports/brand-replacement-report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n報告已生成: {report_path}")
    print("=" * 60)
    print("品牌替換完成！")


if __name__ == "__main__":
    main()
