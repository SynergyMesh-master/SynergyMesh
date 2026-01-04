# GitHub Secrets Configuration Guide

## Overview
This guide provides comprehensive instructions for securely configuring and managing GitHub Secrets across multiple environments in the MachineNativeOps project.

## Prerequisites
- GitHub CLI (gh) installed and authenticated
- Access to repository settings
- Appropriate permissions for secret management

## Environment-Specific Secret Isolation

### 1. Environment Setup
Configure separate environments with their own secret scopes:

```bash
# Set up environment protection rules
gh api \
  -X PUT \
  -H "Accept: application/vnd.github+json" \
  /repos/{owner}/{repo}/environments/prod \
  -f 'deployment_branch_policy[type]=protected_branches' \
  -f 'wait_timer=30'
```

### 2. Secret Hierarchy
```
Global Secrets (All Environments)
├── GITHUB_TOKEN (Auto-generated)
├── REGISTRY_USERNAME
└── REGISTRY_PASSWORD

Environment-Specific Secrets
├── dev/
│   ├── DB_HOST
│   ├── DB_PASSWORD
│   └── API_KEY
├── staging/
│   ├── DB_HOST
│   ├── DB_PASSWORD
│   └── API_KEY
└── prod/
    ├── DB_HOST
    ├── DB_PASSWORD
    └── API_KEY
```

## Secret Creation Commands

### Database Secrets
```bash
# Development
gh secret set DEV_DB_HOST --env dev --body "localhost"
gh secret set DEV_DB_PASSWORD --env dev --body "$(openssl rand -base64 32)"

# Staging
gh secret set STAGING_DB_HOST --env staging --body "staging-db.example.com"
gh secret set STAGING_DB_PASSWORD --env staging --body "$(openssl rand -base64 32)"

# Production
gh secret set PROD_DB_HOST --env prod --body "prod-db.example.com"
gh secret set PROD_DB_PASSWORD --env prod --body "$(openssl rand -base64 32)"
```

### API Keys and Tokens
```bash
# Create secure API tokens
gh secret set API_TOKEN --env dev --body "$(openssl rand -hex 32)"
gh secret set API_TOKEN --env staging --body "$(openssl rand -hex 32)"
gh secret set API_TOKEN --env prod --body "$(openssl rand -hex 32)"
```

### Container Registry Secrets
```bash
# Docker Hub
gh secret set DOCKER_USERNAME --body "your-username"
gh secret set DOCKER_PASSWORD --body "your-password"

# GitHub Container Registry
gh secret set GHCR_TOKEN --body "${{ secrets.GITHUB_TOKEN }}"
```

## Verification Commands

### Check Secret Existence
```bash
# List all secrets for an environment
gh secret list --env prod

# Get specific secret metadata
gh secret get DB_PASSWORD --env prod
```

### Verify Environment Isolation
```bash
# Check prod secrets (should only show prod-specific secrets)
gh api -H "Accept: application/vnd.github+json" \
  /repos/{owner}/{repo}/environments/prod/secrets \
  | jq '.secrets[] | {name: .name, updated_at: .updated_at}'
```

### Test Secret Access in Workflows
```yaml
# .github/workflows/test-secrets.yml
name: Test Secret Access

on:
  workflow_dispatch:

jobs:
  test-secrets:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Access staging secrets
        env:
          DB_HOST: ${{ secrets.DB_HOST }}
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
        run: |
          echo "Testing secret access..."
          echo "DB_HOST: ${DB_HOST:0:5}***" # Safe logging
          echo "Secret access verified ✅"
```

## Automated Rotation

### Setup Cron Job
```bash
# Add to crontab
crontab -e

# Rotate secrets every 30 days at midnight
0 0 1 */1 * /usr/bin/python3 /workspace/scripts/secrets_rotation.py \
  --repo {owner}/{repo} \
  --secret API_TOKEN \
  --envs dev staging prod \
  >> /var/log/secrets_rotation.log 2>&1
```

### Manual Rotation
```bash
# Dry run to see what would happen
python3 scripts/secrets_rotation.py \
  --repo MachineNativeOps/machine-native-ops \
  --secret API_TOKEN \
  --dry-run

# Actual rotation
python3 scripts/secrets_rotation.py \
  --repo MachineNativeOps/machine-native-ops \
  --secret API_TOKEN \
  --envs staging prod

# Verify rotation
python3 scripts/secrets_rotation.py \
  --repo MachineNativeOps/machine-native-ops \
  --secret API_TOKEN \
  --verify
```

## Security Best Practices

### 1. Principle of Least Privilege
- Only grant secret access to specific workflows
- Use environment-specific secrets
- Rotate secrets regularly

### 2. Secret Validation
```bash
# Validate secret format before setting
validate_secret() {
    local secret="$1"
    local min_length=32
    
    if [ ${#secret} -lt $min_length ]; then
        echo "❌ Secret too short (minimum $min_length characters)"
        return 1
    fi
    
    if ! echo "$secret" | grep -qE '^[a-zA-Z0-9]+$'; then
        echo "❌ Secret contains invalid characters"
        return 1
    fi
    
    echo "✅ Secret validation passed"
    return 0
}
```

### 3. Audit Trail Monitoring
```bash
# Monitor secret rotation logs
tail -f /var/log/secrets_rotation.log

# Check rotation history
grep "secret_name" /var/log/secrets_rotation.log | jq -r '.timestamp, .secret_name, .dry_run'
```

### 4. Emergency Access Recovery
```bash
# In case of secret loss, immediately rotate
python3 scripts/secrets_rotation.py \
  --repo MachineNativeOps/machine-native-ops \
  --secret EMERGENCY_ACCESS_KEY \
  --envs prod

# Verify new secret is active
gh secret get EMERGENCY_ACCESS_KEY --env prod
```

## Troubleshooting

### Issue: "Secret not found"
```bash
# Check if secret exists
gh secret list --env prod

# Recreate if missing
gh secret set DB_PASSWORD --env prod --body "$(openssl rand -base64 32)"
```

### Issue: "Permission denied"
```bash
# Verify GitHub CLI authentication
gh auth status

# Re-authenticate if needed
gh auth login
```

### Issue: "Dry run shows no changes"
```bash
# Verify secret names and environments
gh secret list --env staging
gh secret list --env prod

# Check rotation script logs
cat /var/log/secrets_rotation.log | tail -20
```

## Compliance Checklist

- [ ] All secrets use minimum 32-character length
- [ ] Secrets are environment-isolated
- [ ] Automated rotation is configured (30-day cycle)
- [ ] Audit logging is enabled
- [ ] Emergency recovery procedures documented
- [ ] Access controls are properly configured
- [ ] Regular security reviews scheduled

## Next Steps

1. Configure all required secrets for your environments
2. Set up automated rotation schedule
3. Test secret access in CI/CD workflows
4. Monitor rotation logs for anomalies
5. Schedule regular security audits