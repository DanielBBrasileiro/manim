"""
preview_adapter.py — AIOXTool wrapper for the existing preview_tool.

Bridges the existing preview_tool to the new Agentic Runtime,
making it discoverable via the ToolRegistry.
"""

from __future__ import annotations

from typing import Any

from core.harness.tool_base import AIOXTool, PermissionLevel


class PreviewTool(AIOXTool):
    """Generate a fast visual preview from a creative seed or plan."""

    name = "preview"
    description = (
        "Generates a fast wireframe preview (PNG/SVG/ASCII) from a creative "
        "seed text or an existing plan dictionary. No heavy render needed."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "seed": {
                "type": "string",
                "description": "Creative seed text to preview",
            },
            "output_path": {
                "type": "string",
                "description": "Optional output path for the preview file",
            },
            "format": {
                "type": "string",
                "enum": ["png", "svg", "ascii"],
                "description": "Output format (default: png)",
            },
        },
    }
    permission_level = PermissionLevel.READ
    keywords = ("preview", "wireframe", "visualizar", "rascunho", "sketch")
    when_to_use = "When the user wants a quick preview of an idea without full rendering"

    async def _execute(self, params: dict[str, Any]) -> Any:
        from core.tools.preview_tool import (
            generate_ascii_preview,
            generate_preview,
            generate_preview_from_seed,
        )

        seed = params.get("seed") or params.get("prompt", "")
        output_path = params.get("output_path")
        fmt = params.get("format", "png")

        if fmt == "ascii":
            from core.compiler.creative_compiler import compile_seed
            from core.intelligence.model_router import TASK_FAST_PLAN

            result = compile_seed(seed, task_type=TASK_FAST_PLAN)
            ascii_output = generate_ascii_preview(result["creative_plan"])
            return {"format": "ascii", "preview": ascii_output}

        path = generate_preview_from_seed(seed, output_path=output_path)
        return {"format": fmt, "path": path}


class RenderTool(AIOXTool):
    """Execute the full render pipeline for a creative plan."""

    name = "render"
    description = (
        "Executes the complete Manim → Remotion render pipeline. "
        "Takes a compiled plan and produces the final video/still artifacts."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "briefing_path": {
                "type": "string",
                "description": "Path to the briefing YAML file",
            },
        },
    }
    permission_level = PermissionLevel.WRITE
    keywords = ("render", "renderizar", "video", "produzir", "gerar", "build")
    when_to_use = "When the user wants to render a final video or image from a briefing"

    async def _execute(self, params: dict[str, Any]) -> Any:
        from core.tools.render_tool import render_pipeline

        briefing_path = params.get("briefing_path")
        if not briefing_path:
            return {"error": "briefing_path is required"}

        import yaml
        from pathlib import Path

        path = Path(briefing_path)
        if not path.exists():
            return {"error": f"Briefing not found: {briefing_path}"}

        with open(path) as f:
            brief = yaml.safe_load(f)

        from core.compiler.creative_compiler import compile_seed
        seed = brief.get("creative_seed", str(brief))
        result = compile_seed(seed)
        plan = result["creative_plan"]

        output = render_pipeline(plan, briefing=brief)
        return output


class BrandSyncTool(AIOXTool):
    """Synchronize brand identity tokens across engines."""

    name = "brand_sync"
    description = (
        "Syncs the visual identity (colors, typography, motion presets) "
        "across Manim theme and Remotion theme files."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "identity": {
                "type": "string",
                "description": "Identity name to sync (default: aiox_default)",
            },
        },
    }
    permission_level = PermissionLevel.WRITE
    keywords = ("sync", "brand", "identidade", "theme", "tokens", "sincronizar")
    when_to_use = "When the user wants to update brand tokens or sync visual identity"

    async def _execute(self, params: dict[str, Any]) -> Any:
        import subprocess
        from pathlib import Path

        identity = params.get("identity", "aiox_default")
        root = Path(__file__).resolve().parent.parent.parent
        result = subprocess.run(
            ["python3", "core/cli/brand.py", identity],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {
            "identity": identity,
            "success": result.returncode == 0,
            "stdout": result.stdout[:500] if result.stdout else "",
            "stderr": result.stderr[:500] if result.stderr else "",
        }


class ScenePlanTool(AIOXTool):
    """Generate a creative plan from a text seed."""

    name = "scene_plan"
    description = (
        "Compiles a text seed into a creative plan with archetype, "
        "motion signature, timeline, and entropy analysis."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "seed": {
                "type": "string",
                "description": "Creative seed text to plan",
            },
            "quality": {
                "type": "string",
                "enum": ["fast", "standard", "quality"],
                "description": "Planning quality level",
            },
        },
        "required": ["seed"],
    }
    permission_level = PermissionLevel.READ
    keywords = ("plan", "planejar", "ideia", "conceito", "criar", "cena", "scene")
    when_to_use = "When the user describes a creative idea and needs a structured plan"

    async def _execute(self, params: dict[str, Any]) -> Any:
        from core.compiler.creative_compiler import compile_seed
        from core.intelligence.model_router import TASK_FAST_PLAN, TASK_PLAN, TASK_QUALITY_PLAN

        seed = params.get("seed") or params.get("prompt", "")
        quality = params.get("quality", "fast")
        task_map = {
            "fast": TASK_FAST_PLAN,
            "standard": TASK_PLAN,
            "quality": TASK_QUALITY_PLAN,
        }
        task_type = task_map.get(quality, TASK_FAST_PLAN)

        result = compile_seed(seed, task_type=task_type)
        plan = result.get("creative_plan", {})
        return {
            "archetype": plan.get("archetype"),
            "motion_signature": plan.get("interpretation", {}).get("motion_signature"),
            "regime": plan.get("interpretation", {}).get("regime"),
            "entropy": plan.get("entropy"),
            "timeline_phases": len(plan.get("timeline", [])),
            "has_llm_plan": bool(plan.get("llm_scene_plan")),
        }


class MemoryQueryTool(AIOXTool):
    """Query the creative memory for past sessions and patterns."""

    name = "memory_query"
    description = (
        "Searches the creative memory store for past sessions, "
        "patterns, and previously generated plans."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query for memory entries",
            },
            "limit": {
                "type": "integer",
                "description": "Max results to return (default: 5)",
            },
        },
    }
    permission_level = PermissionLevel.READ
    keywords = ("memory", "memoria", "historico", "passado", "session", "sessao")
    when_to_use = "When the user wants to find past sessions or creative patterns"

    async def _execute(self, params: dict[str, Any]) -> Any:
        from core.memory.session_store import list_sessions

        limit = params.get("limit", 5)
        sessions = list_sessions()[:limit]

        return {
            "total_sessions": len(list_sessions()),
            "results": [
                {
                    "session_id": s.get("session_id"),
                    "input": s.get("input", "")[:100],
                    "status": s.get("status"),
                    "archetype": (s.get("creative_plan") or {}).get("archetype"),
                    "created_at": s.get("created_at"),
                }
                for s in sessions
            ],
        }


class StoryboardTool(AIOXTool):
    """Generate a storyboard breakdown from a plan."""

    name = "storyboard"
    description = (
        "Generates a storyboard breakdown with act structure, "
        "timing, and visual primitives from a creative plan."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "seed": {
                "type": "string",
                "description": "Creative seed for storyboard generation",
            },
        },
        "required": ["seed"],
    }
    permission_level = PermissionLevel.READ
    keywords = ("storyboard", "timeline", "acts", "atos", "narrativa", "historia")
    when_to_use = "When the user wants a storyboard breakdown of a creative idea"

    async def _execute(self, params: dict[str, Any]) -> Any:
        from core.tools.storyboard_tool import generate_storyboard

        seed = params.get("seed") or params.get("prompt", "")
        return generate_storyboard(seed)
