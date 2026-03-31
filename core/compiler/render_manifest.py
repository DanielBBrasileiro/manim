"""
render_manifest.py — Builds the cinematic render manifest from a creative plan.

Extracted from creative_compiler.py to keep modules under 500 lines.
"""
import copy
from pathlib import Path

import yaml

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
            "gain": 0.3,
        },
        "layout": layout_contract.get("formats", {}).get("vertical_9_16", {}),
    }


def _coerce_brief(seed: dict | str) -> dict:
    if not isinstance(seed, dict):
        return {"prompt": str(seed)}

    creative_seed = seed.get("creative_seed")
    if isinstance(creative_seed, dict):
        return copy.deepcopy(creative_seed)

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
    agitation = _word_cap(
        brief.get("agitation_text")
        or brief.get("hook_text")
        or _default_agitation_copy(plan),
    )
    resolve_word = _word_cap(
        brief.get("resolve_word") or DEFAULT_RESOLVE_BY_ARCHETYPE.get(plan.get("archetype"), "AIOX"),
        limit=2,
    )
    title = _word_cap(brief.get("title") or "Invisible Architecture")

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
