from .intent_parser import parse_intent
from .rule_engine import apply_rules
from .mutation_engine import mutate_entropy, mutate_motion
from .scoring_engine import novelty_score, coherence_score
from .signature_simulator import simulate_signature
from core.agents import zara, kael
from core.intelligence.model_router import TASK_PLAN

import copy
from pathlib import Path

import yaml

BEHAVIOR_BY_PRIMITIVE = {
    "living_curve": "coherent_flow",
    "particle_system": "chaotic_burst",
    "physics_field": "vortex_pull",
    "fbm_noise": "oscillatory_wave",
    "neural_grid": "laminar_flow",
    "narrative_container": "convergence_field",
    "storage_hex": "convergence_field",
}

TENSION_BY_EFFECT = {
    "grain_overlay": "medium",
    "motion_blur": "medium",
    "color_inversion": "high",
    "post_glitch_light": "high",
    "diagonal_accent": "medium",
}

ROOT = Path(__file__).resolve().parent.parent.parent
TEXT_WORD_LIMIT = 5
DEFAULT_CAMERA_BY_ACT = {
    "genesis": "static_breathe",
    "turbulence": "track_subject",
    "resolution": "static_breathe",
}
DEFAULT_PRIMITIVES_BY_ACT = {
    "genesis": ["living_curve"],
    "turbulence": ["particle_system"],
    "resolution": ["living_curve", "neural_grid"],
}
DEFAULT_EMOTION_BY_ACT = {
    "genesis": "curiosity",
    "turbulence": "tension",
    "resolution": "mastery",
}
DEFAULT_TENSION_BY_ACT = {
    "genesis": "low",
    "turbulence": "high",
    "resolution": "medium",
}
DEFAULT_RESOLVE_BY_ARCHETYPE = {
    "emergence": "Clarity",
    "chaos_to_order": "Resolve",
    "order_to_chaos": "Rupture",
    "fragmented_reveal": "Signal",
    "loop_stability": "Stillness",
    "gravitational_collapse": "Gravity",
}


def apply_scene_plan_guidance(plan: dict, scene_plan: dict) -> dict:
    guided = copy.deepcopy(plan)
    guided["duration"] = scene_plan.get("duration", guided.get("duration", 12))
    guided["assets"] = scene_plan.get("assets", {})
    guided["effects"] = scene_plan.get("effects", [])

    scenes = scene_plan.get("scenes", [])
    if not isinstance(scenes, list) or not scenes:
        return guided

    total_duration = sum(float(scene.get("duration", 0) or 0) for scene in scenes) or 1.0
    cursor = 0.0
    timeline = []

    for scene in scenes:
        scene_duration = float(scene.get("duration", 0) or 0)
        phase_start = cursor / total_duration
        cursor += scene_duration
        phase_end = min(1.0, cursor / total_duration)

        primitives = scene.get("primitives", []) if isinstance(scene.get("primitives"), list) else []
        effects = guided["effects"]
        behavior = _behavior_from_scene(primitives)
        tension = _tension_from_scene(primitives, effects)

        timeline.append(
            {
                "phase": [round(phase_start, 3), round(phase_end, 3)],
                "behavior": behavior,
                "tension": tension,
            }
        )

    if timeline:
        timeline[-1]["phase"][1] = 1.0
        guided["timeline"] = timeline

    return guided


def build_render_manifest(plan: dict, seed: dict | str) -> dict:
    brief = _coerce_brief(seed)
    narrative_contract = _load_contract("contracts/narrative.yaml")
    layout_contract = _load_contract("contracts/layout.yaml")
    duration = float(plan.get("duration", 12) or 12.0)
    fps = int(layout_contract.get("formats", {}).get("vertical_9_16", {}).get("fps", 60) or 60)

    acts = _build_act_windows(duration, plan, narrative_contract)
    text_beats = _collect_text_beats(brief, acts, duration, plan)
    cues_by_act: dict[str, list[dict]] = {act["id"]: [] for act in acts}
    for cue in text_beats:
        cues_by_act.setdefault(cue["act"], []).append(cue)

    for act in acts:
        act["text_cues"] = cues_by_act.get(act["id"], [])

    resolve_word = _word_cap(
        brief.get("resolve_word")
        or brief.get("final_signature_word")
        or DEFAULT_RESOLVE_BY_ARCHETYPE.get(plan.get("archetype"), "AIOX"),
        limit=2,
    )

    return {
        "duration": duration,
        "duration_in_frames": int(round(duration * fps)),
        "fps": fps,
        "title": brief.get("title") or "AIOX v4.0",
        "tagline": brief.get("tagline") or "Invisible Architecture",
        "emotional_target": brief.get("emotional_target") or _infer_emotional_target(plan),
        "visual_metaphor": brief.get("visual_metaphor") or _infer_visual_metaphor(plan),
        "resolve_word": resolve_word,
        "acts": acts,
        "text_cues": text_beats,
        "audio": {
            "enabled": True,
            "bed": "audio/aiox_signal_bed.m4a",
            "gain": 0.22,
        },
        "layout": layout_contract.get("formats", {}).get("vertical_9_16", {}),
    }


def _behavior_from_scene(primitives: list) -> str:
    for primitive in primitives:
        behavior = BEHAVIOR_BY_PRIMITIVE.get(str(primitive).lower())
        if behavior:
            return behavior
    return "coherent_flow"


def _tension_from_scene(primitives: list, effects: list) -> str:
    for effect in effects:
        tension = TENSION_BY_EFFECT.get(str(effect).lower())
        if tension == "high":
            return tension

    primitive_set = {str(item).lower() for item in primitives}
    if {"particle_system", "fbm_noise"} & primitive_set:
        return "high"
    if {"living_curve", "neural_grid"} & primitive_set:
        return "low"
    return "medium"


def enrich_with_entropy(plan: dict) -> dict:
    """Invoca as personas físicas reais (Zara/Kael) com o arquétipo já escolhido pela Rule Engine."""
    archetype = plan.get("archetype", "emergence")
    
    # Define entropia numérica bruta via regra ZARA
    entropy_base = zara.define_entropy(archetype)
    plan["entropy"] = entropy_base
    
    # Interpreta Semântica (turbulento, etc)
    from core.intelligence.entropy_interpreter import interpret_entropy
    interpretation = interpret_entropy(entropy_base)
    
    # Force bias if exists
    bias = zara.resolve_motion_bias(archetype)
    if bias:
        interpretation["motion_signature"] = bias
        
    plan["interpretation"] = interpretation
    
    # ---------------------------------------------
    # FASE 1 (ELITE): A Linguagem Temporal (Timeline)
    # ---------------------------------------------
    timeline = []
    if archetype == "emergence":
        timeline = [
             {"phase": [0.0, 0.4], "behavior": "coherent_flow", "tension": "low"},
             {"phase": [0.4, 0.8], "behavior": bias or "scattered_to_aligned", "tension": "medium"},
             {"phase": [0.8, 1.0], "behavior": "convergence_field", "tension": "high"}
        ]
    elif archetype == "chaos_to_order":
        timeline = [
             {"phase": [0.0, 0.3], "behavior": "chaotic_burst", "tension": "high"},
             {"phase": [0.3, 0.7], "behavior": bias or "vortex_pull", "tension": "medium"},
             {"phase": [0.7, 1.0], "behavior": "laminar_flow", "tension": "low"}
        ]
    elif archetype == "order_to_chaos":
        timeline = [
             {"phase": [0.0, 0.4], "behavior": "laminar_flow", "tension": "low"},
             {"phase": [0.4, 0.7], "behavior": bias or "oscillatory_wave", "tension": "medium"},
             {"phase": [0.7, 1.0], "behavior": "chaotic_dispersion", "tension": "high"}
        ]
    else:
        timeline = [
             {"phase": [0.0, 0.5], "behavior": bias or "laminar_flow", "tension": "medium"},
             {"phase": [0.5, 1.0], "behavior": "breathing_field", "tension": "medium"}
        ]
        
    plan["timeline"] = timeline
    
    return plan

def negotiate(plan: dict) -> dict:
    """Fase 4 (Elite): Negociação Multi-Agente Darwiniana."""
    if float(plan.get("llm_confidence", 0.0)) >= 0.85:
        return copy.deepcopy(plan)

    best_plan = copy.deepcopy(plan)
    max_score = 0.0
    
    for _ in range(5):
        # 1. Uma: A fiscal do Histórico Repetitivo
        uma_score = novelty_score(best_plan)
        
        # 2. Aria: A diretora de coerência semântica e estética
        aria_score = coherence_score(best_plan)
        
        # 3. Zara: A diretora de comportamento e caos
        # Zara recompensa planos que ousam na escala física (Entropia alta e Rhythm alto)
        fiz = best_plan.get("entropy", {}).get("physical", 0.0)
        stru = best_plan.get("entropy", {}).get("structural", 0.0)
        zara_score = (fiz + (1.0 - stru)) / 2.0
        
        # Somatório ponderado do conflito
        # A coerência (Aria) é o peso principal, mas a Novidade (Uma) é o veto final.
        total = (uma_score * 0.4) + (aria_score * 0.4) + (zara_score * 0.2)
        
        # Consenso Absoluto Encontrado
        if uma_score > 0.6 and aria_score > 0.8:
            return best_plan
            
        if total > max_score:
            max_score = total
            
        # Negação/Conflito: Votação para Mutação via Espaço Latente (Vetores)
        best_plan = mutate_entropy(best_plan)
        if uma_score < 0.4:
            # Uma exige mudança drástica no DNA vetorial
            best_plan = mutate_motion(best_plan)
            
    return best_plan

def compile_seed(
    seed: dict,
    identity: str = 'aiox_default',
    asset_registry: dict | None = None,
    task_type: str = TASK_PLAN,
):
    """Ponto de Entrada Mestre do AIOX OS v5 (Autonomia Elite)."""

    intent = parse_intent(seed, asset_registry=asset_registry, task_type=task_type)
    plan = apply_rules(intent, identity)
    plan = enrich_with_entropy(plan)

    if getattr(intent, "scene_plan", None):
        plan["llm_scene_plan"] = intent.scene_plan
        plan["llm_confidence"] = getattr(intent, "confidence", 0.0)
        plan["llm_metadata"] = getattr(intent, "llm_metadata", {})
        plan = apply_scene_plan_guidance(plan, intent.scene_plan)
    
    # 4. Negociação Darwiniana (Crítica Multi-Agente)
    plan = negotiate(plan)
    render_manifest = build_render_manifest(plan, seed)
    plan["render_manifest"] = render_manifest
    
    # 5. Simulador Final
    signature = simulate_signature(plan)
    
    return {
        "intent": str(intent),
        "creative_plan": plan,
        "output_signature": signature,
        "render_manifest": render_manifest
    }


def _coerce_brief(seed: dict | str) -> dict:
    if not isinstance(seed, dict):
        return {"prompt": str(seed)}

    if len(seed) == 1:
        only_value = next(iter(seed.values()))
        if isinstance(only_value, dict):
            return copy.deepcopy(only_value)

    return copy.deepcopy(seed)


def _load_contract(relative_path: str) -> dict:
    path = ROOT / relative_path
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _build_act_windows(duration: float, plan: dict, narrative_contract: dict) -> list[dict]:
    structure = narrative_contract.get("structure", {}).get("acts", {})
    ordered_ids = ["genesis", "turbulence", "resolution"]
    timeline = plan.get("timeline", [])
    llm_scenes = plan.get("llm_scene_plan", {}).get("scenes", [])

    acts: list[dict] = []
    cursor = 0.0
    for index, act_id in enumerate(ordered_ids):
        act_contract = structure.get(act_id, {})
        ratio = float(act_contract.get("duration_ratio", 0.33) or 0.33)
        act_duration = duration * ratio if index < len(ordered_ids) - 1 else max(0.0, duration - cursor)
        start = round(cursor, 3)
        end = round(min(duration, cursor + act_duration), 3)
        midpoint = ((start + end) / 2.0) / max(duration, 0.001)
        behavior, tension = _timeline_state_for_progress(timeline, midpoint)
        visual_primitives = _primitives_for_act(act_id, llm_scenes) or list(DEFAULT_PRIMITIVES_BY_ACT[act_id])

        acts.append(
            {
                "id": act_id,
                "start_sec": start,
                "end_sec": end,
                "emotion": act_contract.get("emotion", DEFAULT_EMOTION_BY_ACT[act_id]),
                "behavior": behavior,
                "tension": tension or DEFAULT_TENSION_BY_ACT[act_id],
                "camera": DEFAULT_CAMERA_BY_ACT[act_id],
                "visual_primitives": visual_primitives,
                "text_cues": [],
            }
        )
        cursor += act_duration

    if acts:
        acts[-1]["end_sec"] = round(duration, 3)
    return acts


def _timeline_state_for_progress(timeline: list[dict], progress: float) -> tuple[str, str]:
    for block in timeline:
        phase = block.get("phase", [0.0, 1.0])
        if len(phase) != 2:
            continue
        start, end = phase
        if float(start) <= progress <= float(end):
            return str(block.get("behavior", "coherent_flow")), str(block.get("tension", "medium"))
    return "coherent_flow", "medium"


def _primitives_for_act(act_id: str, llm_scenes: list[dict]) -> list[str]:
    primitives: list[str] = []
    if isinstance(llm_scenes, list):
        for scene in llm_scenes:
            if not isinstance(scene, dict):
                continue
            scene_act = str(scene.get("act", "")).strip().lower()
            if scene_act and scene_act != act_id:
                continue
            for primitive in scene.get("primitives", []):
                text = str(primitive).strip()
                if text and text not in primitives:
                    primitives.append(text)
    return primitives


def _collect_text_beats(brief: dict, acts: list[dict], duration: float, plan: dict) -> list[dict]:
    text_beats = brief.get("text_beats")
    if isinstance(text_beats, list) and text_beats:
        cues = [_normalize_text_beat(item, acts, duration) for item in text_beats]
        return [cue for cue in cues if cue is not None]

    return _default_text_beats(brief, acts, plan)


def _normalize_text_beat(item: dict, acts: list[dict], duration: float) -> dict | None:
    if not isinstance(item, dict):
        return None

    act_id = str(item.get("act", "")).strip().lower()
    if act_id not in {act["id"] for act in acts}:
        act_id = "turbulence"

    act_window = next(act for act in acts if act["id"] == act_id)
    at_ratio = item.get("at_ratio")
    if at_ratio is not None:
        at_sec = act_window["start_sec"] + (act_window["end_sec"] - act_window["start_sec"]) * float(at_ratio)
    else:
        at_sec = float(item.get("at_sec", act_window["start_sec"]))

    if act_id == "genesis":
        at_sec = max(at_sec, 2.0)

    text = _word_cap(str(item.get("text", "")).strip())
    if not text:
        return None

    return {
        "act": act_id,
        "at_sec": round(min(duration, max(0.0, at_sec)), 3),
        "text": text,
        "position": _normalize_position(item.get("position", "bottom_zone")),
        "role": str(item.get("role", "narration")).strip() or "narration",
        "weight": int(item.get("weight", 400)),
        "color_state": str(item.get("color_state", "default")).strip() or "default",
    }


def _default_text_beats(brief: dict, acts: list[dict], plan: dict) -> list[dict]:
    turbulence = next(act for act in acts if act["id"] == "turbulence")
    resolution = next(act for act in acts if act["id"] == "resolution")
    title = _word_cap(brief.get("title") or "Invisible Architecture")
    agitation = _word_cap(
        brief.get("agitation_text")
        or brief.get("hook_text")
        or _default_agitation_copy(plan),
    )
    resolve_word = _word_cap(
        brief.get("resolve_word") or DEFAULT_RESOLVE_BY_ARCHETYPE.get(plan.get("archetype"), "AIOX"),
        limit=2,
    )

    return [
        {
            "act": "turbulence",
            "at_sec": round(turbulence["start_sec"] + 0.9, 3),
            "text": agitation,
            "position": "top_zone",
            "role": "hook",
            "weight": 320,
            "color_state": "default",
        },
        {
            "act": "turbulence",
            "at_sec": round(max(turbulence["start_sec"] + 2.4, turbulence["end_sec"] - 1.6), 3),
            "text": title,
            "position": "bottom_zone",
            "role": "narration",
            "weight": 420,
            "color_state": "default",
        },
        {
            "act": "resolution",
            "at_sec": round(max(resolution["start_sec"] + 1.4, resolution["end_sec"] - 2.0), 3),
            "text": resolve_word,
            "position": "center_climax",
            "role": "resolve",
            "weight": 560,
            "color_state": "default",
        },
    ]


def _default_agitation_copy(plan: dict) -> str:
    archetype = str(plan.get("archetype", "emergence"))
    if archetype == "chaos_to_order":
        return "order fights the noise"
    if archetype == "order_to_chaos":
        return "systems bend before rupture"
    if archetype == "fragmented_reveal":
        return "signal breaks the surface"
    if archetype == "gravitational_collapse":
        return "everything falls inward"
    return "silence before the surge"


def _normalize_position(position: str) -> str:
    allowed = {"top_zone", "bottom_zone", "center_climax", "center"}
    value = str(position or "bottom_zone").strip().lower()
    return value if value in allowed else "bottom_zone"


def _word_cap(text: str, limit: int = TEXT_WORD_LIMIT) -> str:
    words = [word for word in str(text or "").strip().split() if word]
    return " ".join(words[:limit]).strip()


def _infer_emotional_target(plan: dict) -> str:
    archetype = str(plan.get("archetype", "emergence"))
    if archetype == "chaos_to_order":
        return "transform tension into mastery"
    if archetype == "order_to_chaos":
        return "reveal fracture before impact"
    if archetype == "fragmented_reveal":
        return "make pressure feel elegant"
    return "make hidden order feel inevitable"


def _infer_visual_metaphor(plan: dict) -> str:
    archetype = str(plan.get("archetype", "emergence"))
    if archetype == "chaos_to_order":
        return "noise collapsing into architecture"
    if archetype == "order_to_chaos":
        return "precision cracking under pressure"
    if archetype == "fragmented_reveal":
        return "signal piercing a dark field"
    return "a living curve teaching matter to align"
