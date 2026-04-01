"""
contract_loader.py — Unified brand context for quality scoring.

Loads tokens.json + YAML contracts into QualityContract with caching.
Resolves cross-references (easing names → cubic-bezier values).
"""
from __future__ import annotations

import json
import yaml
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent

_EASING_RESOLVED = {
    "spring": "cubic-bezier(0.16, 1, 0.3, 1)",
    "smooth": "cubic-bezier(0.4, 0, 0.2, 1)",
    "linear": "cubic-bezier(0, 0, 1, 1)",
    "exponential_in_out": "cubic-bezier(0.87, 0, 0.13, 1)",
    "there_and_back": "cubic-bezier(0.36, 0.07, 0.19, 0.97)",
}


class QualityContract:
    """Unified container for all brand design laws."""

    def __init__(self) -> None:
        self.tokens = self._load_json(ROOT / "assets" / "brand" / "tokens.json")
        self.laws = self._load_yaml(ROOT / "contracts" / "global_laws.yaml")
        self.typography = self._load_yaml(ROOT / "contracts" / "typography.yaml")
        self.motion = self._load_yaml(ROOT / "contracts" / "motion.yaml")
        self.layout = self._load_yaml(ROOT / "contracts" / "layout.yaml")

    def _load_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            return {}

    def _brand(self) -> dict[str, Any]:
        return self.tokens.get("brand", {})

    def _colors(self) -> dict[str, Any]:
        return self._brand().get("color_states", {}).get("dark", {})

    def _accent(self) -> dict[str, Any]:
        return self._brand().get("color_states", {}).get("accent", {})

    def get_palette_list(self) -> list[str]:
        """Allowed hex/rgba values for pixel-level audit."""
        colors = self._colors()
        accent = self._accent()
        return [
            colors.get("background", "#000000").lower(),
            colors.get("foreground", "#ffffff").lower(),
            colors.get("stroke", "rgba(255,255,255,0.85)").lower(),
            colors.get("text_secondary", "rgba(255,255,255,0.55)").lower(),
            accent.get("color", "#ff3366").lower(),
        ]

    def get_vision_context(self) -> str:
        """Injects real token values into vision LLM prompt. No generic placeholders."""
        colors = self._colors()
        accent = self._accent()
        brand = self._brand()
        anti = brand.get("anti_patterns", [])
        materials = brand.get("materials", {})
        grain = materials.get("grain", 0.06)

        constraints = self.laws.get("constraints", {})
        min_neg_space = constraints.get("min_negative_space", 0.40)
        max_colors = constraints.get("max_colors", 2)
        max_weights = constraints.get("typography", {}).get("max_weights", 2)

        anti_text = "\n".join(f"  - {p}" for p in anti) if anti else "  - no gradients, no shadows, no logos"

        return (
            "# AIOX BRAND DESIGN LAWS (MANDATORY — EVALUATE AGAINST THESE EXACT VALUES)\n"
            f"BACKGROUND: {colors.get('background', '#000000')} (primary canvas)\n"
            f"FOREGROUND: {colors.get('foreground', '#FFFFFF')} (text and strokes)\n"
            f"STROKE: {colors.get('stroke', 'rgba(255,255,255,0.85)')}\n"
            f"TEXT_SECONDARY: {colors.get('text_secondary', 'rgba(255,255,255,0.55)')}\n"
            f"ACCENT: {accent.get('color', '#FF3366')} — MAX {accent.get('max_screen_coverage', '2%')} COVERAGE\n"
            f"MAX COLORS IN FRAME: {max_colors}\n"
            f"NEGATIVE SPACE: >= {int(min_neg_space * 100)}% OF FRAME AREA MUST BE EMPTY\n"
            f"MAX FONT WEIGHTS: {max_weights} (300=Whisper, 500=Statement)\n"
            "FONT FAMILIES: PP Neue Montreal, Inter, Helvetica Neue (sans-serif only)\n"
            "MAX WORDS PER SCREEN: 5\n"
            "GRAIN TEXTURE: present (subtle film grain ~{:.2f} intensity)\n"
            "ANTI-PATTERNS (FORBIDDEN):\n"
            "{}\n"
            "COMPOSITION: Rule of Thirds. Min 64px edge margin (breathing room).\n"
            "PREMIUM SIGNAL: mathematical precision, high contrast, intentional emptiness."
        ).format(grain, anti_text)

    def get_archetype_context(self, archetype: str) -> str:
        """Load archetype-specific scoring context."""
        arch_path = ROOT / "contracts" / "narrative" / "archetypes" / f"{archetype}.yaml"
        if not arch_path.exists():
            return ""
        try:
            data = yaml.safe_load(arch_path.read_text(encoding="utf-8")) or {}
            phases = data.get("phases", [])
            desc = data.get("description", "")
            phase_summary = ", ".join(str(p.get("id", "?")) for p in phases)
            return f"ARCHETYPE: {archetype} — {desc}\nACTS: {phase_summary}"
        except Exception:
            return ""

    def resolve_easing(self, name: str) -> str:
        """Resolve easing name to cubic-bezier string."""
        return _EASING_RESOLVED.get(name.lower(), name)


@lru_cache(maxsize=1)
def load_quality_contract() -> QualityContract:
    return QualityContract()
