from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent


def save_training_pair(
    prompt: str,
    completion: dict[str, Any],
    approved: bool,
    metadata: dict[str, Any] | None = None,
    path: str | None = None,
) -> bool:
    if not approved or not prompt or not completion:
        return False

    target = Path(path) if path else ROOT / "core" / "memory" / "training_pairs.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "prompt": prompt,
        "completion": json.dumps(completion, ensure_ascii=True),
    }
    if metadata:
        row["metadata"] = metadata
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    return True
