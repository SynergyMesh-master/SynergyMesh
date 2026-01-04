#!/usr/bin/env python3
"""
GitHub Secrets Rotation Automation
Automatically rotates secrets across environments with audit logging
"""

import subprocess
import sys
from datetime import datetime
import json
import os

class SecretsRotator:
    def __init__(self, repo_owner, repo_name, dry_run=False):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.dry_run = dry_run
        self.log_file = "/var/log/secrets_rotation.log"
        self.environments = ["dev", "staging", "prod"]
        
    def generate_secure_token(self, length=32):
        """Generate cryptographically secure random token"""
        return subprocess.check_output([
            "openssl", "rand", "-hex", str(length)
        ]).decode().strip()
    
    def rotate_secret(self, secret_name, environments=None):
        """Rotate a specific secret across environments"""
        if environments is None:
            environments = self.environments
            
        results = {}
        old_tokens = {}
        new_token = self.generate_secure_token()
        
        # Store old tokens for verification
        for env in environments:
            old_tokens[env] = self._get_current_secret(secret_name, env)
        
        # Rotate secret in each environment
        for env in environments:
            if not self.dry_run:
                try:
                    result = subprocess.run([
                        "gh", "secret", "set", secret_name,
                        "--env", env,
                        "--body", new_token
                    ], check=True, capture_output=True, text=True)
                    results[env] = {"status": "success", "output": result.stdout}
                except subprocess.CalledProcessError as e:
                    results[env] = {"status": "failed", "error": e.stderr}
            else:
                results[env] = {"status": "dry_run", "new_token": new_token}
        
        # Log rotation event
        self._log_rotation_event(secret_name, environments, old_tokens, results)
        
        return results
    
    def _get_current_secret(self, secret_name, env):
        """Get current secret value for verification"""
        try:
            result = subprocess.run([
                "gh", "secret", "get", secret_name,
                "--env", env,
                "--json", "value", "-q", ".value"
            ], check=True, capture_output=True, text=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
    
    def _log_rotation_event(self, secret_name, environments, old_tokens, results):
        """Log rotation event with audit trail"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "secret_name": secret_name,
            "environments": environments,
            "dry_run": self.dry_run,
            "results": results
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        print(f"✅ Rotation event logged to {self.log_file}")
    
    def verify_rotation(self, secret_name, environments=None):
        """Verify that secrets were successfully rotated"""
        if environments is None:
            environments = self.environments
            
        verification_results = {}
        
        for env in environments:
            try:
                result = subprocess.run([
                    "gh", "secret", "get", secret_name,
                    "--env", env,
                    "--json", "updatedAt", "-q", ".updatedAt"
                ], check=True, capture_output=True, text=True)
                verification_results[env] = {
                    "status": "verified",
                    "updated_at": result.stdout.strip()
                }
            except subprocess.CalledProcessError as e:
                verification_results[env] = {
                    "status": "verification_failed",
                    "error": str(e)
                }
        
        return verification_results

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Rotate GitHub Secrets")
    parser.add_argument("--repo", required=True, help="Repository (owner/repo)")
    parser.add_argument("--secret", required=True, help="Secret name to rotate")
    parser.add_argument("--envs", nargs="+", default=None, help="Environments (dev staging prod)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--verify", action="store_true", help="Verify rotation")
    
    args = parser.parse_args()
    
    try:
        owner, repo = args.repo.split("/")
        rotator = SecretsRotator(owner, repo, dry_run=args.dry_run)
        
        if args.verify:
            results = rotator.verify_rotation(args.secret, args.envs)
            print("Verification Results:")
            for env, result in results.items():
                status = "✅" if result["status"] == "verified" else "❌"
                print(f"{status} {env}: {result}")
        else:
            results = rotator.rotate_secret(args.secret, args.envs)
            print("Rotation Results:")
            for env, result in results.items():
                status = "✅" if result["status"] in ["success", "dry_run"] else "❌"
                print(f"{status} {env}: {result['status']}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()