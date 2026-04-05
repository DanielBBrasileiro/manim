"""
preview_tool.py — AIOX Studio fast preview generator.
Generates a visual wireframe (PNG via matplotlib, or SVG fallback) in < 1s.
No Manim, no numpy required.
"""

import os
import math
import random
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = ROOT / "output" / "preview"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _entropy(plan: dict, key: str) -> float:
    """Return normalised entropy value [0.0 – 1.0] for a key."""
    raw = plan.get("entropy", {}).get(key, 0.5)
    try:
        return max(0.0, min(1.0, float(raw)))
    except (TypeError, ValueError):
        return 0.5


def _regime(plan: dict) -> str:
    return plan.get("interpretation", {}).get("regime", "laminar").lower()


def _motion_sig(plan: dict) -> str:
    return plan.get("interpretation", {}).get("motion_signature", "")


def _pacing(plan: dict) -> str:
    return str(plan.get("pacing", ""))


def _archetype(plan: dict) -> str:
    return str(plan.get("archetype", "unknown"))


def _aesthetic(plan: dict) -> str:
    return str(plan.get("aesthetic_family", ""))


def _output_path(plan: dict, ext: str, output_path: str = None) -> Path:
    if output_path:
        return Path(output_path)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archetype_slug = _archetype(plan).lower().replace(" ", "_")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR / f"preview_{archetype_slug}_{ts}.{ext}"


# ---------------------------------------------------------------------------
# matplotlib path
# ---------------------------------------------------------------------------

def _generate_matplotlib(plan: dict, output_path: str = None) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.patch.set_facecolor("#000000")
    ax.set_facecolor("#000000")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    regime = _regime(plan)
    phys = _entropy(plan, "physical")
    struct = _entropy(plan, "structural")
    aest = _entropy(plan, "aesthetic")
    motion_sig = _motion_sig(plan)

    # --- procedural geometry ---
    rng = random.Random(42)

    if regime == "laminar":
        # smooth parallel horizontal lines with slight wave
        n_lines = 8
        for i in range(n_lines):
            y_base = 0.15 + (i / (n_lines - 1)) * 0.65
            xs = [j / 200 for j in range(201)]
            ys = [y_base + 0.015 * math.sin(2 * math.pi * x * 3 + i) * phys for x in xs]
            alpha = 0.4 + 0.5 * (1 - abs(i - n_lines / 2) / (n_lines / 2))
            ax.plot(xs, ys, color="#00BFFF", linewidth=0.8, alpha=alpha)

    elif regime == "oscillatory":
        # sinusoidal waves, amplitude driven by physical entropy
        n_waves = 5
        for i in range(n_waves):
            freq = 2 + i * 1.5
            amp = 0.05 + phys * 0.15
            y_off = 0.2 + i * 0.13
            xs = [j / 200 for j in range(201)]
            ys = [y_off + amp * math.sin(2 * math.pi * freq * x) for x in xs]
            ax.plot(xs, ys, color="#7B68EE", linewidth=1.0, alpha=0.75)

    elif regime == "turbulent":
        # scattered points seeded for reproducibility
        n_pts = int(80 + phys * 120)
        for _ in range(n_pts):
            x = rng.gauss(0.5, 0.22)
            y = rng.gauss(0.5, 0.22)
            x = max(0.02, min(0.98, x))
            y = max(0.12, min(0.85, y))
            ax.plot(x, y, "o", color="#FF4500", markersize=2.5, alpha=0.6)

    elif regime in ("vortex",) or "vortex" in motion_sig.lower():
        # spiral of points
        n_pts = 120
        for k in range(n_pts):
            t = k / n_pts * 4 * math.pi
            r = 0.04 + 0.28 * (t / (4 * math.pi))
            x = 0.5 + r * math.cos(t)
            y = 0.5 + r * math.sin(t) * 0.6
            alpha = 0.3 + 0.6 * (k / n_pts)
            ax.plot(x, y, "o", color="#00FF99", markersize=2, alpha=alpha)
    else:
        # default: simple diagonal gradient lines
        for i in range(12):
            t = i / 11
            ax.plot([0, 1], [t * 0.7 + 0.1, (1 - t) * 0.7 + 0.1],
                    color="#AAAAAA", linewidth=0.6, alpha=0.4)

    # --- entropy bar at bottom ---
    bar_y = 0.04
    bar_h = 0.04
    segments = [
        (0.05, struct, "#4FC3F7", "structural"),
        (0.38, aest,   "#CE93D8", "aesthetic"),
        (0.71, phys,   "#FF8A65", "physical"),
    ]
    for bx, val, color, _ in segments:
        # background
        ax.add_patch(mpatches.FancyBboxPatch(
            (bx, bar_y), 0.25, bar_h,
            boxstyle="round,pad=0.005", linewidth=0,
            facecolor="#222222"))
        # fill
        ax.add_patch(mpatches.FancyBboxPatch(
            (bx, bar_y), 0.25 * val, bar_h,
            boxstyle="round,pad=0.005", linewidth=0,
            facecolor=color, alpha=0.8))

    # entropy labels
    ax.text(0.055, bar_y + bar_h + 0.01, f"STR {struct:.2f}",
            color="#4FC3F7", fontsize=5.5, fontfamily="monospace")
    ax.text(0.385, bar_y + bar_h + 0.01, f"AES {aest:.2f}",
            color="#CE93D8", fontsize=5.5, fontfamily="monospace")
    ax.text(0.715, bar_y + bar_h + 0.01, f"PHY {phys:.2f}",
            color="#FF8A65", fontsize=5.5, fontfamily="monospace")

    # --- text overlays ---
    ax.text(0.5, 0.95, _archetype(plan).upper(),
            color="white", fontsize=13, fontfamily="monospace",
            ha="center", va="top", fontweight="bold")

    info_parts = []
    if motion_sig:
        info_parts.append(motion_sig)
    if _pacing(plan):
        info_parts.append(f"pacing:{_pacing(plan)}")
    if _aesthetic(plan):
        info_parts.append(_aesthetic(plan))
    ax.text(0.5, 0.88, "  |  ".join(info_parts),
            color="#AAAAAA", fontsize=6.5, fontfamily="monospace",
            ha="center", va="top")

    # --- regime badge ---
    ax.text(0.98, 0.95, f"[{regime}]",
            color="#00FF99", fontsize=7, fontfamily="monospace",
            ha="right", va="top")

    dest = _output_path(plan, "png", output_path)
    fig.savefig(str(dest), dpi=120, bbox_inches="tight",
                facecolor="#000000", pad_inches=0.05)
    plt.close(fig)
    return str(dest)


# ---------------------------------------------------------------------------
# SVG fallback path
# ---------------------------------------------------------------------------

def _generate_svg(plan: dict, output_path: str = None) -> str:
    W, H = 800, 450
    regime = _regime(plan)
    phys = _entropy(plan, "physical")
    struct = _entropy(plan, "structural")
    aest = _entropy(plan, "aesthetic")
    motion_sig = _motion_sig(plan)
    archetype = _archetype(plan)
    rng = random.Random(42)

    shapes: list[str] = []

    # background
    shapes.append(f'<rect width="{W}" height="{H}" fill="#000000"/>')

    # procedural geometry
    if regime == "laminar":
        n = 8
        for i in range(n):
            y_base = int(80 + (i / (n - 1)) * 260)
            pts = []
            for xi in range(0, W + 1, 5):
                x = xi
                y = y_base + int(12 * math.sin(2 * math.pi * (xi / W) * 3 + i) * phys)
                pts.append(f"{x},{y}")
            shapes.append(
                f'<polyline points="{" ".join(pts)}" fill="none" '
                f'stroke="#00BFFF" stroke-width="1" opacity="0.6"/>')

    elif regime == "oscillatory":
        for i in range(5):
            freq = 2 + i * 1.5
            amp = int((0.05 + phys * 0.15) * H)
            y_off = int(0.2 * H + i * 0.13 * H)
            pts = []
            for xi in range(0, W + 1, 4):
                x = xi
                y = y_off + int(amp * math.sin(2 * math.pi * freq * (xi / W)))
                pts.append(f"{x},{y}")
            shapes.append(
                f'<polyline points="{" ".join(pts)}" fill="none" '
                f'stroke="#7B68EE" stroke-width="1.2" opacity="0.75"/>')

    elif regime == "turbulent":
        n_pts = int(80 + phys * 120)
        for _ in range(n_pts):
            cx = int(rng.gauss(W / 2, W * 0.22))
            cy = int(rng.gauss(H * 0.5, H * 0.22))
            cx = max(10, min(W - 10, cx))
            cy = max(60, min(H - 60, cy))
            shapes.append(
                f'<circle cx="{cx}" cy="{cy}" r="3" '
                f'fill="#FF4500" opacity="0.6"/>')

    elif regime in ("vortex",) or "vortex" in motion_sig.lower():
        n_pts = 120
        for k in range(n_pts):
            t = k / n_pts * 4 * math.pi
            r = int((0.04 + 0.28 * (t / (4 * math.pi))) * min(W, H))
            cx = int(W / 2 + r * math.cos(t))
            cy = int(H / 2 + r * math.sin(t) * 0.6)
            op = round(0.3 + 0.6 * (k / n_pts), 2)
            shapes.append(
                f'<circle cx="{cx}" cy="{cy}" r="2.5" '
                f'fill="#00FF99" opacity="{op}"/>')
    else:
        for i in range(12):
            t = i / 11
            y1 = int((t * 0.7 + 0.1) * H)
            y2 = int(((1 - t) * 0.7 + 0.1) * H)
            shapes.append(
                f'<line x1="0" y1="{y1}" x2="{W}" y2="{y2}" '
                f'stroke="#AAAAAA" stroke-width="0.8" opacity="0.4"/>')

    # entropy bars
    bar_y = H - 35
    bar_h = 16
    segs = [
        (40,  struct, "#4FC3F7", f"STR {struct:.2f}"),
        (305, aest,   "#CE93D8", f"AES {aest:.2f}"),
        (568, phys,   "#FF8A65", f"PHY {phys:.2f}"),
    ]
    bar_w = 200
    for bx, val, color, label in segs:
        shapes.append(
            f'<rect x="{bx}" y="{bar_y}" width="{bar_w}" height="{bar_h}" '
            f'rx="3" fill="#222222"/>')
        shapes.append(
            f'<rect x="{bx}" y="{bar_y}" width="{int(bar_w * val)}" height="{bar_h}" '
            f'rx="3" fill="{color}" opacity="0.85"/>')
        shapes.append(
            f'<text x="{bx + 4}" y="{bar_y - 4}" fill="{color}" '
            f'font-family="monospace" font-size="10">{label}</text>')

    # archetype title
    shapes.append(
        f'<text x="{W // 2}" y="32" fill="white" font-family="monospace" '
        f'font-size="20" font-weight="bold" text-anchor="middle">'
        f'{archetype.upper()}</text>')

    # info line
    info_parts = []
    if motion_sig:
        info_parts.append(motion_sig)
    if _pacing(plan):
        info_parts.append(f"pacing:{_pacing(plan)}")
    if _aesthetic(plan):
        info_parts.append(_aesthetic(plan))
    info_str = "  |  ".join(info_parts)
    shapes.append(
        f'<text x="{W // 2}" y="52" fill="#AAAAAA" font-family="monospace" '
        f'font-size="11" text-anchor="middle">{info_str}</text>')

    # regime badge
    shapes.append(
        f'<text x="{W - 10}" y="28" fill="#00FF99" font-family="monospace" '
        f'font-size="12" text-anchor="end">[{regime}]</text>')

    svg = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">\n'
        + "\n".join(f"  {s}" for s in shapes)
        + "\n</svg>\n"
    )

    dest = _output_path(plan, "svg", output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(svg, encoding="utf-8")
    return str(dest)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_preview(plan: dict, output_path: str = None) -> str:
    """
    Generate a fast visual preview (< 1s) of the given plan.

    Tries matplotlib first (PNG); falls back to pure-SVG if unavailable.
    Returns the absolute path to the generated file.
    """
    try:
        return _generate_matplotlib(plan, output_path)
    except ImportError:
        return _generate_svg(plan, output_path)


def generate_ascii_preview(plan: dict) -> str:
    """
    Return a ~10-line ASCII art preview of the plan for quick terminal display.
    No external dependencies.
    """
    regime = _regime(plan)
    phys = _entropy(plan, "physical")
    struct = _entropy(plan, "structural")
    aest = _entropy(plan, "aesthetic")
    archetype = _archetype(plan)
    motion_sig = _motion_sig(plan)
    pacing = _pacing(plan)
    aesthetic = _aesthetic(plan)

    W = 52  # inner width
    border = "+" + "-" * W + "+"

    def bar(val: float, w: int = 14) -> str:
        filled = int(round(val * w))
        return "[" + "#" * filled + "." * (w - filled) + "]"

    def center(text: str) -> str:
        return "| " + text.center(W - 2) + " |"

    def left(text: str) -> str:
        truncated = text[: W - 2]
        return "| " + truncated.ljust(W - 2) + " |"

    # regime visualisation row (5 chars wide pattern)
    rng = random.Random(int(phys * 100))
    if regime == "laminar":
        vis = "~" * W
    elif regime == "oscillatory":
        vis = "".join("~" if math.sin(i * 0.4) > 0 else "-" for i in range(W))
    elif regime == "turbulent":
        vis = "".join(rng.choice(".*+  ") for _ in range(W))
    elif regime == "vortex" or "vortex" in motion_sig.lower():
        vis = "".join(rng.choice("oO°  ") for _ in range(W))
    else:
        vis = "-" * W

    lines = [
        border,
        center(archetype.upper()),
        center(f"[{regime}]  {aesthetic}"),
        "| " + vis[:W] + " |",
        "| " + vis[:W] + " |",
        border,
        left(f" PHY {bar(phys)}  {phys:.2f}"),
        left(f" STR {bar(struct)}  {struct:.2f}"),
        left(f" AES {bar(aest)}  {aest:.2f}"),
        border,
        left(f" motion : {motion_sig}"),
        left(f" pacing : {pacing}"),
        border,
    ]
    return "\n".join(lines)


def generate_preview_from_seed(
    seed: str,
    asset_registry: dict | None = None,
    identity: str = "aiox_default",
    output_path: str = None,
) -> str:
    """
    Generate a cheap preview directly from a seed by using the fast planning route.
    This avoids running the heavy render pipeline during ideation.
    """
    from core.compiler.creative_compiler import compile_seed
    from core.intelligence.model_router import TASK_FAST_PLAN

    result = compile_seed(seed, identity=identity, asset_registry=asset_registry, task_type=TASK_FAST_PLAN)
    return generate_preview(result["creative_plan"], output_path=output_path)
