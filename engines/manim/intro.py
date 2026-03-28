from manim import *

class IntroManim(Scene):
    def construct(self):
        # Create a blue circle
        circle = Circle(color=BLUE)
        circle.set_fill(BLUE, opacity=0.5)
        
        # Create a pink square
        square = Square(color=PINK)
        square.set_fill(PINK, opacity=0.5)
        
        # Center them (they are by default at ORIGIN)
        circle.move_to(ORIGIN)
        square.move_to(ORIGIN)
        
        # Animations
        self.play(Create(circle))
        self.wait(1)
        self.play(ReplacementTransform(circle, square))
        self.wait(2)
