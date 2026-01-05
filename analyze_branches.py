#!/usr/bin/env python3
"""
Script to analyze all remote branches and identify those with unmerged commits
that should be merged to main.
"""

import subprocess
import json
from datetime import datetime

def run_command(cmd):
    """Run a shell command and return output."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode

def get_all_remote_branches():
    """Get list of all remote branches."""
    output, _ = run_command("cd /workspace/machine-native-ops && git branch -r")
    branches = [b.strip() for b in output.split('\n') if b.strip()]
    # Filter out HEAD reference
    branches = [b for b in branches if '->' not in b]
    return branches

def get_branch_commits(branch):
    """Get commits on a branch that are not in main."""
    cmd = f"cd /workspace/machine-native-ops && git log origin/main..{branch} --oneline"
    output, _ = run_command(cmd)
    commits = output.split('\n') if output.strip() else []
    return commits

def get_branch_info(branch):
    """Get detailed information about a branch."""
    commits = get_branch_commits(branch)
    
    if not commits:
        return None
    
    # Get last commit date
    cmd = f"cd /workspace/machine-native-ops && git log -1 --format=%ci {branch}"
    last_date, _ = run_command(cmd)
    
    # Get last commit message
    cmd = f"cd /workspace/machine-native-ops && git log -1 --format=%s {branch}"
    last_msg, _ = run_command(cmd)
    
    return {
        'name': branch,
        'commit_count': len(commits),
        'commits': commits[:5],  # Show first 5 commits
        'last_commit_date': last_date,
        'last_commit_message': last_msg
    }

def main():
    print("=== Analyzing Remote Branches for Unmerged Commits ===\n")
    
    # Get all remote branches
    branches = get_all_remote_branches()
    print(f"Found {len(branches)} remote branches\n")
    
    # Analyze each branch
    branches_with_commits = []
    for branch in branches:
        info = get_branch_info(branch)
        if info:
            branches_with_commits.append(info)
    
    # Sort by commit count (descending)
    branches_with_commits.sort(key=lambda x: x['commit_count'], reverse=True)
    
    # Display results
    print(f"=== {len(branches_with_commits)} branches have unmerged commits ===\n")
    
    for i, info in enumerate(branches_with_commits, 1):
        print(f"{i}. Branch: {info['name']}")
        print(f"   Commits ahead of main: {info['commit_count']}")
        print(f"   Last commit: {info['last_commit_date']}")
        print(f"   Message: {info['last_commit_message'][:80]}...")
        print(f"   Recent commits:")
        for commit in info['commits']:
            print(f"     - {commit}")
        print()
    
    # Generate merge commands
    print("=== Suggested Merge Commands ===\n")
    for info in branches_with_commits:
        branch_name = info['name'].replace('origin/', '')
        print(f"# Merge {branch_name} ({info['commit_count']} commits)")
        print(f"git checkout {branch_name}")
        print(f"git pull origin {branch_name}")
        print(f"git checkout main")
        print(f"git merge {branch_name} -m 'Merge branch {branch_name}'")
        print()

if __name__ == "__main__":
    main()