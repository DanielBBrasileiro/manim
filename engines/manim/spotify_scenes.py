from manim import *

# Global Config for All Scenes
config.pixel_width = 1920
config.pixel_height = 1080
config.frame_rate = 60
config.background_color = "#191414" # Spotify Black

SPOTIFY_GREEN = "#1DB954"

class UserAction(Scene):
    def construct(self):
        # 1. Phone Icon (Mockup)
        phone = RoundedRectangle(height=5, width=2.5, corner_radius=0.5, color=WHITE)
        play_btn = Triangle(color=SPOTIFY_GREEN).scale(0.3).rotate(-90*DEGREES)
        phone_group = VGroup(phone, play_btn)
        
        self.play(FadeIn(phone_group, shift=UP))
        self.wait(1)
        
        # 2. Click Animation
        self.play(play_btn.animate.scale(1.2), rate_func=there_and_back)
        
        # 3. Pulse Flow
        pulses = VGroup(*[Dot(color=SPOTIFY_GREEN) for _ in range(5)])
        self.play(
            LaggedStart(
                *[p.animate.shift(RIGHT * 10).set_opacity(0) for p in pulses],
                lag_ratio=0.2
            ),
            run_time=2
        )
        self.wait(1)

class KafkaIngestion(Scene):
    def construct(self):
        # Cluster Nodes
        nodes = VGroup(*[Circle(radius=0.4, color=WHITE, fill_opacity=0.1) for _ in range(3)])
        nodes.arrange(DOWN, buff=1)
        label = Text("KAFKA CLUSTER", font_size=36).next_to(nodes, LEFT, buff=1)
        
        self.play(Create(nodes), Write(label))
        
        # High-speed stream
        stream = VGroup(*[
            Dot(color=SPOTIFY_GREEN, radius=0.05).move_to(LEFT * 5 + UP * (i % 3 - 1))
            for i in range(30)
        ])
        
        self.play(
            LaggedStart(
                *[s.animate.move_to(nodes[i % 3].get_center()).set_opacity(0.5) for i, s in enumerate(stream)],
                lag_ratio=0.05
            ),
            run_time=3
        )
        
        # Outflow
        out_stream = VGroup(*[
            Dot(color=WHITE, radius=0.05).move_to(nodes[i % 3].get_center())
            for i in range(15)
        ])
        self.play(
            LaggedStart(
                *[s.animate.shift(RIGHT * 6).set_opacity(0) for i, s in enumerate(out_stream)],
                lag_ratio=0.1
            ),
            run_time=2
        )
        self.wait(1)

class PersonalizationEngine(Scene):
    def construct(self):
        # ML Engine
        box = Rectangle(height=4, width=6, color=SPOTIFY_GREEN)
        title = Text("ML PERSONALIZATION", font_size=40).move_to(box.get_top() + DOWN * 0.5)
        
        self.play(Create(box), Write(title))
        
        # Matrix/Data representation
        grid = NumberPlane(
            x_range=[-2, 2, 1], y_range=[-1, 1, 1],
            background_line_style={"stroke_opacity": 0.2}
        ).scale(0.5).move_to(box.get_center())
        
        self.play(FadeIn(grid))
        
        # Points appearing and connecting
        dots = VGroup(*[Dot(color=BLUE) for _ in range(8)])
        for d in dots: d.move_to([np.random.uniform(-1.5, 1.5), np.random.uniform(-0.8, 0.8), 0])
        
        self.play(Create(dots))
        
        # Recommendation generation
        rec_box = RoundedRectangle(height=1, width=3, color=WHITE).next_to(box, RIGHT, buff=1)
        rec_text = Text("New Playlist", font_size=24, color=WHITE).move_to(rec_box.get_center())
        

class SpotifyFullPipeline(Scene):
    def construct(self):
        # This scene stitches the logic of the three previous parts
        # Scene 1: User Action
        phone = RoundedRectangle(height=5, width=2.5, corner_radius=0.5, color=WHITE)
        play_btn = Triangle(color=SPOTIFY_GREEN).scale(0.3).rotate(-90*DEGREES)
        phone_group = VGroup(phone, play_btn)
        
        self.play(FadeIn(phone_group, shift=UP))
        self.play(play_btn.animate.scale(1.2), rate_func=there_and_back)
        pulses = VGroup(*[Dot(color=SPOTIFY_GREEN) for _ in range(5)])
        self.play(
            LaggedStart(
                *[p.animate.shift(RIGHT * 10).set_opacity(0) for p in pulses],
                lag_ratio=0.2
            ),
            run_time=2
        )
        self.play(FadeOut(phone_group))
        self.wait(0.5)

        # Scene 2: Kafka Ingestion
        nodes = VGroup(*[Circle(radius=0.4, color=WHITE, fill_opacity=0.1) for _ in range(3)])
        nodes.arrange(DOWN, buff=1)
        label = Text("KAFKA CLUSTER", font_size=36).next_to(nodes, LEFT, buff=1)
        self.play(Create(nodes), Write(label))
        
        stream = VGroup(*[
            Dot(color=SPOTIFY_GREEN, radius=0.05).move_to(LEFT * 5 + UP * (i % 3 - 1))
            for i in range(20)
        ])
        self.play(
            LaggedStart(
                *[s.animate.move_to(nodes[i % 3].get_center()).set_opacity(0.5) for i, s in enumerate(stream)],
                lag_ratio=0.05
            ),
            run_time=2
        )
        self.play(FadeOut(nodes), FadeOut(label), FadeOut(stream))
        self.wait(0.5)

        # Scene 3: ML Personalization
        box = Rectangle(height=4, width=6, color=SPOTIFY_GREEN)
        ml_title = Text("ML PERSONALIZATION", font_size=40).move_to(box.get_top() + DOWN * 0.5)
        self.play(Create(box), Write(ml_title))
        
        grid = NumberPlane(x_range=[-2, 2, 1], y_range=[-1, 1, 1], background_line_style={"stroke_opacity": 0.2}).scale(0.5).move_to(box.get_center())
        self.play(FadeIn(grid))
        
        dots = VGroup(*[Dot(color=BLUE) for _ in range(8)])
        for d in dots: d.move_to([np.random.uniform(-1.5, 1.5), np.random.uniform(-0.8, 0.8), 0])
        self.play(Create(dots))
        
        finish_text = Text("Spotify: Made For You", color=WHITE, font_size=48).to_edge(DOWN, buff=2)
        self.play(Write(finish_text), run_time=2)
        self.wait(2)
