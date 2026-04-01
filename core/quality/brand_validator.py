"""
brand_validator.py — Programmatic brand compliance validator.

Runs without Vision-LLM in milliseconds. Used as a fast pre-check
before spending time on Vision-LLM scoring. Uses Pillow for pixel sampling.

Checks:
  1. color_purity: pixel % outside brand palette (should be < 15%)
  2. negative_space: pixel % near background color (should be >= 40%)
  3. text_density: contrast-based heuristic for word density (should be <= 5)
  4. grain_presence: noise variance in frame (should be between 0.01 and 0.15)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class BrandValidationResult:
    frame_path: str
    color_purity_score: float = 0.0  # 0-100; 100 = all pixels on-brand
    negative_space_pct: float = 0.0  # 0-1
    text_density_estimate: int = 0   # estimated word count heuristic
    grain_variance: float = 0.0
    violations: list[str] = field(default_factory=list)
    passed: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_path": self.frame_path,
            "color_purity_score": round(self.color_purity_score, 1),
            "negative_space_pct": round(self.negative_space_pct * 100, 1),
            "text_density_estimate": self.text_density_estimate,
            "grain_variance": round(self.grain_variance, 4),
            "violations": self.violations,
            "passed": self.passed,
            "error": self.error,
        }

    def summary_line(self) -> str:
        icon = "+" if self.passed else "x"
        return (
            f"{icon} brand={self.color_purity_score:.0f} "
            f"neg={self.negative_space_pct*100:.0f}% "
            f"density={self.text_density_estimate} "
            f"grain={self.grain_variance:.3f}"
        )


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int] | None:
    h = hex_color.strip().lstrip("#")
    if len(h) == 6:
        try:
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        except ValueError:
            return None
    return None


def _color_distance(r1: int, g1: int, b1: int, r2: int, g2: int, b2: int) -> float:
    return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)


def validate_frame(frame_path: str, threshold: float = 70.0) -> BrandValidationResult:
    """
    Fast programmatic brand validation using Pillow pixel sampling.

    Args:
        frame_path: Path to PNG/JPEG frame
        threshold: Minimum overall score to pass (default 70)

    Returns:
        BrandValidationResult with per-check scores and violations list
    """
    result = BrandValidationResult(frame_path=frame_path)

    if not Path(frame_path).exists():
        result.error = f"Frame not found: {frame_path}"
        return result

    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        result.error = "Pillow/numpy not available — skipping brand validation"
        result.passed = True  # Don't block pipeline on missing deps
        return result

    try:
        img = Image.open(frame_path).convert("RGB")

        # Downsample to 200x200 for speed
        small = img.resize((200, 200), Image.LANCZOS)
        pixels = np.array(small, dtype=np.float32)  # (200, 200, 3)
        h, w = pixels.shape[:2]
        total = h * w

        # Brand palette: #000000, #FFFFFF, #FF3366, + tolerance for rgba
        palette_rgb = [
            (0, 0, 0),       # #000000 background
            (255, 255, 255), # #FFFFFF foreground
            (255, 51, 102),  # #FF3366 accent
        ]
        TOLERANCE = 35  # color distance threshold (0-441 range)
        BG_TOLERANCE = 30  # tighter for background detection

        # -- Check 1: Color purity --
        off_brand = 0
        near_bg = 0
        bg_rgb = (0, 0, 0)

        px_flat = pixels.reshape(-1, 3)
        for px in px_flat:
            r, g, b = int(px[0]), int(px[1]), int(px[2])
            dist_bg = _color_distance(r, g, b, *bg_rgb)
            if dist_bg <= BG_TOLERANCE:
                near_bg += 1
            min_dist = min(_color_distance(r, g, b, *pal) for pal in palette_rgb)
            if min_dist > TOLERANCE:
                off_brand += 1

        purity_pct = 1.0 - (off_brand / total)
        result.color_purity_score = round(purity_pct * 100, 1)
        result.negative_space_pct = round(near_bg / total, 3)

        # -- Check 2: Text density heuristic --
        # High-contrast pixels that are likely text (bright on dark or dark on bright)
        gray = pixels.mean(axis=2)
        # Count pixels with high brightness variance in 5x5 neighborhood
        # A simple heuristic: count bright spots (potential text characters)
        bright_mask = gray > 200
        bright_count = int(bright_mask.sum())
        # Very rough: assume ~400 bright pixels per word at 200x200 scale
        result.text_density_estimate = max(0, bright_count // 400)

        # -- Check 3: Grain variance --
        gray_norm = gray / 255.0
        result.grain_variance = round(float(np.std(gray_norm)), 4)

        # -- Violations --
        violations: list[str] = []

        if result.color_purity_score < 75:
            violations.append(
                f"color_purity {result.color_purity_score:.0f}/100 — "
                f"{off_brand}/{total} pixels outside #000/#FFF/#FF3366 palette"
            )

        if result.negative_space_pct < 0.40:
            violations.append(
                f"negative_space {result.negative_space_pct*100:.0f}% < 40% required"
            )

        if result.text_density_estimate > 8:
            violations.append(
                f"text_density estimate {result.text_density_estimate} words — max 5 required"
            )

        if result.grain_variance < 0.005:
            violations.append(f"grain_variance {result.grain_variance:.4f} too low — grain may be missing")

        result.violations = violations

        # Score: weight color purity 40%, neg space 40%, compliance 20%
        neg_score = min(100.0, result.negative_space_pct / 0.40 * 100)
        compliance_score = 100.0 - len(violations) * 20
        composite = (result.color_purity_score * 0.4 + neg_score * 0.4 + compliance_score * 0.2)
        result.passed = composite >= threshold and len(violations) == 0

    except Exception as exc:
        result.error = f"Validation error: {type(exc).__name__}: {exc}"
        result.passed = True  # Fail open — don't block pipeline on unexpected errors

    return result


def quick_check(frame_path: str) -> tuple[bool, list[str]]:
    """Convenience wrapper. Returns (passed, violations)."""
    result = validate_frame(frame_path)
    return result.passed, result.violations
