from __future__ import annotations

import importlib.util
from dataclasses import asdict, dataclass
from typing import Any

from core.intelligence.model_capabilities import load_model_capabilities, refresh_model_capabilities
from core.intelligence.model_profiles import get_active_profile, get_profile


@dataclass(frozen=True)
class RoleResolution:
    role: str
    provider: str
    model: str
    available: bool
    supports_vision: bool
    quality_band: str
    context_budget: int
    observed_latency_ms: float | None


def _provider_available(name: str) -> bool:
    if name == "ollama":
        try:
            return bool(refresh_model_capabilities())
        except Exception:
            return False
    if name == "mlx_vlm":
        return importlib.util.find_spec("mlx_vlm") is not None
    if name == "hf_transformers":
        return importlib.util.find_spec("transformers") is not None
    return False


def resolve_model_roles(profile_name: str | None = None) -> dict[str, RoleResolution]:
    profile = get_profile(profile_name) if profile_name else get_active_profile()
    capabilities = {entry.id: entry for entry in (load_model_capabilities() or refresh_model_capabilities())}
    resolutions: dict[str, RoleResolution] = {}
    provider_ok = _provider_available(profile.provider)

    for role, model in profile.model_roles.items():
        capability = capabilities.get(model)
        resolutions[role] = RoleResolution(
            role=role,
            provider=profile.provider,
            model=model,
            available=provider_ok and (capability is not None or profile.provider != "ollama"),
            supports_vision=bool(getattr(capability, "supports_vision_plan", False)),
            quality_band=str(getattr(capability, "quality_band", "unknown")),
            context_budget=int(getattr(capability, "context_budget", 0) or 0),
            observed_latency_ms=getattr(capability, "observed_latency_ms", None),
        )
    return resolutions


def build_runtime_os_report(profile_name: str | None = None) -> dict[str, Any]:
    profile = get_profile(profile_name) if profile_name else get_active_profile()
    roles = resolve_model_roles(profile.name)
    role_payload = {role: asdict(data) for role, data in roles.items()}
    judges = {
        "visual_judge_fast": role_payload.get("visual_judge_fast"),
        "visual_judge_heavy": role_payload.get("visual_judge_heavy"),
        "variant_ranker": role_payload.get("variant_ranker"),
    }
    return {
        "profile": profile.name,
        "provider": profile.provider,
        "providers": {
            "ollama": _provider_available("ollama"),
            "mlx_vlm": _provider_available("mlx_vlm"),
            "hf_transformers": _provider_available("hf_transformers"),
        },
        "roles": role_payload,
        "judges": judges,
        "judge_stack": list(profile.render_preferences.get("judge_stack", [])),
        "lab": {
            "enabled": profile.name in {"air_m4_lab", "desktop_lab"},
            "hero_target": profile.render_preferences.get("hero_target", "linkedin_feed_4_5"),
            "variant_count": int(profile.render_preferences.get("variant_count", 3) or 3),
        },
    }
