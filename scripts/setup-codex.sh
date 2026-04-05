#!/usr/bin/env bash

set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

check_cmd() {
  local name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    printf "  [ok] %s -> %s\n" "$name" "$(command -v "$name")"
  else
    printf "  [missing] %s\n" "$name"
  fi
}

echo "AIOX Studio / Codex setup check"
echo "Root: $ROOT_DIR"
echo

echo "Core files"
for file in "$ROOT_DIR/AGENTS.md" "$ROOT_DIR/.codex/config.toml" "$ROOT_DIR/docs/codex-setup.md" "$ROOT_DIR/.mcp.json"; do
  if [ -f "$file" ]; then
    printf "  [ok] %s\n" "${file#$ROOT_DIR/}"
  else
    printf "  [missing] %s\n" "${file#$ROOT_DIR/}"
  fi
done

echo
echo "Required commands"
check_cmd python3
check_cmd node
check_cmd npm
check_cmd npx

echo
echo "Project-specific optional commands"
check_cmd manim
check_cmd ffmpeg
check_cmd ollama

echo
echo "Environment hints"
if [ -d "$ROOT_DIR/engines/remotion/node_modules" ]; then
  echo "  [ok] engines/remotion/node_modules present"
else
  echo "  [hint] run: cd engines/remotion && npm install"
fi

if python3 - <<'PY' >/dev/null 2>&1
import playwright  # noqa: F401
PY
then
  echo "  [ok] playwright Python package importable"
else
  echo "  [hint] run: python3 -m pip install -r requirements.txt"
fi

echo
echo "Suggested next steps"
echo "  1. python3 -m pip install -r requirements.txt"
echo "  2. cd engines/remotion && npm install"
echo "  3. python3 -m playwright install chromium"
echo "  4. Review docs/codex-setup.md for optional MCPs/plugins"
