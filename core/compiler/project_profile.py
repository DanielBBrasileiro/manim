"""
project_profile.py — Lightweight validated project profile loader for AIOX Studio.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
PROJECTS_DIR = ROOT / "projects"
STYLE_PACKS_DIR = ROOT / "contracts" / "style_packs"
STILL_FAMILIES_DIR = ROOT / "contracts" / "still_families"
MOTION_GRAMMARS_DIR = ROOT / "contracts" / "motion_grammars"
LAYOUT_CONTRACT_PATH = ROOT / "contracts" / "layout.yaml"
VALID_TYPOGRAPHY_SYSTEMS = {
    "editorial_minimal",
    "editorial_dense",
}


def _yaml_load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _valid_ids_from_dir(path: Path) -> set[str]:
    values: set[str] = set()
    if not path.exists():
        return values
    for item in path.glob("*.yaml"):
        values.add(item.stem)
    return values


def _valid_target_ids() -> set[str]:
    layout = _yaml_load(LAYOUT_CONTRACT_PATH)
    output_targets = layout.get("output_targets", {}) if isinstance(layout.get("output_targets", {}), dict) else {}
    return {str(key).strip() for key in output_targets.keys() if str(key).strip()}


VALID_STYLE_PACKS = _valid_ids_from_dir(STYLE_PACKS_DIR)
VALID_STILL_FAMILIES = _valid_ids_from_dir(STILL_FAMILIES_DIR)
VALID_MOTION_GRAMMARS = _valid_ids_from_dir(MOTION_GRAMMARS_DIR)
VALID_TARGETS = _valid_target_ids()


def normalize_project_profile(profile: Dict[str, Any], project_id: str | None = None) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {
        "id": str(profile.get("id") or project_id or "").strip(),
        "description": str(profile.get("description") or "").strip(),
        "default_targets": [
            str(item).strip()
            for item in profile.get("default_targets", [])
            if str(item).strip() in VALID_TARGETS
        ],
        "default_style_pack": None,
        "default_typography_system": None,
        "default_still_family": None,
        "default_motion_grammar": None,
        "default_negative_space_target": profile.get("default_negative_space_target"),
        "default_accent_intensity": profile.get("default_accent_intensity"),
        "default_grain": profile.get("default_grain"),
        "default_reference_ids": [
            str(item).strip()
            for item in profile.get("default_reference_ids", [])
            if str(item).strip()
        ],
    }

    style_pack = str(profile.get("default_style_pack") or "").strip()
    if style_pack in VALID_STYLE_PACKS:
        normalized["default_style_pack"] = style_pack

    typography_system = str(profile.get("default_typography_system") or "").strip()
    if typography_system in VALID_TYPOGRAPHY_SYSTEMS:
        normalized["default_typography_system"] = typography_system

    still_family = str(profile.get("default_still_family") or "").strip()
    if still_family in VALID_STILL_FAMILIES:
        normalized["default_still_family"] = still_family

    motion_grammar = str(profile.get("default_motion_grammar") or "").strip()
    if motion_grammar in VALID_MOTION_GRAMMARS:
        normalized["default_motion_grammar"] = motion_grammar

    for key in ("default_negative_space_target", "default_accent_intensity", "default_grain"):
        value = normalized.get(key)
        if value in {None, ""}:
            normalized[key] = None
            continue
        try:
            normalized[key] = float(value)
        except (TypeError, ValueError):
            normalized[key] = None

    return normalized


def load_project_profile(project_id: str) -> Optional[Dict[str, Any]]:
    """Loads and normalizes a project profile by its ID (directory name)."""
    if not project_id:
        return None

    profile_path = PROJECTS_DIR / project_id / "project.yaml"
    if not profile_path.exists():
        return None

    try:
        profile = _yaml_load(profile_path)
        if isinstance(profile, dict):
            return normalize_project_profile(profile, project_id=project_id)
    except Exception as e:
        print(f"⚠️ Error loading project profile {project_id}: {e}")

    return None


def get_project_value(plan: Dict[str, Any], key: str) -> Any:
    """Resolve a normalized global default from the project profile stored in the plan."""
    profile = plan.get("project_profile")
    if not isinstance(profile, dict):
        return None

    return profile.get(f"default_{key}")


def apply_project_profile_to_plan(plan: Dict[str, Any], project_id: str) -> Dict[str, Any]:
    """Attaches a project profile to the plan for later resolution."""
    profile = load_project_profile(project_id)
    if profile:
        plan["project_profile"] = profile
        plan["project_id"] = project_id
    return plan
