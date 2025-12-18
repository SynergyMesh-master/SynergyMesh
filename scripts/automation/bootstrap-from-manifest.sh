#!/bin/sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST_PATH="${1:-${REPO_ROOT}/island.bootstrap.stage0.yaml}"

if [ ! -f "${MANIFEST_PATH}" ]; then
  echo "bootstrap manifest not found: ${MANIFEST_PATH}" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
exec "${PYTHON_BIN}" "${REPO_ROOT}/tools/bootstrap_from_manifest.py" "${MANIFEST_PATH}" "${@:2}"
