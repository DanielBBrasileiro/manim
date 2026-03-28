"""
AIOX Studio — Carousel Generator
==================================
Gera carrosséis de imagens para Instagram e LinkedIn.
Aceita: frame sequence de PNG, ou timestamps de um MP4.

Usage standalone:
    python3 core/generators/carousel_generator.py --frames output/frames/ --platform instagram
    python3 core/generators/carousel_generator.py --video output/renders/Main.mp4 --timestamps 0 3 6 9

Uso via orchestrator: chamado quando output.formats inclui "carousel".
"""
import json
import os
from pathlib import Path

# Specs por plataforma (alinhado com contracts/layout.yaml)
PLATFORM_SPECS = {
    "instagram": {
        "width": 1080, "height": 1080,
        "max_frames": 10,
        "format": "jpeg", "quality": 92,
    },
    "instagram_portrait": {
        "width": 1080, "height": 1350,
        "max_frames": 10,
        "format": "jpeg", "quality": 92,
    },
    "linkedin": {
        "width": 1200, "height": 627,
        "max_frames": 9,
        "format": "jpeg", "quality": 90,
    },
}


def _require_pillow():
    try:
        from PIL import Image
        return Image
    except ImportError:
        raise ImportError(
            "Pillow não instalado. Execute: pip install Pillow"
        )


def _fit_and_crop(img, target_w: int, target_h: int):
    """Redimensiona e corta para preencher o target exato (cover)."""
    Image = _require_pillow()
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def _add_frame_number(img, index: int, total: int, spec: dict):
    """Adiciona numeração discreta no canto inferior direito."""
    try:
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        text = f"{index}/{total}"
        w, h = spec["width"], spec["height"]
        margin = int(w * 0.04)
        # Fallback sem font file
        draw.text(
            (w - margin, h - margin),
            text,
            fill=(255, 255, 255, 100),
            anchor="rb"
        )
    except Exception:
        pass  # Numeração é opcional
    return img


def generate_carousel(
    source_frames: list,
    output_dir: str,
    platform: str = "instagram",
    add_numbers: bool = False,
) -> dict:
    """
    Gera um carrossel a partir de uma lista de caminhos de imagens.

    Args:
        source_frames: Lista de paths de imagens (PNG/JPG).
        output_dir:    Diretório de saída.
        platform:      "instagram" | "instagram_portrait" | "linkedin"
        add_numbers:   Adicionar "1/N" em cada frame.

    Returns:
        dict com: frames (lista de paths), manifest_path, platform, count
    """
    Image = _require_pillow()
    spec = PLATFORM_SPECS.get(platform, PLATFORM_SPECS["instagram"])
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    max_frames = spec["max_frames"]
    frames_to_process = source_frames[:max_frames]
    total = len(frames_to_process)

    generated = []
    for i, src_path in enumerate(frames_to_process, start=1):
        img = Image.open(src_path).convert("RGB")
        img = _fit_and_crop(img, spec["width"], spec["height"])

        if add_numbers:
            img = _add_frame_number(img, i, total, spec)

        out_name = f"slide_{i:02d}.{spec['format']}"
        out_path = out_dir / out_name
        save_kwargs = {"quality": spec["quality"]} if spec["format"] == "jpeg" else {}
        img.save(str(out_path), **save_kwargs)
        generated.append(str(out_path))
        print(f"  🖼️  Slide {i}/{total} → {out_name}")

    manifest = {
        "platform": platform,
        "dimensions": f"{spec['width']}x{spec['height']}",
        "frame_count": total,
        "format": spec["format"],
        "quality": spec.get("quality"),
        "slides": [str(Path(p).name) for p in generated],
    }
    manifest_path = out_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"✅ Carrossel {platform} → {out_dir} ({total} slides)")
    print(f"   Manifest → {manifest_path}")
    return {"frames": generated, "manifest_path": str(manifest_path), **manifest}


def carousel_from_video(
    input_mp4: str,
    timestamps: list,
    output_dir: str,
    platform: str = "instagram",
) -> dict:
    """
    Gera carrossel extraindo frames de um MP4 nos timestamps dados.
    Combina gif_generator.extract_frames + generate_carousel.
    """
    from core.generators.gif_generator import extract_frames

    frames_dir = Path(output_dir) / "raw_frames"
    print(f"📹 Extraindo {len(timestamps)} frames do vídeo...")
    frame_paths = extract_frames(input_mp4, timestamps, str(frames_dir))

    if not frame_paths:
        print("❌ Nenhum frame extraído.")
        return {}

    return generate_carousel(frame_paths, output_dir, platform=platform)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AIOX Carousel Generator")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--frames", help="Diretório com PNGs/JPGs")
    group.add_argument("--video", help="MP4 para extrair frames")
    parser.add_argument("--timestamps", nargs="+", type=float, default=[0, 3, 5, 8, 11, 14])
    parser.add_argument("--output", default="output/carousel", help="Diretório de saída")
    parser.add_argument("--platform", choices=list(PLATFORM_SPECS.keys()), default="instagram")
    parser.add_argument("--numbers", action="store_true", help="Adicionar numeração 1/N")
    args = parser.parse_args()

    if args.frames:
        frames_dir = Path(args.frames)
        exts = {".png", ".jpg", ".jpeg", ".webp"}
        frames = sorted([str(p) for p in frames_dir.iterdir() if p.suffix.lower() in exts])
        if not frames:
            print(f"❌ Nenhuma imagem encontrada em {args.frames}")
        else:
            generate_carousel(frames, args.output, platform=args.platform, add_numbers=args.numbers)
    else:
        carousel_from_video(args.video, args.timestamps, args.output, platform=args.platform)
