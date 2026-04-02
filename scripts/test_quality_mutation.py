
import sys
import os
from pathlib import Path

# Add root to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from core.quality.mutator import mutate_render_manifest
from core.quality.frame_scorer import FrameScore, DimensionScore

def test_stills_mutation():
    print("Testing Still Mutations...")
    manifest = {
        "negative_space_target": 0.4,
        "accent_intensity": 0.2,
        "grain": 0.04,
        "quality_constraints": {
            "max_words_per_screen": 5
        }
    }
    
    # Simulate low spatial intelligence
    findings = [
        {"code": "spatial_intelligence", "score": 45},
        {"code": "overcrowding", "score": 30}
    ]
    
    mutated = mutate_render_manifest(manifest, findings)
    
    print(f"Old Negative Space: 0.4 -> New: {mutated.get('negative_space_target')}")
    print(f"Old Max Words: 5 -> New: {mutated.get('quality_constraints', {}).get('max_words_per_screen')}")
    
    assert mutated.get('negative_space_target') > 0.4
    assert mutated.get('quality_constraints', {}).get('max_words_per_screen') < 5
    print("Stills Mutation PASSED")

def test_motion_mutation():
    print("\nTesting Motion Mutations...")
    manifest = {
        "quality_constraints": {
            "minimum_hold_ms": 300
        },
        "copy_budget": {
            "target_silence_ratio": 0.2
        }
    }
    
    findings = [
        {"code": "motion_pacing", "score": 50}
    ]
    
    mutated = mutate_render_manifest(manifest, findings)
    
    print(f"Old Min Hold: 300 -> New: {mutated.get('quality_constraints', {}).get('minimum_hold_ms')}")
    print(f"Old Silence Ratio: 0.2 -> New: {mutated.get('copy_budget', {}).get('target_silence_ratio')}")
    
    assert mutated.get('quality_constraints', {}).get('minimum_hold_ms') > 300
    assert mutated.get('copy_budget', {}).get('target_silence_ratio') > 0.2
    print("Motion Mutation PASSED")

if __name__ == "__main__":
    try:
        test_stills_mutation()
        test_motion_mutation()
        print("\nALL QUALITY MUTATION TESTS PASSED")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
