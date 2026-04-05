"""
storyboard_tool.py — lightweight previs helpers for the Story Engine.

This module turns an artifact plan into:
- a human-readable storyboard summary for terminal review
- JSON/TXT artifacts stored in output/preview for director approval
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = ROOT / "output" / "preview"


def build_storyboard(artifact_plan: dict[str, Any]) -> dict[str, Any]:
    story_atoms = artifact_plan.get("story_atoms", {}) if isinstance(artifact_plan, dict) else {}
    targets = artifact_plan.get("targets", []) if isinstance(artifact_plan, dict) else []

    storyboard_targets = []
    for target in targets:
        if not isinstance(target, dict):
            continue

        storyboard_targets.append(
            {
                "id": target.get("id"),
                "label": target.get("label"),
                "kind": target.get("kind") or target.get("render_mode"),
                "composition": target.get("composition"),
                "render_mode": target.get("render_mode"),
                "format": target.get("format")
                if isinstance(target.get("format"), dict)
                else {
                    "width": target.get("width"),
                    "height": target.get("height"),
                    "safe_zone": target.get("safe_zone"),
                },
                "duration_sec": target.get("duration_sec"),
                "summary": target.get("summary"),
                "beats": target.get("beats", []),
                "slides": target.get("slides", []),
                "chapters": target.get("chapters", []),
            }
        )

    return {
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "story_atoms": {
            "title": story_atoms.get("title"),
            "tagline": story_atoms.get("tagline"),
            "thesis": story_atoms.get("thesis"),
            "emotional_target": story_atoms.get("emotional_target"),
            "visual_metaphor": story_atoms.get("visual_metaphor"),
            "resolve_word": story_atoms.get("resolve_word"),
            "audience": story_atoms.get("audience"),
        },
        "targets": storyboard_targets,
    }


def summarize_storyboard(artifact_plan: dict[str, Any]) -> str:
    storyboard = build_storyboard(artifact_plan)
    atoms = storyboard.get("story_atoms", {})
    targets = storyboard.get("targets", [])

    lines = [
        "Storyboard",
        f"Title: {atoms.get('title') or 'Untitled'}",
        f"Thesis: {atoms.get('thesis') or 'missing'}",
        f"Emotion: {atoms.get('emotional_target') or 'missing'}",
        f"Metaphor: {atoms.get('visual_metaphor') or 'missing'}",
        f"Targets: {len(targets)}",
        "",
    ]

    for target in targets:
        label = target.get("label") or target.get("id") or "target"
        fmt = target.get("format") or {}
        size = f"{fmt.get('width', '?')}x{fmt.get('height', '?')}"
        lines.append(
            f"- {label} [{target.get('kind', 'unknown')}] {size} · {target.get('render_mode', 'render')}"
        )
        if target.get("summary"):
            lines.append(f"  {target['summary']}")

        beats = target.get("beats") or []
        slides = target.get("slides") or []
        chapters = target.get("chapters") or []
        if beats:
            lines.append(
                "  beats: " + " | ".join(str(beat.get("label", "")) for beat in beats[:4] if isinstance(beat, dict))
            )
        if slides:
            lines.append(
                "  slides: " + " | ".join(str(slide.get("archetype", "")) for slide in slides[:6] if isinstance(slide, dict))
            )
        if chapters:
            lines.append(
                "  chapters: " + " | ".join(str(chapter.get("label", "")) for chapter in chapters[:6] if isinstance(chapter, dict))
            )

    return "\n".join(lines).strip()


def write_storyboard(artifact_plan: dict[str, Any], output_stem: str = "storyboard") -> dict[str, str]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = OUTPUT_DIR / f"{output_stem}_{timestamp}"

    storyboard = build_storyboard(artifact_plan)
    text = summarize_storyboard(artifact_plan)

    json_path = base.with_suffix(".json")
    txt_path = base.with_suffix(".txt")

    json_path.write_text(json.dumps(storyboard, indent=2), encoding="utf-8")
    txt_path.write_text(text + "\n", encoding="utf-8")

    return {
        "json": str(json_path),
        "txt": str(txt_path),
    }
