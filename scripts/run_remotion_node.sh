#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_NODE_VERSION="${REMOTION_NODE_VERSION:-20.19.5}"

if [[ -s "${HOME}/.nvm/nvm.sh" ]]; then
  # shellcheck disable=SC1090
  source "${HOME}/.nvm/nvm.sh"
  nvm use "${TARGET_NODE_VERSION}" >/dev/null
fi

exec node "$@"
