"""
project_profile.py — Lightweight project profile loader and resolver for AIOX Studio.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parent.parent.parent
PROJECTS_DIR = ROOT / "projects"


def load_project_profile(project_id: str) -> Optional[Dict[str, Any]]:
    """Loads a project profile by its ID (directory name)."""
    if not project_id:
        return None
        
    profile_path = PROJECTS_DIR / project_id / "project.yaml"
    if not profile_path.exists():
        return None
        
    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = yaml.safe_load(f)
            if isinstance(profile, dict):
                return profile
    except Exception as e:
        print(f"⚠️ Error loading project profile {project_id}: {e}")
        
    return None


def get_project_value(plan: Dict[str, Any], key: str, target_id: Optional[str] = None) -> Any:
    """
    Resolves a value from the project profile stored in the plan.
    Priority: 
    1. Key in target-specific profile (if any)
    2. Key in global profile
    """
    profile = plan.get("project_profile")
    if not isinstance(profile, dict):
        return None
        
    # Project profile fields usually start with 'default_'
    project_key = f"default_{key}"
    
    # In this implementation, we keep it simple: global project defaults
    return profile.get(project_key)


def apply_project_profile_to_plan(plan: Dict[str, Any], project_id: str) -> Dict[str, Any]:
    """Attaches a project profile to the plan for later resolution."""
    profile = load_project_profile(project_id)
    if profile:
        plan["project_profile"] = profile
        plan["project_id"] = project_id
    return plan
