#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

SUMMARY_FILE="${GITHUB_STEP_SUMMARY:-}"
PR_BODY="${PR_BODY:-}"
GOV_SCAN_SCRIPT="governance/35-scripts/scan-governance-directory.py" # numeric prefix retained for governance conventions
PYTEST_VERSION="${PYTEST_VERSION:-7.4.4}"
MANIFEST_PATH="${MANIFEST_PATH:-island.bootstrap.stage0.yaml}"
MANIFEST_STEPS="${MANIFEST_STEPS:-scaffold.directories materialize.templates}"

log() {
  echo "[governed-build] $*"
}

install_minimal_governance_deps() {
  log "Installing minimal governance deps (pyyaml jsonschema)"
  pip install pyyaml jsonschema
}

NODE_PRESENT=false
RUST_PRESENT=false
GO_PRESENT=false
PY_PRESENT=false
JAVA_PRESENT=false

if [[ -f package.json ]]; then
  NODE_PRESENT=true
  log "Install Node dependencies"
  npm install

  log "Lint workspaces"
  npm run lint --workspaces --if-present

  log "Docs lint (if defined)"
  npm run docs:lint --if-present

  log "Workspace tests"
  npm run test --workspaces --if-present

  log "Workspace build"
  npm run build --workspaces --if-present
fi

if [[ -d core ]]; then
  RUST_PRESENT=true
  log "Rust formatting and linting"
  cargo fmt --all -- --check
  cargo clippy --workspace --all-targets -- -D warnings

  log "Rust tests"
  cargo test --workspace --all-features

  log "Rust build"
  cargo build --workspace --all-features
fi

if [[ -d services ]]; then
  GO_PRESENT=true
  log "Go formatting check"
  if gofmt -l ./services | grep -q .; then
    log "Go formatting issues detected"
    exit 1
  fi

  log "Go tests"
  (cd services && go test ./...)

  log "Go build"
  (cd services && go build ./...)
fi

if [[ -f requirements.txt || -f pyproject.toml ]]; then
  PY_PRESENT=true
elif [[ -n "$(find . -maxdepth 3 -name '*.py' -type f -print -quit 2>/dev/null)" ]]; then
  PY_PRESENT=true
fi

if [[ "$PY_PRESENT" = true ]]; then
  log "Python dependencies and tests"
  if [[ -f requirements.txt ]]; then
    pip install -r requirements.txt
  else
    pip install "pytest==${PYTEST_VERSION}"
  fi
  pytest
fi

if [[ -f pom.xml ]]; then
  JAVA_PRESENT=true
  log "Java tests"
  mvn test

  log "Java build"
  mvn clean install -DskipTests
fi

log "Validate manifest bootstrap"
python3 tools/bootstrap_from_manifest.py "${MANIFEST_PATH}" --steps ${MANIFEST_STEPS}

log "Governance validation"
python -m pip install --upgrade pip
if [[ -f requirements-workflow.txt ]]; then
  pip install -r requirements-workflow.txt
else
  log "requirements-workflow.txt missing; installing minimal governance deps"
  install_minimal_governance_deps
fi
governance_validator="${GOVERNANCE_VALIDATE_SCRIPT:-$(find governance -name 'validate-governance-structure.py' -print -quit 2>/dev/null || true)}"
if [[ -n "${governance_validator}" && -f "${governance_validator}" ]]; then
  python "${governance_validator}" --verbose
else
  log "Governance validation script not found; skipping structure validation"
fi
make validate-governance-ci
scan_script="${GOV_SCAN_SCRIPT}"
if [[ ! -f "${scan_script}" ]]; then
  scan_script="$(find governance -name 'scan-governance-directory.py' -print -quit 2>/dev/null || true)"
fi
if [[ -n "${scan_script}" && -f "${scan_script}" ]]; then
  python "${scan_script}" --deep
else
  log "Governance scan script not found; skipping deep scan"
fi

if [[ -n "${PR_BODY}" ]]; then
  log "Validate AI Behavior Contract response body"
  if [[ -x ".github/scripts/validate-ai-response.sh" ]]; then
    .github/scripts/validate-ai-response.sh "${PR_BODY}"
  else
    log "AI response validator script missing; skipping validation"
  fi
fi

if [[ -n "${SUMMARY_FILE}" ]]; then
  node_status=$([ "$NODE_PRESENT" = true ] && echo "executed" || echo "skipped")
  rust_status=$([ "$RUST_PRESENT" = true ] && echo "executed" || echo "skipped")
  go_status=$([ "$GO_PRESENT" = true ] && echo "executed" || echo "skipped")
  python_status=$([ "$PY_PRESENT" = true ] && echo "executed" || echo "skipped")
  java_status=$([ "$JAVA_PRESENT" = true ] && echo "executed" || echo "skipped")
  {
    echo "## Governed Build Summary"
    echo "- Node tasks: ${node_status}"
    echo "- Rust tasks: ${rust_status}"
    echo "- Go tasks: ${go_status}"
    echo "- Python tasks: ${python_status}"
    echo "- Java tasks: ${java_status}"
    echo "- Governance: executed"
  } >>"$SUMMARY_FILE"
fi
