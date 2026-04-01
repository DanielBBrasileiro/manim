from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_GOLDEN_SET_PATH = ROOT / "core" / "quality" / "golden_sets" / "starter.yaml"


@dataclass(frozen=True)
class GoldenSetCase:
    case_id: str
    target: str
    artifact_class: str
    briefing: str = ""
    intent: str = ""
    style_pack: str = ""
    expected_quality_focus: list[str] = field(default_factory=list)
    notes: str = ""
    final_output_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _resolve_golden_set_path(path_or_id: str | None = None) -> Path:
    if not path_or_id:
        return DEFAULT_GOLDEN_SET_PATH

    raw = Path(path_or_id)
    if raw.is_absolute() or raw.exists():
        return raw

    candidate = ROOT / path_or_id
    if candidate.exists():
        return candidate

    local = ROOT / "core" / "quality" / "golden_sets" / f"{path_or_id}.yaml"
    if local.exists():
        return local

    return candidate


def load_golden_set(path_or_id: str | None = None) -> dict[str, Any]:
    path = _resolve_golden_set_path(path_or_id)
    if not path.exists():
        raise FileNotFoundError(f"Golden set not found: {path}")

    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cases_raw = payload.get("cases", []) if isinstance(payload.get("cases", []), list) else []
    cases: list[dict[str, Any]] = []
    for index, entry in enumerate(cases_raw, start=1):
        if not isinstance(entry, dict):
            continue
        case = GoldenSetCase(
            case_id=str(entry.get("case_id") or entry.get("id") or f"case_{index:02d}").strip(),
            target=str(entry.get("target") or "").strip(),
            artifact_class=str(entry.get("artifact_class") or "still").strip().lower(),
            briefing=str(entry.get("briefing") or entry.get("briefing_ref") or "").strip(),
            intent=str(entry.get("intent") or entry.get("prompt") or "").strip(),
            style_pack=str(entry.get("style_pack") or "").strip(),
            expected_quality_focus=[
                str(item).strip()
                for item in entry.get("expected_quality_focus", [])
                if str(item).strip()
            ],
            notes=str(entry.get("notes") or "").strip(),
            final_output_path=str(entry.get("final_output_path") or entry.get("artifact_path") or "").strip(),
        )
        if not case.target:
            continue
        cases.append(case.to_dict())

    return {
        "id": str(payload.get("id") or path.stem).strip(),
        "title": str(payload.get("title") or "AIOX Benchmark Golden Set").strip(),
        "description": str(payload.get("description") or "").strip(),
        "path": str(path),
        "cases": cases,
    }
