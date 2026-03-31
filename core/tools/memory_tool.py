import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def save_entry(entry: dict, path: str | None = None):
    target = Path(path) if path else ROOT / "core" / "memory" / "creative_memory.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(target, 'r') as f: data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {'history': []}
    data['history'].append(entry)
    with open(target, 'w') as f: json.dump(data, f, indent=2)


def save_entry_with_vector(entry: dict, path: str | None = None,
                           archetypes_dir: str | None = None):
    """Save entry and also embed its semantic vector into the record for future retrieval.

    The vector is stored under entry['_semantic_vector'] before persisting to disk.
    If semantic_memory is unavailable the entry is saved without a vector (graceful degradation).
    """
    resolved_archetypes = archetypes_dir or str(ROOT / "contracts" / "narrative" / "archetypes")
    try:
        from core.memory.semantic_memory import encode_signature
        vector = encode_signature(entry, archetypes_dir=resolved_archetypes)
        entry = dict(entry)           # shallow copy — don't mutate caller's dict
        entry['_semantic_vector'] = vector
    except Exception:
        pass  # proceed without vector if encoding fails

    save_entry(entry, path=path)
