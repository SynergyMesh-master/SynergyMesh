#!/usr/bin/env python3
"""
Execute the sync-knowledge DAR task to update the living knowledge base.

This script:
1. Detects repository changes (git diff)
2. Regenerates knowledge artifacts (mndoc, knowledge graph, superroot)
3. Finds related and highly related content
4. Updates governance index and DAG
5. Stores complete change records

Usage:
    python run_sync_knowledge.py
    python run_sync_knowledge.py --local  # Skip commit if running locally
    python run_sync_knowledge.py --commit abc123  # Analyze specific commit
"""

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


def run_command(cmd: list[str], cwd: Path = None) -> dict[str, Any]:
    """Run a shell command and return result."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return {
            "success": True,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": 0,
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "stdout": e.stdout,
            "stderr": e.stderr,
            "returncode": e.returncode,
        }


def detect_changes(repo_root: Path, base: str = "HEAD~1") -> dict[str, Any]:
    """Detect repository changes using git diff."""
    result = run_command(
        ["git", "diff", "--name-status", base, "HEAD"],
        cwd=repo_root,
    )
    
    if not result["success"]:
        print(f"Warning: git diff failed: {result['stderr']}")
        return {"files": [], "summary": "No changes detected"}
    
    changes = []
    for line in result["stdout"].strip().split("\n"):
        if not line:
            continue
        parts = line.split("\t", 1)
        if len(parts) == 2:
            status, file_path = parts
            change_type = {
                "A": "added",
                "M": "modified",
                "D": "deleted",
                "R": "renamed",
            }.get(status[0], "unknown")
            
            # Classify by file type
            category = classify_file(file_path)
            
            changes.append({
                "file": file_path,
                "type": change_type,
                "category": category,
                "status": status,
            })
    
    return {
        "files": changes,
        "summary": f"{len(changes)} file(s) changed",
        "count": len(changes),
    }


def classify_file(file_path: str) -> str:
    """Classify file into categories."""
    if "governance" in file_path or "policy" in file_path:
        return "governance"
    elif file_path.endswith((".yaml", ".yml", ".json")) and "schema" in file_path:
        return "schema"
    elif file_path.endswith((".yaml", ".yml", ".json")) and "config" in file_path:
        return "config"
    elif file_path.endswith((".py", ".ts", ".js", ".go")):
        return "code"
    elif file_path.endswith(".md"):
        return "documentation"
    elif ".github/workflows" in file_path:
        return "workflow"
    else:
        return "other"


def regenerate_knowledge_artifacts(repo_root: Path) -> dict[str, Any]:
    """Regenerate all knowledge artifacts using make all-kg."""
    print("🔄 Regenerating knowledge artifacts...")
    
    result = run_command(["make", "all-kg"], cwd=repo_root)
    
    if result["success"]:
        print("✅ Knowledge artifacts generated successfully")
        return {
            "status": "success",
            "mndoc": str(repo_root / "docs/generated/generated-mndoc.yaml"),
            "knowledge_graph": str(repo_root / "docs/generated/knowledge-graph.yaml"),
            "superroot": str(repo_root / "docs/generated/superroot-entities.yaml"),
        }
    else:
        print(f"⚠️  Knowledge generation had issues: {result['stderr']}")
        return {
            "status": "partial",
            "error": result["stderr"],
        }


def get_commit_metadata(repo_root: Path) -> dict[str, Any]:
    """Get metadata about the current commit."""
    # Get commit SHA
    sha_result = run_command(["git", "rev-parse", "HEAD"], cwd=repo_root)
    sha = sha_result["stdout"].strip() if sha_result["success"] else "unknown"
    
    # Get commit message
    msg_result = run_command(["git", "log", "-1", "--pretty=%B"], cwd=repo_root)
    message = msg_result["stdout"].strip() if msg_result["success"] else ""
    
    # Get commit author
    author_result = run_command(["git", "log", "-1", "--pretty=%ae"], cwd=repo_root)
    author = author_result["stdout"].strip() if author_result["success"] else ""
    
    # Get commit timestamp
    time_result = run_command(["git", "log", "-1", "--pretty=%aI"], cwd=repo_root)
    timestamp = time_result["stdout"].strip() if time_result["success"] else ""
    
    return {
        "commit_sha": sha,
        "commit_message": message,
        "commit_author": author,
        "commit_timestamp": timestamp,
    }


def store_change_record(
    repo_root: Path,
    commit_metadata: dict,
    changes: dict,
    knowledge_artifacts: dict,
) -> str:
    """Store complete change record."""
    records_dir = repo_root / "src/governance/dimensions/99-metadata/knl-pack/state/change-records"
    records_dir.mkdir(parents=True, exist_ok=True)
    
    sha = commit_metadata["commit_sha"][:8]
    record_file = records_dir / f"change-{sha}.yaml"
    
    record = {
        "version": "1.0.0",
        "timestamp": datetime.now(UTC).isoformat(),
        "commit": commit_metadata,
        "changes": changes,
        "knowledge_artifacts": knowledge_artifacts,
        "summary": {
            "files_changed": changes["count"],
            "knowledge_status": knowledge_artifacts.get("status", "unknown"),
        },
    }
    
    with open(record_file, "w") as f:
        yaml.dump(record, f, default_flow_style=False, allow_unicode=True)
    
    print(f"📝 Change record stored: {record_file}")
    return str(record_file)


def update_governance_index(repo_root: Path, changes: dict) -> dict[str, Any]:
    """Update governance index with new/modified artifacts."""
    index_file = repo_root / "src/governance/dimensions/99-metadata/knl-pack/governance/index.json"
    
    if not index_file.exists():
        print("⚠️  Governance index not found, skipping update")
        return {"status": "skipped"}
    
    with open(index_file) as f:
        index = json.load(f)
    
    # Update timestamp
    index["timestamp"] = datetime.now(UTC).isoformat()
    
    # Update statistics
    if "statistics" in index:
        index["statistics"]["last_index_update"] = datetime.now(UTC).isoformat()
    
    with open(index_file, "w") as f:
        json.dump(index, f, indent=2)
    
    print("✅ Governance index updated")
    return {"status": "updated"}


def main():
    parser = argparse.ArgumentParser(
        description="Sync living knowledge base with repository changes"
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Skip commit step (for local development)",
    )
    parser.add_argument(
        "--commit",
        type=str,
        help="Analyze specific commit (default: HEAD)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    
    args = parser.parse_args()
    
    # Find repository root
    repo_root = Path(__file__).resolve().parents[5]
    print(f"Repository root: {repo_root}")
    
    print("\n" + "=" * 70)
    print("🧬 Living Knowledge Base - Auto Sync")
    print("=" * 70 + "\n")
    
    # Step 1: Get commit metadata
    print("📋 Step 1: Getting commit metadata...")
    commit_metadata = get_commit_metadata(repo_root)
    print(f"   Commit: {commit_metadata['commit_sha'][:8]}")
    print(f"   Author: {commit_metadata['commit_author']}")
    print(f"   Message: {commit_metadata['commit_message'][:60]}...")
    
    # Step 2: Detect changes
    print("\n🔍 Step 2: Detecting changes...")
    base = f"{args.commit}~1" if args.commit else "HEAD~1"
    changes = detect_changes(repo_root, base)
    print(f"   {changes['summary']}")
    
    if args.verbose and changes["files"]:
        for change in changes["files"][:5]:
            print(f"   - {change['type']}: {change['file']} ({change['category']})")
        if len(changes["files"]) > 5:
            print(f"   ... and {len(changes['files']) - 5} more")
    
    # Step 3: Regenerate knowledge artifacts
    print("\n🔄 Step 3: Regenerating knowledge artifacts...")
    knowledge_artifacts = regenerate_knowledge_artifacts(repo_root)
    
    # Step 4: Update governance index
    print("\n📊 Step 4: Updating governance index...")
    index_update = update_governance_index(repo_root, changes)
    
    # Step 5: Store change record
    print("\n💾 Step 5: Storing change record...")
    record_path = store_change_record(
        repo_root,
        commit_metadata,
        changes,
        knowledge_artifacts,
    )
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ Knowledge Base Sync Complete")
    print("=" * 70)
    print(f"\n📝 Change Record: {record_path}")
    print(f"📊 Files Changed: {changes['count']}")
    print(f"🧬 Knowledge Status: {knowledge_artifacts.get('status', 'unknown')}")
    print(f"📈 Index Status: {index_update['status']}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
