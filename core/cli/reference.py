#!/usr/bin/env python3
"""
AIOX Studio - Reference / Style Pack Capture
=============================================
Creates reusable style packs from a URL using lightweight heuristics.

The output is intentionally structured for downstream consumers:
- YAML for human editing and repo contracts
- JSON for machine consumption

Usage:
    python3 aiox.py reference https://stripe.com
    python3 aiox.py reference https://stripe.com https://linear.app
    python3 core/cli/reference.py https://stripe.com
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUT_DIR = ROOT / "contracts" / "references"


@dataclass(frozen=True)
class ReferencePackPaths:
    slug: str
    yaml_path: Path
    json_path: Path


def _ensure_scheme(url: str) -> str:
    value = str(url or "").strip()
    if not value:
        return value
    if "://" not in value:
        return f"https://{value}"
    return value


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "reference_pack"


def _reference_slug(url: str) -> str:
    parsed = urlparse(_ensure_scheme(url))
    host = (parsed.hostname or "reference").lower()
    host = host[4:] if host.startswith("www.") else host
    parts = [host.replace(".", "_")]
    path_bits = [bit for bit in parsed.path.split("/") if bit]
    if path_bits:
        parts.extend(path_bits[:2])
    return _slugify("_".join(parts))


def _profile_for_url(url: str) -> dict:
    parsed = urlparse(_ensure_scheme(url))
    hostname = (parsed.hostname or "reference").lower()
    path = (parsed.path or "").lower()
    tokens = {token for token in re.split(r"[^a-z0-9]+", f"{hostname} {path}") if token}

    profile = _match_known_profile(hostname, tokens)
    if profile is not None:
        return profile

    if {"docs", "developer", "api", "dashboard"} & tokens:
        return _build_profile(
            style_classification="technical_minimal",
            tags=["technical", "editorial", "precise", "workspace"],
            palette={
                "background": "#0B0F14",
                "surface": "#111827",
                "text_primary": "#F8FAFC",
                "text_secondary": "#94A3B8",
                "accent": "#7DD3FC",
                "accent_secondary": "#C4B5FD",
                "border": "rgba(148, 163, 184, 0.18)",
                "gradient_primary": "linear-gradient(135deg, #7DD3FC 0%, #C4B5FD 100%)",
            },
            typography={
                "heading": {
                    "family": "Inter, system-ui, sans-serif",
                    "weight": 650,
                    "tracking": "-0.03em",
                },
                "body": {
                    "family": "Inter, system-ui, sans-serif",
                    "weight": 400,
                    "size": "16px",
                    "line_height": 1.6,
                },
                "code": {
                    "family": "ui-monospace, SFMono-Regular, Menlo, monospace",
                    "weight": 400,
                    "size": "14px",
                },
            },
            spacing={
                "section_gap": "96px",
                "content_max_width": "1120px",
                "card_padding": "28px",
                "card_radius": "14px",
                "rhythm": "tight",
            },
            component_motifs=["thin_rules", "pill_ctas", "code_blocks", "dense_cards"],
            motion_motifs=["fade_up_8px", "mask_reveal", "subtle_parallax"],
            do_rules=[
                "keep hierarchy sharp and compact",
                "use precise spacing and restrained accents",
                "make technical surfaces feel premium",
            ],
            dont_rules=[
                "do not use playful gradients or noisy decoration",
                "do not over-texture the layout",
                "do not widen typography beyond the grid",
            ],
            confidence=0.66,
            mood="precise, calm, technical",
        )

    return _build_profile(
        style_classification="editorial_minimal",
        tags=["editorial", "confident", "spacious", "brand_system"],
        palette={
            "background": "#FFFFFF",
            "surface": "#F6F9FC",
            "text_primary": "#0A2540",
            "text_secondary": "#425466",
            "accent": "#635BFF",
            "accent_secondary": "#00D4AA",
            "border": "rgba(66, 84, 102, 0.15)",
            "gradient_primary": "linear-gradient(135deg, #635BFF 0%, #00D4AA 100%)",
        },
        typography={
            "heading": {
                "family": "Inter, system-ui, sans-serif",
                "weight": 650,
                "tracking": "-0.03em",
            },
            "body": {
                "family": "Inter, system-ui, sans-serif",
                "weight": 400,
                "size": "16px",
                "line_height": 1.6,
            },
            "code": {
                "family": "ui-monospace, SFMono-Regular, Menlo, monospace",
                "weight": 400,
                "size": "14px",
            },
        },
        spacing={
            "section_gap": "120px",
            "content_max_width": "1080px",
            "card_padding": "32px",
            "card_radius": "12px",
            "rhythm": "airy",
        },
        component_motifs=["rule_dividers", "pill_ctas", "soft_cards", "sharp_grid"],
        motion_motifs=["fade_up_8px", "settle_resolve", "mask_reveal"],
        do_rules=[
            "keep one dominant accent color",
            "let whitespace carry the composition",
            "make typography do the storytelling",
        ],
        dont_rules=[
            "do not mirror the site literally",
            "do not copy proprietary components verbatim",
            "do not exceed the contract with extra colors",
        ],
        confidence=0.72,
        mood="clean, confident, spacious, technical_but_approachable",
    )


def _match_known_profile(hostname: str, tokens: set[str]) -> dict | None:
    if "stripe" in hostname:
        return _build_profile(
            style_classification="editorial_minimal",
            tags=["editorial", "financial", "spacious", "technical"],
            palette={
                "background": "#FFFFFF",
                "surface": "#F6F9FC",
                "text_primary": "#0A2540",
                "text_secondary": "#425466",
                "accent": "#635BFF",
                "accent_secondary": "#00D4AA",
                "border": "rgba(66, 84, 102, 0.15)",
                "gradient_primary": "linear-gradient(135deg, #635BFF 0%, #00D4AA 100%)",
            },
            typography={
                "heading": {
                    "family": "sohne, Helvetica Neue, Helvetica, sans-serif",
                    "weight": 600,
                    "tracking": "-0.02em",
                },
                "body": {
                    "family": "sohne, Helvetica Neue, Helvetica, sans-serif",
                    "weight": 400,
                    "size": "17px",
                    "line_height": 1.6,
                },
                "code": {
                    "family": "Menlo, Consolas, monospace",
                    "weight": 400,
                    "size": "14px",
                },
            },
            spacing={
                "section_gap": "120px",
                "content_max_width": "1080px",
                "card_padding": "32px",
                "card_radius": "12px",
                "rhythm": "airy",
            },
            component_motifs=["pill_ctas", "thin_rules", "wide_cards", "hero_grid"],
            motion_motifs=["fade_up_8px", "settle_resolve", "mask_reveal"],
            do_rules=[
                "keep the layout spacious and calm",
                "favor thin rules and strong hierarchy",
                "use one decisive accent, not many",
            ],
            dont_rules=[
                "do not copy the brand directly",
                "do not add ornamental motion",
                "do not crowd the frame",
            ],
            confidence=0.9,
            mood="clean, confident, spacious, technical_but_approachable",
        )

    if "linear" in hostname:
        return _build_profile(
            style_classification="product_precision",
            tags=["product", "minimal", "precise", "dark"],
            palette={
                "background": "#0B0D12",
                "surface": "#11131A",
                "text_primary": "#F5F7FA",
                "text_secondary": "#9CA3AF",
                "accent": "#8B5CF6",
                "accent_secondary": "#22D3EE",
                "border": "rgba(148, 163, 184, 0.16)",
                "gradient_primary": "linear-gradient(135deg, #8B5CF6 0%, #22D3EE 100%)",
            },
            typography={
                "heading": {
                    "family": "Inter, system-ui, sans-serif",
                    "weight": 650,
                    "tracking": "-0.04em",
                },
                "body": {
                    "family": "Inter, system-ui, sans-serif",
                    "weight": 400,
                    "size": "16px",
                    "line_height": 1.55,
                },
                "code": {
                    "family": "ui-monospace, SFMono-Regular, Menlo, monospace",
                    "weight": 400,
                    "size": "14px",
                },
            },
            spacing={
                "section_gap": "88px",
                "content_max_width": "1040px",
                "card_padding": "28px",
                "card_radius": "16px",
                "rhythm": "tight",
            },
            component_motifs=["command_palette", "compact_cards", "thin_dividers"],
            motion_motifs=["fade_up_4px", "snap_settle", "mask_reveal"],
            do_rules=[
                "keep the interface compact and efficient",
                "use motion sparingly and with intent",
                "prioritize clarity over flourish",
            ],
            dont_rules=[
                "do not use heavy decorative gradients",
                "do not over-animate transitions",
                "do not add unnecessary borders",
            ],
            confidence=0.91,
            mood="precise, compact, premium, product_native",
        )

    if "vercel" in hostname:
        return _build_profile(
            style_classification="technical_minimal",
            tags=["developer", "dark", "crisp", "platform"],
            palette={
                "background": "#000000",
                "surface": "#111111",
                "text_primary": "#FFFFFF",
                "text_secondary": "#A1A1AA",
                "accent": "#FFFFFF",
                "accent_secondary": "#A1A1AA",
                "border": "rgba(255, 255, 255, 0.10)",
                "gradient_primary": "linear-gradient(135deg, #FFFFFF 0%, #A1A1AA 100%)",
            },
            typography={
                "heading": {
                    "family": "Inter, system-ui, sans-serif",
                    "weight": 700,
                    "tracking": "-0.03em",
                },
                "body": {
                    "family": "Inter, system-ui, sans-serif",
                    "weight": 400,
                    "size": "16px",
                    "line_height": 1.6,
                },
                "code": {
                    "family": "ui-monospace, SFMono-Regular, Menlo, monospace",
                    "weight": 400,
                    "size": "14px",
                },
            },
            spacing={
                "section_gap": "96px",
                "content_max_width": "1120px",
                "card_padding": "30px",
                "card_radius": "14px",
                "rhythm": "balanced",
            },
            component_motifs=["terminal_panels", "thin_rules", "platform_cards"],
            motion_motifs=["fade_up_8px", "mask_reveal", "settle_resolve"],
            do_rules=[
                "keep contrast high and the surface clean",
                "use motion as confirmation, not decoration",
                "let the grid do the heavy lifting",
            ],
            dont_rules=[
                "do not soften the edges too much",
                "do not overuse accent colors",
                "do not make the layout feel ornamental",
            ],
            confidence=0.89,
            mood="crisp, developer-first, minimal, authoritative",
        )

    if "notion" in hostname:
        return _build_profile(
            style_classification="organic_warm",
            tags=["editorial", "warm", "calm", "workspace"],
            palette={
                "background": "#F7F5F2",
                "surface": "#FFFFFF",
                "text_primary": "#111827",
                "text_secondary": "#4B5563",
                "accent": "#F59E0B",
                "accent_secondary": "#10B981",
                "border": "rgba(17, 24, 39, 0.10)",
                "gradient_primary": "linear-gradient(135deg, #F59E0B 0%, #10B981 100%)",
            },
            typography={
                "heading": {
                    "family": "Inter, system-ui, sans-serif",
                    "weight": 650,
                    "tracking": "-0.02em",
                },
                "body": {
                    "family": "Inter, system-ui, sans-serif",
                    "weight": 400,
                    "size": "16px",
                    "line_height": 1.65,
                },
                "code": {
                    "family": "ui-monospace, SFMono-Regular, Menlo, monospace",
                    "weight": 400,
                    "size": "14px",
                },
            },
            spacing={
                "section_gap": "112px",
                "content_max_width": "1040px",
                "card_padding": "30px",
                "card_radius": "18px",
                "rhythm": "airy",
            },
            component_motifs=["paper_cards", "soft_rules", "rounded_ctas"],
            motion_motifs=["fade_up_8px", "subtle_parallax", "mask_reveal"],
            do_rules=[
                "keep the mood calm and organized",
                "use warm accents sparingly",
                "prioritize readability and breathing room",
            ],
            dont_rules=[
                "do not make the design feel cold",
                "do not overload the composition",
                "do not push the accent too hard",
            ],
            confidence=0.87,
            mood="calm, organized, editorial, human",
        )

    return None


def _build_profile(
    *,
    style_classification: str,
    tags: list[str],
    palette: dict,
    typography: dict,
    spacing: dict,
    component_motifs: list[str],
    motion_motifs: list[str],
    do_rules: list[str],
    dont_rules: list[str],
    confidence: float,
    mood: str,
) -> dict:
    return {
        "style_classification": style_classification,
        "classification_tags": tags,
        "palette": palette,
        "typography": typography,
        "spacing": spacing,
        "component_motifs": component_motifs,
        "motion_motifs": motion_motifs,
        "do_rules": do_rules,
        "dont_rules": dont_rules,
        "confidence": confidence,
        "mood": mood,
    }


def build_style_pack(url: str) -> dict:
    normalized_url = _ensure_scheme(url)
    parsed = urlparse(normalized_url)
    hostname = (parsed.hostname or "reference").lower()
    host_no_www = hostname[4:] if hostname.startswith("www.") else hostname
    slug = _reference_slug(normalized_url)
    profile = _profile_for_url(normalized_url)
    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    pack = {
        "source": {
            "url": normalized_url,
            "domain": host_no_www,
            "slug": slug,
            "captured_at": captured_at,
            "inference_method": "heuristic_url_profile",
            "confidence": profile.get("confidence", 0.7),
        },
        "style_classification": profile["style_classification"],
        "classification_tags": profile["classification_tags"],
        "palette": profile["palette"],
        "typography": profile["typography"],
        "spacing": profile["spacing"],
        "component_motifs": profile["component_motifs"],
        "motion_motifs": profile["motion_motifs"],
        "do_rules": profile["do_rules"],
        "dont_rules": profile["dont_rules"],
        "mood": profile["mood"],
        "reference": {
            "type": "web_url",
            "notes": "Heuristic style pack generated without scraping or DOM capture.",
        },
    }
    return pack


def write_style_pack(url: str, output_dir: str | Path | None = None) -> ReferencePackPaths:
    pack = build_style_pack(url)
    out_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    slug = pack["source"]["slug"]
    yaml_path = out_dir / f"{slug}.yaml"
    json_path = out_dir / f"{slug}.json"

    with open(yaml_path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(pack, handle, sort_keys=False, allow_unicode=False)

    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(pack, handle, indent=2, ensure_ascii=False)

    return ReferencePackPaths(slug=slug, yaml_path=yaml_path, json_path=json_path)


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture a reusable AIOX reference/style pack")
    parser.add_argument("urls", nargs="+", help="One or more reference URLs")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where the YAML and JSON style pack files will be written",
    )
    args = parser.parse_args(argv)

    for url in args.urls:
        paths = write_style_pack(url, args.output_dir)
        print(f"Reference pack -> {paths.yaml_path}")
        print(f"Reference pack -> {paths.json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
