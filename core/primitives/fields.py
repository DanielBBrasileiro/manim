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
