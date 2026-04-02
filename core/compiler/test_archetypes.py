import os
import sys

# Add root folder to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.compiler.creative_compiler import enrich_with_entropy

def test():
    print("--- Test 1: Fallback (missing) ---")
    plan1 = enrich_with_entropy({"archetype": "missing_archetype", "duration": 10})
    print(plan1["timeline"])

    print("\n--- Test 2: Standard Emergence (YAML) ---")
    plan2 = enrich_with_entropy({"archetype": "emergence", "duration": 10})
    print(plan2["timeline"])

    print("\n--- Test 3: Chaos to Order (YAML) ---")
    plan3 = enrich_with_entropy({"archetype": "chaos_to_order", "duration": 10})
    print(plan3["timeline"])

    print("\n--- Test 4: Resolution (YAML - Phases) ---")
    plan4 = enrich_with_entropy({"archetype": "resolution", "duration": 10})
    print(plan4["timeline"])

if __name__ == "__main__":
    test()
