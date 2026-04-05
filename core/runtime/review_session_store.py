from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SESSION_DIR = ROOT / ".sessions" / "reviews"


@dataclass(frozen=True)
class ReviewSession:
    review_session_id: str
    created_at: float
    profile: str
    brief: dict[str, Any]
    artifact_plan: dict[str, Any]
    variants: list[dict[str, Any]]
    chosen_variant: str
    quality_report: dict[str, Any]
    exported_targets: list[dict[str, Any]] = field(default_factory=list)
    review_notes: list[str] = field(default_factory=list)
    status: str = "planned"


def generate_review_session_id() -> str:
    return f"review_{int(time.time())}_{uuid.uuid4().hex[:8]}"


def save_review_session(session: ReviewSession, directory: Path | None = None) -> Path:
    target_dir = directory or DEFAULT_SESSION_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{session.review_session_id}.json"
    path.write_text(json.dumps(asdict(session), indent=2, ensure_ascii=True), encoding="utf-8")
    return path


def load_review_session(review_session_id: str, directory: Path | None = None) -> ReviewSession:
    target_dir = directory or DEFAULT_SESSION_DIR
    data = json.loads((target_dir / f"{review_session_id}.json").read_text(encoding="utf-8"))
    return ReviewSession(**data)


def latest_review_session_path(directory: Path | None = None) -> Path | None:
    target_dir = directory or DEFAULT_SESSION_DIR
    if not target_dir.exists():
        return None
    sessions = sorted(target_dir.glob("review_*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    return sessions[0] if sessions else None
