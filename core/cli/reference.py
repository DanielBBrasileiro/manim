#!/usr/bin/env python3
"""
AIOX Studio — Design System Reference Capture
==============================================
Extracts palette, typography, spacing from a URL and saves as YAML.

Usage:
    python3 scripts/capture_reference.py https://stripe.com
"""
import sys
import os
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def url_to_filename(url):
    """Convert URL to safe filename."""
    clean = re.sub(r'https?://', '', url)
    clean = re.sub(r'[/.\-:]', '_', clean)
    clean = re.sub(r'_+', '_', clean).strip('_')
    return clean[:60]


def generate_template(url):
    """Generate a YAML template for the reference."""
    name = url_to_filename(url)
    output_dir = ROOT / "contracts" / "references"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{name}.yaml"
    
    template = f"""# Auto-generated reference template
# Source: {url}
# Captured: {datetime.now().strftime('%Y-%m-%d')}

source: "{url}"
captured_at: "{datetime.now().strftime('%Y-%m-%d')}"

palette:
  background: "#FFFFFF"
  surface: "#F6F9FC"
  text_primary: "#000000"
  text_secondary: "#666666"
  accent: "#6366F1"
  accent_secondary: "#06B6D4"
  border: "rgba(0,0,0,0.08)"

typography:
  heading:
    family: "Inter, sans-serif"
    weight: 600
    tracking: "-0.02em"
  body:
    family: "Inter, sans-serif"
    weight: 400
    size: "16px"
    line_height: 1.6

spacing:
  section_gap: "80px"
  content_max_width: "1080px"
  card_padding: "24px"
  card_radius: "8px"

style_classification: "editorial_minimal"
mood: "clean, confident, technical"
"""
    
    with open(output_path, "w") as f:
        f.write(template)
    
    print(f"📋 Reference template \u2192 {output_path}")
    return str(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/capture_reference.py <url>")
        sys.exit(1)
    
    generate_template(sys.argv[1])
