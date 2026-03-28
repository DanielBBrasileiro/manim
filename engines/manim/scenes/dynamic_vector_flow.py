import numpy as np
from manim import Scene, VGroup, FadeIn
from core.primitives.geometry import AIOXDot
from core.primitives.fields import AIOXNoiseField
from core.primitives.theme_loader import theme

class VectorFlow(Scene):
    def construct(self):
        self.camera.background_color = theme.colors["background"]
        
        # 1. Instancia o campo magnético/vento com alta entropia (caos)
        noise_field = AIOXNoiseField(entropy=0.8)
        
        # 2. Gera 400 partículas aleatórias (A Nuvem de Dados)
        dots = VGroup(*[
            AIOXDot(
                radius=np.random.uniform(0.01, 0.04), 
                is_accent=(np.random.random() > 0.95) # 5% das partículas recebem a cor de sotaque
            ).move_to([np.random.uniform(-8, 8), np.random.uniform(-4, 4), 0])
            for _ in range(400)
        ])
        
        self.add(dots)
        self.play(FadeIn(dots, run_time=1))
        
        # 3. A Mágica: O Atualizador de Física (Updater)
        # O Manim vai chamar essa função a cada frame (60 vezes por segundo)
        time_tracker = [0.0]
        
        def update_particles(mob, dt):
            time_tracker[0] += dt * 0.5 # Velocidade da evolução do tempo
            current_time = time_tracker[0]
            
            for dot in mob:
                # Pergunta ao campo de ruído para onde ir
                force = noise_field.get_vector(dot.get_center(), current_time)
                # Empurra a partícula naquela direção
                dot.shift(force * dt)
                
                # Opcional: Efeito Pac-Man (se sair da tela, volta do outro lado)
                x, y, z = dot.get_center()
                if x > 8: dot.set_x(-8)
                if x < -8: dot.set_x(8)
                if y > 4.5: dot.set_y(-4.5)
                if y < -4.5: dot.set_y(4.5)

        # Anexa as leis da física às partículas e deixa rodar por 8 segundos
        dots.add_updater(update_particles)
        self.wait(8)
        dots.remove_updater(update_particles)
