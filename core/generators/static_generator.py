"""
AIOX Studio — Static Content Generator
=======================================
Generates static visual content (posts, thumbnails, posters, carousels)
by rendering HTML/React → taking a screenshot with Playwright/Puppeteer.

Usage:
    python3 core/generators/static_generator.py --brief briefings/post.yaml

Flow:
    1. Read briefing YAML
    2. Load format template (dimensions, safe zones)
    3. Load style preset (palette, typography, composition)
    4. Load reference overrides (if any)
    5. Generate HTML from template
    6. Screenshot with Playwright
    7. Export to output/
"""
import yaml
import json
import os
import sys
import subprocess
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def resolve_style(brief):
    """Load style preset, with optional reference overrides."""
    style_id = brief.get("meta", {}).get("style", "monochrome_cinema")
    
    # Base style
    style_path = ROOT / f"templates/styles/{style_id}.yaml"
    if style_path.exists():
        style = load_yaml(style_path)
    else:
        style = load_yaml(ROOT / "templates/styles/monochrome_cinema.yaml")
    
    # Reference overrides
    ref_id = brief.get("meta", {}).get("reference")
    if ref_id:
        ref_path = ROOT / f"contracts/references/{ref_id}.yaml"
        if ref_path.exists():
            ref = load_yaml(ref_path)
            # Override palette and typography from reference
            if brief.get("overrides", {}).get("palette_mode") == "reference":
                style["palette"].update(ref.get("palette", {}))
            if brief.get("overrides", {}).get("typography_mode") == "reference":
                style["typography"].update(ref.get("typography", {}))
    
    return style


def resolve_format(brief):
    """Load format template for dimensions and export settings."""
    fmt_id = brief.get("meta", {}).get("format", "linkedin_post")
    fmt_path = ROOT / f"templates/formats/{fmt_id}.yaml"
    if fmt_path.exists():
        return load_yaml(fmt_path)
    return {"dimensions": {"width": 1080, "height": 1350}, "export": {"format": "png"}}


def generate_html(brief, style, fmt):
    """Generate the HTML that will be screenshotted."""
    dims = fmt["dimensions"]
    narrative = brief.get("narrative", {})
    content = narrative.get("content", {})
    
    headline = content.get("headline", "")
    subline = content.get("subline", "")
    accent_element = content.get("accent_element", "")
    
    pal = style.get("palette", {})
    typo = style.get("typography", {})
    comp = style.get("composition", {})
    
    bg = pal.get("background", "#000000")
    fg = pal.get("text_primary", pal.get("foreground", "#FFFFFF"))
    fg2 = pal.get("text_secondary", "rgba(255,255,255,0.55)")
    accent = pal.get("accent", fg)
    
    h_family = typo.get("heading", {}).get("family", "Helvetica Neue, sans-serif")
    h_weight = typo.get("heading", {}).get("weight", 600)
    h_tracking = typo.get("heading", {}).get("tracking", "-0.02em")
    
    b_family = typo.get("body", typo.get("narrative", {})).get("family", h_family)
    b_weight = typo.get("body", typo.get("narrative", {})).get("weight", 400)
    
    breathing = comp.get("border_breathing", "64px")
    grain = style.get("effects", {}).get("grain", 0)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  
  body {{
    width: {dims['width']}px;
    height: {dims['height']}px;
    background: {bg};
    color: {fg};
    font-family: {b_family};
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: {breathing};
    overflow: hidden;
    position: relative;
  }}
  
  .headline {{
    font-family: {h_family};
    font-weight: {h_weight};
    font-size: clamp(2rem, 5vw, 3.5rem);
    letter-spacing: {h_tracking};
    line-height: 1.15;
    max-width: 85%;
    margin-bottom: 24px;
  }}
  
  .subline {{
    font-weight: {b_weight};
    font-size: 1.125rem;
    line-height: 1.6;
    color: {fg2};
    max-width: 75%;
  }}
  
  .brand {{
    position: absolute;
    bottom: {breathing};
    right: {breathing};
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    opacity: 0.4;
    text-transform: uppercase;
  }}
  
  .accent-line {{
    position: absolute;
    top: 15%;
    right: 10%;
    width: 1px;
    height: 35%;
    background: {accent if accent else fg};
    opacity: 0.15;
  }}
  
  .grain {{
    position: absolute;
    inset: 0;
    opacity: {grain};
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
    mix-blend-mode: overlay;
    pointer-events: none;
  }}
</style>
</head>
<body>
  <div class="headline">{{headline}}</div>
  <div class="subline">{{subline}}</div>
  <div class="brand">AIOX</div>
  <div class="accent-line"></div>
  <div class="grain"></div>
</body>
</html>"""
    return html.replace("{{headline}}", headline).replace("{{subline}}", subline)


def generate(brief_path):
    brief = load_yaml(brief_path)
    style = resolve_style(brief)
    fmt = resolve_format(brief)
    
    dims = fmt["dimensions"]
    title = brief.get("meta", {}).get("title", "untitled")
    safe_title = title.lower().replace(" ", "_")[:40]
    
    print(f"📐 Format: {dims['width']}x{dims['height']}")
    print(f"🎨 Style: {style.get('name', 'custom')}")
    
    # Generate HTML
    html = generate_html(brief, style, fmt)
    
    # Write temp HTML
    tmp_html = f"/tmp/aiox_{safe_title}.html"
    with open(tmp_html, "w") as f:
        f.write(html)
    print(f"📄 HTML \u2192 {tmp_html}")
    
    # Screenshot via Playwright
    output_format = fmt.get("export", {}).get("format", "png")
    output_dir = ROOT / "output" / "static"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_title}.{output_format}"

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(
                viewport={"width": dims["width"], "height": dims["height"]}
            )
            page.goto(f"file://{tmp_html}", wait_until="networkidle")
            page.wait_for_timeout(500)  # Allow fonts/grain to render
            screenshot_opts = {"path": str(output_path), "full_page": False}
            if output_format == "jpeg":
                screenshot_opts["type"] = "jpeg"
                screenshot_opts["quality"] = fmt.get("export", {}).get("quality", 92)
            page.screenshot(**screenshot_opts)
            browser.close()
        print(f"✅ Static export → {output_path}")
    except ImportError:
        print("⚠️  Playwright not installed. Run: pip install playwright && playwright install chromium")
        print(f"   HTML ready at: {tmp_html}")
    except Exception as e:
        print(f"❌ Screenshot failed: {e}")
        print(f"   HTML ready at: {tmp_html}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--brief", required=True)
    args = parser.parse_args()
    generate(args.brief)
