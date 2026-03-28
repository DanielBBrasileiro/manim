from manim import *

class AssetsDemo(Scene):
    def construct(self):
        # Load external image
        logo = ImageMobject("logo.png")
        logo.scale(0.5)
        logo.to_edge(UP)
        
        # Create some text objects
        formula = Text("f(x) = integral of e^(-x^2) dx", font_size=24)
        formula.next_to(logo, DOWN, buff=1.0)
        
        # Animations
        self.play(FadeIn(logo, shift=DOWN))
        self.play(Write(formula))
        self.wait(2)
        
        # Transform image
        self.play(logo.animate.scale(1.5).move_to(ORIGIN))
        self.play(FadeOut(formula))
        self.wait(1)
