from manim import Scene, FadeIn, Wait, LaggedStart
from core.primitives.geometry import AIOXDot, AIOXLine, NeuralGrid
from core.primitives.theme_loader import theme

class AIOXBenchmark(Scene):
    def construct(self):
        # O Manim cuida APENAS da geometria. Zero texto.
        
        # Opcional: Para testar o modo claro, descomente a linha abaixo:
        # theme.set_state("inverted")
        
        self.camera.background_color = theme.colors["background"]

        # 1. Cria a grid base
        grid = NeuralGrid(rows=7, cols=11, spacing=1.2)
        
        # 2. Cria o dot de acento (a anomalia no sistema)
        accent_dot = AIOXDot(is_accent=True, radius=0.15)
        accent_dot.move_to(grid[35].get_center()) # Move para o centro
        
        # 3. Animação (Física)
        self.play(FadeIn(grid, run_time=2))
        self.play(FadeIn(accent_dot, scale=0.5))
        self.wait(1)
        
        # Uma linha conectando pontos do grid
        line = AIOXLine(grid[10].get_center(), grid[60].get_center(), weight="primary")
        self.play(FadeIn(line))
        
        self.wait(2)
