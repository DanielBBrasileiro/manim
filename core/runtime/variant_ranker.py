from __future__ import annotations

import json
import os
from typing import Any

from core.intelligence.model_router import TASK_VARIANT_RANKER, get_route
from core.intelligence.ollama_client import OLLAMA_URL, _base_url, _post_json


def _heuristic_score(variant: dict[str, Any], artifact_plan: dict[str, Any]) -> tuple[float, list[str]]:
    score = 50.0
    reasons: list[str] = []
    hero_target = str(variant.get("hero_target", "")).strip()
    if hero_target == "linkedin_feed_4_5":
        score += 8
        reasons.append("hero_target_alignment")
    if str(variant.get("composition_mode", "")).strip() in {"poster_focus", "single_metaphor", "resolve_lockup"}:
        score += 10
        reasons.append("composition_mode_premium")
    if str(variant.get("typography_behavior", "")).strip() in {"quiet_hierarchy", "thesis_poster", "hero_lockup"}:
        score += 10
        reasons.append("typography_behavior_premium")
    if str(variant.get("shot_grammar", "")).strip() in {"single_curve", "contained_break", "mid_event_flip"}:
        score += 12
        reasons.append("shot_grammar_signal")
    style_pack = str(variant.get("style_pack_id", "")).strip()
    style_hits = {
        str(item.get("pack_id", "")).strip(): float(item.get("score", 0.0) or 0.0)
        for item in artifact_plan.get("style_retrieval_results", [])
        if isinstance(item, dict)
    }
    if style_pack in style_hits:
        score += style_hits[style_pack] * 20
        reasons.append("style_retrieval_match")
    return round(score, 2), reasons


def _llm_rank_variants(artifact_plan: dict[str, Any]) -> dict[str, Any] | None:
    if os.getenv("AIOX_VARIANT_RANKER_DISABLE_LLM", "").strip().lower() in {"1", "true", "yes", "on"}:
        return None
    route = get_route(TASK_VARIANT_RANKER)
    variants = artifact_plan.get("variants", [])
    if not variants:
        return None
    timeout_seconds = route.timeout_seconds
    timeout_override = os.getenv("AIOX_VARIANT_RANKER_TIMEOUT_SECONDS", "").strip()
    if timeout_override:
        try:
            timeout_seconds = max(1.0, float(timeout_override))
        except ValueError:
            timeout_seconds = route.timeout_seconds
    payload = {
        "model": route.model,
        "stream": False,
        "keep_alive": route.keep_alive,
        "format": {
            "type": "object",
            "properties": {
                "chosen_variant": {"type": "string"},
                "variant_scores": {"type": "object"},
                "chosen_variant_reason": {"type": "string"},
            },
            "required": ["chosen_variant", "variant_scores", "chosen_variant_reason"],
        },
        "prompt": (
            "Rank these AIOX creative variants for premium visual quality, narrative authority, "
            "negative space, hook strength, and elegance. Return JSON only.\n\n"
            f"Story atoms:\n{json.dumps(artifact_plan.get('story_atoms', {}), ensure_ascii=True)}\n\n"
            f"Family spec:\n{json.dumps(artifact_plan.get('family_spec', {}), ensure_ascii=True)}\n\n"
            f"Variants:\n{json.dumps(variants, ensure_ascii=True)}"
        ),
        "options": {"temperature": 0.1},
    }
    try:
        response = _post_json(_base_url(OLLAMA_URL) + "/api/generate", payload, timeout=timeout_seconds)
        raw = response.get("response", "")
        parsed = json.loads(raw) if isinstance(raw, str) and raw.strip() else {}
        if isinstance(parsed, dict) and parsed.get("chosen_variant"):
            return parsed
    except Exception:
        return None
    return None


def rank_variants(artifact_plan: dict[str, Any]) -> dict[str, Any]:
    variants = [variant for variant in artifact_plan.get("variants", []) if isinstance(variant, dict)]
    if not variants:
        return {"chosen_variant": "", "variant_scores": {}, "chosen_variant_reason": "no_variants"}

    llm_result = _llm_rank_variants(artifact_plan)
    if llm_result:
        return {
            "chosen_variant": str(llm_result.get("chosen_variant", "")).strip() or variants[0].get("id", "variant_01"),
            "variant_scores": llm_result.get("variant_scores", {}),
            "chosen_variant_reason": str(llm_result.get("chosen_variant_reason", "llm_ranked")).strip() or "llm_ranked",
        }

    scored: list[tuple[str, float, list[str]]] = []
    for variant in variants:
        variant_id = str(variant.get("id", "")).strip()
        score, reasons = _heuristic_score(variant, artifact_plan)
        scored.append((variant_id, score, reasons))
    scored.sort(key=lambda item: item[1], reverse=True)
    chosen_variant, _, chosen_reasons = scored[0]
    return {
        "chosen_variant": chosen_variant,
        "variant_scores": {variant_id: {"score": score, "reasons": reasons} for variant_id, score, reasons in scored},
        "chosen_variant_reason": ",".join(chosen_reasons) if chosen_reasons else "heuristic_ranked",
    }
