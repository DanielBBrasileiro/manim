from __future__ import annotations

import json
import re
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from core.quality.brand_validator import validate_frame

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_REFERENCE_OUTPUT_DIR = ROOT / "contracts" / "references"

COLOR_RE = re.compile(
    r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b|rgba?\([^)]+\)|hsla?\([^)]+\)"
)
FONT_FAMILY_RE = re.compile(r"font-family\s*:\s*([^;}{]+)", re.IGNORECASE)
FONT_FACE_RE = re.compile(r"@font-face\s*{[^}]*font-family\s*:\s*([^;}{]+)", re.IGNORECASE | re.DOTALL)
FONT_SRC_RE = re.compile(r"url\(([^)]+)\)", re.IGNORECASE)
SPACING_RE = re.compile(r"(?:margin|padding|gap|row-gap|column-gap)\s*:\s*([^;}{]+)", re.IGNORECASE)
MAX_WIDTH_RE = re.compile(r"max-width\s*:\s*([^;}{]+)", re.IGNORECASE)
RADIUS_RE = re.compile(r"border-radius\s*:\s*([^;}{]+)", re.IGNORECASE)
TRANSITION_RE = re.compile(r"transition\s*:\s*([^;}{]+)", re.IGNORECASE)
ANIMATION_RE = re.compile(r"animation(?:-name)?\s*:\s*([^;}{]+)", re.IGNORECASE)

JS_MOTION_LIBS = {
    "gsap": "gsap",
    "framer-motion": "framer_motion",
    "motion": "motion_one_or_framer",
    "locomotive": "locomotive_scroll",
    "lenis": "lenis",
    "barba": "barba",
    "swiper": "swiper",
    "three": "three_js",
}


@dataclass(frozen=True)
class ReferenceTranslationPaths:
    slug: str
    yaml_path: Path
    json_path: Path


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(value).lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "reference_snapshot"


def _clean_css_value(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip().strip("\"'"))


def _normalize_font_name(value: str) -> str:
    cleaned = _clean_css_value(value)
    cleaned = cleaned.split(",")[0].strip()
    return cleaned.strip("\"'")


def _read_zip_text(member: zipfile.ZipFile, name: str) -> str:
    try:
        raw = member.read(name)
    except KeyError:
        return ""
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def _extract_asset_inventory(names: list[str]) -> dict[str, Any]:
    lower_names = [name.lower() for name in names]
    return {
        "html_files": [name for name in names if name.lower().endswith(".html")],
        "css_files": [name for name in names if name.lower().endswith(".css")],
        "js_files": [name for name in names if name.lower().endswith((".js", ".mjs"))],
        "font_files": [name for name in names if name.lower().endswith((".woff", ".woff2", ".ttf", ".otf"))],
        "image_assets": [name for name in names if name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".svg", ".avif"))],
        "video_assets": [name for name in names if name.lower().endswith((".mp4", ".webm", ".mov"))],
        "motion_libs_detected": sorted(
            {
                library
                for token, library in JS_MOTION_LIBS.items()
                if any(token in name for name in lower_names)
            }
        ),
    }


def _extract_typography_signals(css_texts: list[str], asset_inventory: dict[str, Any]) -> dict[str, Any]:
    families: list[str] = []
    for text in css_texts:
        families.extend(_normalize_font_name(match.group(1)) for match in FONT_FAMILY_RE.finditer(text))
        families.extend(_normalize_font_name(match.group(1)) for match in FONT_FACE_RE.finditer(text))
    family_counts = Counter(name for name in families if name)
    top_families = [name for name, _ in family_counts.most_common(6)]
    return {
        "font_families": top_families,
        "font_family_counts": dict(family_counts.most_common(10)),
        "font_files": list(asset_inventory.get("font_files", [])),
        "font_sources": sorted(
            {
                _clean_css_value(source)
                for text in css_texts
                for source in FONT_SRC_RE.findall(text)
                if any(ext in source.lower() for ext in (".woff", ".woff2", ".ttf", ".otf"))
            }
        ),
        "headline_clue": top_families[0] if top_families else "",
        "body_clue": top_families[1] if len(top_families) > 1 else (top_families[0] if top_families else ""),
    }


def _extract_visual_signals(css_texts: list[str]) -> dict[str, Any]:
    colors = Counter(
        _clean_css_value(match.group(0))
        for text in css_texts
        for match in COLOR_RE.finditer(text)
    )
    spacing = Counter(
        _clean_css_value(match.group(1))
        for text in css_texts
        for match in SPACING_RE.finditer(text)
    )
    max_widths = Counter(
        _clean_css_value(match.group(1))
        for text in css_texts
        for match in MAX_WIDTH_RE.finditer(text)
    )
    radii = Counter(
        _clean_css_value(match.group(1))
        for text in css_texts
        for match in RADIUS_RE.finditer(text)
    )
    transitions = Counter(
        _clean_css_value(match.group(1))
        for text in css_texts
        for match in TRANSITION_RE.finditer(text)
    )
    animations = Counter(
        _clean_css_value(match.group(1))
        for text in css_texts
        for match in ANIMATION_RE.finditer(text)
    )
    return {
        "top_colors": [value for value, _ in colors.most_common(8)],
        "top_spacing_tokens": [value for value, _ in spacing.most_common(8)],
        "max_width_tokens": [value for value, _ in max_widths.most_common(6)],
        "border_radius_tokens": [value for value, _ in radii.most_common(6)],
        "transition_tokens": [value for value, _ in transitions.most_common(6)],
        "animation_tokens": [value for value, _ in animations.most_common(6)],
    }


def _extract_layout_signals(html_texts: list[str], css_texts: list[str]) -> dict[str, Any]:
    combined_css = "\n".join(css_texts)
    combined_html = "\n".join(html_texts)
    return {
        "grid_mentions": combined_css.lower().count("display:grid") + combined_css.lower().count("display: grid"),
        "flex_mentions": combined_css.lower().count("display:flex") + combined_css.lower().count("display: flex"),
        "sticky_mentions": combined_css.lower().count("position:sticky") + combined_css.lower().count("position: sticky"),
        "section_count_hint": len(re.findall(r"<section\b", combined_html, flags=re.IGNORECASE)),
        "hero_count_hint": len(re.findall(r"hero", combined_html, flags=re.IGNORECASE)),
        "card_count_hint": len(re.findall(r"card", combined_html, flags=re.IGNORECASE)),
        "button_count_hint": len(re.findall(r"<button\b", combined_html, flags=re.IGNORECASE)),
    }


def _extract_motion_signals(asset_inventory: dict[str, Any], visual_signals: dict[str, Any], js_texts: list[str]) -> dict[str, Any]:
    js_combined = "\n".join(js_texts).lower()
    detected = set(asset_inventory.get("motion_libs_detected", []))
    for token, label in JS_MOTION_LIBS.items():
        if token in js_combined:
            detected.add(label)
    transition_tokens = list(visual_signals.get("transition_tokens", []))
    animation_tokens = list(visual_signals.get("animation_tokens", []))
    return {
        "motion_libraries": sorted(detected),
        "transition_tokens": transition_tokens,
        "animation_tokens": animation_tokens,
        "motion_density": "restrained" if len(animation_tokens) <= 2 and len(detected) <= 1 else "expressive",
    }


def _material_signals(asset_inventory: dict[str, Any], visual_signals: dict[str, Any]) -> dict[str, Any]:
    colors = [value.lower() for value in visual_signals.get("top_colors", [])]
    dark_background = any(value in {"#000", "#000000", "#0b0d12", "#0f0f0f"} for value in colors)
    rounded = any("999" in token or token.endswith("px") for token in visual_signals.get("border_radius_tokens", []))
    return {
        "dark_bias": dark_background,
        "rounded_bias": rounded,
        "image_asset_count": len(asset_inventory.get("image_assets", [])),
        "video_asset_count": len(asset_inventory.get("video_assets", [])),
        "surface_language": "soft_ui" if rounded else "editorial_flat",
    }


def analyze_screenshots(paths: list[str] | None) -> dict[str, Any]:
    screenshot_paths = [Path(path) for path in (paths or []) if str(path).strip()]
    if not screenshot_paths:
        return {"provided": False, "count": 0}

    reports = []
    for path in screenshot_paths:
        if not path.exists():
            continue
        result = validate_frame(str(path))
        reports.append(result)
    if not reports:
        return {"provided": True, "count": 0, "valid": False}

    avg_negative_space = round(sum(item.negative_space_pct for item in reports) / len(reports), 3)
    avg_text_density = round(sum(item.text_density_estimate for item in reports) / len(reports), 2)
    avg_color_purity = round(sum(item.color_purity_score for item in reports) / len(reports), 1)
    return {
        "provided": True,
        "count": len(reports),
        "valid": True,
        "avg_negative_space_pct": avg_negative_space,
        "avg_text_density_estimate": avg_text_density,
        "avg_color_purity_score": avg_color_purity,
        "hierarchy_clue": "strong" if avg_text_density <= 5 and avg_negative_space >= 0.4 else "mixed",
        "poster_impact_clue": "high" if avg_negative_space >= 0.5 and avg_color_purity >= 80 else "moderate",
    }


def analyze_site_zip(zip_path: str | Path, screenshots: list[str] | None = None, notes: str | None = None) -> dict[str, Any]:
    path = Path(zip_path)
    if not path.exists():
        raise FileNotFoundError(f"Site snapshot ZIP not found: {path}")

    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        asset_inventory = _extract_asset_inventory(names)
        html_texts = [_read_zip_text(archive, name) for name in asset_inventory["html_files"][:12]]
        css_texts = [_read_zip_text(archive, name) for name in asset_inventory["css_files"][:20]]
        js_texts = [_read_zip_text(archive, name) for name in asset_inventory["js_files"][:10]]

    typography = _extract_typography_signals(css_texts, asset_inventory)
    visual = _extract_visual_signals(css_texts)
    layout = _extract_layout_signals(html_texts, css_texts)
    motion = _extract_motion_signals(asset_inventory, visual, js_texts)
    material = _material_signals(asset_inventory, visual)
    screenshots_report = analyze_screenshots(screenshots)

    return {
        "source": {
            "type": "site_snapshot_zip",
            "zip_path": str(path),
            "site_id": _slugify(path.stem),
            "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "screenshots": [str(item) for item in (screenshots or []) if str(item).strip()],
            "notes": str(notes or "").strip(),
        },
        "asset_inventory": asset_inventory,
        "typography_dna": typography,
        "layout_dna": layout,
        "motion_dna": motion,
        "material_dna": material,
        "visual_signals": visual,
        "screenshot_analysis": screenshots_report,
    }


def synthesize_design_dna(analysis: dict[str, Any]) -> dict[str, Any]:
    typography = analysis.get("typography_dna", {})
    layout = analysis.get("layout_dna", {})
    motion = analysis.get("motion_dna", {})
    material = analysis.get("material_dna", {})
    visual = analysis.get("visual_signals", {})
    screenshots = analysis.get("screenshot_analysis", {})

    top_colors = visual.get("top_colors", [])
    negative_space_clue = screenshots.get("avg_negative_space_pct")
    dark_bias = bool(material.get("dark_bias"))
    dense_layout = bool(layout.get("card_count_hint", 0) > 8 or layout.get("section_count_hint", 0) > 8)
    expressive_motion = str(motion.get("motion_density") or "restrained") == "expressive"

    emotional_brand_dna = []
    if dark_bias:
        emotional_brand_dna.append("authoritative_dark")
    else:
        emotional_brand_dna.append("editorial_bright")
    if expressive_motion:
        emotional_brand_dna.append("energetic_precision")
    else:
        emotional_brand_dna.append("restrained_clarity")
    if dense_layout:
        emotional_brand_dna.append("product_density")
    else:
        emotional_brand_dna.append("hero_space")

    return {
        "typography_dna": {
            "headline_family_hint": typography.get("headline_clue"),
            "body_family_hint": typography.get("body_clue"),
            "font_stack_count": len(typography.get("font_families", [])),
            "tone": "editorial_dense" if dense_layout else "editorial_minimal",
        },
        "layout_composition_dna": {
            "negative_space_clue": negative_space_clue,
            "density_mode": "dense" if dense_layout else "spacious",
            "grid_bias": "grid" if layout.get("grid_mentions", 0) >= layout.get("flex_mentions", 0) else "flex",
            "hero_bias": "strong" if layout.get("hero_count_hint", 0) > 0 else "mixed",
        },
        "motion_dna": {
            "motion_density": motion.get("motion_density"),
            "library_clues": motion.get("motion_libraries", []),
            "transition_clues": motion.get("transition_tokens", []),
        },
        "material_effect_dna": {
            "surface_language": material.get("surface_language"),
            "dark_bias": dark_bias,
            "rounded_bias": material.get("rounded_bias"),
            "color_signature": top_colors[:4],
        },
        "emotional_brand_dna": {
            "signals": emotional_brand_dna,
            "notes": str(analysis.get("source", {}).get("notes") or ""),
        },
    }


def translate_site_dna_to_aiox(analysis: dict[str, Any], dna: dict[str, Any]) -> dict[str, Any]:
    layout_dna = dna.get("layout_composition_dna", {})
    motion_dna = dna.get("motion_dna", {})
    material = dna.get("material_effect_dna", {})
    typography = dna.get("typography_dna", {})
    screenshots = analysis.get("screenshot_analysis", {})

    negative_space = screenshots.get("avg_negative_space_pct")
    if negative_space is None:
        negative_space = 0.42 if layout_dna.get("density_mode") == "dense" else 0.58
    accent_intensity = 0.45 if motion_dna.get("motion_density") == "expressive" else 0.16
    if material.get("dark_bias"):
        style_pack_hint = "silent_luxury" if accent_intensity <= 0.2 else "kinetic_editorial"
    else:
        style_pack_hint = "kinetic_editorial" if accent_intensity > 0.25 else "silent_luxury"

    typography_system_hint = "editorial_dense" if typography.get("tone") == "editorial_dense" else "editorial_minimal"
    still_family_hint = "editorial_portrait" if layout_dna.get("density_mode") == "dense" else "poster_minimal"
    motion_grammar_hint = "kinetic_editorial" if motion_dna.get("motion_density") == "expressive" else "cinematic_restrained"
    grain_hint = 0.08 if material.get("surface_language") == "soft_ui" else 0.04

    emulate = [
        "Borrow hierarchy discipline and spacing rhythm rather than literal page structure.",
        "Translate typography tone and negative-space regime into AIOX compositions.",
        "Reuse motion temperament, not site-specific implementation details.",
    ]
    avoid = [
        "Do not copy proprietary layout modules, iconography, or exact component markup.",
        "Do not port site-specific gradients, logos, or product screenshots verbatim.",
        "Treat JS motion libraries as implementation clues, not design DNA by themselves.",
    ]
    if style_pack_hint == "silent_luxury":
        emulate.append("Preserve restraint, larger empty fields, and premium calm.")
    else:
        emulate.append("Preserve editorial snap, denser information flow, and sharper cadence.")

    return {
        "style_pack_hint": style_pack_hint,
        "typography_system_hint": typography_system_hint,
        "still_family_hint": still_family_hint,
        "motion_grammar_hint": motion_grammar_hint,
        "negative_space_target_hint": round(float(negative_space), 3),
        "accent_intensity_hint": round(float(accent_intensity), 2),
        "grain_hint": round(float(grain_hint), 2),
        "material_hint": material.get("surface_language", "editorial_flat"),
        "emulate": emulate,
        "avoid_literal_copy": avoid,
        "implementation_detail_warnings": [
            "Font file presence is a clue; final AIOX font choice should still obey contract availability.",
            "Transition and animation CSS may reflect framework defaults rather than the core visual DNA.",
        ],
    }


def build_reference_contract(analysis: dict[str, Any], dna: dict[str, Any], translation: dict[str, Any]) -> dict[str, Any]:
    source = analysis.get("source", {})
    colors = analysis.get("visual_signals", {}).get("top_colors", [])
    fonts = analysis.get("typography_dna", {}).get("font_families", [])
    return {
        "source": {
            "type": source.get("type", "site_snapshot_zip"),
            "zip_path": source.get("zip_path"),
            "site_id": source.get("site_id"),
            "captured_at": source.get("captured_at"),
            "screenshots": source.get("screenshots", []),
            "inference_method": "zip_snapshot_translation",
        },
        "style_classification": translation.get("style_pack_hint"),
        "classification_tags": list(dna.get("emotional_brand_dna", {}).get("signals", [])),
        "palette": {
            "observed_colors": colors[:6],
            "accent_hint": colors[0] if colors else "",
        },
        "typography": {
            "observed_families": fonts[:6],
            "headline_hint": dna.get("typography_dna", {}).get("headline_family_hint"),
            "body_hint": dna.get("typography_dna", {}).get("body_family_hint"),
        },
        "spacing": {
            "max_width_tokens": analysis.get("visual_signals", {}).get("max_width_tokens", [])[:4],
            "spacing_tokens": analysis.get("visual_signals", {}).get("top_spacing_tokens", [])[:6],
            "density_mode": dna.get("layout_composition_dna", {}).get("density_mode"),
        },
        "motion_motifs": list(analysis.get("motion_dna", {}).get("motion_libraries", [])) + list(
            analysis.get("motion_dna", {}).get("transition_tokens", [])[:3]
        ),
        "composition_rules": {
            "negative_space_target": translation.get("negative_space_target_hint"),
            "still_family_hint": translation.get("still_family_hint"),
            "motion_grammar_hint": translation.get("motion_grammar_hint"),
        },
        "reference_analysis": analysis,
        "design_dna": dna,
        "aiox_translation": translation,
        "reference": {
            "type": "site_snapshot_zip",
            "notes": "Reference translation layer output. Use as design DNA guidance, not literal reproduction.",
        },
    }


def write_reference_contract(
    contract: dict[str, Any],
    *,
    output_dir: str | Path | None = None,
    slug: str | None = None,
) -> ReferenceTranslationPaths:
    out_dir = Path(output_dir) if output_dir else DEFAULT_REFERENCE_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    resolved_slug = _slugify(slug or contract.get("source", {}).get("site_id") or "reference_snapshot")
    yaml_path = out_dir / f"{resolved_slug}.yaml"
    json_path = out_dir / f"{resolved_slug}.json"
    yaml_path.write_text(yaml.safe_dump(contract, sort_keys=False, allow_unicode=False), encoding="utf-8")
    json_path.write_text(json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8")
    return ReferenceTranslationPaths(slug=resolved_slug, yaml_path=yaml_path, json_path=json_path)
