#!/bin/sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TEMPLATE="$REPO_ROOT/templates/sync/watch-and-sync.island-ai.v1.sh"

if [ ! -x "$TEMPLATE" ]; then
  echo "Template sync script not found: $TEMPLATE" >&2
  exit 1
fi

exec "$TEMPLATE" "$@"
