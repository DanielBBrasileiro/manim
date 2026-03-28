from manim import *

class PipelineScene(Scene):
    def construct(self):
        # 1. Assets
        python_logo = ImageMobject("python_logo.png").scale(0.4)
        db_logo = ImageMobject("db_logo.png").scale(0.4)
        gear = ImageMobject("gear.png").scale(0.3)
        
        # 2. Position
        python_logo.to_edge(LEFT, buff=1)
        gear.move_to(ORIGIN)
        db_logo.to_edge(RIGHT, buff=1)
        
        # 3. Titles
        t1 = Text("Source", font_size=24).next_to(python_logo, UP)
        t2 = Text("Process", font_size=24).next_to(gear, UP)
        t3 = Text("Storage", font_size=24).next_to(db_logo, UP)
        
        # 4. Pipeline Line
        # A line that connects them
        line1 = Line(python_logo.get_right(), gear.get_left(), color=BLUE_B)
        line2 = Line(gear.get_right(), db_logo.get_left(), color=BLUE_B)
        
        # 5. Animation Flow
        # Entry Line
        start_line = Line(LEFT * 7, python_logo.get_left(), color=YELLOW)
        
        self.play(Create(start_line))
        self.play(
            FadeIn(python_logo, shift=RIGHT),
            Write(t1)
        )
        self.wait(0.5)
        
        # Flow to Process
        self.play(Create(line1))
        self.play(
            FadeIn(gear, shift=RIGHT),
            Write(t2),
            Rotate(gear, angle=2*PI, run_time=2)
        )
        self.wait(0.5)
        
        # Flow to DB
        self.play(Create(line2))
        self.play(
            FadeIn(db_logo, shift=RIGHT),
            Write(t3)
        )
        self.wait(1)
        
        # Closing
        final_text = Text("Pipeline Complete", color=GREEN).to_edge(DOWN)
        self.play(Write(final_text))
        self.wait(2)
