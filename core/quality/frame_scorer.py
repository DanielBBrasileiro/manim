"""
frame_scorer.py — Vision-LLM quality scoring for rendered frames.

Uses the vision model (Qwen3-VL or equivalent) to evaluate rendered
frames against the AIOX premium design checklist derived from
contracts/global_laws.yaml and brand DNA.

Scoring dimensions are now artifact-aware and loaded from judge profiles.
Stills use the premium_still profile; motion uses the motion_frame profile.
"""

from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.env_loader import load_repo_env
from core.quality.brand_validator import validate_frame

load_repo_env()


# ---------------------------------------------------------------------------
# Quality checklist (derived from contracts/global_laws.yaml)
# ---------------------------------------------------------------------------

LEGACY_QUALITY_DIMENSIONS = {
    "composition": {
        "weight": 0.25,
        "criteria": [
            "Negative space >= 40% of frame area",
            "Visual hierarchy is clear (1 focal point)",
            "Elements are balanced (not cluttered)",
            "Safe zone respected (no content bleeding edges)",
        ],
    },
    "typography": {
        "weight": 0.20,
        "criteria": [
            "Max 2 font weights used",
            "Max 5 words per screen",
            "No serif fonts",
            "No uppercase prose (only labels/titles)",
            "Text is readable against background",
        ],
    },
    "color": {
        "weight": 0.20,
        "criteria": [
            "Max 2 colors in palette",
            "No gradients",
            "Sufficient contrast ratio",
            "Colors feel cohesive and intentional",
        ],
    },
    "motion_signature": {
        "weight": 0.15,
        "criteria": [
            "Implied sense of movement/tension in still frame",
            "Visual rhythm matches intended pacing",
            "Elements suggest physical behavior (gravity, momentum)",
        ],
    },
    "brand_compliance": {
        "weight": 0.20,
        "criteria": [
            "No logos present",
            "No drop shadows",
            "No gradients",
            "Minimalist aesthetic upheld",
            "Premium feel — no cheap/generic patterns",
        ],
    },
}


@dataclass(frozen=True)
class DimensionScore:
    """Score for a single quality dimension."""
    name: str
    score: int  # 0-100
    weight: float
    issues: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class FrameScore:
    """Complete quality assessment of a single frame."""
    frame_path: str
    dimensions: list[DimensionScore] = field(default_factory=list)
    composite_score: float = 0.0
    passed: bool = False
    raw_llm_response: str = ""
    latency_ms: float = 0.0
    model_used: str = ""
    judge_profile: str = ""
    threshold_used: float = 70.0
    artifact_class: str = ""
    hard_veto: bool = False
    hard_veto_reasons: list[dict[str, Any]] = field(default_factory=list)
    objective_signals: dict[str, Any] = field(default_factory=dict)
    quality_band: str = "unscored"
    structural_invalidity: bool = False
    premium_shortfall: bool = False
    error: str | None = None

    def compute_composite(self) -> float:
        if not self.dimensions:
            return 0.0
        total_weight = sum(d.weight for d in self.dimensions)
        if total_weight == 0:
            return 0.0
        self.composite_score = sum(
            d.score * d.weight for d in self.dimensions
        ) / total_weight
        return self.composite_score

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_path": self.frame_path,
            "composite_score": round(self.composite_score, 1),
            "passed": self.passed,
            "dimensions": [
                {
                    "name": d.name,
                    "score": d.score,
                    "weight": d.weight,
                    "issues": d.issues,
                    "notes": d.notes,
                }
                for d in self.dimensions
            ],
            "latency_ms": round(self.latency_ms, 2),
            "model": self.model_used,
            "judge_profile": self.judge_profile,
            "threshold_used": round(self.threshold_used, 1),
            "artifact_class": self.artifact_class,
            "hard_veto": self.hard_veto,
            "hard_veto_reasons": self.hard_veto_reasons,
            "objective_signals": self.objective_signals,
            "quality_band": self.quality_band,
            "structural_invalidity": self.structural_invalidity,
            "premium_shortfall": self.premium_shortfall,
            "error": self.error,
        }

    def summary_line(self) -> str:
        icon = "✓" if self.passed else "✗"
        dims = " | ".join(
            f"{d.name[:4]}={d.score}" for d in self.dimensions
        )
        return f"{icon} {self.composite_score:.0f}/100 [{dims}] {self.quality_band} — {Path(self.frame_path).name}"


# ---------------------------------------------------------------------------
# Vision prompt construction
# ---------------------------------------------------------------------------

def _normalize_render_mode(render_mode: str | None) -> str:
    mode = str(render_mode or "still").strip().lower()
    if mode in {"still", "image", "poster", "premium_still", "thumbnail"}:
        return "still"
    return "motion"


def _resolve_judge_profile(context: dict[str, Any] | None, render_mode: str) -> dict[str, Any]:
    """Build the vision scoring prompt with unified brand context."""
    from core.quality.contract_loader import load_quality_contract

    contract = load_quality_contract()
    profile_id = ""
    if isinstance(context, dict):
        profile_id = str(
            context.get("judge_profile")
            or context.get("judge_profile_id")
            or ""
        ).strip()
    profile = contract.get_judge_profile(render_mode, profile_id)
    if not profile:
        profile = {
            "id": f"legacy_{render_mode}",
            "dimensions": LEGACY_QUALITY_DIMENSIONS,
        }
    return profile


def _resolve_threshold(threshold: float, judge_profile: dict[str, Any]) -> float:
    profile_threshold = float(judge_profile.get("threshold", threshold) or threshold)
    return max(float(threshold or 0.0), profile_threshold)


def _objective_signal_block(signals: dict[str, Any]) -> str:
    if not signals:
        return ""

    lines = [
        f"HARD_VETO: {signals.get('hard_veto', False)}",
        f"NEGATIVE_SPACE_PCT: {signals.get('negative_space_pct', 0.0)}",
        f"TEXT_DENSITY_ESTIMATE: {signals.get('text_density_estimate', 0)}",
        f"COLOR_PURITY_SCORE: {signals.get('color_purity_score', 0.0)}",
        f"GRAIN_VARIANCE: {signals.get('grain_variance', 0.0)}",
    ]
    if "recommended_negative_space_target" in signals:
        lines.append(f"NEGATIVE_SPACE_TARGET: {signals['recommended_negative_space_target']}")
    if "max_words_per_screen" in signals:
        lines.append(f"MAX_WORDS_PER_SCREEN: {signals['max_words_per_screen']}")
    if "silence_ratio" in signals:
        lines.append(f"SILENCE_RATIO: {signals['silence_ratio']}")
    if "minimum_hold_ms" in signals:
        lines.append(f"MINIMUM_HOLD_MS: {signals['minimum_hold_ms']}")
    if "breath_points_count" in signals:
        lines.append(f"BREATH_POINTS_COUNT: {signals['breath_points_count']}")
    if "transition_hint" in signals:
        lines.append(f"TRANSITION_HINT: {signals['transition_hint']}")
    if signals.get("hard_veto_codes"):
        lines.append(f"HARD_VETO_CODES: {', '.join(signals['hard_veto_codes'])}")
    return "\n# OBJECTIVE SIGNALS\n" + "\n".join(lines) + "\n"


def _collect_objective_signals(frame_path: str, context: dict[str, Any] | None, render_mode: str) -> dict[str, Any]:
    context = context or {}
    brand_result = validate_frame(frame_path)
    act_profile = context.get("act_quality_profile", {})
    profiles = [value for value in act_profile.values() if isinstance(value, dict)] if isinstance(act_profile, dict) else []
    silence_values = [float(item.get("silence_ratio", 0.0) or 0.0) for item in profiles]
    hold_values = [int(item.get("minimum_hold_ms", 0) or 0) for item in profiles]
    stagger_sizes = [len(item.get("stagger_profile", []) or []) for item in profiles]
    breath_points_count = sum(len(item.get("breath_points", []) or []) for item in profiles)
    transition_hint = next(
        (str(item.get("transition_to", "")).strip() for item in profiles if str(item.get("transition_to", "")).strip()),
        "",
    )
    hard_veto_reasons = list((context or {}).get("hard_veto_reasons", []) or [])
    if not hard_veto_reasons and brand_result.hard_veto_reasons:
        hard_veto_reasons = list(brand_result.hard_veto_reasons)

    return {
        "render_mode": render_mode,
        "color_purity_score": float(brand_result.color_purity_score or 0.0),
        "negative_space_pct": float(brand_result.negative_space_pct or 0.0),
        "text_density_estimate": int(brand_result.text_density_estimate or 0),
        "grain_variance": float(brand_result.grain_variance or 0.0),
        "recommended_negative_space_target": float((context or {}).get("negative_space_target", 0.4) or 0.4),
        "max_words_per_screen": int((context or {}).get("max_words_per_screen", 5) or 5),
        "silence_ratio": round(sum(silence_values) / len(silence_values), 3) if silence_values else float((context or {}).get("silence_ratio", 0.0) or 0.0),
        "minimum_hold_ms": round(sum(hold_values) / len(hold_values), 1) if hold_values else 0.0,
        "stagger_count": round(sum(stagger_sizes) / len(stagger_sizes), 2) if stagger_sizes else 0.0,
        "breath_points_count": breath_points_count,
        "transition_hint": transition_hint or str((context or {}).get("transition_to", "")).strip(),
        "hard_veto": bool(hard_veto_reasons),
        "hard_veto_codes": [str(item.get("code", "")).strip() for item in hard_veto_reasons if isinstance(item, dict)],
        "hard_veto_reasons": hard_veto_reasons,
        "brand_validation_passed": bool(brand_result.passed),
    }


def _veto_dimensions(judge_profile: dict[str, Any], hard_veto_reasons: list[dict[str, Any]]) -> list[DimensionScore]:
    dimension_specs = judge_profile.get("dimensions", {}) if isinstance(judge_profile.get("dimensions", {}), dict) else {}
    if not dimension_specs:
        dimension_specs = LEGACY_QUALITY_DIMENSIONS
    veto_messages = [
        str(item.get("detail", "Structural veto triggered.")).strip()
        for item in hard_veto_reasons
        if isinstance(item, dict)
    ] or ["Structural veto triggered."]
    dimensions: list[DimensionScore] = []
    for dim_name, dim_info in dimension_specs.items():
        score = 8 if dim_name in {"brand_discipline", "spatial_intelligence", "hierarchy_strength", "motion_coherence"} else 18
        dimensions.append(
            DimensionScore(
                name=dim_name,
                score=score,
                weight=dim_info.get("weight", 0.0),
                issues=veto_messages,
                notes="Structural invalidity due to hard veto. Craft score suppressed.",
            )
        )
    return dimensions


def _adjust_dimension_score(score: DimensionScore, delta: int = 0, issue: str | None = None) -> DimensionScore:
    issues = list(score.issues)
    if issue and issue not in issues:
        issues.append(issue)
    return DimensionScore(
        name=score.name,
        score=max(0, min(100, int(round(score.score + delta)))),
        weight=score.weight,
        issues=issues,
        notes=score.notes,
    )


def _calibrate_dimensions(
    dimensions: list[DimensionScore],
    *,
    signals: dict[str, Any],
    render_mode: str,
) -> list[DimensionScore]:
    calibrated = list(dimensions)
    by_name = {item.name: item for item in calibrated}
    negative_space_pct = float(signals.get("negative_space_pct", 0.0) or 0.0)
    negative_space_target = float(signals.get("recommended_negative_space_target", 0.4) or 0.4)
    text_density = int(signals.get("text_density_estimate", 0) or 0)
    max_words = int(signals.get("max_words_per_screen", 5) or 5)
    color_purity = float(signals.get("color_purity_score", 0.0) or 0.0)
    grain_variance = float(signals.get("grain_variance", 0.0) or 0.0)
    silence_ratio = float(signals.get("silence_ratio", 0.0) or 0.0)
    minimum_hold_ms = float(signals.get("minimum_hold_ms", 0.0) or 0.0)
    breath_points_count = int(signals.get("breath_points_count", 0) or 0)
    transition_hint = str(signals.get("transition_hint", "") or "").strip().lower()
    stagger_count = float(signals.get("stagger_count", 0.0) or 0.0)

    space_penalty = max(0.0, negative_space_target - negative_space_pct)
    if "spatial_intelligence" in by_name and space_penalty > 0:
        by_name["spatial_intelligence"] = _adjust_dimension_score(
            by_name["spatial_intelligence"],
            delta=-int(min(24, round(space_penalty * 100))),
            issue=f"Negative space below target ({negative_space_pct:.2f} < {negative_space_target:.2f}).",
        )
    if text_density > max_words:
        excess = text_density - max_words
        if "hierarchy_strength" in by_name:
            by_name["hierarchy_strength"] = _adjust_dimension_score(
                by_name["hierarchy_strength"],
                delta=-(8 + min(12, excess * 3)),
                issue=f"Text density is too high for clear hierarchy ({text_density}>{max_words}).",
            )
        if "typographic_craft" in by_name:
            by_name["typographic_craft"] = _adjust_dimension_score(
                by_name["typographic_craft"],
                delta=-(6 + min(10, excess * 2)),
                issue=f"Text density reduces typographic control ({text_density}>{max_words}).",
            )
        if "poster_impact" in by_name:
            by_name["poster_impact"] = _adjust_dimension_score(
                by_name["poster_impact"],
                delta=-(6 + min(10, excess * 2)),
                issue="Poster impact is diluted by overcrowding.",
            )
    if color_purity < 85:
        if "brand_discipline" in by_name:
            by_name["brand_discipline"] = _adjust_dimension_score(
                by_name["brand_discipline"],
                delta=-int(min(20, round((85 - color_purity) * 0.7))),
                issue=f"Palette purity is weak ({color_purity:.1f}/100).",
            )
        if "material_finish" in by_name:
            by_name["material_finish"] = _adjust_dimension_score(
                by_name["material_finish"],
                delta=-int(min(12, round((85 - color_purity) * 0.4))),
                issue="Finish feels less controlled because the palette drifts off-brand.",
            )
    if grain_variance < 0.01 or grain_variance > 0.15:
        if "material_finish" in by_name:
            by_name["material_finish"] = _adjust_dimension_score(
                by_name["material_finish"],
                delta=-8,
                issue=f"Material finish falls outside the expected grain window ({grain_variance:.4f}).",
            )

    if render_mode == "motion":
        if silence_ratio < 0.25 or breath_points_count == 0:
            if "silence_quality" in by_name:
                by_name["silence_quality"] = _adjust_dimension_score(
                    by_name["silence_quality"],
                    delta=-10,
                    issue=f"Silence placement is weak (silence_ratio={silence_ratio:.2f}, breath_points={breath_points_count}).",
                )
        if minimum_hold_ms < 220 or stagger_count <= 0:
            if "temporal_rhythm" in by_name:
                by_name["temporal_rhythm"] = _adjust_dimension_score(
                    by_name["temporal_rhythm"],
                    delta=-10,
                    issue=f"Temporal rhythm lacks hold or stagger control (hold={minimum_hold_ms:.0f}ms, stagger={stagger_count:.1f}).",
                )
        if not transition_hint:
            if "transition_quality" in by_name:
                by_name["transition_quality"] = _adjust_dimension_score(
                    by_name["transition_quality"],
                    delta=-8,
                    issue="Transition intent is missing, reducing motion authorship.",
                )
        elif transition_hint == "cut" and minimum_hold_ms < 260:
            if "transition_quality" in by_name:
                by_name["transition_quality"] = _adjust_dimension_score(
                    by_name["transition_quality"],
                    delta=-6,
                    issue="Cut transitions feel abrupt for the current hold structure.",
                )
    else:
        if space_penalty > 0 and "poster_impact" in by_name:
            by_name["poster_impact"] = _adjust_dimension_score(
                by_name["poster_impact"],
                delta=-int(min(16, round(space_penalty * 70))),
                issue="Poster impact is weakened by compressed breathing room.",
            )

    return [by_name.get(item.name, item) for item in calibrated]


def _classify_quality(score: FrameScore, judge_profile: dict[str, Any]) -> None:
    threshold = float(score.threshold_used or 70.0)
    premium_threshold = float(judge_profile.get("premium_threshold", threshold + 8) or (threshold + 8))
    craft_floor = float(judge_profile.get("craft_floor", max(60.0, threshold - 4)) or max(60.0, threshold - 4))
    if score.hard_veto:
        score.quality_band = "structural_invalidity"
        score.structural_invalidity = True
        score.premium_shortfall = True
        return
    if score.composite_score < craft_floor:
        score.quality_band = "craft_weakness"
        score.premium_shortfall = True
        return
    if score.composite_score < premium_threshold:
        score.quality_band = "premium_shortfall"
        score.premium_shortfall = True
        return
    score.quality_band = "premium_ready"


def _build_score_prompt(context: dict[str, Any] | None = None, render_mode: str = "still") -> tuple[str, dict[str, Any]]:
    """Build the vision scoring prompt with unified brand context."""
    from core.quality.contract_loader import load_quality_contract

    contract = load_quality_contract()
    brand_laws = contract.get_vision_context()
    judge_profile = _resolve_judge_profile(context, render_mode)
    dimension_specs = judge_profile.get("dimensions", {}) if isinstance(judge_profile.get("dimensions", {}), dict) else {}
    if not dimension_specs:
        dimension_specs = LEGACY_QUALITY_DIMENSIONS
    objective_signals = (context or {}).get("objective_signals", {})
    if not objective_signals and (context or {}).get("frame_path"):
        objective_signals = _collect_objective_signals(str((context or {}).get("frame_path", "")), context, render_mode)

    archetype = (context or {}).get("archetype", "")
    archetype_block = ""
    if archetype:
        archetype_block = contract.get_archetype_context(archetype)
        if archetype_block:
            archetype_block = f"\n# ARCHETYPE CONTEXT\n{archetype_block}\n"

    criteria_text = ""
    for dim_name, dim_info in dimension_specs.items():
        criteria = dim_info.get("criteria", [])
        criteria_list = "\n".join(f"    - {c}" for c in criteria)
        criteria_text += f"\n  {dim_name} (weight={dim_info.get('weight', 0.0)}):\n{criteria_list}\n"

    context_block = ""
    if context:
        context_block = f"\nAdditional context about this frame:\n{json.dumps(context, indent=2)[:500]}\n"

    contract_context_lines: list[str] = []
    if context:
        for label, keys in (
            ("STYLE PACK", ("style_pack_id", "style_pack")),
            ("TYPOGRAPHY SYSTEM", ("typography_system",)),
            ("STILL FAMILY", ("still_family",)),
        ):
            value = next((context.get(key) for key in keys if context.get(key)), None)
            if value:
                contract_context_lines.append(f"{label}: {value}")
    contract_context = (
        "\n# ACTIVE CONTRACTS\n" + "\n".join(contract_context_lines) + "\n"
        if contract_context_lines
        else ""
    )
    objective_context = _objective_signal_block(objective_signals)

    response_shape = {
        dim_name: {"score": 85, "issues": [], "notes": "Short rationale"}
        for dim_name in dimension_specs
    }

    prompt = f"""You are a premium visual quality auditor for AIOX Studio.
Analyze this rendered frame against the design laws and quality checklist below.

# MANDATORY DESIGN LAWS
{brand_laws}
{archetype_block}
{contract_context}
{objective_context}
# JUDGE PROFILE
PROFILE: {judge_profile.get("id", f"{render_mode}_judge")}
ARTIFACT_CLASS: {judge_profile.get("artifact_class", render_mode)}
RENDER MODE: {render_mode}

# QUALITY CHECKLIST
{criteria_text}
{context_block}

For each dimension, provide:
- score: integer 0-100 (0=terrible, 50=acceptable, 70=good, 90=excellent)
- issues: list of specific problems found (empty if none)
- notes: brief explanation of the score

Return ONLY a JSON object with this exact shape:
{json.dumps(response_shape, indent=2)}

No markdown. No prose. Only the JSON object.
"""
    return prompt, judge_profile


# ---------------------------------------------------------------------------
# Frame encoding
# ---------------------------------------------------------------------------

def _encode_frame(frame_path: str) -> str:
    """Encode a frame as base64 for the vision API."""
    with open(frame_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ---------------------------------------------------------------------------
# Scoring engine
# ---------------------------------------------------------------------------

def score_frame(
    frame_path: str,
    *,
    threshold: float = 70.0,
    context: dict[str, Any] | None = None,
    timeout: float = 30.0,
) -> FrameScore:
    """
    Score a single rendered frame using the vision LLM.

    Args:
        frame_path: Path to the PNG/JPEG frame to evaluate
        threshold: Minimum composite score to pass (default 70)
        context: Optional context about the frame (archetype, intent, etc.)
        timeout: Vision model timeout in seconds

    Returns:
        FrameScore with per-dimension scores and pass/fail status
    """
    result = FrameScore(frame_path=frame_path)
    start = time.time()

    # Validate frame exists
    if not Path(frame_path).exists():
        result.error = f"Frame not found: {frame_path}"
        result.latency_ms = (time.time() - start) * 1000
        return result

    # Encode frame
    try:
        image_b64 = _encode_frame(frame_path)
    except Exception as exc:
        result.error = f"Failed to encode frame: {exc}"
        result.latency_ms = (time.time() - start) * 1000
        return result

    # Build prompt
    render_mode = _normalize_render_mode((context or {}).get("render_mode", "still"))
    scoring_context = dict(context or {})
    scoring_context["frame_path"] = frame_path
    result.objective_signals = _collect_objective_signals(frame_path, scoring_context, render_mode)
    scoring_context["objective_signals"] = result.objective_signals
    prompt, judge_profile = _build_score_prompt(scoring_context, render_mode=render_mode)
    result.judge_profile = str(judge_profile.get("id", ""))
    result.artifact_class = str(judge_profile.get("artifact_class", render_mode))
    result.threshold_used = _resolve_threshold(threshold, judge_profile)
    result.hard_veto = bool(result.objective_signals.get("hard_veto"))
    result.hard_veto_reasons = list(result.objective_signals.get("hard_veto_reasons", []) or [])

    if result.hard_veto:
        result.dimensions = _veto_dimensions(judge_profile, result.hard_veto_reasons)
        result.compute_composite()
        result.passed = False
        _classify_quality(result, judge_profile)
        result.latency_ms = (time.time() - start) * 1000
        return result

    # Call vision model via Ollama
    try:
        from core.intelligence.model_router import get_route, TASK_VISION_PLAN
        from core.intelligence.ollama_client import _post_json, _base_url, OLLAMA_URL

        route = get_route(TASK_VISION_PLAN)
        result.model_used = route.model

        payload = {
            "model": route.model,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
            "keep_alive": route.keep_alive,
            "options": {"temperature": 0.05, "num_predict": 1024},
        }

        raw = _post_json(
            _base_url(OLLAMA_URL) + "/api/generate",
            payload,
            timeout=timeout,
        )

        response_text = raw.get("response", "")
        result.raw_llm_response = response_text
        result.latency_ms = (time.time() - start) * 1000

        # Parse response
        dimensions = _parse_score_response(response_text, judge_profile)
        dimensions = _calibrate_dimensions(
            dimensions,
            signals=result.objective_signals,
            render_mode=render_mode,
        )
        result.dimensions = dimensions
        result.compute_composite()
        result.passed = result.composite_score >= result.threshold_used
        _classify_quality(result, judge_profile)

        # Unload vision model to reclaim VRAM
        try:
            from core.intelligence.ollama_client import unload_vision_model
            unload_vision_model()
        except Exception:
            pass

        return result

    except Exception as exc:
        result.error = f"Vision scoring failed: {type(exc).__name__}: {exc}"
        result.latency_ms = (time.time() - start) * 1000
        return result


def _parse_score_response(response_text: str, judge_profile: dict[str, Any] | None = None) -> list[DimensionScore]:
    """Parse the JSON score response from the vision LLM."""
    # Try to extract JSON from the response
    text = response_text.strip()

    # Handle common markdown wrapping
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (```json and ```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start:end])
            except json.JSONDecodeError:
                return _fallback_dimensions(judge_profile)
        else:
            return _fallback_dimensions(judge_profile)

    dimension_specs = {}
    if isinstance(judge_profile, dict):
        dimension_specs = judge_profile.get("dimensions", {}) if isinstance(judge_profile.get("dimensions", {}), dict) else {}
    if not dimension_specs:
        dimension_specs = LEGACY_QUALITY_DIMENSIONS

    dimensions = []
    for dim_name, dim_info in dimension_specs.items():
        dim_data = data.get(dim_name, {})
        if isinstance(dim_data, dict):
            score = max(0, min(100, int(dim_data.get("score", 50))))
            issues = dim_data.get("issues", [])
            if not isinstance(issues, list):
                issues = [str(issues)] if issues else []
            notes = str(dim_data.get("notes", ""))
        else:
            score = 50
            issues = []
            notes = "No data from LLM"

        dimensions.append(DimensionScore(
            name=dim_name,
            score=score,
            weight=dim_info["weight"],
            issues=issues,
            notes=notes,
        ))

    return dimensions


def _fallback_dimensions(judge_profile: dict[str, Any] | None = None) -> list[DimensionScore]:
    """Return neutral scores when LLM parsing fails."""
    dimension_specs = {}
    if isinstance(judge_profile, dict):
        dimension_specs = judge_profile.get("dimensions", {}) if isinstance(judge_profile.get("dimensions", {}), dict) else {}
    if not dimension_specs:
        dimension_specs = LEGACY_QUALITY_DIMENSIONS
    return [
        DimensionScore(
            name=dim_name,
            score=50,
            weight=dim_info["weight"],
            issues=["LLM response could not be parsed"],
            notes="Fallback score — manual review recommended",
        )
        for dim_name, dim_info in dimension_specs.items()
    ]


# ---------------------------------------------------------------------------
# Batch scoring
# ---------------------------------------------------------------------------

def score_frames(
    frame_paths: list[str],
    *,
    threshold: float = 70.0,
    context: dict[str, Any] | None = None,
) -> list[FrameScore]:
    """Score multiple frames sequentially (vision model is single-threaded)."""
    results = []
    for path in frame_paths:
        score = score_frame(path, threshold=threshold, context=context)
        results.append(score)
    return results


def batch_summary(scores: list[FrameScore]) -> dict[str, Any]:
    """Summarize a batch of frame scores."""
    if not scores:
        return {"total": 0, "passed": 0, "failed": 0, "avg_score": 0.0}

    passed = [s for s in scores if s.passed]
    failed = [s for s in scores if not s.passed]
    avg = sum(s.composite_score for s in scores) / len(scores)

    return {
        "total": len(scores),
        "passed": len(passed),
        "failed": len(failed),
        "avg_score": round(avg, 1),
        "worst_frame": min(scores, key=lambda s: s.composite_score).frame_path if scores else None,
        "best_frame": max(scores, key=lambda s: s.composite_score).frame_path if scores else None,
    }
