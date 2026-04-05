from __future__ import annotations

import os
from dataclasses import dataclass

from core.env_loader import load_repo_env
from core.intelligence.model_profiles import (
    ROLE_COPY_REFINER,
    ROLE_FAST_PLAN,
    ROLE_PLAN,
    ROLE_QUALITY_PLAN,
    ROLE_REFERENCE_PARSER,
    ROLE_VISUAL_JUDGE_FAST,
    ROLE_VISUAL_JUDGE_HEAVY,
    ROLE_TEXT_RERANKER,
    ROLE_STYLE_RETRIEVER,
    ROLE_CONCEPT_ARTIST,
    ROLE_THUMBNAIL_REFINER,
    ROLE_VARIANT_RANKER,
    ROLE_VISION_PLAN,
    get_active_profile,
)

load_repo_env()


TASK_PLAN = ROLE_PLAN
TASK_FAST_PLAN = ROLE_FAST_PLAN
TASK_QUALITY_PLAN = ROLE_QUALITY_PLAN
TASK_VISION_PLAN = ROLE_VISION_PLAN
TASK_COPY_REFINER = ROLE_COPY_REFINER
TASK_VARIANT_RANKER = ROLE_VARIANT_RANKER
TASK_REFERENCE_PARSER = ROLE_REFERENCE_PARSER
TASK_VISUAL_JUDGE_FAST = ROLE_VISUAL_JUDGE_FAST
TASK_VISUAL_JUDGE_HEAVY = ROLE_VISUAL_JUDGE_HEAVY
TASK_TEXT_RERANKER = ROLE_TEXT_RERANKER
TASK_STYLE_RETRIEVER = ROLE_STYLE_RETRIEVER
TASK_CONCEPT_ARTIST = ROLE_CONCEPT_ARTIST
TASK_THUMBNAIL_REFINER = ROLE_THUMBNAIL_REFINER


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
    profile = get_active_profile()
    timeout = _timeout_for_task(task_type, retry=False, default=14.0, profile_timeouts=profile.timeouts)
    retry_timeout = _timeout_for_task(task_type, retry=True, default=22.0, profile_timeouts=profile.retry_timeouts)

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
            model=profile.model_roles.get(TASK_FAST_PLAN, os.environ.get("OLLAMA_TEXT_FAST_MODEL", "qwen3:4b-instruct-2507-q4_K_M")),
            keep_alive=os.environ.get("OLLAMA_KEEP_ALIVE_FAST", "4m"),
            timeout_seconds=timeout,
            retry_timeout_seconds=retry_timeout,
            quality_fallback_model=_quality_model(),
        )

    if task_type == TASK_QUALITY_PLAN:
        return ModelRoute(
            task_type=task_type,
            model=profile.model_roles.get(TASK_QUALITY_PLAN, _quality_model()),
            keep_alive=os.environ.get("OLLAMA_KEEP_ALIVE_QUALITY", "0"),
            timeout_seconds=retry_timeout,
            retry_timeout_seconds=retry_timeout,
            quality_fallback_model=None,
        )

    if task_type == TASK_VISION_PLAN:
        return ModelRoute(
            task_type=task_type,
            model=profile.model_roles.get(TASK_VISION_PLAN, os.environ.get("OLLAMA_VISION_MODEL", "qwen3-vl:4b-instruct-q4_K_M")),
            keep_alive=os.environ.get("OLLAMA_KEEP_ALIVE_VISION", "0"),
            timeout_seconds=retry_timeout,
            retry_timeout_seconds=retry_timeout,
            quality_fallback_model=None,
        )

    if task_type == TASK_COPY_REFINER:
        return ModelRoute(
            task_type=task_type,
            model=profile.model_roles.get(TASK_COPY_REFINER, os.environ.get("OLLAMA_TEXT_MODEL", "qwen2.5:7b-instruct-q4_K_M")),
            keep_alive=os.environ.get("OLLAMA_KEEP_ALIVE_TEXT", "8m"),
            timeout_seconds=timeout,
            retry_timeout_seconds=retry_timeout,
            quality_fallback_model=profile.model_roles.get(TASK_QUALITY_PLAN, _quality_model()),
        )

    if task_type in {
        TASK_REFERENCE_PARSER,
        TASK_VISUAL_JUDGE_FAST,
        TASK_VISUAL_JUDGE_HEAVY,
        TASK_CONCEPT_ARTIST,
        TASK_THUMBNAIL_REFINER,
    }:
        return ModelRoute(
            task_type=task_type,
            model=profile.model_roles.get(task_type, os.environ.get("OLLAMA_VISION_MODEL", "qwen3-vl:4b-instruct-q4_K_M")),
            keep_alive=os.environ.get("OLLAMA_KEEP_ALIVE_VISION", "0"),
            timeout_seconds=retry_timeout,
            retry_timeout_seconds=retry_timeout,
            quality_fallback_model=None,
        )

    if task_type in {TASK_TEXT_RERANKER, TASK_STYLE_RETRIEVER}:
        return ModelRoute(
            task_type=task_type,
            model=profile.model_roles.get(task_type, _quality_model()),
            keep_alive=os.environ.get("OLLAMA_KEEP_ALIVE_QUALITY", "0"),
            timeout_seconds=retry_timeout,
            retry_timeout_seconds=retry_timeout,
            quality_fallback_model=None,
        )

    if task_type == TASK_VARIANT_RANKER:
        return ModelRoute(
            task_type=task_type,
            model=profile.model_roles.get(TASK_VARIANT_RANKER, os.environ.get("OLLAMA_TEXT_FAST_MODEL", "qwen3:4b-instruct-2507-q4_K_M")),
            keep_alive=os.environ.get("OLLAMA_KEEP_ALIVE_FAST", "4m"),
            timeout_seconds=timeout,
            retry_timeout_seconds=retry_timeout,
            quality_fallback_model=profile.model_roles.get(TASK_QUALITY_PLAN, _quality_model()),
        )

    if prefer_quality:
        return get_route(TASK_QUALITY_PLAN, prefer_quality=False)

    return ModelRoute(
        task_type=task_type,
        model=profile.model_roles.get(TASK_PLAN, os.environ.get("OLLAMA_TEXT_MODEL", "qwen2.5:7b-instruct-q4_K_M")),
        keep_alive=os.environ.get("OLLAMA_KEEP_ALIVE_TEXT", "8m"),
        timeout_seconds=timeout,
        retry_timeout_seconds=retry_timeout,
        quality_fallback_model=_quality_model(),
    )


def confidence_threshold() -> float:
    return _get_float("AIOX_LLM_CONFIDENCE_THRESHOLD", 0.70)


def allow_quality_fallback() -> bool:
    return os.environ.get("AIOX_LLM_DISABLE_QUALITY_FALLBACK", "0").strip() not in {"1", "true", "yes"}


def quality_fallback_mode() -> str:
    mode = os.environ.get("AIOX_LLM_QUALITY_FALLBACK_MODE", "explicit").strip().lower()
    if mode in {"auto", "explicit", "off"}:
        return mode
    return "explicit"


def auto_quality_fallback_enabled() -> bool:
    return allow_quality_fallback() and quality_fallback_mode() == "auto"


def debug_enabled() -> bool:
    return os.environ.get("AIOX_LLM_DEBUG", "0").strip() in {"1", "true", "yes"}


def _quality_model() -> str:
    return os.environ.get("OLLAMA_TEXT_QUALITY_MODEL", "qwen2.5:14b-instruct-q4_K_M")


def _keep_alive_for_task(task_type: str) -> str:
    if task_type == TASK_FAST_PLAN:
        return os.environ.get("OLLAMA_KEEP_ALIVE_FAST", "4m")
    if task_type == TASK_QUALITY_PLAN:
        return os.environ.get("OLLAMA_KEEP_ALIVE_QUALITY", "0")
    if task_type == TASK_VISION_PLAN:
        return os.environ.get("OLLAMA_KEEP_ALIVE_VISION", "0")
    return os.environ.get("OLLAMA_KEEP_ALIVE_TEXT", "8m")


def _timeout_for_task(task_type: str, retry: bool, default: float, profile_timeouts: dict[str, float] | None = None) -> float:
    prefix = "OLLAMA_RETRY_TIMEOUT_" if retry else "OLLAMA_TIMEOUT_"
    generic_name = "OLLAMA_RETRY_TIMEOUT_SECONDS" if retry else "OLLAMA_TIMEOUT_SECONDS"

    if task_type == TASK_FAST_PLAN:
        task_name = f"{prefix}FAST_SECONDS"
    elif task_type == TASK_QUALITY_PLAN:
        task_name = f"{prefix}QUALITY_SECONDS"
    elif task_type == TASK_VISION_PLAN:
        task_name = f"{prefix}VISION_SECONDS"
    else:
        task_name = f"{prefix}PLAN_SECONDS"

    if profile_timeouts and task_type in profile_timeouts:
        default = float(profile_timeouts[task_type])
    return _get_float(task_name, _get_float(generic_name, default))


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default
