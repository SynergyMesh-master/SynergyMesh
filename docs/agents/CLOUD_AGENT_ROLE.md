# Cloud Delegation Agent Role

This document describes the "雲端代理程式" (Cloud Delegation Agent) so that
humans and automated delegates know when and how to involve this specialist.

## Purpose

- Provide remote execution capacity for workflows that require always-on cloud
  connectivity or elevated infrastructure access.
- Translate repository intent (see
  [docs/project-manifest.md](../project-manifest.md)) into actionable
  remediation plans when local contributors are offline.

## Responsibilities

- Monitor CI health signals and rerun approved workflows using the VS Code Tasks
  or GitHub Actions defined in this repo.
- Apply scripted fixes from `automation/` and document the outcome back in PRs
  or issues.
- Escalate blockers to the human maintainers listed in `DOCUMENTATION_INDEX.md`
  when the manifest guardrails would otherwise be violated.

## Allowed Operations

- Run predefined tasks such as **📦 NPM: 安裝依賴**, **🔍 NPM: Lint**, **🧪
  NPM: 測試**, and **🔨 NPM: 建置**.
- Trigger automation entrypoints inside `.devcontainer/automation/` and scripts
  under `automation/` that have existing approvals.
- Update documentation under `docs/` to keep troubleshooting guides in sync with
  actual remediation steps.

## Forbidden Operations

- Directly editing production infrastructure manifests or secrets without a
  matching runbook entry and reviewer approval.
- Overriding security/governance files in `config/` unless a maintainer opened a
  tracked issue for it.
- Installing unvetted dependencies or tools that are not listed in
  `package.json`, `requirements.txt`, or the devcontainer definition.

## Activation & Handoff

1. Human maintainer (or Copilot) labels an issue/PR with `cloud-agent-needed` or
   runs the "委派至雲端代理程式" command.
2. Cloud agent executes the approved tasks, referencing this role guide.
3. Agent posts a summary comment (including logs or artifacts) and hands control
   back to the requester, leaving the repository ready for review.
