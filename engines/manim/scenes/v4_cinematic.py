"""
V4.1 Cinematic Scene - AIOX Primal Data Standard.
Higher visual density, same monochrome philosophy.
"""
import sys
import os
sys.path.append(os.getcwd())

from manim import *
from core.primitives import LivingCurve, NarrativeContainer, ColorInversion
from core.primitives.elements import DataStream, NeuralGrid, StorageHex
from engines.manim.manim_theme import TOKENS, DARK, INVERTED, PHYSICS
import json

class V4CinematicScene(Scene):
    def construct(self):
        self.camera.background_color = BACKGROUND_COLOR
        self.narrative = TOKENS['narrative']
        self.events = []
        
        # 1. Background Grid (Ambient texture)
        self.grid = NeuralGrid(size=10, density=0.5)
        self.add(self.grid)
        
        # 2. Main Narrative Loop
        for act in self.narrative['acts']:
            self.render_act(act)
            
        self.export_events()

    def render_act(self, act):
        if act['name'] == 'genesis':
            self.render_genesis(act)
        elif act['name'] == 'turbulence':
            self.render_turbulence(act)
        elif act['name'] == 'resolution':
            self.render_resolution(act)

    def render_genesis(self, act):
        self.play(Create(self.grid, run_time=2))
        
        self.curve = LivingCurve(growth_progress=0.0).set_stroke(WHITE, 2)
        self.node = StorageHex().shift(LEFT * 3)
        self.play(Create(self.node), run_time=1)
        
        self.play(
            self.curve.animate(run_time=3, rate_func=slow_into).grow_to(0.7, noise=0.0),
        )
        self.wait(1)

    def render_turbulence(self, act):
        # 1. Complexity Spike: DataStreams
        self.streams = VGroup(*[DataStream().shift(UP * (i-1)) for i in range(3)])
        self.play(FadeIn(self.streams), run_time=1)
        
        # 2. Tension: Noise + Grid Warp
        self.play(
            self.curve.animate(run_time=3).grow_to(1.1, noise=0.5),
            self.grid.animate(run_time=3).scale(1.5).set_stroke(opacity=0.3),
            *[s.flow_animation() for s in self.streams]
        )
        
        # 3. COLOR INVERSION
        self.log_event("climax", "inversion", self.renderer.time)
        bg = ColorInversion.invert(self, duration=0.1)
        
        # Shift all to black
        self.curve.set_stroke(BLACK)
        self.grid.set_stroke(BLACK)
        self.node.set_stroke(BLACK)
        self.streams.set_stroke(BLACK)
            
        self.wait(2)
        self.revert_bg = bg

    def render_resolution(self, act):
        ColorInversion.revert(self, self.revert_bg, duration=1.0)
        
        # Reset colors to white
        self.curve.set_stroke(WHITE)
        self.grid.set_stroke(WHITE)
        self.node.set_stroke(WHITE)
        self.streams.set_stroke(WHITE)
            
        # Dramatic Scale back to clarity
        elements = VGroup(self.curve, self.grid, self.node, self.streams)
        self.play(
            elements.animate(run_time=4, rate_func=smooth).scale(0.8).shift(UP * 0.5),
        )
        self.wait(1)

    def log_event(self, name, type, time):
        self.events.append({"name": name, "type": type, "timestamp": time})

    def export_events(self):
        output_path = "assets/brand/timing_events.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.events, f, indent=2)

from engines.manim.manim_theme import BACKGROUND_COLOR
