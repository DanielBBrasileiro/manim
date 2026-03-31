from __future__ import annotations

import json
import os
import socket
import time
import urllib.error
import urllib.request
from typing import Any

from core.env_loader import load_repo_env
from core.intelligence.llm_cache import (
    SCENE_PLAN_SCHEMA_VERSION,
    build_cache_key,
    load_cached_scene_plan,
    save_cached_scene_plan,
)
from core.intelligence.model_router import (
    TASK_FAST_PLAN,
    TASK_PLAN,
    TASK_QUALITY_PLAN,
    TASK_VISION_PLAN,
    auto_quality_fallback_enabled,
    confidence_threshold,
    debug_enabled,
    get_route,
)
from core.intelligence.scene_plan import ScenePlan

load_repo_env()

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT_SECONDS", "8.0"))


def check_ollama_health(url: str | None = None, timeout: float | None = None) -> dict[str, Any]:
    target_url = _base_url(url or OLLAMA_URL) + "/api/tags"
    try:
        response = _get_json(target_url, timeout=timeout or OLLAMA_TIMEOUT)
        models = [item.get("name") for item in response.get("models", []) if isinstance(item, dict)]
        return {
            "ok": True,
            "url": target_url,
            "models": models,
            "error": None,
        }
    except Exception as exc:
        return {
            "ok": False,
            "url": target_url,
            "models": [],
            "error": f"{type(exc).__name__}: {exc}",
        }


def check_model_availability(model: str, url: str | None = None, timeout: float | None = None) -> dict[str, Any]:
    health = check_ollama_health(url=url, timeout=timeout)
    models = health.get("models", [])
    is_available = model in models
    return {
        "ok": health["ok"] and is_available,
        "model": model,
        "available_models": models,
        "error": None if is_available else health.get("error") or f"Model not installed: {model}",
    }


def generate_scene_plan(
    prompt: str,
    asset_registry: dict[str, Any] | None = None,
    task_type: str = TASK_PLAN,
    prefer_quality: bool = False,
    return_metadata: bool = False,
) -> ScenePlan | tuple[ScenePlan | None, dict[str, Any]]:
    if not prompt.strip():
        return _return(None, _empty_metadata(task_type), return_metadata)

    route = get_route(task_type=task_type, prefer_quality=prefer_quality)
    cache_key = build_cache_key(prompt, asset_registry or {}, route.task_type, route.model, SCENE_PLAN_SCHEMA_VERSION)
    cached = load_cached_scene_plan(cache_key)
    if cached:
        try:
            plan = ScenePlan.from_dict(cached["scene_plan"])
            metadata = {
                "task_type": route.task_type,
                "model": cached.get("model", route.model),
                "fallback_used": False,
                "from_cache": True,
                "confidence": cached.get("confidence", plan.confidence),
                "error": None,
                "latency_ms": 0,
                "route_model": route.model,
                "retry_count": 0,
                "retry_reason": None,
            }
            plan.llm_metadata = metadata
            return _return(plan, metadata, return_metadata)
        except Exception:
            pass

    plan, metadata = _generate_with_fallback(prompt, asset_registry or {}, route)
    if plan is not None:
        plan.llm_metadata = metadata
        save_cached_scene_plan(cache_key, plan.to_dict(), metadata.get("model", route.model), plan.confidence)
    return _return(plan, metadata, return_metadata)


def unload_vision_model() -> bool:
    route = get_route(TASK_VISION_PLAN)
    return unload_model(route.model, timeout=route.timeout_seconds)


def unload_quality_model() -> bool:
    route = get_route(TASK_QUALITY_PLAN)
    return unload_model(route.model, timeout=route.timeout_seconds)


def unload_model(model: str, timeout: float | None = None) -> bool:
    try:
        _post_json(
            _base_url(OLLAMA_URL) + "/api/generate",
            {
                "model": model,
                "prompt": "unload",
                "stream": False,
                "keep_alive": "0",
            },
            timeout=timeout or OLLAMA_TIMEOUT,
        )
        return True
    except Exception:
        return False


def _generate_with_fallback(prompt: str, asset_registry: dict[str, Any], route) -> tuple[ScenePlan | None, dict[str, Any]]:
    first_attempt = _attempt_scene_plan(
        prompt,
        asset_registry,
        route,
        strict=False,
        retry_count=0,
        retry_reason=None,
        timeout_seconds=route.timeout_seconds,
    )
    if _is_good_plan(first_attempt["plan"], first_attempt["metadata"]):
        _finalize_route(route)
        return first_attempt["plan"], first_attempt["metadata"]

    if route.task_type == TASK_VISION_PLAN:
        _finalize_route(route)
        return first_attempt["plan"], first_attempt["metadata"]

    retry_route = route
    retry_timeout = getattr(route, "retry_timeout_seconds", route.timeout_seconds)
    retry_reason = first_attempt["metadata"].get("error") or (
        f"confidence_below_threshold:{first_attempt['plan'].confidence:.2f}"
        if first_attempt["plan"] is not None
        else "empty_plan"
    )

    use_quality_route = False
    if _should_use_quality_fallback(first_attempt, route):
        quality_check = check_model_availability(route.quality_fallback_model, timeout=retry_timeout)
        if quality_check["ok"]:
            retry_route = get_route(TASK_QUALITY_PLAN)
            retry_timeout = retry_route.timeout_seconds
            use_quality_route = True
        else:
            _debug(f"quality fallback unavailable -> {quality_check['error']}")

    second_attempt = _attempt_scene_plan(
        prompt,
        asset_registry,
        retry_route,
        strict=True,
        fallback_used=use_quality_route,
        retry_count=1,
        retry_reason=retry_reason,
        timeout_seconds=retry_timeout,
    )
    _finalize_route(retry_route)
    if second_attempt["plan"] is not None:
        return second_attempt["plan"], second_attempt["metadata"]
    return None, second_attempt["metadata"] if second_attempt["metadata"].get("error") else first_attempt["metadata"]


def _attempt_scene_plan(
    prompt: str,
    asset_registry: dict[str, Any],
    route,
    strict: bool,
    fallback_used: bool = False,
    retry_count: int = 0,
    retry_reason: str | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    start = time.time()
    metadata = {
        "task_type": route.task_type,
        "model": route.model,
        "fallback_used": fallback_used,
        "from_cache": False,
        "confidence": None,
        "error": None,
        "latency_ms": None,
        "route_model": route.model,
        "retry_count": retry_count,
        "retry_reason": retry_reason,
    }

    model_check = check_model_availability(route.model, timeout=timeout_seconds or route.timeout_seconds)
    if not model_check["ok"]:
        metadata["error"] = model_check["error"]
        metadata["latency_ms"] = _latency_ms(start)
        _debug(f"model unavailable -> {route.model}")
        return {"plan": None, "metadata": metadata}

    payload = _build_request_payload(prompt, asset_registry, route, strict=strict)
    try:
        response = _post_json(
            _base_url(OLLAMA_URL) + "/api/generate",
            payload,
            timeout=timeout_seconds or route.timeout_seconds,
        )
        plan = _parse_scene_plan_response(response, metadata)
        metadata["latency_ms"] = _latency_ms(start)
        if plan is not None:
            metadata["confidence"] = plan.confidence
        return {"plan": plan, "metadata": metadata}
    except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError) as exc:
        metadata["error"] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        metadata["error"] = f"{type(exc).__name__}: {exc}"

    metadata["latency_ms"] = _latency_ms(start)
    _debug(f"ollama request failed -> {metadata['error']}")
    return {"plan": None, "metadata": metadata}


def _build_request_payload(prompt: str, asset_registry: dict[str, Any], route, strict: bool) -> dict[str, Any]:
    return {
        "model": route.model,
        "prompt": _build_prompt(prompt, asset_registry, strict=strict),
        "stream": False,
        "format": ScenePlan.json_schema(),
        "keep_alive": route.keep_alive,
        "options": {
            "temperature": 0.05 if strict else 0.2,
        },
    }


def _parse_scene_plan_response(response: dict[str, Any], metadata: dict[str, Any]) -> ScenePlan | None:
    content = response.get("response")
    if not isinstance(content, str) or not content.strip():
        metadata["error"] = "Empty response"
        return None

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        metadata["error"] = f"Invalid JSON: {exc}"
        return None

    try:
        plan = ScenePlan.from_dict(parsed)
        return plan
    except Exception as exc:
        metadata["error"] = f"Invalid ScenePlan schema: {exc}"
        return None


def _post_json(url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Invalid Ollama response")
    return parsed


def _get_json(url: str, timeout: float) -> dict[str, Any]:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Invalid Ollama response")
    return parsed


def _base_url(url: str) -> str:
    return url[:-13] if url.endswith("/api/generate") else url.rstrip("/")


def _build_prompt(prompt: str, asset_registry: dict[str, Any], strict: bool = False) -> str:
    registry_json = json.dumps(asset_registry, ensure_ascii=True)
    strict_block = ""
    if strict:
        strict_block = """
Strict mode:
- Obey the schema exactly.
- Do not include extra keys.
- Use only allowed archetypes and effects from the registry.
- If uncertain, lower confidence instead of inventing data.
""".strip()
    return f"""
You are planning motion-driven creative scenes for AIOX Studio.
Return one JSON object only. No markdown. No prose.

Constraints:
- Use only archetypes listed in the registry.
- Use only primitives/effects listed in the registry.
- Keep duration between 6 and 20 seconds.
- confidence must be a float between 0 and 1.
- Prefer concise, executable scene plans.
- Structure the plan in 3 acts: genesis, turbulence, resolution.
- Genesis should normally have no text cues in the first 2 seconds.
- Resolution should feel more ordered than genesis.
- If you include text_cues, each cue must have at most 5 words.
- Prefer top_zone and bottom_zone for narrative text. Reserve center or center_climax for the emotional peak.
- Camera cues, when useful, should be one of: static_breathe, track_subject, dramatic_zoom, observational.
{strict_block}

Registry:
{registry_json}

Required JSON shape:
{{
  "archetype": "emergence",
  "duration": 12,
  "pacing": "cinematic",
  "scenes": [
    {{
      "id": "intro",
      "duration": 3,
      "act": "genesis",
      "primitives": ["living_curve"],
      "params": {{"density": "low"}},
      "camera": "static_breathe",
      "layout_zone": "none",
      "text_cues": []
    }}
  ],
  "assets": {{
    "palette": "brand/tokens.json#dark_mode"
  }},
  "effects": ["grain_overlay"],
  "confidence": 0.85
}}

User prompt:
{prompt}
""".strip()


def _is_good_plan(plan: ScenePlan | None, metadata: dict[str, Any]) -> bool:
    if plan is None:
        return False
    return float(plan.confidence) >= confidence_threshold()


def _should_use_quality_fallback(first_attempt: dict[str, Any], route) -> bool:
    if not auto_quality_fallback_enabled():
        return False
    if not route.quality_fallback_model or route.task_type == TASK_QUALITY_PLAN:
        return False

    plan = first_attempt.get("plan")
    if plan is not None:
        return float(plan.confidence) < confidence_threshold()

    error = str(first_attempt.get("metadata", {}).get("error") or "")
    if not error:
        return False

    return error.startswith("Invalid JSON:") or error.startswith("Invalid ScenePlan schema:") or error == "Empty response"


def _finalize_route(route) -> None:
    if route.task_type == TASK_VISION_PLAN:
        unload_model(route.model, timeout=route.timeout_seconds)
    elif route.task_type == TASK_QUALITY_PLAN:
        unload_model(route.model, timeout=route.timeout_seconds)


def _latency_ms(start: float) -> int:
    return int((time.time() - start) * 1000)


def _empty_metadata(task_type: str) -> dict[str, Any]:
    return {
        "task_type": task_type,
        "model": None,
        "fallback_used": False,
        "from_cache": False,
        "confidence": None,
        "error": "Empty prompt",
        "latency_ms": 0,
        "route_model": None,
        "retry_count": 0,
        "retry_reason": None,
    }


def _return(plan: ScenePlan | None, metadata: dict[str, Any], return_metadata: bool):
    if return_metadata:
        return plan, metadata
    return plan


def _debug(message: str):
    if debug_enabled():
        print(f"[AIOX LLM] {message}")
