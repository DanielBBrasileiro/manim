"""
post_processor.py — Cinematic post-processing for AIOX renders.

Applies film-grade effects that transform digital output into
premium cinematic output. All effects use Pillow + NumPy only.

Effects:
  grain        — Film grain texture (existing, from tokens.json grain: 0.06)
  halation     — Optical bloom on highlights (simulates film response)
  breath_exposure — Sinusoidal exposure variation ±2% (living camera feel)
  color_grade  — Narrative-act-aware LUT: genesis=cool, turbulence=contrast, resolution=warm
  vignette     — Subtle edge darkening for cinematic framing

Presets (archetype-driven):
  genesis_preset     — grain + halation(soft) + breath_exposure + color_grade(genesis)
  turbulence_preset  — grain + halation(intense) + color_grade(turbulence) + vignette
  resolution_preset  — grain + color_grade(resolution) + breath_exposure(gentle)
  default_preset     — grain + vignette
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PostProcessConfig:
    """Configuration for a post-processing run."""
    grain: float = 0.06          # Film grain intensity (0-1)
    halation: float = 0.0        # Optical bloom on highlights (0-1)
    halation_warmth: float = 0.3 # Warm tint for halation (0-1)
    breath_exposure: float = 0.0 # Exposure breath amplitude (0-0.05)
    breath_phase: float = 0.0    # Phase offset for breath (0-2π)
    color_grade: str = "none"    # "none" | "genesis" | "turbulence" | "resolution"
    vignette: float = 0.0        # Vignette strength (0-1)

    @classmethod
    def genesis(cls) -> "PostProcessConfig":
        return cls(grain=0.055, halation=0.12, halation_warmth=0.15,
                   breath_exposure=0.018, color_grade="genesis", vignette=0.15)

    @classmethod
    def turbulence(cls) -> "PostProcessConfig":
        return cls(grain=0.075, halation=0.22, halation_warmth=0.35,
                   color_grade="turbulence", vignette=0.25)

    @classmethod
    def resolution_act(cls) -> "PostProcessConfig":
        return cls(grain=0.05, breath_exposure=0.012, breath_phase=math.pi * 0.5,
                   color_grade="resolution", vignette=0.10)

    @classmethod
    def default(cls) -> "PostProcessConfig":
        return cls(grain=0.06, vignette=0.10)


# Preset registry
_PRESETS: dict[str, PostProcessConfig] = {
    "genesis": PostProcessConfig.genesis(),
    "turbulence": PostProcessConfig.turbulence(),
    "resolution": PostProcessConfig.resolution_act(),
    "default": PostProcessConfig.default(),
}


def get_preset(act_id: str, archetype: str = "") -> PostProcessConfig:
    """
    Select a PostProcessConfig based on narrative act and archetype.

    Priority: act_id match → archetype-derived → default
    """
    act_lower = act_id.lower()

    # Direct act match
    for key in ("genesis", "turbulence", "resolution"):
        if key in act_lower:
            return _PRESETS[key]

    # Archetype-derived fallback
    high_chaos = {"fragmented_reveal", "order_to_chaos", "signal_break", "chaotic_dispersion"}
    if archetype in high_chaos:
        return _PRESETS["turbulence"]

    calm_close = {"resolution", "synchronization", "loop_stability", "expansion_field"}
    if archetype in calm_close:
        return _PRESETS["resolution"]

    return _PRESETS["default"]


def apply_grain(pixels, intensity: float):
    """Apply film grain texture using Gaussian noise."""
    import numpy as np
    noise = np.random.normal(0, intensity * 255, pixels.shape).astype(np.float32)
    return np.clip(pixels.astype(np.float32) + noise, 0, 255).astype(np.uint8)


def apply_halation(pixels, strength: float, warmth: float):
    """
    Halation: optical bloom on bright highlights.

    Simulates film emulsion's light-scattering around bright areas.
    Different from glow: softer falloff, warm color shift in highlights.
    Strength: 0 = disabled, 1 = strong bloom
    Warmth: adds subtle warm (R+G) shift to bloom areas
    """
    import numpy as np
    from PIL import Image

    if strength < 0.01:
        return pixels

    img = Image.fromarray(pixels.astype(np.uint8), mode="RGB")
    width, height = img.size

    # Extract highlight mask (pixels > 200 brightness)
    arr = pixels.astype(np.float32)
    gray = arr.mean(axis=2)
    highlight_mask = np.clip((gray - 200) / 55.0, 0, 1)  # smooth threshold

    # Blur the highlights heavily for bloom
    from PIL import ImageFilter
    mask_img = Image.fromarray((highlight_mask * 255).astype(np.uint8), mode="L")
    blurred = mask_img.filter(ImageFilter.GaussianBlur(radius=max(2, int(min(width, height) * 0.015))))
    bloom = np.array(blurred, dtype=np.float32) / 255.0

    # Apply warm tint to bloom (add R and slightly G)
    bloom_rgb = np.stack([
        bloom * (1.0 + warmth * 0.3),   # R channel warmer
        bloom * (1.0 + warmth * 0.1),   # G slightly warm
        bloom * 1.0,                      # B unchanged
    ], axis=2)

    result = arr + bloom_rgb * strength * 40
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_breath_exposure(pixels, amplitude: float, phase: float):
    """
    Breath exposure: sinusoidal ±amplitude variation in overall exposure.

    Gives the render a subtle "living camera" feel — the exposure
    oscillates as if a human is holding the camera and breathing.
    Amplitude: 0.02 = ±2% exposure variation (recommended)
    """
    import numpy as np

    if amplitude < 0.001:
        return pixels

    factor = 1.0 + amplitude * math.sin(phase)
    result = pixels.astype(np.float32) * factor
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_color_grade(pixels, grade: str):
    """
    Narrative-act LUT (simplified 3-channel curves).

    genesis:    Cool shift — desaturated, slightly blue. Curiosity/uncertainty.
    turbulence: High contrast + warm highlights. Tension/heat.
    resolution: Balanced with slight warmth. Mastery/completion.
    """
    import numpy as np

    if grade == "none" or not grade:
        return pixels

    arr = pixels.astype(np.float32)

    if grade == "genesis":
        # Cool, slightly desaturated
        arr[:, :, 0] *= 0.94   # reduce red
        arr[:, :, 1] *= 0.97   # reduce green slightly
        arr[:, :, 2] *= 1.06   # boost blue
        # Slight desaturation: blend toward gray
        gray = arr.mean(axis=2, keepdims=True)
        arr = arr * 0.88 + gray * 0.12

    elif grade == "turbulence":
        # High contrast + warm highlights
        # S-curve: boost darks toward black, boost lights toward white
        normalized = arr / 255.0
        # Simple contrast S-curve: 3x^2 - 2x^3 (smooth step) mapped to ±boost
        contrast_boost = 1.25
        mid = 0.5
        normalized = mid + (normalized - mid) * contrast_boost
        # Warm shift in highlights
        warm_mask = np.clip((normalized - 0.7) / 0.3, 0, 1)
        normalized[:, :, 0] += warm_mask * 0.06   # warm reds
        normalized[:, :, 1] += warm_mask * 0.02   # slight green
        arr = np.clip(normalized * 255, 0, 255)

    elif grade == "resolution":
        # Balanced + slight warmth
        arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.03, 0, 255)  # very slight warm
        arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.97, 0, 255)  # reduce blue slightly
        # Lift blacks very subtly (0.02 toe)
        arr = np.clip(arr + 5, 0, 255)

    return np.clip(arr, 0, 255).astype(np.uint8)


def apply_vignette(pixels, strength: float):
    """Subtle circular vignette — edge darkening for cinematic framing."""
    import numpy as np

    if strength < 0.01:
        return pixels

    h, w = pixels.shape[:2]
    cy, cx = h / 2.0, w / 2.0
    y_idx = np.arange(h, dtype=np.float32)
    x_idx = np.arange(w, dtype=np.float32)
    yy, xx = np.meshgrid(y_idx, x_idx, indexing="ij")
    dist = np.sqrt(((yy - cy) / cy) ** 2 + ((xx - cx) / cx) ** 2)
    vignette_map = 1.0 - np.clip(dist * strength, 0, 1)
    vignette_map = vignette_map[:, :, np.newaxis]
    result = pixels.astype(np.float32) * vignette_map
    return np.clip(result, 0, 255).astype(np.uint8)


def process_frame(
    frame_path: str,
    output_path: str | None = None,
    *,
    config: PostProcessConfig | None = None,
    act_id: str = "default",
    archetype: str = "",
) -> str:
    """
    Apply post-processing to a single rendered frame.

    Args:
        frame_path: Input PNG/JPEG path
        output_path: Output path (defaults to overwrite in place)
        config: Explicit PostProcessConfig (overrides act_id/archetype)
        act_id: Narrative act for preset selection
        archetype: Archetype for preset selection fallback

    Returns:
        Path to processed frame
    """
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        return frame_path  # Fail gracefully

    cfg = config or get_preset(act_id, archetype)
    out_path = output_path or frame_path

    img = Image.open(frame_path).convert("RGB")
    pixels = np.array(img, dtype=np.uint8)

    # Apply effects in order: grade → halation → grain → exposure → vignette
    if cfg.color_grade and cfg.color_grade != "none":
        pixels = apply_color_grade(pixels, cfg.color_grade)

    if cfg.halation > 0:
        pixels = apply_halation(pixels, cfg.halation, cfg.halation_warmth)

    if cfg.grain > 0:
        pixels = apply_grain(pixels, cfg.grain)

    if cfg.breath_exposure > 0:
        pixels = apply_breath_exposure(pixels, cfg.breath_exposure, cfg.breath_phase)

    if cfg.vignette > 0:
        pixels = apply_vignette(pixels, cfg.vignette)

    result_img = Image.fromarray(pixels, mode="RGB")
    result_img.save(out_path, optimize=True)
    return out_path


def process_pipeline_outputs(
    outputs: list[dict[str, Any]],
    *,
    archetype: str = "",
    acts: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    Apply post-processing to all still outputs from a render pipeline.

    Args:
        outputs: render_pipeline output list (dicts with 'output' key)
        archetype: active archetype for preset selection
        acts: pacing acts list (each with act_id for per-act presets)

    Returns:
        outputs with 'post_processed' key added to each still
    """
    act_id = "default"
    if acts:
        # Use turbulence act as default (most common render moment)
        for act in acts:
            if "turbulence" in str(act.get("act_id", "")).lower():
                act_id = "turbulence"
                break
        if act_id == "default" and acts:
            act_id = str(acts[0].get("act_id", "default"))

    processed = []
    for output in outputs:
        if not isinstance(output, dict):
            processed.append(output)
            continue

        out_path = output.get("output", "")
        render_mode = output.get("mode", "video")

        # Only post-process stills (videos need frame-level processing)
        if render_mode == "still" and out_path and out_path.endswith(".png"):
            try:
                process_frame(out_path, act_id=act_id, archetype=archetype)
                output = {**output, "post_processed": True, "post_process_preset": act_id}
            except Exception as exc:
                output = {**output, "post_processed": False, "post_process_error": str(exc)}

        processed.append(output)
    return processed
