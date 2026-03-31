from __future__ import annotations

import json
import time
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
SESSION_ROOT = ROOT / ".sessions"


def ensure_session_root(root: str | Path | None = None) -> Path:
    target = Path(root) if root else SESSION_ROOT
    target.mkdir(parents=True, exist_ok=True)
    return target


def new_session_id(prefix: str = "sess") -> str:
    stamp = int(time.time())
    suffix = uuid.uuid4().hex[:8]
    return f"{prefix}_{stamp}_{suffix}"


def normalize_session_id(session_id: str) -> str:
    session_id = str(session_id).strip()
    if not session_id:
        return new_session_id()
    return session_id if session_id.endswith(".json") else f"{session_id}.json"


def session_path(session_id: str, root: str | Path | None = None) -> Path:
    return ensure_session_root(root) / normalize_session_id(session_id)


def build_session_record(
    intent_text: str | dict[str, Any] | None,
    creative_plan: dict[str, Any] | None = None,
    *,
    execution_graph: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    events: list[dict[str, Any]] | None = None,
    status: str = "draft",
    session_id: str | None = None,
    source: str = "interactive_lab",
) -> dict[str, Any]:
    resolved_session_id = session_id or new_session_id()
    timestamp = time.time()
    record = {
        "session_id": resolved_session_id,
        "status": status,
        "source": source,
        "created_at": timestamp,
        "updated_at": timestamp,
        "input": intent_text if isinstance(intent_text, (str, dict)) else str(intent_text or ""),
        "creative_plan": deepcopy(creative_plan) if creative_plan else {},
        "execution_graph": deepcopy(execution_graph) if execution_graph else {},
        "metadata": deepcopy(metadata) if metadata else {},
        "events": deepcopy(events) if events else [],
    }
    return record


def save_session(
    intent_text: str | dict[str, Any] | None,
    creative_plan: dict[str, Any] | None = None,
    *,
    execution_graph: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    events: list[dict[str, Any]] | None = None,
    status: str = "draft",
    session_id: str | None = None,
    root: str | Path | None = None,
    source: str = "interactive_lab",
) -> dict[str, Any]:
    record = build_session_record(
        intent_text,
        creative_plan,
        execution_graph=execution_graph,
        metadata=metadata,
        events=events,
        status=status,
        session_id=session_id,
        source=source,
    )
    path = session_path(record["session_id"], root=root)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=True, indent=2)
    return record


def load_session(session_id: str, root: str | Path | None = None) -> dict[str, Any] | None:
    path = session_path(session_id, root=root)
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    return normalize_session_record(raw, fallback_session_id=session_id)


def list_sessions(root: str | Path | None = None) -> list[dict[str, Any]]:
    target = ensure_session_root(root)
    records: list[dict[str, Any]] = []
    for path in sorted(target.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            with path.open("r", encoding="utf-8") as handle:
                raw = json.load(handle)
            record = normalize_session_record(raw, fallback_session_id=path.stem)
            record["path"] = str(path)
            records.append(record)
        except Exception:
            records.append(
                {
                    "session_id": path.stem,
                    "status": "corrupt",
                    "path": str(path),
                }
            )
    return records


def append_session_event(
    session_id: str,
    event: dict[str, Any],
    root: str | Path | None = None,
) -> dict[str, Any] | None:
    record = load_session(session_id, root=root)
    if record is None:
        return None

    record.setdefault("events", []).append(deepcopy(event))
    record["updated_at"] = time.time()
    save_session(
        record.get("input"),
        record.get("creative_plan"),
        execution_graph=record.get("execution_graph"),
        metadata=record.get("metadata"),
        events=record.get("events"),
        status=record.get("status", "draft"),
        session_id=record.get("session_id"),
        root=root,
        source=record.get("source", "interactive_lab"),
    )
    return record


def normalize_session_record(raw: dict[str, Any], fallback_session_id: str | None = None) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {
            "session_id": fallback_session_id or new_session_id(),
            "status": "corrupt",
            "input": "",
            "creative_plan": {},
            "execution_graph": {},
            "metadata": {},
            "events": [],
        }

    record = deepcopy(raw)
    session_id = str(record.get("session_id") or fallback_session_id or new_session_id())
    record["session_id"] = session_id
    record["status"] = str(record.get("status", "draft"))
    record["input"] = record.get("input", record.get("prompt", ""))
    record["creative_plan"] = record.get("creative_plan", record.get("plan", {})) or {}
    record["execution_graph"] = record.get("execution_graph", {}) or {}
    record["metadata"] = record.get("metadata", {}) or {}
    record["events"] = record.get("events", []) if isinstance(record.get("events", []), list) else []
    record["created_at"] = float(record.get("created_at", time.time()))
    record["updated_at"] = float(record.get("updated_at", record["created_at"]))
    return record
