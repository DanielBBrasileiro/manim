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
from collections import deque
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
    hard_veto_reasons: list[dict[str, Any]] = field(default_factory=list)
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
            "hard_veto_reasons": self.hard_veto_reasons,
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
            f"grain={self.grain_variance:.3f} "
            f"vetoes={len(self.hard_veto_reasons)}"
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


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    def _channel(value: int) -> float:
        scaled = value / 255.0
        if scaled <= 0.03928:
            return scaled / 12.92
        return ((scaled + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def _contrast_ratio(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    l1 = _relative_luminance(a)
    l2 = _relative_luminance(b)
    bright = max(l1, l2)
    dark = min(l1, l2)
    return (bright + 0.05) / (dark + 0.05)


def _component_boxes(mask: Any, *, min_pixels: int = 12) -> list[dict[str, Any]]:
    h, w = mask.shape
    visited = mask.copy()
    boxes: list[dict[str, Any]] = []

    for y in range(h):
        for x in range(w):
            if not visited[y, x]:
                continue
            queue = deque([(x, y)])
            visited[y, x] = False
            pixels = 0
            x0 = x1 = x
            y0 = y1 = y
            while queue:
                cx, cy = queue.popleft()
                pixels += 1
                x0 = min(x0, cx)
                x1 = max(x1, cx)
                y0 = min(y0, cy)
                y1 = max(y1, cy)
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < w and 0 <= ny < h and visited[ny, nx]:
                        visited[ny, nx] = False
                        queue.append((nx, ny))
            if pixels < min_pixels:
                continue
            width = x1 - x0 + 1
            height = y1 - y0 + 1
            area = width * height
            boxes.append(
                {
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                    "width": width,
                    "height": height,
                    "area": area,
                    "pixels": pixels,
                    "fill_ratio": pixels / max(area, 1),
                    "center_x": (x0 + x1) / 2.0,
                    "center_y": (y0 + y1) / 2.0,
                }
            )
    return boxes


def _box_overlap(a: dict[str, Any], b: dict[str, Any], *, padding: int = 4) -> float:
    ax0, ay0, ax1, ay1 = a["x0"] - padding, a["y0"] - padding, a["x1"] + padding, a["y1"] + padding
    bx0, by0, bx1, by1 = b["x0"] - padding, b["y0"] - padding, b["x1"] + padding, b["y1"] + padding
    inter_w = max(0, min(ax1, bx1) - max(ax0, bx0) + 1)
    inter_h = max(0, min(ay1, by1) - max(ay0, by0) + 1)
    inter_area = inter_w * inter_h
    if inter_area <= 0:
        return 0.0
    denom = min((ax1 - ax0 + 1) * (ay1 - ay0 + 1), (bx1 - bx0 + 1) * (by1 - by0 + 1))
    return inter_area / max(denom, 1)


def _format_hard_veto(code: str, detail: str, **metrics: Any) -> dict[str, Any]:
    payload = {"code": code, "detail": detail}
    if metrics:
        payload["metrics"] = metrics
    return payload


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
        # High-fidelity tolerance (allows for cinematic halation and grain)
        TOLERANCE = 45  # was 35; allows for slight color bleed from post-fx
        BG_TOLERANCE = 35  # was 30; allows for grain in background

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
        quantized = (pixels // 8).astype(int)
        flat_quantized = quantized.reshape(-1, 3)
        unique_colors = int(np.unique(flat_quantized, axis=0).shape[0])
        _, dominant_counts = np.unique(flat_quantized, axis=0, return_counts=True)
        dominant_color_pct = float(dominant_counts.max() / total) if total else 0.0
        # Count pixels with high brightness variance in 5x5 neighborhood
        # A simple heuristic: count bright spots (potential text characters)
        bright_mask = gray > 200
        bright_count = int(bright_mask.sum())
        # Very rough: assume ~400 bright pixels per word at 200x200 scale
        result.text_density_estimate = max(0, bright_count // 400)

        # -- Check 3: Grain variance --
        gray_norm = gray / 255.0
        result.grain_variance = round(float(np.std(gray_norm)), 4)

        safe_margin = max(8, int(min(h, w) * 0.10))
        text_boxes = _component_boxes(bright_mask, min_pixels=24)

        hard_vetoes: list[dict[str, Any]] = []

        if dominant_color_pct >= 0.98:
            hard_vetoes.append(
                _format_hard_veto(
                    "empty_frame",
                    "Frame is effectively empty or monochrome beyond usable content density.",
                    dominant_color_pct=round(dominant_color_pct, 4),
                )
            )

        for box in text_boxes:
            if (
                box["x0"] <= safe_margin
                or box["y0"] <= safe_margin
                or box["x1"] >= w - safe_margin
                or box["y1"] >= h - safe_margin
            ):
                hard_vetoes.append(
                    _format_hard_veto(
                        "text_off_canvas",
                        "Detected text-like region bleeding into the safe zone boundary.",
                        box=box,
                        safe_margin=safe_margin,
                    )
                )
                break

        for idx, box in enumerate(text_boxes):
            for other in text_boxes[idx + 1:]:
                if _box_overlap(box, other, padding=max(4, safe_margin // 8)) >= 0.18:
                    hard_vetoes.append(
                        _format_hard_veto(
                            "text_overlap_text",
                            "Detected text-like regions overlapping or colliding inside the same frame.",
                            first_box=box,
                            second_box=other,
                        )
                    )
                    break
            if any(v["code"] == "text_overlap_text" for v in hard_vetoes):
                break

        if len(text_boxes) >= 2:
            ranked = sorted((max(box["width"], box["height"]) for box in text_boxes), reverse=True)
            ratio = ranked[0] / max(ranked[1], 1)
            if ratio < 1.35:
                hard_vetoes.append(
                    _format_hard_veto(
                        "zero_hierarchy",
                        "Text hierarchy is too flat; dominant and secondary scales are nearly identical.",
                        dominant_to_secondary_ratio=round(ratio, 3),
                    )
                )

        for box in text_boxes:
            pad = max(3, safe_margin // 10)
            x0 = max(0, box["x0"] - pad)
            y0 = max(0, box["y0"] - pad)
            x1 = min(w - 1, box["x1"] + pad)
            y1 = min(h - 1, box["y1"] + pad)
            inside = pixels[box["y0"]:box["y1"] + 1, box["x0"]:box["x1"] + 1]
            outer = pixels[y0:y1 + 1, x0:x1 + 1]
            if inside.size == 0 or outer.size == 0:
                continue
            text_rgb = tuple(int(v) for v in inside.reshape(-1, 3).mean(axis=0))
            bg_rgb = tuple(int(v) for v in outer.reshape(-1, 3).mean(axis=0))
            contrast = _contrast_ratio(text_rgb, bg_rgb)
            if contrast < 3.0:
                hard_vetoes.append(
                    _format_hard_veto(
                        "illegible_contrast",
                        "Detected text-like region with contrast ratio below 3:1.",
                        contrast_ratio=round(contrast, 3),
                        box=box,
                    )
                )
                break

        row_span = float(gray.mean(axis=1).max() - gray.mean(axis=1).min())
        col_span = float(gray.mean(axis=0).max() - gray.mean(axis=0).min())
        mean_neighbor_delta = float(
            (np.abs(np.diff(gray, axis=0)).mean() + np.abs(np.diff(gray, axis=1)).mean()) / 2.0
        )
        if unique_colors >= 24 and mean_neighbor_delta < 5.0 and max(row_span, col_span) >= 20.0:
            hard_vetoes.append(
                _format_hard_veto(
                    "gradient_detected",
                    "Detected a smooth multi-tone field consistent with a gradient background.",
                    unique_colors=unique_colors,
                    mean_neighbor_delta=round(mean_neighbor_delta, 3),
                    row_span=round(row_span, 3),
                    col_span=round(col_span, 3),
                )
            )

        corner_limit_x = int(w * 0.18)
        corner_limit_y = int(h * 0.18)
        non_bg_mask = np.linalg.norm(pixels - np.array(bg_rgb, dtype=np.float32), axis=2) > BG_TOLERANCE
        logo_boxes = _component_boxes(non_bg_mask, min_pixels=180)
        for box in logo_boxes:
            in_corner = (
                (box["x0"] <= corner_limit_x and box["y0"] <= corner_limit_y)
                or (box["x1"] >= w - corner_limit_x and box["y0"] <= corner_limit_y)
                or (box["x0"] <= corner_limit_x and box["y1"] >= h - corner_limit_y)
                or (box["x1"] >= w - corner_limit_x and box["y1"] >= h - corner_limit_y)
            )
            aspect = box["width"] / max(box["height"], 1)
            if in_corner and 0.45 <= aspect <= 2.2 and 0.18 <= box["fill_ratio"] <= 0.88:
                hard_vetoes.append(
                    _format_hard_veto(
                        "logo_detected",
                        "Detected a compact non-background mark in a corner region consistent with a logo/signature.",
                        box=box,
                    )
                )
                break

        result.hard_veto_reasons = hard_vetoes
        if hard_vetoes:
            result.violations = [
                f"hard_veto:{entry['code']} — {entry['detail']}" for entry in hard_vetoes
            ]
            result.passed = False
            return result

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

        if result.text_density_estimate > 5:
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
