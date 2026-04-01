"""
vision_qa_tool.py — AIOXTool adapter for the Vision QA quality gate.

Wraps frame_scorer and auto_iterate as a discoverable harness tool.
Supports:
- Single frame scoring
- Directory evaluation
- Auto-iterate with re-render callbacks
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.harness.tool_base import AIOXTool


class VisionQATool(AIOXTool):
    """Vision-LLM quality gate for rendered frames."""

    name = "vision_qa"
    description = (
        "Evaluate rendered frames for visual quality using Qwen3-VL vision model. "
        "Scores composition, typography, color, motion, and brand compliance. "
        "Can auto-iterate with corrections."
    )
    version = "1.0.0"
    keywords = [
        "quality", "qa", "vision", "score", "evaluate",
        "frame", "render", "check", "review", "audit",
        "composition", "typography", "brand", "compliance",
    ]
    permissions = ["vision_model", "filesystem_read"]

    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "frame_path": {
                    "type": "string",
                    "description": "Path to frame or directory to evaluate",
                },
                "threshold": {
                    "type": "number",
                    "default": 70.0,
                    "description": "Minimum score to pass (0-100)",
                },
                "mode": {
                    "type": "string",
                    "enum": ["score", "evaluate_dir", "auto_iterate"],
                    "default": "score",
                    "description": "Evaluation mode",
                },
                "max_iterations": {
                    "type": "integer",
                    "default": 3,
                    "description": "Max correction cycles (auto_iterate mode)",
                },
                "context": {
                    "type": "object",
                    "description": "Creative context (archetype, intent, etc.)",
                },
            },
            "required": ["frame_path"],
        }

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        frame_path = params.get("frame_path", "")
        threshold = float(params.get("threshold", 70.0))
        mode = params.get("mode", "score")
        context = params.get("context")

        if mode == "evaluate_dir":
            from core.quality.auto_iterate import evaluate_output
            return evaluate_output(
                frame_path,
                threshold=threshold,
                context=context,
            )

        elif mode == "auto_iterate":
            from core.quality.auto_iterate import auto_iterate
            max_iter = int(params.get("max_iterations", 3))
            report = auto_iterate(
                frame_path,
                threshold=threshold,
                max_iterations=max_iter,
                context=context,
            )
            return report.to_dict()

        else:  # mode == "score"
            from core.quality.frame_scorer import score_frame
            score = score_frame(
                frame_path,
                threshold=threshold,
                context=context,
            )
            return score.to_dict()
