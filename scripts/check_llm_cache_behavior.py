#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.intelligence.llm_cache import build_cache_key
from core.intelligence.ollama_client import generate_scene_plan


def main() -> int:
    registry = json.loads((ROOT / "assets" / "registry.json").read_text(encoding="utf-8"))
    prompt_a = "quero algo que respire, com curva limpa e resolucao elegante"
    prompt_b = "quero algo que respire, com curva limpa e resolucao elegante agora"

    with tempfile.TemporaryDirectory() as tmp:
        os.environ["AIOX_LLM_CACHE_DIR"] = tmp
        os.environ["AIOX_LLM_ENABLE_CACHE"] = "1"

        print("1. Mesmo prompt duas vezes")
        _, meta_1 = generate_scene_plan(prompt_a, asset_registry=registry, return_metadata=True)
        _, meta_2 = generate_scene_plan(prompt_a, asset_registry=registry, return_metadata=True)
        print(json.dumps({"first": meta_1, "second": meta_2}, ensure_ascii=True, indent=2))

        print("\n2. Prompt levemente diferente")
        key_a = build_cache_key(prompt_a, registry, "plan", meta_2.get("route_model") or meta_2.get("model") or "unknown")
        key_b = build_cache_key(prompt_b, registry, "plan", meta_2.get("route_model") or meta_2.get("model") or "unknown")
        print(json.dumps({"key_a": key_a, "key_b": key_b, "same_key": key_a == key_b}, ensure_ascii=True, indent=2))

        print("\n3. Registry diferente gera nova chave")
        registry_changed = dict(registry)
        registry_changed["effects"] = list(registry.get("effects", [])) + ["new_effect_for_cache_test"]
        key_c = build_cache_key(prompt_a, registry_changed, "plan", meta_2.get("route_model") or meta_2.get("model") or "unknown")
        print(json.dumps({"key_a": key_a, "key_c": key_c, "same_key": key_a == key_c}, ensure_ascii=True, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
