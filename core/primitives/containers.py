"""
Narrative containers: frames that frame, split, and rotate.
Inspired by the "Invisible Architecture" standard.
"""
from manim import *

class NarrativeContainer(VGroup):
    """A container that can split, rotate, and expand."""
    
    def __init__(self, width=4, height=5, **kwargs):
        super().__init__(**kwargs)
        self.rect = Rectangle(
            width=width, height=height,
            stroke_color=WHITE, stroke_width=0.8,
            fill_opacity=0
        )
        self.add(self.rect)
    
    def split_horizontal(self, gap=0.3):
        """Returns two new rectangles representing a split."""
        w = self.rect.width
        h = self.rect.height
        left = Rectangle(width=w/2 - gap/2, height=h,
                        stroke_color=self.rect.get_stroke_color(), 
                        stroke_width=self.rect.get_stroke_width(), 
                        fill_opacity=0)
        right = Rectangle(width=w/2 - gap/2, height=h,
                         stroke_color=self.rect.get_stroke_color(), 
                         stroke_width=self.rect.get_stroke_width(), 
                         fill_opacity=0)
        left.shift(LEFT * (w/4 + gap/4))
        right.shift(RIGHT * (w/4 + gap/4))
        return [left, right]
    
    def rotate_dramatic(self, angle=15):
        """Dramatic rotation animation."""
        return self.rect.animate.rotate(
            angle * DEGREES,
            rate_func=linear # rate_func usually handled by scene.play
        )
