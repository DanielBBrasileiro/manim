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

    # Contract-specific fix recipes per dimension score range
    _FIXES: dict[str, dict[str, str]] = {
        "typography": {
            "critical": "Reduce to MAX 3 words. Use weight 300 (Whisper). Lowercase only. Remove all text except core statement.",
            "poor":     "Reduce to max 5 words. Use weight 300 or 500 only. No serif. No uppercase prose.",
            "weak":     "Tighten word count. Verify weight is 300 (whisper) or 500 (statement) only.",
        },
        "color": {
            "critical": "Use ONLY #000000 background and #FFFFFF foreground. Remove ALL other colors. Accent #FF3366 max 2% if needed.",
            "poor":     "Eliminate parasitic colors. Palette must be #000/#FFF with optional #FF3366 accent < 2% coverage.",
            "weak":     "Check for off-black or off-white values. Purify to strict #000/#FFF.",
        },
        "composition": {
            "critical": "Increase negative space to >= 50%. Apply Rule of Thirds. Single focal point. Remove all secondary elements.",
            "poor":     "Negative space must be >= 40%. Clear visual hierarchy. 64px minimum edge margin.",
            "weak":     "Increase breathing room. Reduce element density. Confirm single dominant focal point.",
        },
        "motion_signature": {
            "critical": "Add strong directional tension. Elements must imply movement or weight. Use spring physics.",
            "poor":     "Increase implied momentum. Frame should convey physical behavior even as a still.",
            "weak":     "Subtle tension cues: diagonal asymmetry, implied velocity, off-center gravity.",
        },
        "brand_compliance": {
            "critical": "CRITICAL VIOLATIONS: Remove all gradients, shadows, glassmorphism, logos immediately.",
            "poor":     "Remove anti-patterns. Verify no gradients, shadows, glow effects, or tech logos present.",
            "weak":     "Minor compliance issues. Check for subtle shadows or faint gradients.",
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

        fix = _FIXES.get(dim.name, {}).get(tier, f"Improve {dim.name} quality.")
        corrections.append(f"[{dim.name.upper()} {dim.score}/100] {fix}")

        for issue in dim.issues:
            if issue and issue != "LLM response could not be parsed":
                corrections.append(f"  -> {issue}")

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
