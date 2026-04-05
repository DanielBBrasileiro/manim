#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export AIOX_REMOTION_REUSE_BUNDLE="1"

echo "🔥 [Daemon] Iniciando AIOX Render Daemon (Porta 3333)..."
echo "Para parar: Ctrl+C"

cd "${ROOT}/engines/remotion"
exec bash "${ROOT}/scripts/run_remotion_node.sh" "${ROOT}/scripts/remotion_daemon.js"
