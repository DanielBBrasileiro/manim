from manim import SVGMobject, ImageMobject, Group
from .theme_loader import theme
from .geometry import parse_css_color

class AIOXLogo(SVGMobject):
    """Importa SVGs e os submete às Leis de Design (Monocromático ou Accent)"""
    def __init__(self, file_path, style="monochrome", **kwargs):
        super().__init__(file_path, **kwargs)
        
        # Submete o logo à paleta de cores restrita para manter o visual premium
        if style == "monochrome":
            hex_color, alpha = parse_css_color(theme.colors["foreground"])
            self.set_color(hex_color)
            self.set_opacity(alpha)
        elif style == "accent":
            hex_color, alpha = parse_css_color(theme.accent_color)
            self.set_color(hex_color)
        
        # Remove preenchimentos originais que quebrem a estética flat
        self.set_fill(opacity=1 if style != "outline" else 0)
        if style == "outline":
            self.set_stroke(color=hex_color, width=theme.materials["stroke_width"]["secondary"])

class AIOXImage(ImageMobject):
    """Importa PNGs/JPGs. No Manim, imagens rasterizadas são raras em design premium,
    mas se necessárias, devem ser encapsuladas aqui para futura manipulação de opacidade."""
    def __init__(self, file_path, **kwargs):
        super().__init__(file_path, **kwargs)
        # Prepara para efeitos de fade in baseados no tema
