"""
Primal Data Primitives - AIOX v4.1.
Monochrome geometric elements that represent data without using icons.
"""
from manim import *
import numpy as np

class DataStream(VGroup):
    """A stream of moving dots representing data flow."""
    def __init__(self, count=20, width=6, **kwargs):
        super().__init__(**kwargs)
        self.dots = VGroup(*[
            Dot(radius=0.03, color=WHITE).shift(RIGHT * (np.random.random() * width - width/2))
            for _ in range(count)
        ])
        self.add(self.dots)

    def flow_animation(self, run_time=5):
        return self.dots.animate(run_time=run_time, rate_func=linear).shift(RIGHT * 2)

class NeuralGrid(VGroup):
    """A subtle grid of lines that can pulse or warp."""
    def __init__(self, size=8, density=0.5, **kwargs):
        super().__init__(**kwargs)
        lines = VGroup()
        for x in np.arange(-size/2, size/2, density):
            lines.add(Line([x, -size/2, 0], [x, size/2, 0], stroke_width=0.2, stroke_opacity=0.1))
        for y in np.arange(-size/2, size/2, density):
            lines.add(Line([-size/2, y, 0], [size/2, y, 0], stroke_width=0.2, stroke_opacity=0.1))
        self.add(lines)

class StorageHex(RegularPolygon):
    """A minimal hexagon representing a data node."""
    def __init__(self, **kwargs):
        super().__init__(n=6, stroke_width=1, stroke_opacity=0.7, fill_opacity=0, **kwargs)
        self.scale(0.3)
