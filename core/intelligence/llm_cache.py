from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any


SCENE_PLAN_SCHEMA_VERSION = "scene_plan_v1"


def cache_enabled() -> bool:
    return os.environ.get("AIOX_LLM_ENABLE_CACHE", "1").strip() not in {"0", "false", "no"}


def default_cache_dir() -> Path:
    return Path(os.environ.get("AIOX_LLM_CACHE_DIR", "output/cache/llm"))


def build_cache_key(
    prompt: str,
    asset_registry: dict[str, Any],
    task_type: str,
    model: str,
    schema_version: str = SCENE_PLAN_SCHEMA_VERSION,
) -> str:
    payload = {
        "prompt": _normalize_prompt(prompt),
        "asset_registry": asset_registry,
        "task_type": task_type,
        "model": model,
        "schema_version": schema_version,
    }
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def load_cached_scene_plan(cache_key: str, cache_dir: Path | None = None) -> dict[str, Any] | None:
    if not cache_enabled():
        return None
    path = _cache_path(cache_key, cache_dir)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def save_cached_scene_plan(
    cache_key: str,
    scene_plan: dict[str, Any],
    model: str,
    confidence: float,
    cache_dir: Path | None = None,
) -> bool:
    if not cache_enabled() or not scene_plan:
        return False
    payload = {
        "created_at": time.time(),
        "model": model,
        "confidence": confidence,
        "scene_plan": scene_plan,
    }
    path = _cache_path(cache_key, cache_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return True


def _cache_path(cache_key: str, cache_dir: Path | None = None) -> Path:
    base = cache_dir or default_cache_dir()
    return Path(base) / f"{cache_key}.json"


def _normalize_prompt(prompt: str) -> str:
    clean = re.sub(r"\s+", " ", str(prompt).strip().lower())
    return clean
