#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_NODE_VERSION="${REMOTION_NODE_VERSION:-20.19.5}"
FALLBACK_NODE="${HOME}/.nvm/versions/node/v${TARGET_NODE_VERSION}/bin/node"

if [[ -x "${FALLBACK_NODE}" ]]; then
  exec "${FALLBACK_NODE}" "$@"
fi

if [[ -s "${HOME}/.nvm/nvm.sh" ]]; then
  # shellcheck disable=SC1090
  source "${HOME}/.nvm/nvm.sh"
  if nvm use "${TARGET_NODE_VERSION}" >/dev/null 2>&1; then
    exec node "$@"
  fi
fi

exec node "$@"
