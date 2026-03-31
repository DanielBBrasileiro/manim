from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent.parent


def render_still_artifact(
    target: dict[str, Any],
    artifact_plan: dict[str, Any],
    output_path: str | Path,
    slide: dict[str, Any] | None = None,
) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    width = int(target.get("width", 1080) or 1080)
    height = int(target.get("height", 1350) or 1350)
    story_atoms = artifact_plan.get("story_atoms", {})
    style = _load_style_pack(artifact_plan)
    palette = style.get("palette", {})

    image = _vertical_gradient(
        (width, height),
        _hex(palette.get("background", "#050505")),
        _hex(palette.get("surface", "#0B0B0D")),
    )
    image = _add_texture(image)
    draw = ImageDraw.Draw(image)

    margin = int(width * 0.08)
    card = (
        margin,
        int(height * 0.12),
        width - margin,
        int(height * 0.84),
    )
    accent = _hex(palette.get("accent", "#F7F7F7"))
    border = _hex_from_rgba_like(palette.get("border", "rgba(255,255,255,0.14)"), fallback=(255, 255, 255, 30))
    draw.rounded_rectangle(card, radius=int(min(width, height) * 0.028), outline=border, width=2)
    draw.line((card[0], int(height * 0.27), card[2], int(height * 0.27)), fill=accent, width=1)

    kicker_font = _font(int(height * 0.03), weight="regular")
    title_font = _font(int(height * 0.072), weight="bold")
    body_font = _font(int(height * 0.036), weight="regular")
    resolve_font = _font(int(height * 0.05), weight="bold")

    title = str(slide.get("title") if slide else story_atoms.get("title") or target.get("label") or "AIOX")
    archetype = str(slide.get("archetype") if slide else target.get("purpose") or "artifact").replace("_", " ").upper()
    body = _body_text(target, artifact_plan, slide=slide)
    resolve_word = str(story_atoms.get("resolve_word") or "AIOX")

    draw.text((card[0], int(height * 0.18)), archetype, fill=accent, font=kicker_font)
    _draw_wrapped_text(draw, title, title_font, fill=(245, 245, 245), box=(card[0], int(height * 0.31), card[2], int(height * 0.52)), line_gap=14)
    _draw_wrapped_text(draw, body, body_font, fill=(210, 210, 215), box=(card[0], int(height * 0.58), card[2], int(height * 0.73)), line_gap=10)
    draw.text((card[0], int(height * 0.77)), resolve_word, fill=(250, 250, 250), font=resolve_font)

    image.save(output)
    return output


def render_carousel_artifact(
    target: dict[str, Any],
    artifact_plan: dict[str, Any],
    output_dir: str | Path,
) -> list[Path]:
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    slides = target.get("slides", [])
    if not isinstance(slides, list) or not slides:
        slides = [{"archetype": "cover", "title": target.get("label", "AIOX"), "text_blocks": [artifact_plan.get("story_atoms", {}).get("thesis", "")]}]

    rendered: list[Path] = []
    for index, slide in enumerate(slides, start=1):
        slide_path = output_root / f"slide_{index:02d}.png"
        render_still_artifact(target, artifact_plan, slide_path, slide=slide if isinstance(slide, dict) else None)
        rendered.append(slide_path)

    manifest_path = output_root / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "target": target.get("id"),
                "slides": [path.name for path in rendered],
                "count": len(rendered),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return rendered


def render_video_artifact(
    target: dict[str, Any],
    artifact_plan: dict[str, Any],
    output_path: str | Path,
    source_video: str | Path | None = None,
) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    if source_video:
        source = Path(source_video)
        if source.exists():
            shutil.copy2(source, output)
            return output

    with tempfile.TemporaryDirectory(prefix="aiox_video_fallback_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        target_id = str(target.get("id", "")).strip()
        panels: list[Path] = []
        durations: list[float] = []

        if target_id == "youtube_essay_16_9":
            chapters = target.get("chapters", [])
            if not isinstance(chapters, list) or not chapters:
                chapters = [{"archetype": "thesis", "label": artifact_plan.get("story_atoms", {}).get("thesis", "AIOX"), "seconds": 8}]
            for index, chapter in enumerate(chapters, start=1):
                slide = {
                    "archetype": chapter.get("archetype", "chapter"),
                    "title": chapter.get("label", f"Chapter {index}"),
                    "text_blocks": [chapter.get("label", "")],
                }
                panel = tmp_root / f"panel_{index:02d}.png"
                render_still_artifact(target, artifact_plan, panel, slide=slide)
                panels.append(panel)
                durations.append(float(chapter.get("seconds", 8) or 8))
        else:
            beats = target.get("beats", [])
            if not isinstance(beats, list) or not beats:
                beats = [{"label": "resolve", "text": artifact_plan.get("story_atoms", {}).get("resolve_word", "AIOX")}]
            duration_sec = float(target.get("duration_sec", 12) or 12)
            seconds_per_panel = max(2.0, duration_sec / max(len(beats), 1))
            for index, beat in enumerate(beats, start=1):
                slide = {
                    "archetype": beat.get("label", f"beat_{index}"),
                    "title": beat.get("text", beat.get("label", "AIOX")),
                    "text_blocks": [beat.get("text", beat.get("label", ""))],
                }
                panel = tmp_root / f"panel_{index:02d}.png"
                render_still_artifact(target, artifact_plan, panel, slide=slide)
                panels.append(panel)
                durations.append(seconds_per_panel)

        sequence_dir = tmp_root / "sequence"
        sequence_dir.mkdir(parents=True, exist_ok=True)
        frame_index = 1
        for path, seconds in zip(panels, durations):
            repeat_count = max(1, int(round(seconds)))
            for _ in range(repeat_count):
                frame_path = sequence_dir / f"frame_{frame_index:03d}.png"
                shutil.copy2(path, frame_path)
                frame_index += 1

        fps = int(target.get("fps", 30) or 30)
        subprocess.run(
            [
                shutil.which("ffmpeg") or "ffmpeg",
                "-y",
                "-framerate",
                "1",
                "-i",
                str(sequence_dir / "frame_%03d.png"),
                "-vf",
                f"fps={fps},format=yuv420p",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(output),
            ],
            check=True,
            capture_output=True,
        )
    return output


def _body_text(target: dict[str, Any], artifact_plan: dict[str, Any], slide: dict[str, Any] | None) -> str:
    if slide:
        blocks = slide.get("text_blocks", [])
        if isinstance(blocks, list):
            return " ".join(str(block).strip() for block in blocks if str(block).strip())
    beats = target.get("beats", [])
    if isinstance(beats, list):
        texts = [str(beat.get("text", beat.get("label", ""))).strip() for beat in beats if isinstance(beat, dict)]
        texts = [text for text in texts if text]
        if texts:
            return " ".join(texts[:2])
    return str(artifact_plan.get("story_atoms", {}).get("thesis", "Invisible Architecture"))


def _load_style_pack(artifact_plan: dict[str, Any]) -> dict[str, Any]:
    pack_ids = artifact_plan.get("style_pack_ids", [])
    if not isinstance(pack_ids, list) or not pack_ids:
        return {}
    pack_path = ROOT / "contracts" / "references" / f"{pack_ids[0]}.yaml"
    if not pack_path.exists():
        return {}
    try:
        import yaml

        with open(pack_path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: tuple[int, int, int],
    box: tuple[int, int, int, int],
    line_gap: int,
) -> None:
    words = [word for word in str(text).split() if word]
    if not words:
        return
    lines: list[str] = []
    current = words[0]
    max_width = box[2] - box[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        width = draw.textbbox((0, 0), trial, font=font)[2]
        if width > max_width:
            lines.append(current)
            current = word
        else:
            current = trial
    lines.append(current)

    y = box[1]
    for line in lines:
        draw.text((box[0], y), line, fill=fill, font=font)
        bbox = draw.textbbox((box[0], y), line, font=font)
        y = bbox[3] + line_gap
        if y > box[3]:
            break


def _vertical_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGB", size, top)
    draw = ImageDraw.Draw(image)
    width, height = size
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(int(top[index] + (bottom[index] - top[index]) * ratio) for index in range(3))
        draw.line((0, y, width, y), fill=color)
    return image


def _add_texture(image: Image.Image) -> Image.Image:
    overlay = Image.effect_noise(image.size, 12).convert("L").filter(ImageFilter.GaussianBlur(radius=0.4))
    texture = Image.new("RGBA", image.size, (255, 255, 255, 0))
    texture.putalpha(overlay.point(lambda value: min(26, int(value * 0.18))))
    return Image.alpha_composite(image.convert("RGBA"), texture).convert("RGB")


def _hex(value: str) -> tuple[int, int, int]:
    text = str(value or "").strip().lstrip("#")
    if len(text) == 6:
        return tuple(int(text[index:index + 2], 16) for index in (0, 2, 4))
    return (5, 5, 5)


def _hex_from_rgba_like(value: str, fallback: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    text = str(value or "").strip()
    if text.startswith("rgba(") and text.endswith(")"):
        parts = [part.strip() for part in text[5:-1].split(",")]
        if len(parts) == 4:
            try:
                r, g, b = (int(float(parts[index])) for index in range(3))
                a = int(float(parts[3]) * 255) if float(parts[3]) <= 1 else int(float(parts[3]))
                return (r, g, b, a)
            except Exception:
                return fallback
    return (*_hex(text), fallback[3])
