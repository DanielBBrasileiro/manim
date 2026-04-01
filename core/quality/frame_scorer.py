"""
frame_scorer.py — Vision-LLM quality scoring for rendered frames.

Uses the vision model (Qwen3-VL or equivalent) to evaluate rendered
frames against the AIOX premium design checklist derived from
contracts/global_laws.yaml and brand DNA.

Scoring dimensions:
  1. Composition — negative space, balance, hierarchy
  2. Typography — weight, size, readability, word count
  3. Color — palette adherence, contrast, harmony
  4. Motion Signature — implied movement, tension, resolution
  5. Brand Compliance — forbidden patterns, logo rules, gradient rules

Each dimension is scored 0-100. The composite score is a weighted average.
A frame passes the quality gate if composite >= threshold (default 70).
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

load_repo_env()


# ---------------------------------------------------------------------------
# Quality checklist (derived from contracts/global_laws.yaml)
# ---------------------------------------------------------------------------

QUALITY_DIMENSIONS = {
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
            "error": self.error,
        }

    def summary_line(self) -> str:
        icon = "✓" if self.passed else "✗"
        dims = " | ".join(
            f"{d.name[:4]}={d.score}" for d in self.dimensions
        )
        return f"{icon} {self.composite_score:.0f}/100 [{dims}] — {Path(self.frame_path).name}"


# ---------------------------------------------------------------------------
# Vision prompt construction
# ---------------------------------------------------------------------------

def _build_score_prompt(context: dict[str, Any] | None = None) -> str:
    """Build the vision scoring prompt with quality checklist."""
    criteria_text = ""
    for dim_name, dim_info in QUALITY_DIMENSIONS.items():
        criteria_list = "\n".join(f"    - {c}" for c in dim_info["criteria"])
        criteria_text += f"\n  {dim_name} (weight={dim_info['weight']}):\n{criteria_list}\n"

    context_block = ""
    if context:
        context_block = f"\nAdditional context about this frame:\n{json.dumps(context, indent=2)[:500]}\n"

    return f"""You are a premium visual quality auditor for AIOX Studio.
Analyze this rendered frame against the quality checklist below.

For each dimension, provide:
- score: integer 0-100 (0=terrible, 50=acceptable, 70=good, 90=excellent)
- issues: list of specific problems found (empty if none)
- notes: brief explanation of the score

Quality Checklist:
{criteria_text}
{context_block}
Return ONLY a JSON object with this exact shape:
{{
  "composition": {{"score": 85, "issues": [], "notes": "Clean layout with ample negative space"}},
  "typography": {{"score": 90, "issues": [], "notes": "Minimal text, appropriate weight"}},
  "color": {{"score": 80, "issues": [], "notes": "Monochromatic palette, good contrast"}},
  "motion_signature": {{"score": 70, "issues": ["Lacks implied movement"], "notes": "Static feel"}},
  "brand_compliance": {{"score": 95, "issues": [], "notes": "Fully compliant"}}
}}

No markdown. No prose. Only the JSON object.
"""


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
    prompt = _build_score_prompt(context)

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
        dimensions = _parse_score_response(response_text)
        result.dimensions = dimensions
        result.compute_composite()
        result.passed = result.composite_score >= threshold

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


def _parse_score_response(response_text: str) -> list[DimensionScore]:
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
                return _fallback_dimensions()
        else:
            return _fallback_dimensions()

    dimensions = []
    for dim_name, dim_info in QUALITY_DIMENSIONS.items():
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


def _fallback_dimensions() -> list[DimensionScore]:
    """Return neutral scores when LLM parsing fails."""
    return [
        DimensionScore(
            name=dim_name,
            score=50,
            weight=dim_info["weight"],
            issues=["LLM response could not be parsed"],
            notes="Fallback score — manual review recommended",
        )
        for dim_name, dim_info in QUALITY_DIMENSIONS.items()
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
