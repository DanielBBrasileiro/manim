#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_NODE_VERSION="${REMOTION_NODE_VERSION:-20.19.5}"

run_with_node() {
  local node_bin="$1"
  shift
  exec "$node_bin" "$@"
}

if [[ -n "${REMOTION_NODE_BIN:-}" && -x "${REMOTION_NODE_BIN}" ]]; then
  run_with_node "${REMOTION_NODE_BIN}" "$@"
fi

for version in "${TARGET_NODE_VERSION}" "20.20.2" "20.19.5"; do
  candidate="${HOME}/.nvm/versions/node/v${version}/bin/node"
  if [[ -x "${candidate}" ]]; then
    run_with_node "${candidate}" "$@"
  fi
done

if command -v node >/dev/null 2>&1; then
  current_version="$(node -v 2>/dev/null || true)"
  if [[ "${current_version}" == v20.* ]]; then
    run_with_node "$(command -v node)" "$@"
  fi
fi

if [[ -s "${HOME}/.nvm/nvm.sh" ]]; then
  # shellcheck disable=SC1090
  source "${HOME}/.nvm/nvm.sh"
  if nvm use "${TARGET_NODE_VERSION}" >/dev/null 2>&1 || nvm use 20 >/dev/null 2>&1; then
    run_with_node "$(command -v node)" "$@"
  fi
fi

echo "Erro: Node 20.x nao encontrado para Remotion." >&2
echo "Defina REMOTION_NODE_BIN ou instale v20.19.5/v20.20.x via nvm." >&2
exit 127
