"""
Chromatic state management: dark <-> inverted.
The transition between states is a powerful narrative tool.
"""
from manim import *

class ColorInversion:
    """Hard-cut or smooth inversion of the scene palette."""
    
    @staticmethod
    def invert(scene, duration=0.0):
        """Instant or animated inversion to White background."""
        bg = Rectangle(
            width=20, height=20, # Oversized to fill screen
            fill_color=WHITE, fill_opacity=1,
            stroke_width=0
        )
        if duration == 0:
            scene.add_foreground_mobject(bg)
        else:
            scene.play(FadeIn(bg, run_time=duration))
        return bg
    
    @staticmethod  
    def revert(scene, bg_rect, duration=0.8):
        """Smooth reversion to Dark background."""
        scene.play(FadeOut(bg_rect, run_time=duration, rate_func=smooth))
