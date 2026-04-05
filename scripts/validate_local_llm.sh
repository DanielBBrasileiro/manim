#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "AIOX local LLM validation"
echo

echo "1. Health check"
python3 - <<'PY'
from core.intelligence.ollama_client import check_ollama_health
print(check_ollama_health())
PY

echo
echo "2. Smoke test - plan"
python3 scripts/smoke_ollama_pipeline.py --task-type plan

echo
echo "3. Smoke test - fast_plan"
python3 scripts/smoke_ollama_pipeline.py --task-type fast_plan

echo
echo "4. Benchmark"
python3 scripts/benchmark_llm_routes.py --iterations 2

if [[ "${AIOX_LLM_VALIDATE_QUALITY:-0}" == "1" ]]; then
  echo
  echo "4b. Quality benchmark"
  python3 scripts/benchmark_llm_routes.py --iterations 1 --task-types quality_plan --disable-cache
fi

echo
echo "5. Cache behavior"
python3 scripts/check_llm_cache_behavior.py

echo
echo "6. Missing-model sanity"
python3 - <<'PY'
import json, os
from pathlib import Path
os.environ['AIOX_LLM_FORCE_MODEL'] = 'missing-model-for-sanity-check'
from core.intelligence.ollama_client import generate_scene_plan
registry = json.loads(Path('assets/registry.json').read_text())
plan, metadata = generate_scene_plan('quero algo minimalista e respirando', asset_registry=registry, return_metadata=True)
print('plan_is_none', plan is None)
print(metadata)
PY

echo
echo "7. Daemon-off sanity"
python3 - <<'PY'
import json, os
from pathlib import Path
os.environ['OLLAMA_URL'] = 'http://127.0.0.1:65535/api/generate'
from core.compiler.intent_parser import parse_intent
registry = json.loads(Path('assets/registry.json').read_text())
intent = parse_intent('quero algo calmo, emergente e minimalista', asset_registry=registry)
print(intent.source, intent.transformation, intent.pacing, intent.confidence)
PY
