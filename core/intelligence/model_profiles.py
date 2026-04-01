from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from core.env_loader import load_repo_env

load_repo_env()


ROLE_FAST_PLAN = "fast_plan"
ROLE_PLAN = "plan"
ROLE_QUALITY_PLAN = "quality_plan"
ROLE_VISION_PLAN = "vision_plan"
ROLE_COPY_REFINER = "copy_refiner"
ROLE_VARIANT_RANKER = "variant_ranker"


@dataclass(frozen=True)
class RuntimeProfile:
    name: str
    provider: str
    description: str
    model_roles: dict[str, str]
    timeouts: dict[str, float]
    retry_timeouts: dict[str, float]
    render_preferences: dict[str, Any]
    # TurboQuant: server-level args for llama-server KV cache compression
    turbo_server_args: dict[str, Any] | None = None


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default).strip() or default


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


def _base_role_models() -> dict[str, str]:
    return {
        ROLE_FAST_PLAN: _env("OLLAMA_TEXT_FAST_MODEL", "qwen3:4b-instruct-2507-q4_K_M"),
        ROLE_PLAN: _env("OLLAMA_TEXT_MODEL", "qwen2.5:7b-instruct-q4_K_M"),
        ROLE_QUALITY_PLAN: _env("OLLAMA_TEXT_QUALITY_MODEL", "qwen2.5:14b-instruct-q4_K_M"),
        ROLE_VISION_PLAN: _env("OLLAMA_VISION_MODEL", "qwen3-vl:4b-instruct-q4_K_M"),
        ROLE_COPY_REFINER: _env("OLLAMA_COPY_REFINER_MODEL", _env("OLLAMA_TEXT_MODEL", "qwen2.5:7b-instruct-q4_K_M")),
        ROLE_VARIANT_RANKER: _env("OLLAMA_VARIANT_RANKER_MODEL", _env("OLLAMA_TEXT_FAST_MODEL", "qwen3:4b-instruct-2507-q4_K_M")),
    }


def _profile_timeout_map(plan: float, retry: float, *, fast: float | None = None, quality: float | None = None, vision: float | None = None, copy: float | None = None, variant: float | None = None) -> dict[str, float]:
    return {
        ROLE_FAST_PLAN: fast if fast is not None else max(10.0, plan - 4.0),
        ROLE_PLAN: plan,
        ROLE_QUALITY_PLAN: quality if quality is not None else retry,
        ROLE_VISION_PLAN: vision if vision is not None else retry,
        ROLE_COPY_REFINER: copy if copy is not None else plan,
        ROLE_VARIANT_RANKER: variant if variant is not None else max(8.0, plan - 6.0),
    }


def _profile_retry_map(plan: float, retry: float, *, fast: float | None = None, quality: float | None = None, vision: float | None = None, copy: float | None = None, variant: float | None = None) -> dict[str, float]:
    return {
        ROLE_FAST_PLAN: fast if fast is not None else max(14.0, retry - 8.0),
        ROLE_PLAN: retry,
        ROLE_QUALITY_PLAN: quality if quality is not None else retry,
        ROLE_VISION_PLAN: vision if vision is not None else retry,
        ROLE_COPY_REFINER: copy if copy is not None else retry,
        ROLE_VARIANT_RANKER: variant if variant is not None else max(12.0, retry - 10.0),
    }


def _default_profiles() -> dict[str, RuntimeProfile]:
    roles = _base_role_models()
    return {
        "air_m4_safe": RuntimeProfile(
            name="air_m4_safe",
            provider="ollama",
            description="Perfil conservador para Apple Silicon leve, priorizando estabilidade e fallback elegante.",
            model_roles=roles,
            timeouts=_profile_timeout_map(plan=_float_env("OLLAMA_TIMEOUT_PLAN_SECONDS", 18.0), retry=_float_env("OLLAMA_RETRY_TIMEOUT_PLAN_SECONDS", 30.0), fast=_float_env("OLLAMA_TIMEOUT_FAST_SECONDS", 14.0), quality=_float_env("OLLAMA_TIMEOUT_QUALITY_SECONDS", 45.0), vision=_float_env("OLLAMA_TIMEOUT_VISION_SECONDS", 30.0)),
            retry_timeouts=_profile_retry_map(plan=_float_env("OLLAMA_TIMEOUT_PLAN_SECONDS", 18.0), retry=_float_env("OLLAMA_RETRY_TIMEOUT_PLAN_SECONDS", 30.0), fast=_float_env("OLLAMA_RETRY_TIMEOUT_FAST_SECONDS", 22.0), quality=_float_env("OLLAMA_RETRY_TIMEOUT_QUALITY_SECONDS", 70.0), vision=_float_env("OLLAMA_RETRY_TIMEOUT_VISION_SECONDS", 45.0)),
            render_preferences={
                "max_parallel_renders": 1,
                "hero_target": "linkedin_feed_4_5",
                "prefer_native_still": True,
                "prefer_native_video": False,
                "variant_count": 3,
            },
        ),
        "air_m4_quality": RuntimeProfile(
            name="air_m4_quality",
            provider="ollama",
            description="Perfil premium para Apple Silicon com uso controlado de 14B e renders nativos seletivos.",
            model_roles={
                **roles,
                ROLE_COPY_REFINER: roles[ROLE_QUALITY_PLAN],
                ROLE_VARIANT_RANKER: roles[ROLE_QUALITY_PLAN],
            },
            timeouts=_profile_timeout_map(plan=24.0, retry=36.0, fast=16.0, quality=55.0, vision=36.0, copy=40.0, variant=16.0),
            retry_timeouts=_profile_retry_map(plan=24.0, retry=36.0, fast=24.0, quality=80.0, vision=50.0, copy=56.0, variant=22.0),
            render_preferences={
                "max_parallel_renders": 1,
                "hero_target": "linkedin_feed_4_5",
                "prefer_native_still": True,
                "prefer_native_video": True,
                "variant_count": 4,
            },
        ),
        "desktop_quality": RuntimeProfile(
            name="desktop_quality",
            provider="ollama",
            description="Perfil mais agressivo para máquinas com mais memória e throughput de render.",
            model_roles={
                **roles,
                ROLE_PLAN: roles[ROLE_QUALITY_PLAN],
                ROLE_COPY_REFINER: roles[ROLE_QUALITY_PLAN],
                ROLE_VARIANT_RANKER: roles[ROLE_PLAN],
            },
            timeouts=_profile_timeout_map(plan=20.0, retry=32.0, fast=12.0, quality=40.0, vision=24.0, copy=28.0, variant=12.0),
            retry_timeouts=_profile_retry_map(plan=20.0, retry=32.0, fast=18.0, quality=60.0, vision=36.0, copy=40.0, variant=18.0),
            render_preferences={
                "max_parallel_renders": 2,
                "hero_target": "linkedin_feed_4_5",
                "prefer_native_still": True,
                "prefer_native_video": True,
                "variant_count": 5,
            },
        ),
        # ---------------------------------------------------------------
        # TurboQuant profiles — use llama-server with KV cache compression
        # Enables larger models + longer context on Apple Silicon
        # ---------------------------------------------------------------
        "turbo": RuntimeProfile(
            name="turbo",
            provider="turbo",
            description=(
                "TurboQuant turbo4 (3.8x KV compression). "
                "Bumps fast 4B→14B, plan 7B→14B. 32K context on Apple Silicon."
            ),
            model_roles={
                ROLE_FAST_PLAN: _env("AIOX_TURBO_FAST_MODEL", "qwen2.5:14b-instruct-q4_K_M"),
                ROLE_PLAN: _env("AIOX_TURBO_PLAN_MODEL", "qwen2.5:14b-instruct-q4_K_M"),
                ROLE_QUALITY_PLAN: _env("AIOX_TURBO_QUALITY_MODEL", "qwen2.5:14b-instruct-q4_K_M"),
                ROLE_VISION_PLAN: _env("OLLAMA_VISION_MODEL", "qwen3-vl:4b-instruct-q4_K_M"),
                ROLE_COPY_REFINER: _env("AIOX_TURBO_PLAN_MODEL", "qwen2.5:14b-instruct-q4_K_M"),
                ROLE_VARIANT_RANKER: _env("AIOX_TURBO_FAST_MODEL", "qwen2.5:14b-instruct-q4_K_M"),
            },
            timeouts=_profile_timeout_map(
                plan=30.0, retry=50.0,
                fast=20.0, quality=60.0, vision=36.0, copy=40.0, variant=20.0,
            ),
            retry_timeouts=_profile_retry_map(
                plan=30.0, retry=50.0,
                fast=30.0, quality=90.0, vision=50.0, copy=60.0, variant=30.0,
            ),
            render_preferences={
                "max_parallel_renders": 1,
                "hero_target": "linkedin_feed_4_5",
                "prefer_native_still": True,
                "prefer_native_video": True,
                "variant_count": 4,
            },
            turbo_server_args={
                "cache_type_k": "q8_0",
                "cache_type_v": "turbo4",
                "flash_attention": True,
                "context_length": 32768,
            },
        ),
        "turbo_max": RuntimeProfile(
            name="turbo_max",
            provider="turbo",
            description=(
                "TurboQuant turbo3 (4.9x KV compression). "
                "Maximum: 32B quality model with 32K context. Slowest but best quality."
            ),
            model_roles={
                ROLE_FAST_PLAN: _env("AIOX_TURBO_FAST_MODEL", "qwen2.5:14b-instruct-q4_K_M"),
                ROLE_PLAN: _env("AIOX_TURBO_PLAN_MODEL", "qwen2.5:14b-instruct-q4_K_M"),
                ROLE_QUALITY_PLAN: _env("AIOX_TURBO_MAX_QUALITY_MODEL", "qwen2.5:32b-instruct-q4_K_M"),
                ROLE_VISION_PLAN: _env("OLLAMA_VISION_MODEL", "qwen3-vl:4b-instruct-q4_K_M"),
                ROLE_COPY_REFINER: _env("AIOX_TURBO_MAX_QUALITY_MODEL", "qwen2.5:32b-instruct-q4_K_M"),
                ROLE_VARIANT_RANKER: _env("AIOX_TURBO_PLAN_MODEL", "qwen2.5:14b-instruct-q4_K_M"),
            },
            timeouts=_profile_timeout_map(
                plan=45.0, retry=80.0,
                fast=25.0, quality=90.0, vision=45.0, copy=60.0, variant=25.0,
            ),
            retry_timeouts=_profile_retry_map(
                plan=45.0, retry=80.0,
                fast=40.0, quality=120.0, vision=60.0, copy=80.0, variant=40.0,
            ),
            render_preferences={
                "max_parallel_renders": 1,
                "hero_target": "linkedin_feed_4_5",
                "prefer_native_still": True,
                "prefer_native_video": True,
                "variant_count": 5,
            },
            turbo_server_args={
                "cache_type_k": "q8_0",
                "cache_type_v": "turbo3",
                "flash_attention": True,
                "context_length": 32768,
            },
        ),
    }


def available_profiles() -> dict[str, RuntimeProfile]:
    return _default_profiles()


@lru_cache(maxsize=1)
def _detected_model_ids() -> set[str]:
    try:
        from core.intelligence.model_capabilities import load_model_capabilities, refresh_model_capabilities

        capabilities = load_model_capabilities()
        if not capabilities:
            capabilities = refresh_model_capabilities()
        return {entry.id for entry in capabilities}
    except Exception:
        return set()


def _has_quality_stack() -> bool:
    model_ids = _detected_model_ids()
    return (
        "qwen2.5:14b-instruct-q4_K_M" in model_ids
        and "qwen2.5:7b-instruct-q4_K_M" in model_ids
        and "qwen3-vl:4b-instruct-q4_K_M" in model_ids
    )


def detect_default_profile_name() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "darwin" and machine == "arm64":
        if _has_quality_stack():
            return "air_m4_quality"
        return "air_m4_safe"
    return "desktop_quality"


def get_active_profile_name() -> str:
    explicit = os.environ.get("AIOX_MODEL_PROFILE", "").strip().lower()
    profiles = available_profiles()
    if explicit in profiles:
        return explicit
    return detect_default_profile_name()


def get_profile(name: str | None = None) -> RuntimeProfile:
    profiles = available_profiles()
    profile_name = (name or get_active_profile_name()).strip().lower()
    return profiles.get(profile_name, profiles[detect_default_profile_name()])


def get_active_profile() -> RuntimeProfile:
    return get_profile()
