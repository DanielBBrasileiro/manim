from manim import *
from timing_logger import logger
import json
import os

# Configurações de Elite
config.pixel_width = 1920
config.pixel_height = 1080
config.frame_rate = 60
config.background_opacity = 0.0

# Carregamento de Tokens de Marca
with open('../../assets/brand/tokens.json') as f:
    tokens = json.load(f)

# MCP Dynamic Data Placeholder
dynamic_code = ""
if os.path.exists("../../assets/brand/dynamic_data.json"):
    with open("../../assets/brand/dynamic_data.json") as f:
        mcp_data = json.load(f)
        dynamic_code = mcp_data.get("code", "")[:150] # Snippet para o demo

class PythonDBElite(Scene):
    def construct(self):
        logger.start()
        self.camera.background_opacity = 0
        
        # 1. Carregar Assets SVGs (Contraste Branco Minimalista)
        python_svg = "../../assets/logos/tech/python.svg"
        postgres_svg = "../../assets/logos/tech/postgres.svg"
        
        if not os.path.exists(python_svg) or not os.path.exists(postgres_svg):
            raise FileNotFoundError(f"Assets SVG não encontrados em {python_svg} ou {postgres_svg}")

        # SVGs Dinâmicos baseados no Design Tokens (Red Theme)
        primary_color = tokens["colors"]["primary"]
        source = SVGMobject(python_svg).scale(0.8).shift(LEFT * 4).set_color(primary_color)
        dest = SVGMobject(postgres_svg).scale(1.0).shift(RIGHT * 4).set_color(primary_color)
        
        # 2. Executar Coreografia (Efeito Blueprint / DrawBorderThenFill)
        self.play(DrawBorderThenFill(source, run_time=2))
        logger.log("source_ready", self.renderer.time)
        self.wait(0.5)
        
        self.play(DrawBorderThenFill(dest, run_time=2))
        logger.log("dest_ready", self.renderer.time)

        # 2.5 Injeção de Código Real (MCP Proof of Concept)
        if dynamic_code:
            # Salvar em arquivo temporário para o mobject Code
            with open("temp_code.py", "w") as f:
                f.write(dynamic_code)
                
            code_label = Code(
                code_file="temp_code.py",
                background="window"
            ).scale(0.4).next_to(source, DOWN, buff=0.5)
            self.play(Write(code_label))
            self.wait(1)
            self.play(FadeOut(code_label))
            os.remove("temp_code.py")

        self.wait(1)
        
        # 3. Fluxo de Dados Cinematic Physics (Arco + MoveAlongPath)
        brand_primary = tokens["colors"]["primary"]
        
        # Criar a trajetória em arco (Apple aesthetic)
        data_path = ArcBetweenPoints(
            source.get_center(), 
            dest.get_center(), 
            angle=PI/4,
            stroke_opacity=0.1, # Guia sutil
            stroke_color=brand_primary
        )
        self.add(data_path)

        # Sequência de Disparo de Pacotes (Loops)
        for i in range(5):
            dot = Dot(color=brand_primary, radius=0.08)
            trail = TracedPath(dot.get_center, stroke_color=brand_primary, stroke_width=4, dissipating_time=0.3)
            self.add(trail)
            
            # Animação de impacto sincronizada com o arco
            self.play(
                MoveAlongPath(dot, data_path),
                run_time=1.5,
                rate_func=bezier([0, 0, 1, 1]) # Aceleração suave
            )
            
            # Impact Pulse (Postgres reage ao toque do pacote)
            self.play(
                dest.animate.scale(1.15).set_color(brand_primary),
                FadeOut(dot),
                run_time=0.1
            )
            self.play(dest.animate.scale(1/1.15).set_color(WHITE), run_time=0.1)
            self.remove(trail)
            self.wait(0.3)

        logger.log("pipeline_complete", self.renderer.time)
        self.wait(1)
        logger.save()
