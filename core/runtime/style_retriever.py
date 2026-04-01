from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
REFERENCE_DIR = ROOT / "contracts" / "references"


def _tokens(value: Any) -> set[str]:
    if isinstance(value, list):
        words = " ".join(str(item) for item in value)
    else:
        words = str(value or "")
    return {token for token in re.split(r"[^a-z0-9]+", words.lower()) if token}


def load_style_pack_index() -> list[dict[str, Any]]:
    index: list[dict[str, Any]] = []
    for path in sorted(REFERENCE_DIR.glob("*.yaml")):
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        index.append(
            {
                "pack_id": path.stem,
                "path": str(path),
                "style_classification": payload.get("style_classification", ""),
                "tags": payload.get("tags", []),
                "mood": payload.get("mood", ""),
                "component_motifs": payload.get("component_motifs", []),
                "motion_motifs": payload.get("motion_motifs", []),
                "confidence": float(payload.get("confidence", 0.0) or 0.0),
            }
        )
    return index


def search_style_packs(query: str, *, limit: int = 5) -> list[dict[str, Any]]:
    query_tokens = _tokens(query)
    results: list[dict[str, Any]] = []
    for pack in load_style_pack_index():
        pack_tokens = set()
        for key in ("pack_id", "style_classification", "tags", "mood", "component_motifs", "motion_motifs"):
            pack_tokens |= _tokens(pack.get(key))
        overlap = len(query_tokens & pack_tokens)
        lexical_score = overlap / max(len(query_tokens) or 1, 1)
        confidence = float(pack.get("confidence", 0.0) or 0.0)
        score = round((lexical_score * 0.8) + (confidence * 0.2), 4)
        results.append(
            {
                **pack,
                "score": score,
                "matched_terms": sorted(query_tokens & pack_tokens),
            }
        )
    return sorted(results, key=lambda item: (item["score"], item.get("confidence", 0.0)), reverse=True)[: max(limit, 1)]
