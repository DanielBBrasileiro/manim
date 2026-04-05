#!/usr/bin/env python3
"""
server.py — AIOX Studio MCP Server (v5.0)

Exposes the full AIOX v5.0 creative OS as an MCP (Model Context Protocol)
server that any MCP client (Claude Desktop, Cursor, VS Code, etc.) can
invoke via stdio.

Tools exposed:
  1. coordinate     — Multi-agent creative pipeline (Phase 3)
  2. score_frame    — Vision-LLM quality gate (Phase 4)
  3. auto_iterate   — Self-correcting render loop (Phase 4)
  4. compile_seed   — Creative seed → plan compiler
  5. render_still   — Remotion composition → PNG
  6. doctor         — System health diagnostics
  7. list_tools     — Harness tool discovery
  8. list_workers   — Coordinator worker listing
  9. turbo_status   — TurboQuant server health (Phase 2)
  10. memory_query  — Creative memory search

Resources:
  - aiox://profile   — Active model profile
  - aiox://workers   — Available coordinator workers
  - aiox://laws      — Brand global laws (contracts/global_laws.yaml)

Usage:
  claude mcp add aiox-studio -- python3 /path/to/manim/core/mcp/server.py

  Or in .mcp.json:
  {
    "mcpServers": {
      "aiox-studio": {
        "command": "python3",
        "args": ["/path/to/manim/core/mcp/server.py"]
      }
    }
  }

WARNING: In STDIO mode, NEVER write to stdout except via _write_message().
         All logging must go to stderr.
"""
from __future__ import annotations

import asyncio
import json
import sys
import traceback
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path setup — ensure the repo root is on sys.path
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from core.env_loader import load_repo_env

load_repo_env()


# ---------------------------------------------------------------------------
# Logging (stderr only — stdout is the MCP wire)
# ---------------------------------------------------------------------------

def _log(msg: str) -> None:
    print(f"[aiox-mcp] {msg}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Tool definitions (MCP schema)
# ---------------------------------------------------------------------------

TOOLS: list[dict[str, Any]] = [
    {
        "name": "coordinate",
        "description": (
            "Run the AIOX multi-agent creative coordinator. "
            "Spawns 5 workers (Aria, Zara, Kael, Uma, Dara) in parallel "
            "to interpret, plan, review, and optionally build a creative production."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "description": "Creative intent / prompt to coordinate",
                },
                "briefing_path": {
                    "type": "string",
                    "description": "Optional path to a briefing YAML (activates render)",
                },
            },
            "required": ["intent"],
        },
    },
    {
        "name": "score_frame",
        "description": (
            "Score a rendered frame using the Vision-LLM quality gate. "
            "Evaluates composition, typography, color, motion, and brand compliance. "
            "Returns per-dimension scores (0-100) and a composite pass/fail."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "frame_path": {
                    "type": "string",
                    "description": "Absolute path to the frame (PNG/JPG/WEBP)",
                },
                "threshold": {
                    "type": "number",
                    "description": "Minimum composite score to pass (default: 70)",
                },
            },
            "required": ["frame_path"],
        },
    },
    {
        "name": "auto_iterate",
        "description": (
            "Run the self-correcting render loop. Scores a frame, extracts "
            "corrections, and iterates up to max_iterations times."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "frame_path": {
                    "type": "string",
                    "description": "Absolute path to the initial frame",
                },
                "threshold": {
                    "type": "number",
                    "description": "Minimum composite score to pass (default: 70)",
                },
                "max_iterations": {
                    "type": "integer",
                    "description": "Max correction cycles (default: 3)",
                },
            },
            "required": ["frame_path"],
        },
    },
    {
        "name": "compile_seed",
        "description": (
            "Compile a creative seed phrase into a structured AIOX plan "
            "with archetype, motion signature, entropy, and timeline."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "seed": {
                    "type": "string",
                    "description": "Creative seed text to compile",
                },
                "quality": {
                    "type": "string",
                    "enum": ["fast", "standard", "quality"],
                    "description": "Planning quality level (default: fast)",
                },
            },
            "required": ["seed"],
        },
    },
    {
        "name": "render_still",
        "description": "Render a Remotion composition as a PNG still image.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "composition": {
                    "type": "string",
                    "description": "Composition ID (e.g. linkedin-feed-4-5)",
                },
                "output_path": {
                    "type": "string",
                    "description": "Output path for the PNG (default: output/stills/<comp>.png)",
                },
                "props": {
                    "type": "object",
                    "description": "Input props JSON for the composition",
                },
            },
            "required": ["composition"],
        },
    },
    {
        "name": "doctor",
        "description": (
            "Run AIOX system diagnostics. Returns health status for "
            "Ollama, TurboQuant, Remotion, Manim, bundle, and models."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "warm": {
                    "type": "boolean",
                    "description": "Trigger background bundle warm if cold (default: false)",
                },
            },
        },
    },
    {
        "name": "list_tools",
        "description": "List all tools registered in the AIOX harness with their schemas.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "list_workers",
        "description": "List all creative workers available in the coordinator.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "turbo_status",
        "description": (
            "Check TurboQuant llama-server health. Reports install status, "
            "KV cache type, context length, and whether the server is running."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "memory_query",
        "description": "Search the creative memory store for past sessions and patterns.",
        "inputSchema": {
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
        },
    },
]


# ---------------------------------------------------------------------------
# Resource definitions
# ---------------------------------------------------------------------------

RESOURCES: list[dict[str, Any]] = [
    {
        "uri": "aiox://profile",
        "name": "Active Model Profile",
        "description": "Current AIOX model profile configuration",
        "mimeType": "application/json",
    },
    {
        "uri": "aiox://workers",
        "name": "Available Workers",
        "description": "Creative workers registered in the coordinator",
        "mimeType": "application/json",
    },
    {
        "uri": "aiox://laws",
        "name": "Brand Global Laws",
        "description": "AIOX brand constraints from contracts/global_laws.yaml",
        "mimeType": "application/x-yaml",
    },
]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

def _handle_coordinate(args: dict) -> str:
    intent = str(args.get("intent", "")).strip()
    if not intent:
        return json.dumps({"error": "intent is required"})

    context: dict[str, Any] = {}
    bp = args.get("briefing_path")
    if bp:
        context["briefing_path"] = bp

    from core.coordinator.coordinator import CreativeCoordinator

    coordinator = CreativeCoordinator(context=context)
    report = asyncio.run(coordinator.run(intent))
    return json.dumps(report.to_dict(), ensure_ascii=False, default=str)


def _handle_score_frame(args: dict) -> str:
    frame_path = str(args.get("frame_path", "")).strip()
    if not frame_path:
        return json.dumps({"error": "frame_path is required"})

    threshold = float(args.get("threshold", 70.0))

    from core.quality.frame_scorer import score_frame

    result = score_frame(frame_path, threshold=threshold)
    return json.dumps(result.to_dict(), ensure_ascii=False, default=str)


def _handle_auto_iterate(args: dict) -> str:
    frame_path = str(args.get("frame_path", "")).strip()
    if not frame_path:
        return json.dumps({"error": "frame_path is required"})

    from core.quality.auto_iterate import auto_iterate

    report = auto_iterate(
        frame_path,
        threshold=float(args.get("threshold", 70.0)),
        max_iterations=int(args.get("max_iterations", 3)),
    )
    return json.dumps(report.to_dict(), ensure_ascii=False, default=str)


def _handle_compile_seed(args: dict) -> str:
    seed = str(args.get("seed", "")).strip()
    if not seed:
        return json.dumps({"error": "seed is required"})

    quality = args.get("quality", "fast")

    from core.compiler.creative_compiler import compile_seed
    from core.intelligence.model_router import TASK_FAST_PLAN, TASK_PLAN, TASK_QUALITY_PLAN

    task_map = {"fast": TASK_FAST_PLAN, "standard": TASK_PLAN, "quality": TASK_QUALITY_PLAN}
    task_type = task_map.get(quality, TASK_FAST_PLAN)

    result = compile_seed(seed, task_type=task_type)
    plan = result.get("creative_plan", {})
    return json.dumps({
        "archetype": plan.get("archetype"),
        "aesthetic_family": plan.get("aesthetic_family"),
        "motion_signature": plan.get("interpretation", {}).get("motion_signature"),
        "entropy": plan.get("entropy"),
        "pacing": plan.get("pacing"),
        "confidence": plan.get("confidence"),
    }, ensure_ascii=False, default=str)


def _handle_render_still(args: dict) -> str:
    composition = str(args.get("composition", "")).strip()
    if not composition:
        return json.dumps({"error": "composition is required"})

    from core.tools.render_tool import run_remotion_still

    raw_output = args.get("output_path")
    out = Path(raw_output) if raw_output else ROOT / "output" / "stills" / f"{composition}.png"
    props = args.get("props") or None

    try:
        result = run_remotion_still(composition, out, remotion_props=props)
        return json.dumps({"ok": True, "output": str(result), "size_bytes": result.stat().st_size})
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)})


def _handle_doctor(args: dict) -> str:
    warm = bool(args.get("warm", False))

    from core.cli.doctor import _trigger_background_warm, collect_doctor_report

    report = collect_doctor_report()
    if warm and report.get("checks", {}).get("remotion_cli", {}).get("ok"):
        _trigger_background_warm()
        report["bundle_warm_triggered"] = True
    return json.dumps(report, ensure_ascii=True, default=str)


def _handle_list_tools(args: dict) -> str:
    from core.harness.tool_registry import ToolRegistry

    registry = ToolRegistry()
    registry.autodiscover()
    tools = [
        {"name": t.name, "description": t.description, "keywords": list(getattr(t, "keywords", []))}
        for t in registry.list_tools()
    ]
    return json.dumps({"tools": tools, "count": len(tools)})


def _handle_list_workers(args: dict) -> str:
    from core.coordinator.workers import WORKERS

    workers = [
        {"name": name, "persona": w.persona}
        for name, w in WORKERS.items()
    ]
    return json.dumps({"workers": workers, "count": len(workers)})


def _handle_turbo_status(args: dict) -> str:
    from core.intelligence.ollama_client import check_turbo_health

    return json.dumps(check_turbo_health(), default=str)


def _handle_memory_query(args: dict) -> str:
    from core.memory.session_store import list_sessions

    limit = int(args.get("limit", 5))
    all_sessions = list_sessions()

    results = []
    for s in all_sessions[:limit]:
        results.append({
            "session_id": s.get("session_id"),
            "input": str(s.get("input", ""))[:100],
            "status": s.get("status"),
            "archetype": (s.get("creative_plan") or {}).get("archetype"),
            "created_at": s.get("created_at"),
        })

    return json.dumps({"total_sessions": len(all_sessions), "results": results}, default=str)


HANDLERS: dict[str, Any] = {
    "coordinate": _handle_coordinate,
    "score_frame": _handle_score_frame,
    "auto_iterate": _handle_auto_iterate,
    "compile_seed": _handle_compile_seed,
    "render_still": _handle_render_still,
    "doctor": _handle_doctor,
    "list_tools": _handle_list_tools,
    "list_workers": _handle_list_workers,
    "turbo_status": _handle_turbo_status,
    "memory_query": _handle_memory_query,
}


# ---------------------------------------------------------------------------
# Resource handlers
# ---------------------------------------------------------------------------

def _read_resource(uri: str) -> dict[str, Any]:
    if uri == "aiox://profile":
        from core.intelligence.model_profiles import get_active_profile
        profile = get_active_profile()
        content = json.dumps({
            "name": profile.name,
            "provider": profile.provider,
            "description": profile.description,
            "model_roles": profile.model_roles,
            "turbo_server_args": profile.turbo_server_args,
        }, indent=2)
        return {"uri": uri, "mimeType": "application/json", "text": content}

    if uri == "aiox://workers":
        from core.coordinator.workers import WORKERS
        content = json.dumps({
            name: {"persona": w.persona}
            for name, w in WORKERS.items()
        }, indent=2)
        return {"uri": uri, "mimeType": "application/json", "text": content}

    if uri == "aiox://laws":
        laws_path = ROOT / "contracts" / "global_laws.yaml"
        if laws_path.exists():
            content = laws_path.read_text(encoding="utf-8")
        else:
            content = "# global_laws.yaml not found"
        return {"uri": uri, "mimeType": "application/x-yaml", "text": content}

    return {"uri": uri, "mimeType": "text/plain", "text": f"Unknown resource: {uri}"}


# ---------------------------------------------------------------------------
# JSON-RPC / MCP wire protocol (Content-Length framed stdio)
# ---------------------------------------------------------------------------

def _read_message() -> dict | None:
    """Read a Content-Length framed JSON-RPC message from stdin."""
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        stripped = line.rstrip(b"\r\n")
        if not stripped:
            break
        if b":" in stripped:
            key, _, value = stripped.partition(b":")
            headers[key.strip().lower().decode()] = value.strip().decode()

    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None

    raw = sys.stdin.buffer.read(length)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _write_message(payload: dict) -> None:
    """Write a Content-Length framed JSON-RPC message to stdout."""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(header + body)
    sys.stdout.buffer.flush()


def _ok(req_id: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _dispatch(message: dict) -> dict | None:
    method = message.get("method", "")
    req_id = message.get("id")
    params = message.get("params") or {}

    # Notifications (no id) — do not reply
    if req_id is None:
        return None

    # ── Initialize ──
    if method == "initialize":
        return _ok(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {},
            },
            "serverInfo": {
                "name": "aiox-studio",
                "version": "5.0.0",
            },
        })

    # ── Tools ──
    if method == "tools/list":
        return _ok(req_id, {"tools": TOOLS})

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments") or {}
        handler = HANDLERS.get(tool_name)
        if handler is None:
            return _err(req_id, -32601, f"Unknown tool: {tool_name}")
        try:
            _log(f"tool call: {tool_name}")
            content = handler(tool_args)
            return _ok(req_id, {
                "content": [{"type": "text", "text": content}],
                "isError": False,
            })
        except Exception as exc:
            _log(f"tool error: {tool_name} → {exc}")
            tb = traceback.format_exc()
            return _ok(req_id, {
                "content": [{"type": "text", "text": json.dumps({"error": str(exc), "traceback": tb})}],
                "isError": True,
            })

    # ── Resources ──
    if method == "resources/list":
        return _ok(req_id, {"resources": RESOURCES})

    if method == "resources/read":
        uri = params.get("uri", "")
        try:
            resource = _read_resource(uri)
            return _ok(req_id, {"contents": [resource]})
        except Exception as exc:
            return _err(req_id, -32603, f"Resource read error: {exc}")

    return _err(req_id, -32601, f"Method not found: {method}")


# ---------------------------------------------------------------------------
# Server loop
# ---------------------------------------------------------------------------

def serve() -> None:
    """Main loop: read JSON-RPC messages from stdin, dispatch, reply."""
    _log("AIOX Studio MCP Server v5.0 starting...")
    _log(f"Root: {ROOT}")
    _log(f"Tools: {len(TOOLS)} | Resources: {len(RESOURCES)}")

    while True:
        message = _read_message()
        if message is None:
            break
        reply = _dispatch(message)
        if reply is not None:
            _write_message(reply)

    _log("Server stopped.")


if __name__ == "__main__":
    serve()
