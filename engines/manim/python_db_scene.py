from manim import *
from timing_logger import logger
import numpy as np

config.pixel_width = 1920
config.pixel_height = 1080
config.frame_rate = 60
config.background_opacity = 0.0

PYTHON_BLUE = "#3776AB"
POSTGRES_BLUE = "#336791"

class PythonSource(Scene):
    def construct(self):
        logger.start()
        self.camera.background_opacity = 0
        
        # Python-ish Hexagon/Simplified Logo
        logo = RegularPolygon(n=6, color=PYTHON_BLUE, fill_opacity=0.2).scale(1.5).shift(LEFT * 4)
        center_dot = Dot(color=YELLOW).move_to(logo.get_center())
        
        self.play(Create(logo), FadeIn(center_dot))
        logger.log("source_ready", self.renderer.time)
        
        # Stream out
        dots = VGroup(*[Dot(color=PYTHON_BLUE, radius=0.05) for _ in range(10)])
        self.play(
            LaggedStart(
                *[d.animate.shift(RIGHT * 10).set_opacity(0) for d in dots],
                lag_ratio=0.1
            ),
            run_time=2
        )
        logger.log("stream_started", self.renderer.time)
        self.wait(1)
        logger.save()

class DBIngestion(Scene):
    def construct(self):
        logger.start()
        self.camera.background_opacity = 0
        
        # DB Cylinder
        base = Ellipse(width=3, height=1, color=POSTGRES_BLUE, fill_opacity=0.1).shift(DOWN * 1.5)
        top = Ellipse(width=3, height=1, color=POSTGRES_BLUE, fill_opacity=0.2).shift(UP * 1.5)
        side_l = Line(base.get_left(), top.get_left(), color=POSTGRES_BLUE)
        side_r = Line(base.get_right(), top.get_right(), color=POSTGRES_BLUE)
        db = VGroup(base, top, side_l, side_r).shift(RIGHT * 4)
        
        self.play(Create(db))
        logger.log("db_ready", self.renderer.time)
        
        # Fill animation
        fill = Rectangle(height=0.1, width=2.8, color=POSTGRES_BLUE, fill_opacity=0.5).move_to(base.get_center() + UP * 0.1)
        self.play(FadeIn(fill))
        
        for i in range(5):
            self.play(fill.animate.stretch_to_fit_height(0.5 * (i+1)).move_to(base.get_center() + UP * 0.25 * (i+1)), run_time=0.5)
            logger.log(f"db_fill_{i}", self.renderer.time)
            
        self.wait(1)
        logger.save()
