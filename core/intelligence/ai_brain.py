"""
AI Native Brain — Anthropic API integration para decisões criativas.
Fallback para heurísticas se SDK não disponível ou sem API key.
"""

import os
import hashlib
import threading

# In-memory cache: {intent_hash: archetype}
_archetype_cache: dict = {}
# In-memory cache: {identity_hash: aesthetic_family}
_aesthetic_cache: dict = {}

_SDK_AVAILABLE = None  # lazy-check on first call


def _check_sdk() -> bool:
    """Verifica se o SDK da Anthropic está disponível e a API key existe."""
    global _SDK_AVAILABLE
    if _SDK_AVAILABLE is not None:
        return _SDK_AVAILABLE
    if not os.environ.get("ANTHROPIC_API_KEY"):
        _SDK_AVAILABLE = False
        return False
    try:
        import anthropic  # noqa: F401
        _SDK_AVAILABLE = True
    except ImportError:
        _SDK_AVAILABLE = False
    return _SDK_AVAILABLE


def _hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def call_aria_llm(intent: str, available_archetypes: list, archetype_descriptions: dict) -> str | None:
    """
    Chama Claude Haiku para escolher o melhor archetype dado o intent.
    Retorna nome do archetype ou None se falhar.
    """
    if not _check_sdk():
        print("⚡ [Aria] Fallback para heurísticas (SDK não disponível)")
        return None

    cache_key = _hash(intent)
    if cache_key in _archetype_cache:
        return _archetype_cache[cache_key]

    # Monta descrições concisas a partir dos dados YAML
    descriptions_text = ""
    for name in available_archetypes:
        data = archetype_descriptions.get(name, {})
        structure = data.get("structure", [])
        entropy = data.get("entropy_profile", "")
        motion = data.get("motion_bias", "")
        parts = []
        if structure:
            parts.append("structure: " + "→".join(str(s) for s in structure))
        if entropy:
            parts.append(f"entropy: {entropy}")
        if motion:
            parts.append(f"motion: {motion}")
        descriptions_text += f"- {name}: {', '.join(parts)}\n"

    archetypes_list = ", ".join(available_archetypes)

    prompt = f"""You are a creative director AI. Given the user's creative intent, choose the single most fitting narrative archetype from the list below.

Available archetypes:
{descriptions_text}
User intent: "{intent}"

Respond with ONLY the archetype name (exactly as listed). No explanation, no punctuation.
Valid names: {archetypes_list}"""

    result_holder = [None]
    exception_holder = [None]

    def _call():
        try:
            import anthropic
            client = anthropic.Anthropic()
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=20,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = message.content[0].text.strip().lower().replace(" ", "_")
            # Valida que a resposta é um archetype válido
            if raw in available_archetypes:
                result_holder[0] = raw
            else:
                # Tenta match parcial
                for name in available_archetypes:
                    if name in raw or raw in name:
                        result_holder[0] = name
                        break
        except Exception as e:
            exception_holder[0] = e

    t = threading.Thread(target=_call, daemon=True)
    t.start()
    t.join(timeout=3.0)

    if t.is_alive() or exception_holder[0] or result_holder[0] is None:
        if t.is_alive():
            print("⚡ [Aria] Timeout na chamada ao Claude Haiku — fallback para heurísticas")
        elif exception_holder[0]:
            print(f"⚡ [Aria] Erro na API: {exception_holder[0]} — fallback para heurísticas")
        return None

    print(f"🧠 [Aria LLM] Usando Claude Haiku para decisão criativa... → {result_holder[0]}")
    _archetype_cache[cache_key] = result_holder[0]
    return result_holder[0]


def call_aesthetic_llm(identity: str, intent: str = "") -> str | None:
    """
    Chama Claude Haiku para escolher aesthetic_family.
    Retorna nome da família ou None se falhar.
    """
    if not _check_sdk():
        print("⚡ [Aria] Fallback para heurísticas (SDK não disponível)")
        return None

    cache_key = _hash(f"{identity}::{intent}")
    if cache_key in _aesthetic_cache:
        return _aesthetic_cache[cache_key]

    families = ["silent_architecture", "brutalist_signal", "organic_field", "data_narrative"]
    families_text = "\n".join(f"- {f}" for f in families)

    intent_line = f'\nCreative intent context: "{intent}"' if intent else ""

    prompt = f"""You are a creative director AI. Choose the most fitting visual aesthetic family for the given brand identity.

Available aesthetic families:
{families_text}

Descriptions:
- silent_architecture: minimal, geometric, spatial, quiet elegance
- brutalist_signal: raw, high contrast, bold typography, direct
- organic_field: fluid, natural flow, soft curves, biological
- data_narrative: information-dense, structured, analytical, systematic

Brand identity: "{identity}"{intent_line}

Respond with ONLY the aesthetic family name (exactly as listed). No explanation.
Valid names: {', '.join(families)}"""

    result_holder = [None]
    exception_holder = [None]

    def _call():
        try:
            import anthropic
            client = anthropic.Anthropic()
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=30,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = message.content[0].text.strip().lower().replace(" ", "_")
            if raw in families:
                result_holder[0] = raw
            else:
                for name in families:
                    if name in raw or raw in name:
                        result_holder[0] = name
                        break
        except Exception as e:
            exception_holder[0] = e

    t = threading.Thread(target=_call, daemon=True)
    t.start()
    t.join(timeout=3.0)

    if t.is_alive() or exception_holder[0] or result_holder[0] is None:
        if t.is_alive():
            print("⚡ [Aria] Timeout na chamada ao Claude Haiku — fallback para heurísticas")
        elif exception_holder[0]:
            print(f"⚡ [Aria] Erro na API: {exception_holder[0]} — fallback para heurísticas")
        return None

    print(f"🧠 [Aria LLM] Usando Claude Haiku para decisão criativa... → {result_holder[0]}")
    _aesthetic_cache[cache_key] = result_holder[0]
    return result_holder[0]
