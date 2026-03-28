from manim import *

class PremiumPipeline(Scene):
    def construct(self):
        # Configuration
        self.camera.background_color = BLACK
        
        # 1. Assets
        python_logo = ImageMobject("python_logo.png").scale(0.5)
        db_logo = ImageMobject("db_logo.png").scale(0.5)
        gear = ImageMobject("gear.png").scale(0.4)
        
        # 2. Positioning
        python_logo.to_edge(LEFT, buff=1.5)
        gear.move_to(ORIGIN)
        db_logo.to_edge(RIGHT, buff=1.5)
        
        # 3. Glow and Rectangles (Premium Aesthetics)
        python_glow = SurroundingRectangle(python_logo, color=BLUE, buff=0.2)
        python_glow.set_stroke(width=8, opacity=0.3)
        
        db_glow = SurroundingRectangle(db_logo, color=BLUE, buff=0.2)
        db_glow.set_stroke(width=8, opacity=0.3)
        
        # 4. Chained Animation (Source Entry)
        t1 = Text("Source (Clean)", font_size=28, color=WHITE).next_to(python_logo, UP)
        
        self.play(
            LaggedStart(
                FadeIn(python_logo, shift=RIGHT, rate_func=smooth),
                Create(python_glow),
                Write(t1),
                lag_ratio=0.3
            ),
            run_time=2
        )
        self.wait(0.5)
        
        # 5. Pipeline Flow with Easing and Gear
        line1 = Line(python_logo.get_right(), gear.get_left(), color=BLUE_B)
        t2 = Text("Processing...", font_size=28).next_to(gear, UP)
        
        self.play(Create(line1), rate_func=smooth)
        self.play(
            FadeIn(gear, shift=RIGHT),
            Write(t2),
            Rotate(gear, angle=4*PI, run_time=3, rate_func=smooth)
        )
        # Subtle motion for gear
        self.play(gear.animate.scale(1.1), rate_func=there_and_back)
        
        # 6. Storage Entry
        line2 = Line(gear.get_right(), db_logo.get_left(), color=BLUE_B)
        t3 = Text("Stored", font_size=28).next_to(db_logo, UP)
        
        self.play(Create(line2), rate_func=smooth)
        self.play(
            LaggedStart(
                FadeIn(db_logo, scale=1.2, rate_func=smooth),
                Create(db_glow),
                Write(t3),
                lag_ratio=0.2
            )
        )
        
        # 7. Final Branding / Finish
        finish_text = Text("Ready for Remotion", color=YELLOW, weight=BOLD).to_edge(DOWN, buff=1)
        self.play(Write(finish_text), run_time=1.5)
        self.wait(2)
