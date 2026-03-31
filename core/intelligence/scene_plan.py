from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


ALLOWED_ARCHETYPES = {
    "chaos_to_order",
    "order_to_chaos",
    "emergence",
    "gravitational_collapse",
    "fragmented_reveal",
    "loop_stability",
}

ALLOWED_PACING = {"cinematic", "dynamic", "rhythmic", "meditative", "urgent", "fast", "slow"}
ALLOWED_ACTS = {"genesis", "turbulence", "resolution"}
ALLOWED_LAYOUT_ZONES = {"top_zone", "bottom_zone", "center_climax", "center", "none"}
ALLOWED_CAMERA_CUES = {"static_breathe", "track_subject", "dramatic_zoom", "observational"}


@dataclass
class TextCueSpec:
    text: str
    at: float
    role: str = "narration"
    position: str = "bottom_zone"
    weight: int = 400
    color_state: str = "default"


@dataclass
class SceneSpec:
    id: str
    duration: float
    act: str = ""
    primitives: list[str] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)
    camera: str = "observational"
    layout_zone: str = "none"
    text_cues: list[TextCueSpec] = field(default_factory=list)


@dataclass
class ScenePlan:
    archetype: str
    duration: float
    pacing: str
    scenes: list[SceneSpec] = field(default_factory=list)
    assets: dict[str, Any] = field(default_factory=dict)
    effects: list[str] = field(default_factory=list)
    confidence: float = 0.0
    raw_response: dict[str, Any] = field(default_factory=dict)
    llm_metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScenePlan":
        if not isinstance(data, dict):
            raise ValueError("Scene plan must be an object")

        archetype = str(data.get("archetype", "")).strip().lower()
        if archetype not in ALLOWED_ARCHETYPES:
            raise ValueError(f"Unsupported archetype: {archetype or 'missing'}")

        pacing = str(data.get("pacing", "cinematic")).strip().lower()
        if pacing not in ALLOWED_PACING:
            pacing = "cinematic"

        duration = _coerce_float(data.get("duration", 12), default=12.0)
        confidence = _clamp(_coerce_float(data.get("confidence", 0.0), default=0.0), 0.0, 1.0)

        scenes_raw = data.get("scenes", [])
        scenes: list[SceneSpec] = []
        if isinstance(scenes_raw, list):
            for idx, item in enumerate(scenes_raw):
                if not isinstance(item, dict):
                    continue
                scenes.append(
                    SceneSpec(
                        id=str(item.get("id", f"scene_{idx + 1}")).strip() or f"scene_{idx + 1}",
                        duration=_coerce_float(item.get("duration", 0), default=0.0),
                        act=_normalize_choice(item.get("act"), ALLOWED_ACTS, default=""),
                        primitives=_string_list(item.get("primitives")),
                        params=item.get("params", {}) if isinstance(item.get("params"), dict) else {},
                        camera=_normalize_choice(
                            item.get("camera"),
                            ALLOWED_CAMERA_CUES,
                            default="observational",
                        ),
                        layout_zone=_normalize_choice(
                            item.get("layout_zone"),
                            ALLOWED_LAYOUT_ZONES,
                            default="none",
                        ),
                        text_cues=_parse_text_cues(item.get("text_cues")),
                    )
                )

        assets = data.get("assets", {})
        effects = _string_list(data.get("effects"))

        return cls(
            archetype=archetype,
            duration=duration,
            pacing=pacing,
            scenes=scenes,
            assets=assets if isinstance(assets, dict) else {},
            effects=effects,
            confidence=confidence,
            raw_response=data,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "archetype": self.archetype,
            "duration": self.duration,
            "pacing": self.pacing,
            "scenes": [
                {
                    "id": scene.id,
                    "duration": scene.duration,
                    "act": scene.act,
                    "primitives": list(scene.primitives),
                    "params": dict(scene.params),
                    "camera": scene.camera,
                    "layout_zone": scene.layout_zone,
                    "text_cues": [
                        {
                            "text": cue.text,
                            "at": cue.at,
                            "role": cue.role,
                            "position": cue.position,
                            "weight": cue.weight,
                            "color_state": cue.color_state,
                        }
                        for cue in scene.text_cues
                    ],
                }
                for scene in self.scenes
            ],
            "assets": dict(self.assets),
            "effects": list(self.effects),
            "confidence": self.confidence,
        }

    @classmethod
    def json_schema(cls) -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["archetype", "duration", "pacing", "scenes", "assets", "effects", "confidence"],
            "properties": {
                "archetype": {"type": "string", "enum": sorted(ALLOWED_ARCHETYPES)},
                "duration": {"type": "number", "minimum": 6, "maximum": 20},
                "pacing": {"type": "string", "enum": sorted(ALLOWED_PACING)},
                "scenes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["id", "duration", "primitives", "params"],
                        "properties": {
                            "id": {"type": "string"},
                            "duration": {"type": "number", "minimum": 0},
                            "act": {"type": "string", "enum": sorted(ALLOWED_ACTS)},
                            "primitives": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "params": {"type": "object"},
                            "camera": {"type": "string", "enum": sorted(ALLOWED_CAMERA_CUES)},
                            "layout_zone": {"type": "string", "enum": sorted(ALLOWED_LAYOUT_ZONES)},
                            "text_cues": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": ["text", "at"],
                                    "properties": {
                                        "text": {"type": "string"},
                                        "at": {"type": "number", "minimum": 0},
                                        "role": {"type": "string"},
                                        "position": {"type": "string", "enum": sorted(ALLOWED_LAYOUT_ZONES)},
                                        "weight": {"type": "integer", "minimum": 200, "maximum": 700},
                                        "color_state": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                },
                "assets": {"type": "object"},
                "effects": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            },
        }


def _coerce_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _normalize_choice(value: Any, allowed: set[str], default: str) -> str:
    choice = str(value or "").strip().lower()
    if not choice:
        return default
    return choice if choice in allowed else default


def _parse_text_cues(value: Any) -> list[TextCueSpec]:
    if not isinstance(value, list):
        return []

    cues: list[TextCueSpec] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        cues.append(
            TextCueSpec(
                text=text,
                at=_coerce_float(item.get("at", 0), default=0.0),
                role=str(item.get("role", "narration")).strip() or "narration",
                position=_normalize_choice(
                    item.get("position"),
                    ALLOWED_LAYOUT_ZONES,
                    default="bottom_zone",
                ),
                weight=int(_coerce_float(item.get("weight", 400), default=400)),
                color_state=str(item.get("color_state", "default")).strip() or "default",
            )
        )
    return cues
