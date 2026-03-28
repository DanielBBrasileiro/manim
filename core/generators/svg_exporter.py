"""
AIOX Studio — SVG Exporter
============================
Exporta composições visuais como SVG vetorial a partir de:
  - Briefing YAML (narrativa + tipografia)
  - Frame PNG existente (trace via potrace)
  - HTML gerado pelo static_generator

Output: SVG escalável para web, apresentações e impressão.

Usage standalone:
    python3 core/generators/svg_exporter.py --brief briefings/post.yaml
    python3 core/generators/svg_exporter.py --png output/static/post.png
"""
import os
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def _load_tokens() -> dict:
    token_path = ROOT / "assets/brand/tokens.json"
    if token_path.exists():
        with open(token_path) as f:
            return json.load(f)
    return {}


def _load_yaml(path: str) -> dict:
    import yaml
    with open(path) as f:
        return yaml.safe_load(f)


def export_from_brief(brief_path: str, output_path: str = None) -> str:
    """
    Gera SVG a partir de um briefing YAML.
    Usa drawsvg para composição vetorial pura.

    Returns: caminho do SVG gerado.
    """
    try:
        import drawsvg as draw
    except ImportError:
        raise ImportError("drawsvg não instalado. Execute: pip install drawsvg")

    brief = _load_yaml(brief_path)
    tokens = _load_tokens()

    meta = brief.get("meta", {})
    fmt_id = meta.get("format", "square_1_1")

    # Dimensões a partir do formato
    fmt_dims = {
        "square_1_1": (1080, 1080),
        "vertical_9_16": (1080, 1920),
        "wide_16_9": (1920, 1080),
        "instagram_post": (1080, 1080),
        "linkedin_post": (1200, 627),
        "twitter_thumbnail": (1200, 675),
    }
    w, h = fmt_dims.get(fmt_id, (1080, 1080))

    # Cores do tokens.json
    color_states = tokens.get("brand", {}).get("color_states", {})
    dark = color_states.get("dark", {})
    bg = dark.get("background", "#000000")
    fg = dark.get("foreground", "#FFFFFF")
    fg2 = dark.get("text_secondary", "rgba(255,255,255,0.55)")
    accent = color_states.get("accent", {}).get("color", "#FF3366")

    # Conteúdo narrativo
    narrative = brief.get("narrative", {})
    content = narrative.get("content", {})
    headline = content.get("headline", "")
    subline = content.get("subline", "")

    # Grain/materiais
    grain = tokens.get("brand", {}).get("materials", {}).get("grain", 0.06)
    stroke_primary = tokens.get("brand", {}).get("materials", {}).get("stroke_width", {}).get("primary", 1.5)

    d = draw.Drawing(w, h)

    # Background
    d.append(draw.Rectangle(0, 0, w, h, fill=bg))

    # Grain texture via SVG filter
    if grain > 0:
        filt = draw.Filter(id="grain_filter")
        filt.append(draw.Raw(
            f'<feTurbulence type="fractalNoise" baseFrequency="0.65" '
            f'numOctaves="3" stitchTiles="stitch"/>'
            f'<feColorMatrix type="saturate" values="0"/>'
        ))
        d.append(filt)
        d.append(draw.Rectangle(
            0, 0, w, h,
            fill="white",
            fill_opacity=grain,
            filter="url(#grain_filter)"
        ))

    # Linha de respiro (accent line — máx 2% da tela)
    d.append(draw.Line(
        w * 0.88, h * 0.12,
        w * 0.88, h * 0.45,
        stroke=fg, stroke_width=stroke_primary * 0.5, stroke_opacity=0.15
    ))

    # Headline
    if headline:
        padding = int(w * 0.06)
        d.append(draw.Text(
            headline,
            fontSize=int(w * 0.055),
            x=padding, y=int(h * 0.42),
            fill=fg,
            font_family="Helvetica Neue, Inter, sans-serif",
            font_weight="600",
            letter_spacing="-0.02em",
        ))

    # Subline
    if subline:
        padding = int(w * 0.06)
        d.append(draw.Text(
            subline,
            fontSize=int(w * 0.022),
            x=padding, y=int(h * 0.50),
            fill=fg2,
            font_family="Helvetica Neue, Inter, sans-serif",
            font_weight="300",
        ))

    # Brand signature
    d.append(draw.Text(
        "AIOX",
        fontSize=int(w * 0.015),
        x=w - int(w * 0.06), y=h - int(h * 0.04),
        fill=fg, fill_opacity=0.4,
        font_family="Helvetica Neue, sans-serif",
        font_weight="500",
        letter_spacing="0.1em",
        text_anchor="end",
    ))

    title = meta.get("title", "untitled")
    safe_title = title.lower().replace(" ", "_")[:40]
    out_path = Path(output_path) if output_path else ROOT / "output" / "svg" / f"{safe_title}.svg"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    d.save_svg(str(out_path))

    print(f"✅ SVG gerado → {out_path}")
    return str(out_path)


def export_from_png(png_path: str, output_path: str = None) -> str:
    """
    Converte PNG em SVG vetorial via potrace (trace de bitmap).
    Útil para exportar frames Manim como SVG.

    Requer: potrace (brew install potrace) + ImageMagick (brew install imagemagick)
    """
    if not shutil.which("potrace"):
        raise EnvironmentError(
            "potrace não encontrado. Execute: brew install potrace"
        )
    if not shutil.which("magick") and not shutil.which("convert"):
        raise EnvironmentError(
            "ImageMagick não encontrado. Execute: brew install imagemagick"
        )

    png = Path(png_path)
    bmp_path = png.with_suffix(".bmp")
    out_path = Path(output_path) if output_path else png.with_suffix(".svg")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    convert_cmd = "magick" if shutil.which("magick") else "convert"
    print(f"🔄 Convertendo PNG → BMP para trace...")
    subprocess.run(
        [convert_cmd, str(png), str(bmp_path)],
        check=True, capture_output=True
    )

    print(f"✏️  Traçando BMP → SVG (potrace)...")
    subprocess.run(
        ["potrace", "--svg", "-o", str(out_path), str(bmp_path)],
        check=True, capture_output=True
    )
    bmp_path.unlink(missing_ok=True)

    print(f"✅ SVG vetorial → {out_path}")
    return str(out_path)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AIOX SVG Exporter")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--brief", help="Briefing YAML")
    group.add_argument("--png", help="PNG para vetorizar")
    parser.add_argument("--output", help="Caminho de saída .svg")
    args = parser.parse_args()

    if args.brief:
        export_from_brief(args.brief, args.output)
    else:
        export_from_png(args.png, args.output)
