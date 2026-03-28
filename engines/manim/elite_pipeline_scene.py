from manim import *
from timing_logger import logger
import json
import os

# Configurações de Elite (1080p60)
config.pixel_width = 1920
config.pixel_height = 1080
config.frame_rate = 60
config.background_opacity = 0.0

# Robust Path Resolution
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../"))

with open(os.path.join(ROOT, 'assets/brand/tokens.json')) as f:
    tokens = json.load(f)

print(f"INITIALIZED: ROOT at {ROOT}")

class EliteDataPipeline(Scene):
    def construct(self):
        logger.start()
        self.camera.background_opacity = 0
        primary_red = tokens["colors"]["primary"]
        
        # 1. Assets (WQF Standard)
        cloud_svg = os.path.join(ROOT, "assets/logos/tech/cloud.svg")
        rust_svg = os.path.join(ROOT, "assets/logos/tech/rust.svg")
        python_svg = os.path.join(ROOT, "assets/logos/tech/python.svg")
        db_svg = os.path.join(ROOT, "assets/logos/tech/postgres.svg")
        tableau_svg = os.path.join(ROOT, "assets/logos/tech/tableau.svg")

        # Create Mobjects
        lake = SVGMobject(cloud_svg).scale(0.8).shift(LEFT * 5 + UP * 2).set_color(WHITE)
        rust = SVGMobject(rust_svg).scale(0.8).shift(LEFT * 2 + UP * 2).set_color(primary_red)
        python = SVGMobject(python_svg).scale(0.8).shift(RIGHT * 2 + UP * 2).set_color(primary_red)
        db = SVGMobject(db_svg).scale(1.0).shift(RIGHT * 5 + UP * 2).set_color(WHITE)
        tableau = SVGMobject(tableau_svg).scale(1.0).shift(RIGHT * 5 + DOWN * 2).set_color(primary_red)

        # 2. Sequence (VISTA Architecture)
        
        # Act 1: The Hook (Kinetic Entrance)
        self.play(DrawBorderThenFill(lake, run_time=1.5))
        logger.log("lake_ready", self.renderer.time)
        self.wait(0.5)

        # Act 2: High-Speed Ingestion (Rust)
        self.play(DrawBorderThenFill(rust, run_time=1.5))
        logger.log("rust_ready", self.renderer.time)
        
        # Data Packets Lake -> Rust
        path_lake_rust = ArcBetweenPoints(lake.get_center(), rust.get_center(), angle=PI/4)
        for _ in range(3):
            dot = Dot(color=primary_red, radius=0.08)
            self.play(MoveAlongPath(dot, path_lake_rust), run_time=0.6, rate_func=exponential_decay)
            self.remove(dot)

        # Act 3: Python Orchestration
        self.play(DrawBorderThenFill(python, run_time=1.5))
        logger.log("python_ready", self.renderer.time)
        
        # Data Packets Rust -> Python
        path_rust_python = Line(rust.get_center(), python.get_center())
        for _ in range(3):
            dot = Dot(color=WHITE, radius=0.08)
            self.play(MoveAlongPath(dot, path_rust_python), run_time=0.4)
            self.remove(dot)

        # Act 4: Storage & Insights
        self.play(DrawBorderThenFill(db, run_time=1.5))
        logger.log("db_ready", self.renderer.time)
        
        path_python_db = ArcBetweenPoints(python.get_center(), db.get_center(), angle=-PI/4)
        self.play(MoveAlongPath(Dot(color=primary_red), path_python_db), run_time=1)

        self.play(DrawBorderThenFill(tableau, run_time=1.5))
        logger.log("tableau_ready", self.renderer.time)
        
        # Final Impact
        self.play(
            tableau.animate.scale(1.2).set_color(WHITE),
            Flash(tableau, color=primary_red),
            run_time=0.5
        )
        self.play(tableau.animate.scale(1/1.2).set_color(primary_red))

        logger.log("pipeline_complete", self.renderer.time)
        self.wait(1)
        logger.save()
