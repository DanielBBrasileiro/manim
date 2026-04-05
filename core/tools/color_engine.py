"""
color_engine.py — Zero-dependency OKLCH-based Material 3 tonal palette generator.

Replaces the previous RGB-scaling pseudo-HCT with mathematically correct
color-space transforms:

  sRGB → linear RGB → XYZ D65 → OKLab → OKLCH

OKLCH (Björn Ottosson, 2020) provides perceptually uniform Lightness, Chroma,
and Hue separation that closely approximates Material 3's CAM16/HCT model
without external libraries. Tone is mapped to OKLab L ∈ [0, 1], equivalent
to the 0–100 scale used throughout the M3 specification.

Public API (unchanged):
  HCTColorEngine.generate_semantic_tokens(primary_hex) → dict
  get_relative_luminance(hex_color) → float
  get_contrast_ratio(hex1, hex2) → float
  hex_to_rgb(hex_color) → (r, g, b)
"""
import math
from typing import Dict, Any, List, Tuple


# ── sRGB ↔ linear RGB ─────────────────────────────────────────────────────

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c + c for c in hex_color)
    return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"


def _srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c: float) -> float:
    if c <= 0.0031308:
        return 12.92 * c
    return 1.055 * (c ** (1.0 / 2.4)) - 0.055


# ── linear RGB ↔ XYZ D65 ──────────────────────────────────────────────────

def _linear_rgb_to_xyz(r: float, g: float, b: float) -> Tuple[float, float, float]:
    x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b
    return x, y, z


def _xyz_to_linear_rgb(x: float, y: float, z: float) -> Tuple[float, float, float]:
    r =  3.2404542 * x - 1.5371385 * y - 0.4985314 * z
    g = -0.9692660 * x + 1.8760108 * y + 0.0415560 * z
    b =  0.0556434 * x - 0.2040259 * y + 1.0572252 * z
    return r, g, b


# ── XYZ D65 ↔ OKLab (Björn Ottosson, 2020) ───────────────────────────────

def _xyz_to_oklab(x: float, y: float, z: float) -> Tuple[float, float, float]:
    l = 0.8189330101 * x + 0.3618667424 * y - 0.1288597137 * z
    m = 0.0329845436 * x + 0.9293118715 * y + 0.0361456387 * z
    s = 0.0482003018 * x + 0.2643662691 * y + 0.6338517070 * z

    def _cbrt(v: float) -> float:
        return v ** (1.0 / 3.0) if v >= 0 else -((-v) ** (1.0 / 3.0))

    l_, m_, s_ = _cbrt(l), _cbrt(m), _cbrt(s)
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, a, b


def _oklab_to_xyz(L: float, a: float, b: float) -> Tuple[float, float, float]:
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    x =  1.2270138511 * l - 0.5577999807 * m + 0.2812561490 * s
    y = -0.0405801784 * l + 1.1122568696 * m - 0.0716766787 * s
    z = -0.0763812845 * l - 0.4214819784 * m + 1.5861632204 * s
    return x, y, z


# ── OKLab ↔ OKLCH ─────────────────────────────────────────────────────────

def _oklab_to_oklch(L: float, a: float, b: float) -> Tuple[float, float, float]:
    C = math.sqrt(a * a + b * b)
    H = math.degrees(math.atan2(b, a)) % 360.0
    return L, C, H


def _oklch_to_oklab(L: float, C: float, H: float) -> Tuple[float, float, float]:
    h = math.radians(H)
    return L, C * math.cos(h), C * math.sin(h)


# ── High-level round-trip helpers ─────────────────────────────────────────

def hex_to_oklch(hex_color: str) -> Tuple[float, float, float]:
    """Convert sRGB hex to OKLCH (L ∈ [0,1], C ≥ 0, H ∈ [0,360))."""
    r, g, b = hex_to_rgb(hex_color)
    rl = _srgb_to_linear(r / 255.0)
    gl = _srgb_to_linear(g / 255.0)
    bl = _srgb_to_linear(b / 255.0)
    return _oklab_to_oklch(*_xyz_to_oklab(*_linear_rgb_to_xyz(rl, gl, bl)))


def oklch_to_hex(L: float, C: float, H: float) -> str:
    """Convert OKLCH back to sRGB hex, clamping to the sRGB gamut."""
    La, a, b = _oklch_to_oklab(L, C, H)
    rl, gl, bl = _xyz_to_linear_rgb(*_oklab_to_xyz(La, a, b))
    r = max(0, min(255, round(_linear_to_srgb(rl) * 255)))
    g = max(0, min(255, round(_linear_to_srgb(gl) * 255)))
    b = max(0, min(255, round(_linear_to_srgb(bl) * 255)))
    return rgb_to_hex(r, g, b)


# ── WCAG utilities (public, unchanged API) ────────────────────────────────

def get_relative_luminance(hex_color: str) -> float:
    """WCAG 2.1 relative luminance (Y in XYZ, D65)."""
    r, g, b = hex_to_rgb(hex_color)
    return (0.2126 * _srgb_to_linear(r / 255.0) +
            0.7152 * _srgb_to_linear(g / 255.0) +
            0.0722 * _srgb_to_linear(b / 255.0))


def get_contrast_ratio(hex1: str, hex2: str) -> float:
    """WCAG contrast ratio between two hex colors."""
    l1, l2 = get_relative_luminance(hex1), get_relative_luminance(hex2)
    bright, dark = max(l1, l2), min(l1, l2)
    return (bright + 0.05) / (dark + 0.05)


# ── Internal palette builder ──────────────────────────────────────────────

def _generate_tonal_palette(H: float, C: float, steps: List[int]) -> Dict[str, str]:
    """
    M3-style tonal palette: vary L across [0,1] while holding H and C constant.
    Tone 0 → #000000, Tone 100 → #ffffff (by definition, regardless of H/C).
    Out-of-gamut values are clamped to the nearest sRGB boundary.
    """
    tones: Dict[str, str] = {}
    for step in steps:
        if step == 0:
            tones[f"tone_{step}"] = "#000000"
        elif step == 100:
            tones[f"tone_{step}"] = "#ffffff"
        else:
            tones[f"tone_{step}"] = oklch_to_hex(step / 100.0, C, H)
    return tones


# ── Public engine ─────────────────────────────────────────────────────────

class HCTColorEngine:
    """
    OKLCH-based Material 3 Tonal Palette Generator.

    Generates three standard M3 palettes — primary, neutral, neutral-variant —
    and maps them to the six canonical semantic roles required by the pipeline:
      primary, on_primary, surface, on_surface, surface_variant, outline.

    Output shape (backward-compatible + M3-enriched):
      {
        primary, on_primary, surface, on_surface, surface_variant, outline,
        tones: { tone_0 … tone_100 },          ← primary palette
        tones_neutral: { … },                  ← neutral (surface) palette
        tones_neutral_variant: { … },          ← neutral variant (outline) palette
      }
    """

    _WHITE_HOLE_THRESHOLD = 0.90
    _TONAL_STEPS: List[int] = [0, 10, 20, 25, 30, 40, 50, 60, 70, 80, 90, 95, 100]

    @staticmethod
    def generate_semantic_tokens(primary_hex: str) -> Dict[str, Any]:
        primary_lum = get_relative_luminance(primary_hex)

        # Chrome Guard: near-white primaries collapse the tonal scale.
        # Anchor to T60 neutral (#999999) to preserve minimum visual distinction.
        if primary_lum > HCTColorEngine._WHITE_HOLE_THRESHOLD:
            print(
                f"⚠️ [HCTColorEngine] Chrome Guard ativado: primary_lum={primary_lum:.3f} > "
                f"{HCTColorEngine._WHITE_HOLE_THRESHOLD}. Usando tonal_anchor T60 (#999999) "
                f"para evitar colapso da escala tonal (White Hole)."
            )
            tonal_anchor = "#999999"
        else:
            tonal_anchor = primary_hex

        _, C, H = hex_to_oklch(tonal_anchor)

        steps = HCTColorEngine._TONAL_STEPS

        # Three M3 palettes: primary | neutral (very low chroma) | neutral variant
        primary_tones = _generate_tonal_palette(H, C, steps)
        neutral_tones = _generate_tonal_palette(H, max(C * 0.06, 0.008), steps)
        nv_tones      = _generate_tonal_palette(H, max(C * 0.12, 0.015), steps)

        # Semantic role assignment following M3 dark-scheme conventions
        # (AIOX renders on black canvas — dark-scheme is the production path)
        is_dark = primary_lum < 0.15
        if is_dark:
            on_primary  = primary_tones["tone_20"]
            surface     = neutral_tones["tone_10"]
            on_surface  = neutral_tones["tone_90"]
            surface_var = nv_tones["tone_30"]
            outline     = nv_tones["tone_60"]
        else:
            on_primary  = primary_tones["tone_20"]
            surface     = neutral_tones["tone_95"]
            on_surface  = neutral_tones["tone_10"]
            surface_var = nv_tones["tone_90"]
            outline     = nv_tones["tone_50"]

        return {
            # Semantic roles — backward-compatible keys preserved
            "primary":          primary_hex,
            "on_primary":       on_primary,
            "surface":          surface,
            "on_surface":       on_surface,
            "surface_variant":  surface_var,
            "outline":          outline,
            # M3 tonal palettes — official structure for surface tint / elevation
            "tones":                    primary_tones,
            "tones_neutral":            neutral_tones,
            "tones_neutral_variant":    nv_tones,
        }
