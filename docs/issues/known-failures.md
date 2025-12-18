# Known Failure Modes

The repository now auto-reports lint/test/build/audit signals through the
self-awareness workflows. This file explains the most common failure classes so
agents (or humans) can jump straight to the fix.

## ESLint `@typescript-eslint/no-unused-expressions` Crash

- **Symptom**: ESLint throws
  `Cannot read properties of undefined (reading 'allowShortCircuit')`.
- **Cause**: Mixing the legacy rule configuration with the new flat config in
  workspaces such as `core/contract_service/contracts-L1/contracts`.
- **Fix**: Ensure `@typescript-eslint/no-unused-expressions` is disabled and the
  base `no-unused-expressions` rule is enabled with short-circuit/ternary/tagged
  template support. The shared configs already apply this—run
  `npm run lint --workspaces --if-present` to verify.

## Missing TypeScript Compiler

- **Symptom**: `npx tsc -b tsconfig.json` fails with `EACCES` or "tsc not found"
  during workflows.
- **Cause**: The root workspace lacked a TypeScript devDependency.
- **Fix**: `npm install` at the repository root (installs the shared
  `typescript` dependency) and rerun the TypeScript build via
  `npx tsc -b tsconfig.json` or the **🔨 NPM: 建置** task.

## Dirty Workspace Snapshot

- **Symptom**: "Workspace Cleanliness" signal fails in the nightly workflow,
  often accompanied by generated docs or build artifacts.
- **Cause**: Files were generated locally but not committed/ignored.
- **Fix**:
  1. Run `git status -sb --porcelain` to inspect the working tree.
  2. Commit intentional changes, or update `.gitignore` for generated assets.
  3. Re-run the failing signal (e.g., `npm run lint --workspaces --if-present`).

## Dependency Vulnerability Alerts

- **Symptom**: Security audit signal reports vulnerable packages.
- **Cause**: `npm audit --workspaces --include-workspace-root` found CVEs in the
  monorepo lockfile.
- **Fix**: Update the flagged dependency (often with `npm audit fix` or manual
  version bumps). Document intentionally accepted risks in
  `docs/security/SECURITY_SUMMARY.md` and link back here if the exception is
  recurring.

Add new sections whenever you encounter a recurring failure so the repository’s
self-awareness report can link to a precise remediation path.
