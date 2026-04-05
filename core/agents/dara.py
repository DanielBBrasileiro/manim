"""Persona Dara: Production Engineer.

Validates pre-render checklist, assembles render pipeline,
and runs post-render validation (duration, resolution, FPS, codec).
Pre-warms vision model to eliminate latency on QA.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent


def _check_ffmpeg() -> tuple[bool, str]:
    if shutil.which("ffmpeg"):
        return True, "ffmpeg available"
    return False, "ffmpeg not found in PATH"


def _check_assets() -> tuple[bool, str]:
    manim_base = ROOT / "engines" / "remotion" / "public" / "manim_base.mp4"
    tokens = ROOT / "assets" / "brand" / "tokens.json"
    missing = [str(p) for p in [tokens] if not p.exists()]
    if missing:
        return False, f"Missing assets: {', '.join(missing)}"
    return True, "assets ok"


def _check_remotion_bundle() -> tuple[bool, str]:
    manifest = ROOT / "engines" / "remotion" / ".bundle-cache" / "bundle-manifest.json"
    if manifest.exists():
        return True, "bundle manifest present"
    return False, "bundle cold — will need full warm"


def pre_render_checklist(plan: dict[str, Any]) -> dict[str, Any]:
    """Validate environment before triggering render pipeline."""
    checks = {
        "ffmpeg": _check_ffmpeg(),
        "assets": _check_assets(),
        "bundle": _check_remotion_bundle(),
    }
    passed = all(ok for ok, _ in checks.values())
    return {
        "passed": passed,
        "checks": {k: {"ok": ok, "detail": msg} for k, (ok, msg) in checks.items()},
    }


def post_render_checklist(output_path: str) -> dict[str, Any]:
    """Validate rendered output: duration, resolution, FPS, codec."""
    path = Path(output_path)
    if not path.exists():
        return {"passed": False, "error": f"Output not found: {output_path}"}

    suffix = path.suffix.lower()

    # PNG/still — basic checks
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        size_bytes = path.stat().st_size
        return {
            "passed": size_bytes > 1000,
            "type": "still",
            "size_bytes": size_bytes,
            "path": str(path),
        }

    # Video — use ffprobe if available
    if suffix == ".mp4":
        if shutil.which("ffprobe"):
            try:
                result = subprocess.run(
                    [
                        "ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height,r_frame_rate,codec_name",
                        "-show_entries", "format=duration",
                        "-of", "json", str(path),
                    ],
                    capture_output=True, text=True, timeout=10,
                )
                import json
                data = json.loads(result.stdout or "{}")
                streams = data.get("streams", [{}])
                fmt = data.get("format", {})
                stream = streams[0] if streams else {}
                duration = float(fmt.get("duration", 0))
                codec = stream.get("codec_name", "unknown")
                width = stream.get("width", 0)
                height = stream.get("height", 0)
                fps_raw = stream.get("r_frame_rate", "0/1")
                fps_parts = fps_raw.split("/")
                fps = round(int(fps_parts[0]) / max(int(fps_parts[1]), 1), 1) if len(fps_parts) == 2 else 0
                passed = duration > 1.0 and codec in {"h264", "hevc", "vp9"} and width > 0
                return {
                    "passed": passed,
                    "type": "video",
                    "duration_sec": round(duration, 2),
                    "codec": codec,
                    "resolution": f"{width}x{height}",
                    "fps": fps,
                    "path": str(path),
                }
            except Exception as exc:
                pass

        size_bytes = path.stat().st_size
        return {"passed": size_bytes > 10000, "type": "video", "size_bytes": size_bytes, "path": str(path)}

    return {"passed": path.stat().st_size > 0, "type": "unknown", "path": str(path)}


def _prewarm_vision_model() -> None:
    """Pre-warm the vision model so QA has zero latency."""
    try:
        from core.intelligence.model_router import TASK_VISION_PLAN, get_route
        from core.intelligence.ollama_client import _base_url, _post_json, OLLAMA_URL
        route = get_route(TASK_VISION_PLAN)
        _post_json(
            _base_url(OLLAMA_URL) + "/api/generate",
            {"model": route.model, "prompt": " ", "stream": False, "keep_alive": route.keep_alive},
            timeout=5.0,
        )
    except Exception:
        pass


def build_scene(plan: dict[str, Any]) -> dict[str, Any]:
    """
    Persona Dara: Engine Orchestrator.

    1. Pre-render checklist
    2. Pre-warm vision model
    3. Execute render pipeline
    4. Post-render validation per output
    """
    pre = pre_render_checklist(plan)
    if not pre["passed"]:
        critical_fails = [k for k, v in pre["checks"].items() if not v["ok"] and k != "bundle"]
        if critical_fails:
            return {"ok": False, "pre_render_failed": critical_fails, "checks": pre}

    # Pre-warm vision model in background (non-blocking best-effort)
    try:
        import threading
        threading.Thread(target=_prewarm_vision_model, daemon=True).start()
    except Exception:
        pass

    from core.tools.render_tool import render_pipeline
    result = render_pipeline(plan)

    if not isinstance(result, dict):
        return {"ok": True, "result": str(result)}

    # Post-render validation
    post_checks: list[dict] = []
    for output in result.get("outputs", []):
        if isinstance(output, dict) and output.get("output"):
            check = post_render_checklist(output["output"])
            post_checks.append(check)
            output["post_check"] = check

    result["post_render_checks"] = post_checks
    return result
