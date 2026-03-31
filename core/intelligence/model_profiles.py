from __future__ import annotations

import os
import platform
from dataclasses import dataclass
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
                ROLE_VARIANT_RANKER: roles[ROLE_PLAN],
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
    }


def available_profiles() -> dict[str, RuntimeProfile]:
    return _default_profiles()


def detect_default_profile_name() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "darwin" and machine == "arm64":
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
