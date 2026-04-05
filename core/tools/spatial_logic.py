"""
spatial_logic.py - Translates Python geometric constraints into DOM/React physical properties.
Implements the 4 core Material Design motion patterns to ensure "single-take" continuity elements 
between the Manim Engine and the Remotion UI Engine.
"""
from typing import Dict, Any, Tuple

def get_shared_axis_transform(axis: str = "x", is_incoming: bool = True) -> Dict[str, str]:
    """
    Calculates transformation matrices for Shared Axis navigation.
    X-Axis: Timeline progression (Left/Right)
    Z-Axis: Depth detail (Up-scale/Down-scale)
    """
    if axis.lower() == "x":
        # Standard X progression (30px offset like MDC)
        offset = "30px" if is_incoming else "-30px"
        return {
            "transform_from": f"translate3d({offset}, 0, 0)",
            "transform_to": "translate3d(0, 0, 0)",
            "opacity_from": "0",
            "opacity_to": "1"
        }
    elif axis.lower() == "z":
        # Depth transition: Incoming arrives slightly small, Output blows up towards camera
        scale_from = "0.95" if is_incoming else "1.0"
        scale_to = "1.0" if is_incoming else "1.1" # Outwards expansion
        return {
            "transform_from": f"scale3d({scale_from}, {scale_from}, {scale_from})",
            "transform_to": f"scale3d({scale_to}, {scale_to}, {scale_to})",
            "opacity_from": "0",
            "opacity_to": "1"
        }
    
    # Fallback to pure fade
    return {"transform_from": "none", "transform_to": "none", "opacity_from": "0", "opacity_to": "1"}

def get_container_transform(
    origin_bounds: Tuple[float, float, float, float], 
    target_bounds: Tuple[float, float, float, float]
) -> Dict[str, str]:
    """
    Implements 'The Bridge' (Container Transform) transferring context from Manim to Remotion.
    Bounds are structured as (x, y, width, height) relative to the screen.
    Returns CSS `transform` strings enforcing sub-pixel hardware acceleration `translate3d`.
    """
    # Calculate geometric difference
    o_x, o_y, o_w, o_h = origin_bounds
    t_x, t_y, t_w, t_h = target_bounds
    
    # Determine the pixel delta for CSS translations
    delta_x = o_x - t_x
    delta_y = o_y - t_y
    
    # Determine the scale ratio from origin shape to destination shape
    scale_w = o_w / t_w if t_w else 1.0
    scale_h = o_h / t_h if t_h else 1.0

    return {
        "transform_origin": "top left",
        # We start morphed exactly matching Manim's last state
        "initial_state": f"translate3d({delta_x}px, {delta_y}px, 0) scale3d({scale_w}, {scale_h}, 1.0)",
        # We end matching Remotion's native DOM grid (Layout Metamorphosis)
        "final_state": "translate3d(0, 0, 0) scale3d(1.0, 1.0, 1.0)",
        # Emphasized Easing required for physical realism
        "easing_curve": "cubic-bezier(0.2, 0.0, 0, 1.0)",
        "duration_ms": 700 # Material Long 1 spec for morphs
    }

def calculate_stagger(index: int, total_elements: int, importance_weight: float = 1.0) -> int:
    """
    Instead of fixed math delays, calculates an organic hierarchical cascade duration.
    Elements enter with a 50ms overlap relative to their sequential index.
    
    Returns standard CSS animation-delay in milliseconds.
    """
    base_stagger_overlap = 50 # ms overlap
    delay = int(index * base_stagger_overlap * importance_weight)
    return delay
