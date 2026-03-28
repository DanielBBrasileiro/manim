import re
from manim import Dot, Line, VGroup
from .theme_loader import theme

def parse_css_color(color_str):
    """Traduz cores CSS (rgba) para o formato nativo do Manim (Hex, Alpha)"""
    if color_str.startswith("rgba"):
        match = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)", color_str)
        if match:
            r, g, b = map(int, match.groups()[:3])
            a = float(match.group(4)) if match.group(4) else 1.0
            # Converte RGB para Hexadecimal
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            return hex_color, a
    return color_str, 1.0

class AIOXDot(Dot):
    """Ponto base que respeita o tema automaticamente."""
    def __init__(self, is_accent=False, **kwargs):
        raw_color = theme.accent_color if is_accent else theme.colors["foreground"]
        hex_color, alpha = parse_css_color(raw_color)
        super().__init__(color=hex_color, fill_opacity=alpha, **kwargs)

class AIOXLine(Line):
    """Linha que usa os stroke_widths e cores do contrato."""
    def __init__(self, start, end, weight="primary", **kwargs):
        raw_color = theme.colors["stroke"]
        hex_color, alpha = parse_css_color(raw_color)
        stroke_width = theme.materials["stroke_width"].get(weight, 1.5)
        super().__init__(start, end, color=hex_color, stroke_opacity=alpha, stroke_width=stroke_width, **kwargs)

class NeuralGrid(VGroup):
    """Grid procedural inspirado no vídeo de benchmark."""
    def __init__(self, rows=5, cols=5, spacing=1.0, **kwargs):
        super().__init__(**kwargs)
        for r in range(rows):
            for c in range(cols):
                dot = AIOXDot(radius=0.05).move_to([c * spacing - (cols*spacing)/2, r * spacing - (rows*spacing)/2, 0])
                self.add(dot)
