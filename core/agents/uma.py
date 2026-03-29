import json
import random

def evaluate(signature: dict, history_path: str = 'core/memory/creative_memory.json') -> bool:
    '''Persona Uma: Memory and Repetition Control.'''
    try:
        with open(history_path, 'r') as f:
            data = json.load(f)
            history = data.get('history', [])
            if not history: return True
            last_entry = history[-1]
            last_archetype = last_entry.get('creative_plan', {}).get('archetype')
            if signature.get('structure') == last_archetype: # compare to signature structure
                return False if random.random() < 0.7 else True
    except FileNotFoundError:
        pass
    return True
