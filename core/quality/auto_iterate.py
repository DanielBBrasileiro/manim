"""
auto_iterate.py — Self-correcting render loop.

When a frame fails the quality gate, the auto-iterator:
1. Extracts actionable issues from the FrameScore
2. Builds a correction prompt with specific fixes
3. Re-requests the creative plan from the coordinator
4. Triggers a re-render
5. Re-scores the output

The loop has a configurable max_iterations (default 3) to prevent
infinite rendering. Each iteration narrows the correction scope.

This transforms the pipeline from "render once, hope it works" to
"render, evaluate, correct, render again" — fully autonomous.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from core.quality.frame_scorer import (
    FrameScore,
    batch_summary,
    score_frame,
)


@dataclass
class IterationResult:
    """Result from a single auto-iterate cycle."""
    iteration: int
    score: FrameScore
    corrections_applied: list[str]
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "iteration": self.iteration,
            "composite_score": round(self.score.composite_score, 1),
            "passed": self.score.passed,
            "corrections": self.corrections_applied,
            "duration_ms": round(self.duration_ms, 2),
        }


@dataclass
class AutoIterateReport:
    """Complete report from an auto-iterate session."""
    frame_path: str
    iterations: list[IterationResult] = field(default_factory=list)
    final_score: float = 0.0
    final_passed: bool = False
    total_iterations: int = 0
    max_iterations: int = 3
    total_duration_ms: float = 0.0
    improvement_history: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_path": self.frame_path,
            "final_score": round(self.final_score, 1),
            "final_passed": self.final_passed,
            "total_iterations": self.total_iterations,
            "max_iterations": self.max_iterations,
            "improvement_history": [round(s, 1) for s in self.improvement_history],
            "iterations": [r.to_dict() for r in self.iterations],
            "total_duration_ms": round(self.total_duration_ms, 2),
        }

    def as_markdown(self) -> str:
        icon = "✅" if self.final_passed else "⚠️"
        lines = [
            f"## {icon} Auto-Iterate Report",
            "",
            f"**Frame:** `{Path(self.frame_path).name}`",
            f"**Final Score:** {self.final_score:.0f}/100 ({'PASS' if self.final_passed else 'FAIL'})",
            f"**Iterations:** {self.total_iterations}/{self.max_iterations}",
            f"**Duration:** {self.total_duration_ms:.0f}ms",
            "",
            "### Score History",
            "",
        ]
        for result in self.iterations:
            s = result.score
            lines.append(
                f"- **Iter {result.iteration}:** {s.composite_score:.0f}/100 "
                f"({'PASS' if s.passed else 'FAIL'}) — "
                f"{len(result.corrections_applied)} corrections"
            )
            for corr in result.corrections_applied:
                lines.append(f"  - {corr}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Issue extraction
# ---------------------------------------------------------------------------

def extract_corrections(score: FrameScore) -> list[str]:
    """Extract contract-bound actionable corrections from a FrameScore."""
    corrections: list[str] = []

    if score.hard_veto:
        for entry in score.hard_veto_reasons:
            if not isinstance(entry, dict):
                continue
            detail = str(entry.get("detail", "Resolve structural veto.")).strip()
            code = str(entry.get("code", "hard_veto")).strip().upper()
            corrections.append(f"[{code}] Resolve structural invalidity before any craft refinement. {detail}")
        return corrections

    _FIXES: dict[str, dict[str, str]] = {
        "hierarchy_strength": {
            "critical": "Establish one dominant element immediately. Increase the scale gap, suppress secondary copy, and make the focal order obvious within half a second.",
            "poor": "Strengthen primary-vs-secondary contrast. Reduce competing elements and let one message own the frame.",
            "weak": "Tighten hierarchy so supporting elements stop competing with the hero statement.",
        },
        "typographic_craft": {
            "critical": "Rewrite the text architecture. Shorten lines, improve line breaks, tighten tracking for large type, and restore a deliberate measure.",
            "poor": "Refine line breaking, measure, and role contrast so the typography feels authored instead of merely readable.",
            "weak": "Polish the type system: cleaner breaks, better rag, and stronger size relationships.",
        },
        "spatial_intelligence": {
            "critical": "Increase negative space aggressively. Rebalance focal, support, and empty zones until the frame breathes with intention.",
            "poor": "Open more breathing room and reduce compression around the focal element.",
            "weak": "Give the layout cleaner tension by protecting empty space and edge margins.",
        },
        "poster_impact": {
            "critical": "Rebuild the frame as a poster, not a paused design. Remove noise, enlarge the dominant statement, and restore stop power.",
            "poor": "Increase scroll-stopping force through stronger hierarchy and cleaner isolation.",
            "weak": "Sharpen the poster read so the frame lands faster and harder.",
        },
        "brand_discipline": {
            "critical": "Strip every off-brand signal immediately. Purify palette, remove ornamental noise, and return to strict accent restraint.",
            "poor": "Tighten palette discipline and reduce accent misuse so the frame feels premium, not decorative.",
            "weak": "Remove subtle off-brand drift and restore cleaner restraint.",
        },
        "material_finish": {
            "critical": "Rebuild the finish layer. Grain, contrast, and texture must feel intentional instead of dirty or accidental.",
            "poor": "Refine the surface treatment so grain and contrast feel premium and controlled.",
            "weak": "Clean up finish details; the material layer needs more discipline.",
        },
        "emotional_coherence": {
            "critical": "Realign the frame mood with the intended emotional target. Every element should support the same emotional read.",
            "poor": "Clarify the emotional tone so the composition feels more intentional and less neutral.",
            "weak": "Tighten mood alignment; the frame should feel more emotionally specific.",
        },
        "originality": {
            "critical": "Move away from safe template behavior. Keep the contracts, but introduce a more authored compositional idea.",
            "poor": "Reduce generic startup-design cues and make the frame feel more deliberately authored.",
            "weak": "Push one compositional decision further so the result feels less default.",
        },
        "motion_coherence": {
            "critical": "Recompose the motion sentence. The frame should imply one clear motion language instead of multiple competing behaviors.",
            "poor": "Tighten the motion logic so elements feel governed by the same physical and editorial intent.",
            "weak": "Reduce motion ambiguity and make the movement read cleaner.",
        },
        "temporal_rhythm": {
            "critical": "Re-time the sequence. Introduce holds, remove constant activity, and make cadence legible.",
            "poor": "Add clearer beat spacing and stronger timing contrast between phrases.",
            "weak": "Refine the rhythm so the pacing feels more deliberate.",
        },
        "transition_quality": {
            "critical": "Redesign the act handoff. The transition should feel motivated, premium, and structurally legible.",
            "poor": "Give the transition more intention; it currently feels arbitrary or abrupt.",
            "weak": "Polish the handoff so act edges feel cleaner.",
        },
        "emotional_arc": {
            "critical": "Reconnect the frame to the act emotion. Motion intensity and composition should clearly serve the narrative arc.",
            "poor": "Strengthen emotional alignment between the frame and the act it belongs to.",
            "weak": "Clarify the act emotion a little more through pacing and emphasis.",
        },
        "silence_quality": {
            "critical": "Place stillness intentionally. The motion needs breathing room to gain authority.",
            "poor": "Increase silence between phrases so movement can land with more meaning.",
            "weak": "Add a touch more restraint; the sequence needs cleaner breath points.",
        },
    }

    for dim in score.dimensions:
        if dim.score >= 70:
            continue

        if dim.score < 40:
            tier = "critical"
        elif dim.score < 60:
            tier = "poor"
        else:
            tier = "weak"

        fix = _FIXES.get(dim.name, {}).get(tier, f"Improve {dim.name} quality with a more deliberate authored decision.")
        corrections.append(f"[{dim.name.upper()} {dim.score}/100] {fix}")

        for issue in dim.issues:
            if issue and issue != "LLM response could not be parsed":
                corrections.append(f"  -> {issue}")

        if dim.notes and dim.notes not in {"", "No data from LLM"}:
            corrections.append(f"  -> Critic: {dim.notes}")

    return corrections


def build_correction_prompt(
    original_intent: str,
    corrections: list[str],
    iteration: int,
) -> str:
    """Build a targeted correction prompt for re-planning."""
    correction_text = "\n".join(f"  - {c}" for c in corrections)

    return f"""The previous render of "{original_intent}" failed quality review.

Iteration {iteration} corrections required:
{correction_text}

Adjust the creative plan to address these specific issues while
preserving the original intent. Focus only on the flagged problems.
Do not change aspects that already scored well.
"""


# ---------------------------------------------------------------------------
# Auto-iterate loop
# ---------------------------------------------------------------------------

def auto_iterate(
    frame_path: str,
    *,
    threshold: float = 70.0,
    max_iterations: int = 3,
    context: dict[str, Any] | None = None,
    on_correction: Callable[[str, list[str], int], str | None] | None = None,
    on_rerender: Callable[[str, dict[str, Any]], str | None] | None = None,
) -> AutoIterateReport:
    """
    Self-correcting render loop.

    Args:
        frame_path: Path to the initial rendered frame
        threshold: Minimum composite score to pass
        max_iterations: Maximum correction cycles
        context: Optional creative context for scoring
        on_correction: Callback(intent, corrections, iteration) -> new_frame_path or None.
                       Called when corrections are needed. Should trigger re-render
                       and return the path to the new frame, or None to stop.
        on_rerender: Callback(frame_path, score_dict) -> new_frame_path or None.
                     Alternative simpler callback for re-render triggers.

    Returns:
        AutoIterateReport with complete iteration history
    """
    report = AutoIterateReport(
        frame_path=frame_path,
        max_iterations=max_iterations,
    )
    start = time.monotonic()
    current_path = frame_path
    original_intent = (context or {}).get("intent", "unknown")

    for iteration in range(1, max_iterations + 1):
        iter_start = time.monotonic()

        # Score current frame
        score = score_frame(
            current_path,
            threshold=threshold,
            context=context,
        )

        corrections = extract_corrections(score) if not score.passed else []

        result = IterationResult(
            iteration=iteration,
            score=score,
            corrections_applied=corrections,
            duration_ms=(time.monotonic() - iter_start) * 1000,
        )
        report.iterations.append(result)
        report.improvement_history.append(score.composite_score)

        # Check if passed
        if score.passed or score.error:
            break

        # Check if we have corrections to apply
        if not corrections:
            break

        # Check if we have a callback to apply corrections
        new_path = None
        if on_correction:
            correction_prompt = build_correction_prompt(
                original_intent, corrections, iteration
            )
            new_path = on_correction(correction_prompt, corrections, iteration)
        elif on_rerender:
            new_path = on_rerender(current_path, score.to_dict())

        if new_path and Path(new_path).exists():
            current_path = new_path
        else:
            # No re-render capability — stop iterating
            break

    # Finalize report
    report.total_iterations = len(report.iterations)
    report.total_duration_ms = (time.monotonic() - start) * 1000

    if report.iterations:
        last = report.iterations[-1]
        report.final_score = last.score.composite_score
        report.final_passed = last.score.passed

    return report


# ---------------------------------------------------------------------------
# Standalone scoring (no re-render, just evaluate)
# ---------------------------------------------------------------------------

def evaluate_output(
    output_dir: str,
    *,
    threshold: float = 70.0,
    context: dict[str, Any] | None = None,
    extensions: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".webp"),
) -> dict[str, Any]:
    """
    Evaluate all frames in an output directory.

    Returns a summary with individual frame scores.
    """
    output_path = Path(output_dir)
    if not output_path.exists():
        return {"error": f"Directory not found: {output_dir}", "scores": []}

    frames = sorted([
        str(f) for f in output_path.iterdir()
        if f.suffix.lower() in extensions
    ])

    if not frames:
        return {"error": "No frames found in directory", "scores": []}

    scores = []
    for frame_path in frames:
        score = score_frame(frame_path, threshold=threshold, context=context)
        scores.append(score)

    return {
        "summary": batch_summary(scores),
        "scores": [s.to_dict() for s in scores],
    }
