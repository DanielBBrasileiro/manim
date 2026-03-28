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

    entropy: 0.0 = vento calmo e suave | 1.0 = tempestade caótica orgânica
    seed:    None = único a cada render | int = determinístico (entropy ≤ 0.2)
    """

    def __init__(self, entropy: float = 0.5, seed: int = None):
        self.entropy = entropy
        self.seed = seed

        # Complexidade = número de oitavas FBM
        self.octaves = int(np.interp(entropy, [0, 1], [1, 6]))
        self.strength = float(np.interp(entropy, [0, 1], [0.08, 2.8]))
        self.lacunarity = 2.0       # frequência dobra a cada oitava
        self.persistence = 0.5      # amplitude cai 50% a cada oitava

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
