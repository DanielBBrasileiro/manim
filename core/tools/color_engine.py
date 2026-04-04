"""
color_engine.py - A zero-dependency pseudo-HCT color engine replicating Material 3 tokens.
Calculates WCAG relative luminance and generates scalable semantic tonal palettes.
"""
import math
from typing import Dict, Any, Tuple

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c + c for c in hex_color)
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"

def get_relative_luminance(hex_color: str) -> float:
    """Calculates WCAG relative luminance."""
    r, g, b = hex_to_rgb(hex_color)
    def srgb_to_lin(color_channel: int) -> float:
        c = color_channel / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * srgb_to_lin(r) + 0.7152 * srgb_to_lin(g) + 0.0722 * srgb_to_lin(b)

def get_contrast_ratio(hex1: str, hex2: str) -> float:
    """Returns the WCAG contrast ratio between two hex colors."""
    l1 = get_relative_luminance(hex1)
    l2 = get_relative_luminance(hex2)
    bright = max(l1, l2)
    dark = min(l1, l2)
    return (bright + 0.05) / (dark + 0.05)

def adjust_tone(hex_color: str, factor: float) -> str:
    """
    Crude perceptual tone adjustment. 
    factor > 1.0 lightens, factor < 1.0 darkens.
    """
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hex(
        int(r + (255 - r) * (factor - 1.0) if factor > 1 else r * factor),
        int(g + (255 - g) * (factor - 1.0) if factor > 1 else g * factor),
        int(b + (255 - b) * (factor - 1.0) if factor > 1 else b * factor)
    )

class HCTColorEngine:
    """
    Pseudo-HCT Tonal Palette Generator.
    Approximates Material 3 behavior, forcing an explicit 'on-primary' to ensure legibility.
    """
    
    @staticmethod
    def generate_semantic_tokens(primary_hex: str) -> Dict[str, str]:
        # Semantic mapping
        primary = primary_hex
        
        # Decide if 'on-primary' should be white or black based on primary luminance
        primary_lum = get_relative_luminance(primary)
        on_primary = "#ffffff" if primary_lum < 0.4 else "#1a1a1a"
        
        # Surface generation: usually a very tinted neutral
        surface = "#ffffff"
        on_surface = "#1a1a1a"
        
        # If dark mode brand, flip surface logic (this could be parameterized)
        if primary_lum < 0.15:
            surface = "#121212"
            on_surface = "#ffffff"
            
        surface_variant = adjust_tone(surface, 0.9 if surface == "#ffffff" else 1.5)
        outline = adjust_tone(surface, 0.8 if surface == "#ffffff" else 1.8)

        # M3 HCT Array Generation (0-100 steps)
        # Note: True HCT involves complex CAM16 matrices. This is a highly-tuned perceptual fake
        # aiming to closely mimic the luminance distribution for MD3 constraints.
        tones = {}
        target_steps = [0, 10, 20, 25, 30, 40, 50, 60, 70, 80, 90, 95, 100]
        
        # M3 assigns Tone 40 as the primary baseline for light themes, and Tone 80 for dark.
        # We estimate a curve where 0 is black, 100 is white, and the brand color sits near 40.
        for step in target_steps:
            if step == 0:
                tones[f"tone_{step}"] = "#000000"
            elif step == 100:
                tones[f"tone_{step}"] = "#ffffff"
            elif step == 40:
                tones[f"tone_{step}"] = primary
            else:
                # Calculate simple blending to approach black or white
                ratio = step / 100.0
                if step < 40:
                    darkness = step / 40.0
                    tones[f"tone_{step}"] = adjust_tone(primary, 0.3 + (darkness * 0.7))
                else:
                    lightness = (step - 40) / 60.0
                    tones[f"tone_{step}"] = adjust_tone(primary, 1.0 + lightness)

        return {
            "primary": primary,
            "on_primary": on_primary,
            "surface": surface,
            "on_surface": on_surface,
            "surface_variant": surface_variant,
            "outline": outline,
            "tones": tones
        }
