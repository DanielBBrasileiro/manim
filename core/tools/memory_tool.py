import json

def save_entry(entry: dict, path: str = 'core/memory/creative_memory.json'):
    try:
        with open(path, 'r') as f: data = json.load(f)
    except FileNotFoundError:
        data = {'history': []}
    data['history'].append(entry)
    with open(path, 'w') as f: json.dump(data, f, indent=2)
