from __future__ import annotations

import os
from dataclasses import dataclass

from core.env_loader import load_repo_env

load_repo_env()


TASK_PLAN = "plan"
TASK_FAST_PLAN = "fast_plan"
TASK_QUALITY_PLAN = "quality_plan"
TASK_VISION_PLAN = "vision_plan"


@dataclass(frozen=True)
class ModelRoute:
    task_type: str
    model: str
    keep_alive: str
    timeout_seconds: float
    retry_timeout_seconds: float
    quality_fallback_model: str | None = None


def get_route(task_type: str = TASK_PLAN, prefer_quality: bool = False) -> ModelRoute:
    forced = os.environ.get("AIOX_LLM_FORCE_MODEL", "").strip()
    routing_mode = os.environ.get("AIOX_LLM_ROUTING_MODE", "auto").strip().lower()
    timeout = _get_float("OLLAMA_TIMEOUT_SECONDS", 14.0)
    retry_timeout = _get_float("OLLAMA_RETRY_TIMEOUT_SECONDS", 22.0)

    if forced:
        keep_alive = _keep_alive_for_task(task_type)
        return ModelRoute(
            task_type=task_type,
            model=forced,
            keep_alive=keep_alive,
            timeout_seconds=retry_timeout if prefer_quality else timeout,
            retry_timeout_seconds=retry_timeout,
            quality_fallback_model=None,
        )

    if routing_mode == "quality" and task_type == TASK_PLAN:
        prefer_quality = True

    if routing_mode == "fast" and task_type == TASK_PLAN:
        task_type = TASK_FAST_PLAN

    if task_type == TASK_FAST_PLAN:
        return ModelRoute(
            task_type=task_type,
            model=os.environ.get("OLLAMA_TEXT_FAST_MODEL", "qwen3:4b-instruct-2507-q4_K_M"),
            keep_alive=os.environ.get("OLLAMA_KEEP_ALIVE_FAST", "4m"),
            timeout_seconds=timeout,
            retry_timeout_seconds=retry_timeout,
            quality_fallback_model=_quality_model(),
        )

    if task_type == TASK_QUALITY_PLAN:
        return ModelRoute(
            task_type=task_type,
            model=_quality_model(),
            keep_alive=os.environ.get("OLLAMA_KEEP_ALIVE_QUALITY", "2m"),
            timeout_seconds=retry_timeout,
            retry_timeout_seconds=retry_timeout,
            quality_fallback_model=None,
        )

    if task_type == TASK_VISION_PLAN:
        return ModelRoute(
            task_type=task_type,
            model=os.environ.get("OLLAMA_VISION_MODEL", "qwen3-vl:4b-instruct-q4_K_M"),
            keep_alive=os.environ.get("OLLAMA_KEEP_ALIVE_VISION", "0"),
            timeout_seconds=retry_timeout,
            retry_timeout_seconds=retry_timeout,
            quality_fallback_model=None,
        )

    if prefer_quality:
        return get_route(TASK_QUALITY_PLAN, prefer_quality=False)

    return ModelRoute(
        task_type=task_type,
        model=os.environ.get("OLLAMA_TEXT_MODEL", "qwen2.5:7b-instruct-q4_K_M"),
        keep_alive=os.environ.get("OLLAMA_KEEP_ALIVE_TEXT", "8m"),
        timeout_seconds=timeout,
        retry_timeout_seconds=retry_timeout,
        quality_fallback_model=_quality_model(),
    )


def confidence_threshold() -> float:
    return _get_float("AIOX_LLM_CONFIDENCE_THRESHOLD", 0.70)


def allow_quality_fallback() -> bool:
    return os.environ.get("AIOX_LLM_DISABLE_QUALITY_FALLBACK", "0").strip() not in {"1", "true", "yes"}


def debug_enabled() -> bool:
    return os.environ.get("AIOX_LLM_DEBUG", "0").strip() in {"1", "true", "yes"}


def _quality_model() -> str:
    return os.environ.get("OLLAMA_TEXT_QUALITY_MODEL", "qwen2.5:14b-instruct-q4_K_M")


def _keep_alive_for_task(task_type: str) -> str:
    if task_type == TASK_FAST_PLAN:
        return os.environ.get("OLLAMA_KEEP_ALIVE_FAST", "4m")
    if task_type == TASK_QUALITY_PLAN:
        return os.environ.get("OLLAMA_KEEP_ALIVE_QUALITY", "2m")
    if task_type == TASK_VISION_PLAN:
        return os.environ.get("OLLAMA_KEEP_ALIVE_VISION", "0")
    return os.environ.get("OLLAMA_KEEP_ALIVE_TEXT", "8m")


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default
