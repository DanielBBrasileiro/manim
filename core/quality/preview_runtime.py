from __future__ import annotations

from pathlib import Path
from typing import Any

from core.tools.preview_tool import generate_preview


def build_preview_bundle(
    plan: dict[str, Any],
    artifact_plan: dict[str, Any],
    *,
    output_path: str | None = None,
) -> dict[str, Any]:
    preview_path = generate_preview(plan, output_path=output_path)
    targets = []

    for target in artifact_plan.get("targets", []):
        if not isinstance(target, dict):
            continue
        render_mode = str(target.get("render_mode", "still")).strip().lower()
        duration_sec = float(target.get("duration_sec", plan.get("duration", 12)) or 12.0)
        fps = int(target.get("fps", 30) or 30)
        preview_duration = 0.0 if render_mode in {"still", "carousel"} else min(duration_sec, 4.0)
        preview_fps = 1 if render_mode in {"still", "carousel"} else min(fps, 12)
        targets.append(
            {
                "target_id": str(target.get("id", "")).strip(),
                "render_mode": render_mode,
                "preview_mode": "still_preview" if render_mode in {"still", "carousel"} else "motion_preview",
                "preview_asset": preview_path,
                "preview_duration_sec": preview_duration,
                "preview_fps": preview_fps,
                "simplified": True,
                "keyframes": list(target.get("poster_test_frames", []) or target.get("qa_sampling_frames", [])[:3]),
            }
        )

    return {
        "preview_path": preview_path,
        "preview_exists": Path(preview_path).exists(),
        "targets": targets,
        "preview_policy": dict(artifact_plan.get("preview_policy", {})),
    }
