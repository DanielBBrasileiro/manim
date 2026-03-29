"""
AIOX Noise Fields — v4.3
=========================
Substituição do noise harmônico (sin/cos) por Fractal Brownian Motion (FBM)
via opensimplex. Fallback automático para harmônico se opensimplex ausente.

Diferença visual:
  Harmônico  → repetições periódicas visíveis, parece gerado por computador
  Simplex FBM → fluxo orgânico contínuo, sem padrões periódicos, parece natural
"""
import numpy as np

try:
    from opensimplex import OpenSimplex
    _HAS_SIMPLEX = True
except ImportError:
    _HAS_SIMPLEX = False


class AIOXNoiseField:
    """
    Campo vetorial procedural baseado em FBM (Fractal Brownian Motion).

    Agora reativo à Persona Zara: recebe uma "Motion Signature" semântica
    em vez de um número cego.
    """

    def __init__(self, signature: str = "breathing_field", strength_override=None, seed: int = None):
        self.signature = signature
        self.seed = seed

        # Assinaturas Visuais definem a matemática do caos
        if signature == "breathing_field":
            # Calmo, lento, expansão laminar
            self.octaves = 2
            self.strength = 0.15
            self.lacunarity = 1.5
            self.persistence = 0.3
        elif signature == "vortex_pull":
            # Giro central, atrator
            self.octaves = 3
            self.strength = 0.6
            self.lacunarity = 2.0
            self.persistence = 0.5
        elif signature == "chaotic_dispersion":
            # Alta variação, rajadas, tempestuoso
            self.octaves = 5
            self.strength = 1.8
            self.lacunarity = 2.5
            self.persistence = 0.7
        elif signature == "elastic_snap":
            # Fraturado, afiado, quebra de ritmo
            self.octaves = 6
            self.strength = 3.5
            self.lacunarity = 3.0
            self.persistence = 0.8
        elif signature == "laminar_flow" or signature == "coherent_flow":
            # Fluxo direcional suave, baixa turbulência
            self.octaves = 1
            self.strength = 0.08
            self.lacunarity = 1.2
            self.persistence = 0.2
        elif signature == "oscillatory_wave" or signature == "pulsing_wave":
            # Onda pulsante periódica
            self.octaves = 3
            self.strength = 0.4
            self.lacunarity = 1.8
            self.persistence = 0.5
        elif signature == "convergence_field":
            # Atração para centro, similar a vortex mas mais suave
            self.octaves = 2
            self.strength = 0.35
            self.lacunarity = 1.6
            self.persistence = 0.4
        elif signature == "fragmented_noise":
            # Fragmentado, quebrado, alta lacunarity
            self.octaves = 5
            self.strength = 1.2
            self.lacunarity = 3.5
            self.persistence = 0.6
        elif signature == "chaotic_burst":
            # Caótico explosivo, entre elastic_snap e chaotic_dispersion
            self.octaves = 6
            self.strength = 2.5
            self.lacunarity = 2.8
            self.persistence = 0.75
        elif signature == "scattered_to_aligned":
            # Começa disperso, converge para alinhamento
            self.octaves = 4
            self.strength = 0.9
            self.lacunarity = 2.2
            self.persistence = 0.55
        else:
            self.octaves = int(np.interp(0.5, [0, 1], [1, 6]))
            self.strength = 1.0
            self.lacunarity = 2.0
            self.persistence = 0.5

        if strength_override is not None:
            self.strength = strength_override

        if _HAS_SIMPLEX:
            _seed = seed if seed is not None else np.random.randint(0, 2**31)
            # Um gerador por dimensão para evitar correlações
            self._nx = OpenSimplex(_seed)
            self._ny = OpenSimplex(_seed + 1)
            self._nz = OpenSimplex(_seed + 2)
        else:
            # Fallback harmônico — mantém compatibilidade total
            rng = np.random.default_rng(seed)
            self.offsets = rng.uniform(-100, 100, (self.octaves, 3))
            self.frequencies = [1.5 ** i for i in range(self.octaves)]
            self.amplitudes = [0.8 ** i for i in range(self.octaves)]

    # ── FBM com Simplex ──────────────────────────────────────────────────────

    def _fbm(self, gen, x: float, y: float, z: float, time: float) -> float:
        """Fractal Brownian Motion: soma de oitavas de simplex noise."""
        value = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_val = 0.0

        for _ in range(self.octaves):
            value += gen.noise4(
                x * frequency,
                y * frequency,
                z * frequency,
                time * frequency * 0.3
            ) * amplitude
            max_val += amplitude
            amplitude *= self.persistence
            frequency *= self.lacunarity

        return value / max_val  # normaliza para [-1, 1]

    # ── API pública ──────────────────────────────────────────────────────────

    def get_vector(self, point, time: float = 0.0) -> np.ndarray:
        """
        Recebe coordenadas [x, y, z] + tempo e retorna força [dx, dy, dz].
        Drop-in replacement do método anterior — API idêntica.
        """
        x, y, z = float(point[0]), float(point[1]), float(point[2])

        if _HAS_SIMPLEX:
            vx = self._fbm(self._nx, x, y, z, time)
            vy = self._fbm(self._ny, x, y, z, time)
            vz = self._fbm(self._nz, x, y, z, time) * 0.3  # z reduzido para cenas 2D
        else:
            # Fallback harmônico (idêntico ao original)
            vx, vy, vz = 0.0, 0.0, 0.0
            for i in range(self.octaves):
                freq = self.frequencies[i]
                amp = self.amplitudes[i]
                ox, oy, oz = self.offsets[i]
                vx += np.sin((y + oy + time) * freq) * amp
                vy += np.cos((x + ox - time) * freq) * amp
                vz += np.sin((z + oz + time * 0.5) * freq) * amp

        vector = np.array([vx, vy, vz])
        norm = np.linalg.norm(vector)
        if norm > 1e-6:
            vector = (vector / norm) * self.strength

        # Aplicação de Forças Especiais por Assinatura
        if self.signature == "vortex_pull":
            # Espiral concêntrico em direção ao centro
            dist = np.sqrt(x*x + y*y) + 0.01
            # Rotação anti-horária
            vortex_vec = np.array([-y, x, 0]) / dist
            # Puxão magnético fraco pro centro
            pull_vec = np.array([-x, -y, 0]) / dist
            
            # Mistura FBM com vórtice perfeito
            vector = vector * 0.4 + (vortex_vec * 0.8 + pull_vec * 0.3) * self.strength
            
        elif self.signature == "elastic_snap":
            # Vetores saltam erraticamente em posições fracionárias
            if int(time * 10) % 3 == 0:
                vector *= 2.5
                
        elif self.signature == "breathing_field":
            # Pulso senoidal lento no tempo
            breath_cycle = np.sin(time * 1.5) * 0.5 + 0.5
            vector *= (0.5 + breath_cycle)

        elif self.signature in ("laminar_flow", "coherent_flow"):
            # Fluxo laminar: componente dominante na direção x, perturbação mínima em y
            vector[0] = abs(vector[0]) * self.strength  # fluxo unidirecional positivo
            vector[1] *= 0.1  # turbulência lateral suprimida
            vector[2] *= 0.05

        elif self.signature in ("oscillatory_wave", "pulsing_wave"):
            # Modulação periódica em amplitude
            wave_cycle = np.sin(time * 2.5) * 0.5 + 0.5
            vector *= (0.3 + wave_cycle * 0.7)

        elif self.signature == "convergence_field":
            # Atração suave para o centro (sem rotação, apenas puxão radial)
            dist = np.sqrt(x*x + y*y) + 0.01
            pull_vec = np.array([-x, -y, 0]) / dist
            vector = vector * 0.3 + pull_vec * self.strength * 0.7

        elif self.signature == "fragmented_noise":
            # Vetores quebrados: inversão abrupta baseada em posição fracionária
            if (int(abs(x) * 4) + int(abs(y) * 4)) % 2 == 0:
                vector *= -0.8

        elif self.signature == "chaotic_burst":
            # Explosivo: magnitude amplificada em pulsos rápidos irregulares
            burst = abs(np.sin(time * 7.3 + x * 2.1)) ** 0.4
            vector *= (0.5 + burst * 2.0)

        elif self.signature == "scattered_to_aligned":
            # Começa caótico (t=0) e converge para fluxo laminar com o tempo
            alignment = min(time / 5.0, 1.0)  # alinha completamente em ~5s
            laminar_vec = np.array([self.strength, 0.0, 0.0])
            vector = vector * (1.0 - alignment) + laminar_vec * alignment

        return vector

    def get_scalar(self, x: float, y: float, time: float = 0.0) -> float:
        """Valor escalar em (x, y) — útil para colorização por intensidade."""
        if _HAS_SIMPLEX:
            return self._fbm(self._nx, x, y, 0.0, time)
        return float(np.sin(x * 1.3 + time) * np.cos(y * 0.9 - time * 0.7))

    def warp_point(self, point, time: float = 0.0, scale: float = 1.0) -> np.ndarray:
        """Domain warping: aplica dois passos FBM para turbulência mais complexa."""
        p = np.array(point, dtype=float)
        v1 = self.get_vector(p, time)
        v2 = self.get_vector(p + v1 * scale, time + 1.7)
        return p + v2 * scale

    @property
    def engine(self) -> str:
        return "opensimplex_fbm" if _HAS_SIMPLEX else "harmonic_fallback"


def get_physics_preset(signature: str) -> dict:
    """
    Retorna configuração de PhysicsBody + campos para a Motion Signature.

    Cada preset define:
      - "noise_field": instância de AIOXNoiseField calibrada
      - "mass": float — inércia da partícula (maior = mais resistente a forças)
      - "damping": float — coeficiente de amortecimento (0=sem atrito, 1=parado)
      - "gravity": float — aceleração gravitacional (negativa = anti-gravidade)
      - "max_speed": float — velocidade máxima permitida
      - "repulsion_radius": float — raio de repulsão entre partículas
      - "description": str — intenção física do preset
    """
    presets = {
        "vortex_pull": {
            "noise_field": AIOXNoiseField(signature="vortex_pull"),
            "mass": 0.8,
            "damping": 0.05,
            "gravity": 0.0,
            "max_speed": 4.0,
            "repulsion_radius": 0.3,
            "description": "Partículas orbitam um atrator central com pouco atrito",
        },
        "elastic_snap": {
            "noise_field": AIOXNoiseField(signature="elastic_snap"),
            "mass": 0.3,
            "damping": 0.6,
            "gravity": 0.0,
            "max_speed": 12.0,
            "repulsion_radius": 0.1,
            "description": "Partículas leves disparam e freiam abruptamente — snap elástico",
        },
        "chaotic_burst": {
            "noise_field": AIOXNoiseField(signature="chaotic_burst"),
            "mass": 0.5,
            "damping": 0.02,
            "gravity": -0.1,
            "max_speed": 15.0,
            "repulsion_radius": 0.05,
            "description": "Explosão caótica com quase nenhum amortecimento e anti-gravidade leve",
        },
        "laminar_flow": {
            "noise_field": AIOXNoiseField(signature="laminar_flow"),
            "mass": 1.5,
            "damping": 0.4,
            "gravity": 0.0,
            "max_speed": 1.0,
            "repulsion_radius": 0.5,
            "description": "Fluxo suave e ordenado — partículas pesadas com alto amortecimento",
        },
        "coherent_flow": {
            "noise_field": AIOXNoiseField(signature="coherent_flow"),
            "mass": 1.5,
            "damping": 0.4,
            "gravity": 0.0,
            "max_speed": 1.0,
            "repulsion_radius": 0.5,
            "description": "Alias de laminar_flow — mesma física, nome semântico para entropy_interpreter",
        },
        "convergence_field": {
            "noise_field": AIOXNoiseField(signature="convergence_field"),
            "mass": 1.0,
            "damping": 0.15,
            "gravity": 0.0,
            "max_speed": 2.5,
            "repulsion_radius": 0.2,
            "description": "Partículas são atraídas suavemente para o centro sem rotação intensa",
        },
        "oscillatory_wave": {
            "noise_field": AIOXNoiseField(signature="oscillatory_wave"),
            "mass": 0.9,
            "damping": 0.1,
            "gravity": 0.0,
            "max_speed": 3.0,
            "repulsion_radius": 0.35,
            "description": "Partículas oscilam periodicamente — amortecimento baixo para manter ritmo",
        },
        "pulsing_wave": {
            "noise_field": AIOXNoiseField(signature="pulsing_wave"),
            "mass": 0.9,
            "damping": 0.1,
            "gravity": 0.0,
            "max_speed": 3.0,
            "repulsion_radius": 0.35,
            "description": "Alias de oscillatory_wave — nome semântico para entropy_interpreter",
        },
        "chaotic_dispersion": {
            "noise_field": AIOXNoiseField(signature="chaotic_dispersion"),
            "mass": 0.6,
            "damping": 0.03,
            "gravity": 0.05,
            "max_speed": 10.0,
            "repulsion_radius": 0.08,
            "description": "Dispersão tempestuosa com leve gravidade e quase sem atrito",
        },
        "fragmented_noise": {
            "noise_field": AIOXNoiseField(signature="fragmented_noise"),
            "mass": 0.4,
            "damping": 0.35,
            "gravity": 0.0,
            "max_speed": 6.0,
            "repulsion_radius": 0.15,
            "description": "Fragmentos que se movem em direções abruptas com amortecimento moderado",
        },
        "scattered_to_aligned": {
            "noise_field": AIOXNoiseField(signature="scattered_to_aligned"),
            "mass": 1.1,
            "damping": 0.2,
            "gravity": 0.0,
            "max_speed": 4.5,
            "repulsion_radius": 0.25,
            "description": "Inicia caótico e converge — massa média para transição gradual",
        },
        "breathing_field": {
            "noise_field": AIOXNoiseField(signature="breathing_field"),
            "mass": 2.0,
            "damping": 0.5,
            "gravity": 0.0,
            "max_speed": 0.8,
            "repulsion_radius": 0.6,
            "description": "Expansão calma e cíclica — partículas pesadas e muito amortecidas",
        },
    }

    if signature in presets:
        return presets[signature]

    # Fallback genérico para assinaturas desconhecidas
    return {
        "noise_field": AIOXNoiseField(signature=signature),
        "mass": 1.0,
        "damping": 0.2,
        "gravity": 0.0,
        "max_speed": 5.0,
        "repulsion_radius": 0.3,
        "description": f"Preset genérico para assinatura desconhecida: {signature}",
    }
