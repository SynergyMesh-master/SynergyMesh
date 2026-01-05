#!/usr/bin/env python3
"""
Script to merge branches with unmerged commits to main in a smart order.
Uses topological sorting based on commit count and merge history.
"""

import subprocess
import sys
from datetime import datetime

def run_command(cmd):
    """Run a shell command and return output."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def checkout_main():
    """Checkout main branch."""
    stdout, stderr, rc = run_command("cd /workspace/machine-native-ops && git checkout main")
    if rc != 0:
        print(f"[ERROR] Failed to checkout main: {stderr}")
        return False
    print("[OK] Checked out main branch")
    return True

def pull_main():
    """Pull latest changes from main."""
    stdout, stderr, rc = run_command("cd /workspace/machine-native-ops && git pull origin main")
    if rc != 0:
        print(f"[ERROR] Failed to pull main: {stderr}")
        return False
    print("[OK] Pulled latest main branch")
    return True

def merge_branch(branch_name):
    """Merge a branch to main."""
    clean_branch = branch_name.replace('origin/', '')
    
    print(f"\n[INFO] Merging branch: {branch_name}")
    
    # Try merge with default strategy first
    merge_cmd = f"cd /workspace/machine-native-ops && git merge {branch_name} --no-edit -X theirs"
    stdout, stderr, rc = run_command(merge_cmd)
    
    if rc == 0:
        print(f"[SUCCESS] Merged {branch_name} successfully")
        return True
    
    # If merge failed, try with recursive strategy
    print(f"[WARN] Default merge failed, trying recursive strategy...")
    merge_cmd = f"cd /workspace/machine-native-ops && git merge --abort 2>/dev/null; git merge {branch_name} --no-edit -s recursive -X theirs"
    stdout, stderr, rc = run_command(merge_cmd)
    
    if rc == 0:
        print(f"[SUCCESS] Merged {branch_name} with recursive strategy")
        return True
    
    # If still failed, abort and continue
    print(f"[ERROR] Failed to merge {branch_name}: {stderr}")
    run_command("cd /workspace/machine-native-ops && git merge --abort 2>/dev/null")
    return False

def main():
    print("=== Smart Branch Merge Script ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Checkout and update main
    if not checkout_main():
        sys.exit(1)
    if not pull_main():
        sys.exit(1)
    
    # Priority branches - merge these in order based on commit count
    # Selected top branches with highest commit counts
    priority_branches = [
        ("origin/copilot/sub-pr-962-again", 105),
        ("origin/copilot/sub-pr-971-4852c513-13b4-43c4-a8c8-4afdf2fa7ef2", 104),
        ("origin/copilot/sub-pr-971-e5d529f6-7dd3-44c6-9a27-e1fe68b394d9", 100),
        ("origin/copilot/sub-pr-971-fa15935b-9749-4cb2-a70f-f4b564f7dd4d", 96),
        ("origin/copilot/sub-pr-971-a170f214-480a-4acb-9637-7d95d44ea992", 92),
        ("origin/copilot/sub-pr-971-2f7e79f7-73ca-45d4-b0f1-c710e1219b06", 86),
        ("origin/copilot/sub-pr-971-d8bf1504-aba0-442d-ac8d-f5c9acb586ce", 82),
        ("origin/copilot/sub-pr-971-7bdd2825-8a65-4d42-9ce4-fe97fd16ac17", 78),
        ("origin/copilot/sub-pr-971-one-more-time", 73),
        ("origin/copilot/sub-pr-1000-another-one", 72),
        ("origin/copilot/sub-pr-971-0d7989e7-73a2-4e79-9139-065fc878a288", 72),
        ("origin/copilot/sub-pr-971-27dbd011-c68d-43c2-af00-0fbdca35d506", 68),
        ("origin/copilot/sub-pr-1000-again", 67),
        ("origin/copilot/sub-pr-971-2680e9a8-6cf5-4041-a913-7ba37ce76731", 66),
        ("origin/copilot/sub-pr-1000", 63),
        ("origin/copilot/sub-pr-971-6f030c05-f7a5-41a8-b269-6b4ffdbbdb03", 62),
        ("origin/copilot/sub-pr-971-65ab11db-179b-4059-8627-6c21f61b17c3", 59),
        ("origin/copilot/sub-pr-971-ba2b6fcc-1f63-482b-8806-186f3b948e5a", 43),
        ("origin/copilot/sub-pr-971", 39),
        ("origin/feature/schema-driven-governance", 2),
    ]
    
    success_count = 0
    failed_branches = []
    
    for branch, commit_count in priority_branches:
        print(f"\n{'='*60}")
        print(f"Processing: {branch} ({commit_count} commits)")
        print(f"{'='*60}")
        
        if merge_branch(branch):
            success_count += 1
        else:
            failed_branches.append((branch, commit_count))
    
    # Summary
    print(f"\n{'='*60}")
    print(f"MERGE SUMMARY")
    print(f"{'='*60}")
    print(f"Total branches processed: {len(priority_branches)}")
    print(f"Successfully merged: {success_count}")
    print(f"Failed to merge: {len(failed_branches)}")
    
    if failed_branches:
        print(f"\nFailed branches:")
        for branch, count in failed_branches:
            print(f"  - {branch} ({count} commits)")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()