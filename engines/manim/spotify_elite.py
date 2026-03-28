from manim import *
from timing_logger import logger
import numpy as np

config.pixel_width = 1920
config.pixel_height = 1080
config.frame_rate = 60
config.background_opacity = 0.0

SPOTIFY_GREEN = "#1DB954"

class SpotifyElite(MovingCameraScene):
    def construct(self):
        # 0. Setup
        logger.start()
        self.camera.background_opacity = 0
        
        # 1. App Source (Left)
        # Refined with subtle fill
        phone = RoundedRectangle(height=5, width=2.5, corner_radius=0.4, color=WHITE, stroke_width=2)
        play_btn = Triangle(color=SPOTIFY_GREEN, fill_opacity=0.8).scale(0.3).rotate(-90*DEGREES)
        app = VGroup(phone, play_btn).shift(LEFT * 6)
        
        self.play(FadeIn(app, shift=RIGHT))
        logger.log("user_ready", self.renderer.time)
        self.wait(1)
        
        # 2. Ingestion: Kafka Cluster (Center)
        # Using fill for a more premium "Apple" glass look
        kafka = VGroup(*[
            Circle(radius=0.5, color=WHITE, stroke_width=1, fill_color=WHITE, fill_opacity=0.05) 
            for _ in range(3)
        ])
        kafka.arrange(DOWN, buff=1.2)
        kafka_group = VGroup(kafka).shift(RIGHT * 2)
        
        pulse = Dot(color=SPOTIFY_GREEN, fill_opacity=1).scale(1.5).move_to(app.get_center())
        
        self.play(
            self.camera.frame.animate.move_to(RIGHT * 2),
            pulse.animate.move_to(kafka.get_center()),
            FadeIn(kafka_group),
            run_time=3,
            rate_func=smooth
        )
        logger.log("kafka_hit", self.renderer.time)
        self.wait(1)
        
        # 3. Processing: ML Engine (Right)
        # Transparent box with subtle stroke
        ml_box = RoundedRectangle(height=4, width=7, corner_radius=0.5, color=SPOTIFY_GREEN, stroke_width=2, fill_opacity=0.05)
        ml_box.shift(RIGHT * 12)
        
        self.play(
            self.camera.frame.animate.move_to(RIGHT * 12),
            FadeIn(ml_box),
            run_time=3,
            rate_func=smooth
        )
        
        logger.log("ml_processing_start", self.renderer.time)
        
        # ML Particles (Data flow representation)
        dots = VGroup(*[
            Dot(color=BLUE, radius=0.04, fill_opacity=0.6).move_to(
                ml_box.get_center() + [np.random.uniform(-2.8,2.8), np.random.uniform(-1.5,1.5), 0]
            ) for _ in range(25)
        ])
        
        self.play(
            LaggedStart(*[FadeIn(d, scale=0.5) for d in dots], lag_ratio=0.05),
            run_time=2
        )
        
        # Final "Success" State
        success_glow = ml_box.copy().set_stroke(width=10, opacity=0.2)
        self.play(FadeIn(success_glow), rate_func=there_and_back)
        
        logger.log("ml_complete", self.renderer.time)
        self.wait(2)
        
        logger.save()
