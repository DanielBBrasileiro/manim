from __future__ import annotations

import os
from pathlib import Path


_LOADED = False


def load_repo_env(env_path: str | None = None) -> bool:
    global _LOADED
    if _LOADED:
        return False

    path = Path(env_path) if env_path else Path(__file__).resolve().parent.parent / ".env"
    if not path.exists():
        _LOADED = True
        return False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

    _LOADED = True
    return True
