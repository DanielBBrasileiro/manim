import numpy as np
from manim import Scene, VGroup, FadeIn, Create, GrowFromCenter, LaggedStartMap, UP, PI, there_and_back, smooth
from core.primitives.geometry import AIOXDot, AIOXLine
from core.primitives.theme_loader import theme

class NeuralMesh(Scene):
    def construct(self):
        # 1. Puxa o vácuo absoluto do tema (Background)
        self.camera.background_color = theme.colors["background"]

        # 2. Gera 45 pontos em coordenadas aleatórias usando NumPy
        np.random.seed(42) # Seed fixa para o design ser reproduzível
        num_nodes = 45
        points = [np.array([np.random.uniform(-6, 6), np.random.uniform(-3.5, 3.5), 0]) for _ in range(num_nodes)]

        # Cria os objetos AIOXDot baseados nessas coordenadas
        nodes = VGroup(*[AIOXDot(radius=0.05).move_to(p) for p in points])

        # 3. Calcula distâncias e cria a Teia (Connections)
        threshold = 2.5 # Distância máxima para conectar dois pontos
        connections = VGroup()
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                dist = np.linalg.norm(points[i] - points[j])
                if dist < threshold:
                    # Usa a linha secundária (mais fina/translúcida) para a teia
                    line = AIOXLine(points[i], points[j], weight="secondary")
                    connections.add(line)

        # 4. Cria a Anomalia/Nó Central (Accent)
        core_point = np.array([0, 0, 0])
        core_node = AIOXDot(is_accent=True, radius=0.15).move_to(core_point)
        
        # 5. Coreografia (O Cinematográfico)
        
        # A. Revelação lenta dos nós flutuando levemente para cima
        self.play(LaggedStartMap(FadeIn, nodes, shift=UP*0.2, lag_ratio=0.03), run_time=2, rate_func=smooth)
        
        # B. As linhas de conexão se desenham organicamente
        self.play(Create(connections, lag_ratio=0.05), run_time=3, rate_func=smooth)
        
        # C. O nó central surge
        self.play(GrowFromCenter(core_node), run_time=1)
        
        # D. Pulso: O nó central se conecta brutalmente aos nós mais próximos
        pulse_lines = VGroup()
        for node in nodes:
            if np.linalg.norm(node.get_center() - core_node.get_center()) < threshold * 1.5:
                # Usa a linha primária (mais grossa) para impacto
                pulse_lines.add(AIOXLine(core_node.get_center(), node.get_center(), weight="primary"))
        
        self.play(Create(pulse_lines, lag_ratio=0.1), run_time=1.5)
        
        # E. Respiração final: A malha inteira rotaciona levemente e volta
        mesh = VGroup(nodes, connections, core_node, pulse_lines)
        self.play(mesh.animate.rotate(PI/16).scale(1.05), run_time=4, rate_func=there_and_back)
        
        self.wait(1)
