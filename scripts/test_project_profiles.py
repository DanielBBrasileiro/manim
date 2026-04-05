import sys
import os
from pathlib import Path

# Add root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.compiler.creative_compiler import compile_seed
from core.compiler.project_profile import load_project_profile

def test_project_defaults():
    print("Testing Project Profile Defaults...")
    
    # Base briefing with NO targets and NO styling
    brief = {
        "title": "Smoke Test",
        "project_id": "linkedin_tecnico"
    }
    
    result = compile_seed(brief)
    manifest = result["render_manifest"]
    artifact_plan = result["artifact_plan"]
    
    print(f"Project ID in Artifact Plan: {artifact_plan.get('project_id')}")
    assert artifact_plan.get("project_id") == "linkedin_tecnico"
    
    # Check default target for linkedin_tecnico
    target_ids = [t["id"] for t in manifest["targets"]]
    print(f"Resolved Targets: {target_ids}")
    assert "linkedin_feed_4_5" in target_ids
    
    # Check default motion grammar for linkedin_tecnico
    motion = manifest["motion_grammar"]
    print(f"Resolved Motion Grammar: {motion}")
    assert motion == "kinetic_editorial"
    
    # Check negative space target for linkedin_tecnico
    neg_space = manifest["negative_space_target"]
    print(f"Resolved Negative Space: {neg_space}")
    assert abs(neg_space - 0.48) < 0.01

    print("Defaults Test PASSED")


def test_briefing_override():
    print("\nTesting Briefing Override over Project Defaults...")
    
    # Briefing with EXPLICIT override
    brief = {
        "title": "Override Test",
        "project_id": "linkedin_tecnico",
        "motion_grammar": "cinematic_restrained",
        "targets": ["short_cinematic_vertical"]
    }
    
    result = compile_seed(brief)
    manifest = result["render_manifest"]
    
    # Check override targets
    target_ids = [t["id"] for t in manifest["targets"]]
    print(f"Resolved Targets: {target_ids}")
    assert "short_cinematic_vertical" in target_ids
    assert "linkedin_feed_4_5" not in target_ids
    
    # Check override motion
    motion = manifest["motion_grammar"]
    print(f"Resolved Motion Grammar: {motion}")
    assert motion == "cinematic_restrained"

    print("Override Test PASSED")


if __name__ == "__main__":
    try:
        test_project_defaults()
        test_briefing_override()
        print("\nALL PROJECT PROFILE TESTS PASSED")
    except Exception as e:
        print(f"\nTESTS FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
