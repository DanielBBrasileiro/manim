import json

def save_entry(entry: dict, path: str = 'core/memory/creative_memory.json'):
    try:
        with open(path, 'r') as f: data = json.load(f)
    except FileNotFoundError:
        data = {'history': []}
    data['history'].append(entry)
    with open(path, 'w') as f: json.dump(data, f, indent=2)


def save_entry_with_vector(entry: dict, path: str = 'core/memory/creative_memory.json',
                           archetypes_dir: str = 'contracts/narrative/archetypes'):
    """Save entry and also embed its semantic vector into the record for future retrieval.

    The vector is stored under entry['_semantic_vector'] before persisting to disk.
    If semantic_memory is unavailable the entry is saved without a vector (graceful degradation).
    """
    try:
        from core.memory.semantic_memory import encode_signature
        vector = encode_signature(entry, archetypes_dir=archetypes_dir)
        entry = dict(entry)           # shallow copy — don't mutate caller's dict
        entry['_semantic_vector'] = vector
    except Exception:
        pass  # proceed without vector if encoding fails

    save_entry(entry, path=path)
