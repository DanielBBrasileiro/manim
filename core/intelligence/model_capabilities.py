from __future__ import annotations

import json
import os
import re
import socket
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from core.env_loader import load_repo_env

load_repo_env()

ROOT = Path(__file__).resolve().parent.parent.parent
CACHE_PATH = ROOT / "core" / "memory" / "model_capabilities.json"
OLLAMA_TAGS_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/generate").replace("/api/generate", "/api/tags")


@dataclass
class ModelCapability:
    id: str
    provider: str = "ollama"
    supports_text_plan: bool = True
    supports_vision_plan: bool = False
    supports_structured_json: bool = True
    quality_band: str = "medium"
    context_budget: int = 6000
    observed_latency_ms: float | None = None
    observed_success_rate: float | None = None
    observed_memory_pressure: str | None = None
    recommended_roles: list[str] = field(default_factory=list)
    observation_count: int = 0
    success_count: int = 0
    last_task_type: str | None = None
    updated_at: float = field(default_factory=time.time)


def _fetch_tags(url: str = OLLAMA_TAGS_URL, timeout: float = 2.0) -> list[str]:
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return [item.get("name") for item in payload.get("models", []) if isinstance(item, dict) and item.get("name")]


def _read_cache() -> dict[str, Any]:
    if not CACHE_PATH.exists():
        return {"models": [], "updated_at": None}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"models": [], "updated_at": None}


def _write_cache(models: list[ModelCapability]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "models": [asdict(model) for model in models],
        "updated_at": time.time(),
    }
    CACHE_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _size_hint(model: str) -> float:
    match = re.search(r"(\d+(?:\.\d+)?)b", model.lower())
    if not match:
        return 7.0
    try:
        return float(match.group(1))
    except ValueError:
        return 7.0


def infer_model_capability(model: str) -> ModelCapability:
    lowered = model.lower()
    size = _size_hint(model)
    supports_vision = "vl" in lowered or "vision" in lowered
    if size >= 14:
        quality_band = "high"
        context_budget = 9000
    elif size >= 7:
        quality_band = "medium"
        context_budget = 7000
    else:
        quality_band = "fast"
        context_budget = 5000

    roles = ["plan", "copy_refiner"]
    if quality_band == "fast":
        roles = ["fast_plan", "variant_ranker"]
    elif quality_band == "high":
        roles = ["quality_plan", "copy_refiner", "variant_ranker"]

    if supports_vision:
        roles.append("vision_plan")

    return ModelCapability(
        id=model,
        supports_vision_plan=supports_vision,
        quality_band=quality_band,
        context_budget=context_budget,
        recommended_roles=sorted(set(roles)),
    )


def load_model_capabilities() -> list[ModelCapability]:
    raw = _read_cache().get("models", [])
    capabilities: list[ModelCapability] = []
    for item in raw:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        capabilities.append(ModelCapability(**item))
    return capabilities


def get_model_capability(model: str) -> ModelCapability:
    cached = {entry.id: entry for entry in load_model_capabilities()}
    return cached.get(model, infer_model_capability(model))


def refresh_model_capabilities(installed_models: list[str] | None = None) -> list[ModelCapability]:
    models = installed_models
    if models is None:
        try:
            models = _fetch_tags()
        except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError, OSError):
            return load_model_capabilities()

    existing = {entry.id: entry for entry in load_model_capabilities()}
    refreshed: list[ModelCapability] = []
    for model in models:
        capability = existing.get(model, infer_model_capability(model))
        capability.updated_at = time.time()
        refreshed.append(capability)

    _write_cache(refreshed)
    return refreshed


def record_model_observation(
    model: str,
    *,
    success: bool,
    latency_ms: float | None = None,
    memory_pressure: str | None = None,
    task_type: str | None = None,
) -> ModelCapability:
    capabilities = {entry.id: entry for entry in load_model_capabilities()}
    capability = capabilities.get(model, infer_model_capability(model))
    capability.observation_count += 1
    if success:
        capability.success_count += 1
    capability.observed_success_rate = round(capability.success_count / max(capability.observation_count, 1), 4)
    if latency_ms is not None:
        previous = capability.observed_latency_ms
        if previous is None:
            capability.observed_latency_ms = round(float(latency_ms), 2)
        else:
            capability.observed_latency_ms = round(((previous * (capability.observation_count - 1)) + float(latency_ms)) / capability.observation_count, 2)
    if memory_pressure:
        capability.observed_memory_pressure = memory_pressure
    if task_type:
        capability.last_task_type = task_type
    capability.updated_at = time.time()
    capabilities[capability.id] = capability
    _write_cache(list(capabilities.values()))
    return capability


def build_capability_snapshot() -> dict[str, Any]:
    capabilities = refresh_model_capabilities()
    return {
        "count": len(capabilities),
        "models": [asdict(entry) for entry in capabilities],
    }
