def apply_layout_resistance(current_pos: float, dimension: float, constant: float = 0.55) -> float:
    """
    Applies Apple-style rubber banding (elastic resistance) to a position 
    that exceeds a layout boundary.
    
    Formula: f(x, d, c) = (1 - (1 / ((x * c / d) + 1))) * d
    Where:
        x = distance past the limit
        d = dimension of the container / screen
        c = resistance constant (default 0.55)
        
    Returns the damped offset to add to the base position.
    """
    if current_pos <= 0:
        return 0.0
        
    # Apply standard Apple rubber_banding formula
    # x = current_pos (the amount of overflow)
    # The return value is the "resisted" offset.
    return (1.0 - (1.0 / ((current_pos * constant / dimension) + 1.0))) * dimension

def apply_material_depth(level: int) -> dict:
    """
    Translates Material Design Elevation levels (0-5) into Z-Space physical coordinates.
    Returns logic for both Manim (Python) and Remotion (React/CSS) parity.
    Depth simulates a directional light casting umbra (hard) and penumbra (soft) shadows.
    """
    level = max(0, min(5, level))
    
    # CSS Shadows using standard MD3 umbra, penumbra, ambient format
    # format: y-offset blur spread color
    css_shadows = {
        0: "none",
        1: "0px 1px 2px 0px rgba(0,0,0,0.3), 0px 1px 3px 1px rgba(0,0,0,0.15)",
        2: "0px 1px 2px 0px rgba(0,0,0,0.3), 0px 2px 6px 2px rgba(0,0,0,0.15)",
        3: "0px 1px 3px 0px rgba(0,0,0,0.3), 0px 4px 8px 3px rgba(0,0,0,0.15)",
        4: "0px 2px 3px 0px rgba(0,0,0,0.3), 0px 6px 10px 4px rgba(0,0,0,0.15)",
        5: "0px 4px 4px 0px rgba(0,0,0,0.3), 0px 8px 12px 6px rgba(0,0,0,0.15)",
    }
    
    # Manim Z-Axis depth approximation
    manim_depth = {
        0: {"z_index": 0, "glow_radius": 0.0},
        1: {"z_index": 1, "glow_radius": 0.1},
        2: {"z_index": 2, "glow_radius": 0.25},
        3: {"z_index": 3, "glow_radius": 0.5},
        4: {"z_index": 4, "glow_radius": 0.75},
        5: {"z_index": 5, "glow_radius": 1.2},
    }

    return {
        "remotion_box_shadow": css_shadows[level],
        "manim_z_index": manim_depth[level]["z_index"],
        "manim_glow": manim_depth[level]["glow_radius"]
    }

