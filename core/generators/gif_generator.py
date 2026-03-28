"""
AIOX Studio — GIF Generator
============================
Converte MP4 em GIF otimizado via dois passes de ffmpeg + gifsicle.

Usage standalone:
    python3 core/generators/gif_generator.py --input output/renders/Main.mp4 --fps 12

Uso via orchestrator: chamado automaticamente quando output.formats inclui "gif".
"""
import subprocess
import os
import shutil
from pathlib import Path


def _check_deps():
    missing = []
    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg (brew install ffmpeg)")
    if not shutil.which("gifsicle"):
        missing.append("gifsicle (brew install gifsicle)")
    if missing:
        print(f"⚠️  Dependências ausentes: {', '.join(missing)}")
        return False
    return True


def encode_gif(
    input_mp4: str,
    output_gif: str,
    fps: int = 12,
    width: int = 1080,
    loop: int = 0,
    optimize: bool = True,
) -> bool:
    """
    Gera GIF otimizado com dois passes de paleta.

    Args:
        input_mp4:  Caminho do vídeo fonte.
        output_gif: Caminho de saída do GIF.
        fps:        Frames por segundo (10-15 recomendado para social).
        width:      Largura em pixels (-1 mantém proporção).
        loop:       0 = loop infinito, 1 = sem loop.
        optimize:   Aplica gifsicle --optimize=3 após geração.
    Returns:
        True se sucesso, False se falha.
    """
    if not _check_deps():
        return False

    input_path = Path(input_mp4)
    output_path = Path(output_gif)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    palette_path = output_path.parent / f"{output_path.stem}_palette.png"
    vf_scale = f"fps={fps},scale={width}:-1:flags=lanczos"

    print(f"🎨 GIF Passe 1: Gerando paleta otimizada...")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(input_path),
             "-vf", f"{vf_scale},palettegen=max_colors=256:stats_mode=diff",
             str(palette_path)],
            check=True, capture_output=True
        )

        print(f"🎬 GIF Passe 2: Codificando com paleta...")
        subprocess.run(
            ["ffmpeg", "-y",
             "-i", str(input_path),
             "-i", str(palette_path),
             "-lavfi", f"{vf_scale}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5",
             "-loop", str(loop),
             str(output_path)],
            check=True, capture_output=True
        )

        palette_path.unlink(missing_ok=True)

        if optimize and shutil.which("gifsicle"):
            print(f"🗜️  GIF Otimizando com gifsicle...")
            subprocess.run(
                ["gifsicle", "--optimize=3", "--colors=256",
                 "-o", str(output_path), str(output_path)],
                check=True, capture_output=True
            )

        size_kb = output_path.stat().st_size // 1024
        print(f"✅ GIF gerado → {output_path} ({size_kb}KB)")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ GIF falhou: {e.stderr.decode() if e.stderr else e}")
        palette_path.unlink(missing_ok=True)
        return False


def encode_webm(input_mp4: str, output_webm: str, bitrate: str = "1200k") -> bool:
    """
    Converte MP4 em WebM VP9 (2 passes para melhor compressão).
    ~40% menor que H.264 com qualidade equivalente.
    """
    if not shutil.which("ffmpeg"):
        print("⚠️  ffmpeg não encontrado.")
        return False

    output_path = Path(output_webm)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = str(output_path.parent / "ffmpeg2pass")

    print(f"🎬 WebM Passe 1: análise de bitrate...")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_mp4,
             "-c:v", "libvpx-vp9", "-b:v", bitrate,
             "-pass", "1", "-an", "-f", "null", "/dev/null",
             "-passlogfile", log_file],
            check=True, capture_output=True
        )

        print(f"🎬 WebM Passe 2: codificando VP9...")
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_mp4,
             "-c:v", "libvpx-vp9", "-b:v", bitrate,
             "-pass", "2", "-c:a", "libopus",
             "-passlogfile", log_file,
             str(output_path)],
            check=True, capture_output=True
        )

        for ext in ["-0.log", "-0.log.mbtree"]:
            Path(log_file + ext).unlink(missing_ok=True)

        size_kb = output_path.stat().st_size // 1024
        print(f"✅ WebM gerado → {output_path} ({size_kb}KB)")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ WebM falhou: {e.stderr.decode() if e.stderr else e}")
        return False


def extract_frames(
    input_mp4: str,
    timestamps: list,
    output_dir: str,
    fmt: str = "png",
    width: int = 1080,
) -> list:
    """
    Extrai frames PNG/WebP em timestamps específicos (em segundos).

    Returns:
        Lista de caminhos dos frames gerados.
    """
    if not shutil.which("ffmpeg"):
        print("⚠️  ffmpeg não encontrado.")
        return []

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    generated = []

    stem = Path(input_mp4).stem
    for ts in timestamps:
        out_path = out_dir / f"{stem}_{ts}s.{fmt}"
        try:
            cmd = ["ffmpeg", "-y", "-ss", str(ts), "-i", input_mp4,
                   "-vf", f"scale={width}:-1", "-frames:v", "1"]
            if fmt == "webp":
                cmd += ["-q:v", "85"]
            cmd.append(str(out_path))
            subprocess.run(cmd, check=True, capture_output=True)
            generated.append(str(out_path))
            print(f"  📸 Frame {ts}s → {out_path.name}")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Frame {ts}s falhou: {e}")

    print(f"✅ {len(generated)}/{len(timestamps)} frames extraídos → {out_dir}")
    return generated


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AIOX GIF/WebM/Frame Generator")
    parser.add_argument("--input", required=True, help="MP4 de entrada")
    parser.add_argument("--output", help="Arquivo de saída (inferido se omitido)")
    parser.add_argument("--format", choices=["gif", "webm", "frames"], default="gif")
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--timestamps", nargs="+", type=float, default=[0, 3, 6, 9, 12],
                        help="Timestamps para extração de frames")
    args = parser.parse_args()

    input_path = Path(args.input)
    if args.format == "gif":
        out = args.output or str(input_path.with_suffix(".gif"))
        encode_gif(args.input, out, fps=args.fps, width=args.width)
    elif args.format == "webm":
        out = args.output or str(input_path.with_suffix(".webm"))
        encode_webm(args.input, out)
    elif args.format == "frames":
        out_dir = args.output or str(input_path.parent / "frames")
        extract_frames(args.input, args.timestamps, out_dir)
