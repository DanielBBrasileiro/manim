#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTION_ROOT="${ROOT}/engines/remotion"
DEFAULT_NODE_VERSION="20.19.5"

resolve_target_node_version() {
  if [[ -n "${REMOTION_NODE_VERSION:-}" ]]; then
    printf '%s\n' "${REMOTION_NODE_VERSION}"
    return 0
  fi

  local marker
  for marker in \
    "${ROOT}/.node-version" \
    "${ROOT}/.nvmrc" \
    "${REMOTION_ROOT}/.node-version" \
    "${REMOTION_ROOT}/.nvmrc"; do
    if [[ -f "${marker}" ]]; then
      tr -d '[:space:]' < "${marker}"
      return 0
    fi
  done

  printf '%s\n' "${DEFAULT_NODE_VERSION}"
}

node_version_matches() {
  local node_bin="$1"
  local target_version="$2"
  "${node_bin}" -p "process.versions.node === '${target_version}'" 2>/dev/null | grep -qx 'true'
}

TARGET_NODE_VERSION="$(resolve_target_node_version)"
FALLBACK_NODE="${HOME}/.nvm/versions/node/v${TARGET_NODE_VERSION}/bin/node"

if [[ -n "${REMOTION_NODE_BIN:-}" && -x "${REMOTION_NODE_BIN}" ]]; then
  if node_version_matches "${REMOTION_NODE_BIN}" "${TARGET_NODE_VERSION}"; then
    exec "${REMOTION_NODE_BIN}" "$@"
  fi
  echo "[AIOX] REMOTION_NODE_BIN points to ${REMOTION_NODE_BIN}, but it is not Node ${TARGET_NODE_VERSION}." >&2
  exit 1
fi

if command -v node >/dev/null 2>&1; then
  CURRENT_NODE_BIN="$(command -v node)"
  if node_version_matches "${CURRENT_NODE_BIN}" "${TARGET_NODE_VERSION}"; then
    exec "${CURRENT_NODE_BIN}" "$@"
  fi
fi

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

echo "[AIOX] FATAL: could not resolve Node ${TARGET_NODE_VERSION} for Remotion." >&2
echo "Checked, in order:" >&2
echo "  1. REMOTION_NODE_BIN" >&2
echo "  2. current PATH node" >&2
echo "  3. ${FALLBACK_NODE}" >&2
echo "  4. nvm use ${TARGET_NODE_VERSION}" >&2
echo "Version markers:" >&2
echo "  - ${ROOT}/.node-version" >&2
echo "  - ${ROOT}/.nvmrc" >&2
echo "  - ${REMOTION_ROOT}/.node-version" >&2
echo "  - ${REMOTION_ROOT}/.nvmrc" >&2
echo "Run with an explicit binary if needed:" >&2
echo "  REMOTION_NODE_BIN=/absolute/path/to/node bash scripts/run_remotion_node.sh <command>" >&2
exit 1
