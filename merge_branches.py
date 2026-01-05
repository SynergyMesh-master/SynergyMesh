#!/usr/bin/env python3
"""
Automated Branch Merge Script
Merges all remote branches into main with conflict resolution
"""

import subprocess
import sys
from datetime import datetime

def run_command(cmd, check=True, capture=True):
    """Run a shell command"""
    if capture:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        return result
    else:
        return subprocess.run(cmd, shell=True, check=check)

def main():
    print("=" * 50)
    print("Automated Branch Merge Script")
    print("=" * 50)
    
    # Get current time
    start_time = datetime.now()
    
    # Checkout main and pull
    print("\nStep 1: Updating main branch...")
    run_command("git checkout main")
    run_command("git pull origin main")
    
    # Get all branches
    print("\nStep 2: Getting branch list...")
    result = run_command("git branch -r | grep -v 'main' | grep -v 'HEAD' | sed 's/origin\\///'")
    branches = [b.strip() for b in result.stdout.strip().split('\n') if b.strip()]
    
    total = len(branches)
    print(f"Found {total} branches to process")
    
    # Statistics
    merged = 0
    skipped = 0
    failed = 0
    
    # Process each branch
    for i, branch in enumerate(branches, 1):
        print(f"\n[{i}/{total}] Processing: {branch}")
        
        # Check if already merged
        result = run_command(f"git merge-base --is-ancestor origin/{branch} origin/main", check=False)
        if result.returncode == 0:
            print("  ✓ Already merged")
            skipped += 1
            continue
        
        # Check for unique commits
        result = run_command(f"git log origin/main..origin/{branch} --oneline")
        unique_commits = len([l for l in result.stdout.strip().split('\n') if l.strip()])
        
        if unique_commits == 0:
            print("  ✓ No unique commits")
            skipped += 1
            continue
        
        print(f"  → Found {unique_commits} unique commit(s)")
        
        # Try different merge strategies
        merge_success = False
        
        strategies = [
            ("Normal merge", "git merge origin/{branch} --no-edit --no-ff"),
            ("Ours strategy", "git merge origin/{branch} -X ours --no-edit --no-ff"),
            ("Theirs strategy", "git merge origin/{branch} -X theirs --no-edit --no-ff"),
        ]
        
        for strategy_name, cmd_template in strategies:
            cmd = cmd_template.format(branch=branch)
            print(f"  → Trying {strategy_name}...")
            result = run_command(cmd, check=False)
            
            if result.returncode == 0:
                print(f"  ✓ {strategy_name} successful")
                merge_success = True
                merged += 1
                break
            else:
                # Abort merge
                run_command("git merge --abort", check=False)
        
        if not merge_success:
            print(f"  ✗ Failed to merge {branch}")
            failed += 1
    
    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    print("\n" + "=" * 50)
    print("Merge Summary")
    print("=" * 50)
    print(f"Total branches: {total}")
    print(f"Successfully merged: {merged}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print(f"Time elapsed: {elapsed:.2f} seconds")
    print("=" * 50)
    
    # Push if we merged anything
    if merged > 0:
        print("\nPushing merged changes...")
        run_command("git push origin main")
        print("✓ Pushed successfully")
    
    print("\nBranch merge process completed!")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())