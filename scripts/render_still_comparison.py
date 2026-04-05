#!/usr/bin/env python3
import argparse
import copy
import json
import subprocess
from pathlib import Path

import yaml

try:
    from playwright.sync_api import sync_playwright
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"Playwright Python package is required: {exc}")

ROOT = Path(__file__).resolve().parent.parent
BRIEFING_PATH = ROOT / "briefings" / "creative_seed.yaml"
ENTRY_POINT = ROOT / "engines" / "remotion" / "debug" / "still-comparison-page.tsx"
REMOTION_SHIM = ROOT / "engines" / "remotion" / "debug" / "remotion-still-shim.tsx"
ESBUILD_BIN = ROOT / "engines" / "remotion" / "node_modules" / "@esbuild" / "darwin-arm64" / "bin" / "esbuild"
OUTPUT_DIR = ROOT / "output" / "stills" / "comparison_2026_04_02"
BUNDLE_JS = OUTPUT_DIR / "still-comparison.js"
DEFAULT_PACKS = [
    "silent_luxury",
    "signal_burst",
    "carbon_authority",
    "data_ink",
]
VIEWPORT = {"width": 1080, "height": 1350}


def load_briefing_story_atoms() -> dict:
    with BRIEFING_PATH.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    seed = copy.deepcopy(raw.get("creative_seed") or raw)
    title = seed.get("title") or "Invisible Architecture"
    tagline = seed.get("tagline") or "Pressure becomes signal"
    thesis = seed.get("thesis") or "Systems become premium when pressure becomes readable"
    resolve_word = seed.get("resolve_word") or seed.get("resolveWord") or "Signal"

    return {
        "title": title,
        "tagline": tagline,
        "thesis": thesis,
        "resolve_word": resolve_word,
    }


def build_props(style_pack: str, story_atoms: dict) -> dict:
    return {
        "target": "linkedin_feed_4_5",
        "renderManifest": {
            "target": "linkedin_feed_4_5",
            "targetId": "linkedin_feed_4_5",
            "targetKind": "still",
            "width": VIEWPORT["width"],
            "height": VIEWPORT["height"],
            "style_pack": style_pack,
            "story_atoms": story_atoms,
            "summary": story_atoms.get("thesis"),
            "seed": f"comparison-{style_pack}",
            "frameOverride": 0,
            "stillFrame": 0,
        },
    }


def ensure_bundle() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(ESBUILD_BIN),
        str(ENTRY_POINT),
        "--bundle",
        "--platform=browser",
        "--format=iife",
        "--target=chrome120",
        f"--outfile={BUNDLE_JS}",
        f"--alias:remotion={REMOTION_SHIM}",
    ]
    subprocess.run(cmd, cwd=str(ROOT), check=True, timeout=120)
    if not BUNDLE_JS.exists() or BUNDLE_JS.stat().st_size == 0:
        raise RuntimeError(f"Failed to build still comparison bundle: {BUNDLE_JS}")


def write_html(style_pack: str, props: dict) -> Path:
    html_path = OUTPUT_DIR / f"test_{style_pack}.html"
    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AIOX Still Comparison {style_pack}</title>
    <style>
      html, body, #root {{
        margin: 0;
        width: {VIEWPORT["width"]}px;
        height: {VIEWPORT["height"]}px;
        overflow: hidden;
        background: #000;
      }}
      body {{
        position: relative;
      }}
    </style>
  </head>
  <body>
    <div id="root"></div>
    <script>
      window.__AIOX_STILL_PROPS__ = {json.dumps(props, ensure_ascii=False)};
    </script>
    <script src="./{BUNDLE_JS.name}"></script>
  </body>
</html>
"""
    html_path.write_text(html, encoding="utf-8")
    return html_path


def screenshot_html(html_path: Path, output_path: Path) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=1)
        page.goto(html_path.resolve().as_uri(), wait_until="load")
        page.wait_for_timeout(400)
        page.screenshot(path=str(output_path))
        browser.close()
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(f"Still screenshot failed: {output_path}")


def write_readme(results: list[dict]) -> Path:
    readme_path = OUTPUT_DIR / "README_comparison.md"
    lines = [
        "# AIOX Still Comparison",
        "",
        f"- Base briefing: `{BRIEFING_PATH}`",
        "- Target: `linkedin_feed_4_5`",
        "- Variable changed between runs: `style_pack` only",
        "- Render path: esbuild browser bundle + Playwright screenshot",
        "",
        "## Outputs",
    ]
    for item in results:
        lines.append(f"- `{item['style_pack']}` -> `{item['output_path']}`")
    readme_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return readme_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--style-pack", action="append", dest="style_packs")
    args = parser.parse_args()

    packs = args.style_packs or DEFAULT_PACKS
    story_atoms = load_briefing_story_atoms()
    ensure_bundle()

    results = []
    for style_pack in packs:
        props = build_props(style_pack, story_atoms)
        html_path = write_html(style_pack, props)
        output_path = OUTPUT_DIR / f"test_{style_pack}.png"
        screenshot_html(html_path, output_path)
        results.append(
            {
                "style_pack": style_pack,
                "output_path": str(output_path),
                "html_path": str(html_path),
            }
        )

    readme_path = write_readme(results)
    print(
        json.dumps(
            {
                "briefing_used": str(BRIEFING_PATH),
                "bundle_path": str(BUNDLE_JS),
                "results": results,
                "readme_path": str(readme_path),
                "all_ok": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
