import hashlib
import random
from typing import Any, Dict, List, Tuple

class PhysicalGrid:
    """
    Translates boundary variables from the layout schema into static Pymunk bodies.
    Manages deterministic seeds for physics convergence to ensure reproducible renders.
    """
    
    def __init__(self, briefing_id: str, layout_bounds: Dict[str, Any]):
        """
        Args:
            briefing_id: The unique identifier to guarantee identical seed.
            layout_bounds: Geometric definitions from layout.yaml defining walls/slits.
        """
        self.briefing_id = briefing_id
        self.layout = layout_bounds
        self.seed = self._generate_deterministic_seed(briefing_id)
        
        # We enforce Python's global random state specifically for standard entropy (Manim fallback)
        random.seed(self.seed)

    def _generate_deterministic_seed(self, briefing_id: str) -> int:
        """Creates a stable 32-bit integer seed from the briefing identifier."""
        hash_obj = hashlib.sha256(briefing_id.encode("utf-8"))
        return int(hash_obj.hexdigest()[:8], 16)
        
    def generate_static_boundaries(self) -> List[Tuple[float, float, float, float]]:
        """
        Parses the layout representation into a list of geometric line segments.
        Format matching Manim's required static boundary definition:
        [(x1, y1, x2, y2), ...]
        """
        boundaries = []
        # Fallback empty constraints
        if not self.layout:
            return boundaries
            
        # Example representation mapping for walls: left, right, top, bottom
        viewport = self.layout.get("viewport", {"width": 1080, "height": 1920})
        w = viewport["width"] / 100.0  # Normalize to Manim's 1-unit relative coords if needed
        h = viewport["height"] / 100.0
        
        # Left wall
        boundaries.append((-w/2, -h/2, -w/2, h/2))
        # Right wall
        boundaries.append((w/2, -h/2, w/2, h/2))
        # Floor (adds specific collision plane for data settling)
        boundaries.append((-w/2, -h/2, w/2, -h/2))
        
        return boundaries
