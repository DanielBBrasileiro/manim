import json
import random

try:
    from core.memory import semantic_memory as _sem
    _SEMANTIC_AVAILABLE = True
except ImportError:
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from core.memory import semantic_memory as _sem
        _SEMANTIC_AVAILABLE = True
    except ImportError:
        _sem = None
        _SEMANTIC_AVAILABLE = False


def evaluate(signature: dict, history_path: str = 'core/memory/creative_memory.json') -> bool:
    '''Persona Uma: Memory and Repetition Control.

    Uses semantic vector similarity when available (semantic_memory module).
    Falls back to exact archetype string comparison if semantic_memory is absent.

    Blocking logic (semantic mode):
      diversity_score < 0.3  → block with 85% probability (too similar to history)
      diversity_score > 0.7  → always accept (genuinely diverse)
      0.3 ≤ score ≤ 0.7     → probabilistic acceptance proportional to diversity
    '''
    try:
        with open(history_path, 'r') as f:
            data = json.load(f)
        history = data.get('history', [])
    except FileNotFoundError:
        history = []

    if not history:
        return True

    # --- Semantic path ---
    if _SEMANTIC_AVAILABLE and _sem is not None:
        try:
            diversity_score = _sem.get_diversity_score(signature, history, top_k=5)

            if diversity_score < 0.3:
                # Very similar to recent history — block with 85% probability
                return random.random() >= 0.85

            if diversity_score > 0.7:
                # Genuinely diverse — always accept
                return True

            # Intermediate zone [0.3, 0.7] — linear probability
            # Maps 0.3→30% accept, 0.7→100% accept
            accept_probability = (diversity_score - 0.3) / (0.7 - 0.3)
            return random.random() < accept_probability

        except Exception:
            # Semantic evaluation failed — fall through to legacy logic
            pass

    # --- Legacy fallback: exact archetype string comparison ---
    last_entry = history[-1]
    last_archetype = last_entry.get('creative_plan', {}).get('archetype')
    if signature.get('structure') == last_archetype:
        return False if random.random() < 0.7 else True

    return True
