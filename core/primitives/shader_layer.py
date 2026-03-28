"""
AIOX Shader Layer — v4.4
=========================
Renderização GLSL via moderngl (headless) com fallback numpy para ambientes
sem GPU. Estratégia Option C: bake shader → texture → Manim ImageMobject.

Shaders incluídos:
  FBM_FIELD         — campo de turbulência Fractal Brownian Motion
  SDF_SHAPES        — primitivos geométricos via Signed Distance Fields
  CHROMATIC_ABBR    — aberração cromática (pré-composição, sem pós-proc.)

Uso em Manim:
    layer = ShaderLayer(1920, 1080, ShaderLayer.FBM_FIELD)
    img = layer.to_image_mobject(time=0.0, uniforms={"u_entropy": 0.7})
    self.add(img)
    self.add_updater(lambda _, dt: img.become(
        layer.to_image_mobject(time=layer.t + dt)
    ))
"""
import numpy as np
from pathlib import Path

try:
    import moderngl
    _HAS_MGL = True
except ImportError:
    _HAS_MGL = False

# ── GLSL Shaders ─────────────────────────────────────────────────────────────

_VERT = """
#version 330
in vec2 in_vert;
out vec2 v_uv;
void main() {
    v_uv = in_vert * 0.5 + 0.5;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
"""

# --- FBM Field: turbulência procedural orgânica ---
FBM_FIELD = """
#version 330
uniform float u_time;
uniform float u_entropy;    // 0.0–1.0
uniform vec2  u_resolution;
in  vec2 v_uv;
out vec4 frag_color;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1,0)), u.x),
               mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), u.x), u.y);
}

float fbm(vec2 p, int octaves) {
    float v = 0.0, amp = 0.5, freq = 1.0;
    for (int i = 0; i < 8; i++) {
        if (i >= octaves) break;
        v   += amp * noise(p * freq + u_time * 0.2);
        amp  *= 0.5;
        freq *= 2.0;
    }
    return v;
}

void main() {
    vec2 uv = v_uv;
    float ar = u_resolution.x / u_resolution.y;
    uv.x *= ar;

    int oct = int(mix(1.0, 7.0, u_entropy));
    float n = fbm(uv * 2.5, oct);

    // Domain warp para mais complexidade
    vec2 q = vec2(fbm(uv + vec2(0.0, 0.0), oct),
                  fbm(uv + vec2(5.2, 1.3), oct));
    float r = fbm(uv + 4.0 * q + u_time * 0.1, oct);

    // Monochrome — respeitando brand palette
    float lum = mix(0.0, r, u_entropy * 0.85 + 0.05);
    frag_color = vec4(vec3(lum), lum * 0.9);
}
"""

# --- SDF Shapes: primitivos geométricos perfeitos ---
SDF_SHAPES = """
#version 330
uniform float u_time;
uniform vec2  u_resolution;
uniform float u_stroke_width;  // 0.002–0.008
uniform int   u_shape;         // 0=circle 1=line 2=rect 3=cross 4=ring
in  vec2 v_uv;
out vec4 frag_color;

float sdf_circle(vec2 p, float r) { return length(p) - r; }

float sdf_line(vec2 p, vec2 a, vec2 b) {
    vec2 pa = p - a, ba = b - a;
    float h = clamp(dot(pa,ba)/dot(ba,ba), 0.0, 1.0);
    return length(pa - ba*h);
}

float sdf_rect(vec2 p, vec2 b) {
    vec2 d = abs(p) - b;
    return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
}

float sdf_ring(vec2 p, float r1, float r2) {
    float d = length(p);
    return max(d - r2, r1 - d);
}

float stroke(float d, float w) {
    return 1.0 - smoothstep(0.0, w, abs(d));
}

void main() {
    vec2 uv = (v_uv - 0.5);
    float ar = u_resolution.x / u_resolution.y;
    uv.x *= ar;

    float d = 1e9;
    float sw = u_stroke_width;

    if (u_shape == 0) d = sdf_circle(uv, 0.28);
    else if (u_shape == 1) d = sdf_line(uv, vec2(-0.35, 0.0), vec2(0.35, 0.0));
    else if (u_shape == 2) d = sdf_rect(uv, vec2(0.32, 0.20));
    else if (u_shape == 3) {
        d = min(sdf_line(uv, vec2(-0.3, 0.0), vec2(0.3, 0.0)),
                sdf_line(uv, vec2(0.0, -0.3), vec2(0.0, 0.3)));
    }
    else if (u_shape == 4) d = sdf_ring(uv, 0.22, 0.30);

    // Pulse suave baseado no tempo
    float pulse = 1.0 + 0.04 * sin(u_time * 2.1);
    d /= pulse;

    float alpha = stroke(d, sw);

    // Opacidade respira (brand: grain + breath)
    float breath = 0.85 + 0.1 * sin(u_time * 1.3);
    frag_color = vec4(1.0, 1.0, 1.0, alpha * breath);
}
"""

# --- Chromatic Aberration: efeito lente pré-composição ---
CHROMATIC_ABBR = """
#version 330
uniform sampler2D u_texture;
uniform float u_strength;   // 0.002–0.012
uniform float u_time;
in  vec2 v_uv;
out vec4 frag_color;

void main() {
    vec2 uv  = v_uv;
    vec2 dir = uv - 0.5;
    float dist = length(dir);

    // Aberração aumenta radialmente (como lente real)
    float s = u_strength * dist * dist * 4.0;

    // Offset temporal leve para micro-tremor orgânico
    float jitter = sin(u_time * 17.3) * 0.0002;

    vec2 r_uv = uv + dir * (s + jitter);
    vec2 b_uv = uv - dir * (s - jitter);

    float r = texture(u_texture, r_uv).r;
    float g = texture(u_texture, uv).g;
    float b = texture(u_texture, b_uv).b;
    float a = texture(u_texture, uv).a;

    frag_color = vec4(r, g, b, a);
}
"""


# ── ShaderLayer ───────────────────────────────────────────────────────────────

class ShaderLayer:
    """
    Renderiza GLSL fragment shaders em textura numpy/PNG.
    Requer moderngl; fallback para numpy se indisponível.

    Args:
        width, height:  Dimensões da textura de saída.
        shader_src:     Código GLSL do fragment shader (use constantes acima).
    """

    FBM_FIELD = FBM_FIELD
    SDF_SHAPES = SDF_SHAPES
    CHROMATIC_ABBR = CHROMATIC_ABBR

    def __init__(self, width: int = 1920, height: int = 1080,
                 shader_src: str = None):
        self.width = width
        self.height = height
        self.shader_src = shader_src or FBM_FIELD
        self.t = 0.0
        self._ctx = None
        self._prog = None
        self._fbo = None
        self._vao = None

        if _HAS_MGL:
            self._init_gl()

    def _init_gl(self):
        try:
            self._ctx = moderngl.create_standalone_context()
            self._prog = self._ctx.program(
                vertex_shader=_VERT,
                fragment_shader=self.shader_src,
            )
            # Full-screen quad
            vertices = np.array([
                -1.0, -1.0,  1.0, -1.0,
                -1.0,  1.0,  1.0,  1.0,
            ], dtype="f4")
            vbo = self._ctx.buffer(vertices.tobytes())
            self._vao = self._ctx.simple_vertex_array(
                self._prog, vbo, "in_vert"
            )
            self._fbo = self._ctx.simple_framebuffer((self.width, self.height))
        except Exception as e:
            print(f"⚠️  ShaderLayer: moderngl init falhou ({e}). Usando fallback numpy.")
            self._ctx = None

    def render(self, time: float = None, uniforms: dict = None) -> np.ndarray:
        """
        Renderiza um frame e retorna array RGBA (H, W, 4) uint8.

        Args:
            time:     Tempo em segundos.
            uniforms: Dict com valores para os uniforms do shader.
        Returns:
            numpy array RGBA (height, width, 4)
        """
        if time is not None:
            self.t = time

        u = uniforms or {}

        if _HAS_MGL and self._ctx is not None:
            return self._render_gl(u)
        return self._render_fallback(u)

    def _render_gl(self, uniforms: dict) -> np.ndarray:
        self._fbo.use()
        self._ctx.clear(0.0, 0.0, 0.0, 0.0)

        # Injetar uniforms
        def _set(name, val):
            if name in self._prog:
                try:
                    self._prog[name].value = val
                except Exception:
                    pass

        _set("u_time", float(self.t))
        _set("u_resolution", (float(self.width), float(self.height)))
        for k, v in uniforms.items():
            _set(k, v)

        self._vao.render(moderngl.TRIANGLE_STRIP)
        raw = self._fbo.read(components=4)
        arr = np.frombuffer(raw, dtype=np.uint8).reshape(self.height, self.width, 4)
        return np.flipud(arr)  # OpenGL origin é bottom-left

    def _render_fallback(self, uniforms: dict) -> np.ndarray:
        """Fallback numpy: FBM analítico sem GPU."""
        entropy = float(uniforms.get("u_entropy", 0.5))
        h, w = self.height, self.width
        y, x = np.meshgrid(
            np.linspace(-1, 1, h),
            np.linspace(-1, 1, w),
            indexing="ij"
        )
        t = self.t
        octaves = int(np.interp(entropy, [0, 1], [1, 5]))
        val = np.zeros((h, w))
        amp, freq = 0.5, 1.0
        for _ in range(octaves):
            val += amp * (
                np.sin(x * freq * 3.1 + t * 0.4) *
                np.cos(y * freq * 2.7 - t * 0.3)
            )
            amp *= 0.5
            freq *= 2.0

        val = (val - val.min()) / (val.max() - val.min() + 1e-8)
        val = (val * 255 * (entropy * 0.8 + 0.1)).clip(0, 255).astype(np.uint8)
        rgba = np.stack([val, val, val, (val * 0.9).astype(np.uint8)], axis=-1)
        return rgba

    def save_png(self, path: str, time: float = None, uniforms: dict = None) -> str:
        """Renderiza e salva como PNG."""
        try:
            from PIL import Image
        except ImportError:
            raise ImportError("Pillow não instalado: pip install Pillow")
        arr = self.render(time, uniforms)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(arr, "RGBA").save(path)
        return path

    def to_image_mobject(self, time: float = None, uniforms: dict = None):
        """Renderiza e retorna Manim ImageMobject."""
        try:
            from manim import ImageMobject
            import tempfile, os
        except ImportError:
            raise ImportError("manim não está no PYTHONPATH")

        tmp = tempfile.mktemp(suffix=".png", prefix="aiox_shader_")
        self.save_png(tmp, time, uniforms)
        img = ImageMobject(tmp)
        try:
            os.unlink(tmp)
        except Exception:
            pass
        return img

    def render_sequence(
        self,
        output_dir: str,
        duration: float,
        fps: int = 60,
        uniforms_fn=None,
    ) -> list:
        """
        Renderiza sequência de frames PNG para um vídeo de shader.

        Args:
            output_dir:  Diretório para os PNGs.
            duration:    Duração em segundos.
            fps:         Frames por segundo.
            uniforms_fn: Função (t) -> dict de uniforms por frame.
        Returns:
            Lista de caminhos PNG gerados.
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        n_frames = int(duration * fps)
        paths = []

        print(f"🎨 ShaderLayer: renderizando {n_frames} frames ({duration}s @ {fps}fps)...")
        for i in range(n_frames):
            t = i / fps
            u = uniforms_fn(t) if uniforms_fn else {}
            path = str(out_dir / f"frame_{i:05d}.png")
            self.save_png(path, time=t, uniforms=u)
            paths.append(path)

        print(f"✅ {n_frames} frames → {out_dir}")
        return paths

    def __del__(self):
        if _HAS_MGL and self._ctx is not None:
            try:
                self._fbo.release()
                self._vao.release()
                self._prog.release()
                self._ctx.release()
            except Exception:
                pass

    @property
    def engine(self) -> str:
        return "moderngl_glsl" if (_HAS_MGL and self._ctx) else "numpy_fallback"
